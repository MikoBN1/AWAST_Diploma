import asyncio
import logging
import os
import tempfile
from datetime import datetime
from typing import Dict, Optional, Set

import httpx
import yaml
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.scan_model import Scan
from models.vulnerability_model import Vulnerability
from schemas.report_schema import Vulnerability as VulnerabilitySchema
from services.database_service import AsyncDatabaseService
from services.websocket_service import manager

logger = logging.getLogger(__name__)

_cancelled_scans: Set[str] = set()


def _dedupe_alerts_by_cwe(alerts: list[dict]) -> list[dict]:
    """
    Remove duplicates primarily by CWE (cweid/cve), falling back to
    alert+url+param as a secondary key when CWE info is missing.
    This keeps the first occurrence and drops the rest.
    """
    seen: set[str] = set()
    result: list[dict] = []

    for a in alerts:
        cweid = str(a.get("cweid") or "").strip()
        cve = (a.get("cve") or "").strip()

        if cweid:
            key = f"CWE-{cweid}"
        elif cve:
            key = cve
        else:
            key = f"{a.get('alert')}|{a.get('url')}|{a.get('param')}"

        if key in seen:
            continue

        seen.add(key)
        result.append(a)

    return result

# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

async def _zap_get(client: httpx.AsyncClient, url: str, params: dict) -> dict:
    """Wrapper around GET to ZAP that normalizes error handling."""
    resp = await client.get(url, params=params)
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError:
        try:
            msg = resp.json().get("message", resp.text)
        except Exception:
            msg = resp.text
        raise HTTPException(status_code=400, detail=f"ZAP API Error: {msg}")
    return resp.json()


async def _setup_zap_session(
    target_url: str,
    cookies: Optional[Dict[str, str]] = None,
) -> str:
    has_cookies = bool(cookies)
    logger.info(f"Setting up ZAP plan for {target_url} (has_cookies={has_cookies})")

    cookie_string = ""
    if has_cookies:
        cookie_string = "; ".join(f"{k}={v}" for k, v in cookies.items())

    plan = {
        "env": {
            "contexts": [
                {
                    "name": "AWAST_Context",
                    "urls": [target_url],
                }
            ],
            "parameters": {"failOnError": True, "progressToStdout": True},
        },
        "jobs": [],
    }

    if cookie_string:
        plan["jobs"].append(
            {
                "type": "replacer",
                "name": "AWAST_AUTH_COOKIES",
                "parameters": {
                    "enabled": True,
                },
                "rules": [
                    {
                        "description": "AWAST_AUTH_COOKIES",
                        "enabled": True,
                        "matchType": "REQ_HEADER",
                        "matchRegex": False,
                        "matchString": "Cookie",
                        "replacement": cookie_string,
                    }
                ],
            }
        )

    plan["jobs"].append(
        {
            "type": "spider",
            "parameters": {
                "maxDepth": 0,
            },
        }
    )

    plan["jobs"].append(
        {
            "type": "activeScan",
        }
    )

    shared_dir = getattr(settings, "ZAP_AUTOMATION_SHARED_DIR", "C:\\zap\\wrk\\")
    
    try:
        os.makedirs(shared_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create ZAP Automation shared_dir '{shared_dir}': {e}")
        raise HTTPException(status_code=500, detail="Configuration error.")

    try:
        fd, file_path = tempfile.mkstemp(
            suffix=".yaml",
            prefix="zap_plan_",
            dir=shared_dir,
            text=True,
        )
        with os.fdopen(fd, "w") as f:
            yaml.safe_dump(plan, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Secure ZAP Automation plan generated at {file_path}")

        return file_path

    except Exception as e:
        logger.error(f"Failed to write ZAP config securely: {e}")
        raise HTTPException(status_code=500, detail="Configuration error.")


# ---------------------------------------------------------------------------
# Public ZAP spider helpers
# ---------------------------------------------------------------------------

async def start_spider(
    target: str,
    cookies: Optional[Dict[str, str]] = None,
    login_url: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            await _setup_zap_session(target_url=target, cookies=cookies)
        except Exception as e:
            logger.warning("Failed to setup ZAP session for spider: %s", e)
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/spider/action/scan/",
            {"apikey": settings.ZAP_API_KEY, "url": target},
        )


async def get_spider_status(scan_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/spider/view/status/",
            {"apikey": settings.ZAP_API_KEY, "scanId": scan_id},
        )


async def stop_spider(scan_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/spider/action/stop/",
            {"apikey": settings.ZAP_API_KEY, "scanId": scan_id},
        )


# ---------------------------------------------------------------------------
# Scan orchestration
# ---------------------------------------------------------------------------

async def start_scan(
    target: str,
    user_id: str,
    db: AsyncSession,
    cookies: Optional[Dict[str, str]] = None,
    login_url: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> dict:
    """
    Configure ZAP via Automation Framework, run the plan, and track gracefully.
    """
    database_service = AsyncDatabaseService(lambda: db)

    has_cookies = bool(cookies)
    # Decide which ZAP engine we will orchestrate:
    # - with cookies: Automation Framework plan (runPlan/planProgress)
    # - without cookies: direct Active Scan (ascan/scan + ascan/status)
    scan_type = "automation" if has_cookies else "ascan"

    if has_cookies:
        plan_path_local = await _setup_zap_session(target_url=target, cookies=cookies)

        safe_filename = os.path.basename(plan_path_local)
        internal_dir = getattr(settings, "ZAP_AUTOMATION_INTERNAL_DIR", "/zap/wrk/")
        internal_dir = internal_dir.rstrip("/") + "/"
        zap_internal_path = f"{internal_dir}{safe_filename}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            data = await _zap_get(
                client,
                f"{settings.ZAP_API_URL}/JSON/automation/action/runPlan/",
                {
                    "apikey": settings.ZAP_API_KEY,
                    "filePath": zap_internal_path,
                },
            )

        plan_raw = data.get("planId") or data.get("runPlan")
        if plan_raw is None:
            if data.get("Result") == "OK":
                plan_raw = "1"  
            else:
                msg = data.get("message", str(data))
                logger.error("ZAP runPlan failed for %s: %s", target, msg)
                raise HTTPException(status_code=400, detail=f"ZAP API Error: {msg}")

        runner_id = str(plan_raw)
    else:
        async with httpx.AsyncClient(timeout=60.0) as client:
            data = await _zap_get(
                client,
                f"{settings.ZAP_API_URL}/JSON/ascan/action/scan/",
                {
                    "apikey": settings.ZAP_API_KEY,
                    "url": target,
                },
            )

        scan_raw = data.get("scan")
        if scan_raw is None:
            msg = data.get("message", str(data))
            logger.error("ZAP ascan scan failed for %s: %s", target, msg)
            raise HTTPException(status_code=400, detail=f"ZAP API Error: {msg}")

        runner_id = str(scan_raw)

    try:
        zap_index_int = int(runner_id)
    except ValueError:
        zap_index_int = 1

    scan_data = Scan(
        target=target,
        created_at=datetime.utcnow(),
        zap_index=zap_index_int,
        user_id=user_id,
        scan_type=scan_type,
    )
    created_scan = await database_service.create(scan_data)
    logger.info(
        "Started ZAP scan for target %s with runner_id=%s (has_cookies=%s)",
        target,
        runner_id,
        has_cookies,
    )

    return {
        "scan_id": created_scan.scan_id,
        "scan_index": runner_id,
        "zap_index": runner_id,
    }

async def get_scan_status(scan_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/automation/view/planProgress/",
            {"apikey": settings.ZAP_API_KEY, "planId": scan_id},
        )


# ---------------------------------------------------------------------------
# Alerts helpers
# ---------------------------------------------------------------------------

async def get_alerts() -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/core/view/alerts/",
            {"apikey": settings.ZAP_API_KEY},
        )


async def get_alerts_with_evidence(baseurl: str = None) -> dict:
    params = {"apikey": settings.ZAP_API_KEY}
    if baseurl:
        params["baseurl"] = baseurl

    async with httpx.AsyncClient(timeout=60.0) as client:
        data = await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/core/view/alerts/",
            params,
        )
        alerts = data.get("alerts", [])
        alerts = _dedupe_alerts_by_cwe(alerts)

        seen = set()
        unique_alerts = []

        for a in alerts:
            key = (a.get("alert"), a.get("url"), a.get("param"))
            if key in seen:
                continue
            seen.add(key)
            if a.get("evidence"):
                unique_alerts.append(
                    {
                        "alert": a.get("alert"),
                        "risk": a.get("risk"),
                        "confidence": a.get("confidence"),
                        "url": a.get("url"),
                        "param": a.get("param"),
                        "evidence": a.get("evidence"),
                        "solution": a.get("solution"),
                        "reference": a.get("reference"),
                        "tags": a.get("tags"),
                        "cweid": a.get("cweid"),
                    }
                )

        return {"count": len(unique_alerts), "alerts": unique_alerts}


async def get_alerts_summary() -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/core/view/alertsSummary/",
            {"apikey": settings.ZAP_API_KEY},
        )


async def get_alert_by_id(alert_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/core/view/alert/",
            {"apikey": settings.ZAP_API_KEY, "id": alert_id},
        )


# ---------------------------------------------------------------------------
# Scan lifecycle: abort + run
# ---------------------------------------------------------------------------

async def abort_scan(scan_id: str) -> dict:
    from core.database import async_session

    async with async_session() as db:
        database_service = AsyncDatabaseService(lambda: db)
        scan = await database_service.get(Scan, scan_id=scan_id)
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")

        zap_index = str(scan.zap_index)

    _cancelled_scans.add(str(scan_id))

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            await _zap_get(
                client,
                f"{settings.ZAP_API_URL}/JSON/spider/action/stopAllScans/",
                {"apikey": settings.ZAP_API_KEY},
            )
        except Exception as e:
            logger.warning("ZAP spider stopAllScans failed for %s: %s", scan_id, e)

        try:
            await _zap_get(
                client,
                f"{settings.ZAP_API_URL}/JSON/ascan/action/stopAllScans/",
                {"apikey": settings.ZAP_API_KEY},
            )
        except Exception:
            pass

    async with async_session() as db:
        database_service = AsyncDatabaseService(lambda: db)
        await database_service.update(
            Scan,
            {"scan_id": scan_id},
            {"status": "stopped"},
        )

    await manager.broadcast(
        str(scan_id),
        {
            "type": "stopped",
            "message": "Scan was stopped by user",
        },
    )
    logger.info("Scan %s stopped by user", scan_id)
    return {"status": "stopped", "scan_id": str(scan_id)}


async def run_scan(scan_id: int, target_url: str, scan_index: str):
    from core.database import async_session

    async with async_session() as db:
        await _run_scan_internal(scan_id, target_url, scan_index, db)


async def _run_scan_internal(
    scan_id: int,
    target_url: str,
    scan_index: str,
    db: AsyncSession,
) -> None:
    """
    Poll ZAP for scan progress based on the configured scan_type.
    """
    database_service = AsyncDatabaseService(lambda: db)

    # Load the Scan record once to determine which ZAP engine we should poll.
    scan = await database_service.get(Scan, scan_id=scan_id)
    if not scan:
        # Fail fast but avoid leaking sensitive details.
        logger.error("Scan record not found for scan_id=%s", scan_id)
        return

    # Backwards compatibility: default to "ascan" if column is missing/NULL.
    raw_scan_type = getattr(scan, "scan_type", None) or "ascan"
    if raw_scan_type not in {"automation", "ascan"}:
        logger.warning("Unknown scan_type '%s' for scan_id=%s, defaulting to 'ascan'", raw_scan_type, scan_id)
        scan_type = "ascan"
    else:
        scan_type = raw_scan_type

    # Normalize zap_index to a string identifier for ZAP APIs.
    zap_runner_id = str(scan.zap_index if scan.zap_index is not None else scan_index)

    logger.info(
        "Tracking scan_id=%s, target=%s, zap_runner_id=%s, scan_type=%s",
        scan_id,
        target_url,
        zap_runner_id,
        scan_type,
    )

    try:
        seen_alert_ids = set()

        async with httpx.AsyncClient(timeout=60.0) as client:
            cancelled = False

            while True:
                scan_id_str = str(scan_id)
                if scan_id_str in _cancelled_scans:
                    _cancelled_scans.discard(scan_id_str)
                    cancelled = True
                    logger.info("Scan %s cancelled by user", scan_id)
                    break

                time_finished = None
                progress = 0

                # Automation Framework plan progress (когда скан запущен через runPlan)
                if scan_type == "automation":
                    progress_resp = await _zap_get(
                        client,
                        f"{settings.ZAP_API_URL}/JSON/automation/view/planProgress/",
                        {
                            "apikey": settings.ZAP_API_KEY,
                            "planId": zap_runner_id,
                        },
                    )
                    progress_data = progress_resp.get("planProgress", {}) or {}
                    time_finished = progress_data.get("timeFinished")
                    progress = int(progress_data.get("percentComplete", 0))

                # Active Scan progress (когда скан запущен напрямую через ascan/action/scan)
                if scan_type == "ascan":
                    ascan_status = await _zap_get(
                        client,
                        f"{settings.ZAP_API_URL}/JSON/ascan/view/status/",
                        {
                            "apikey": settings.ZAP_API_KEY,
                            "scanId": zap_runner_id,
                        },
                    )
                    ascan_progress = int(ascan_status.get("status", 0))
                    progress = ascan_progress
                    if ascan_progress >= 100 and time_finished is None:
                        # Для ascan нет timeFinished, но для логики достаточно статуса 100%.
                        time_finished = "completed"

                alerts_resp = await _zap_get(
                    client,
                    f"{settings.ZAP_API_URL}/JSON/core/view/alerts/",
                    {"apikey": settings.ZAP_API_KEY, "baseurl": target_url},
                )
                
                current_alerts = alerts_resp.get("alerts", [])
                new_alerts = []
                
                for alert in current_alerts:
                    aid_str = str(alert.get("id", alert.get("alertId", "")))
                    if aid_str and aid_str not in seen_alert_ids:
                        new_alerts.append({
                            "id": aid_str,
                            "name": alert.get("alert", "Unknown"),
                            "risk": alert.get("risk", "Info"),
                            "url": alert.get("url", ""),
                        })
                        seen_alert_ids.add(aid_str)

                await manager.broadcast(
                    scan_id_str,
                    {
                        "type": "progress",
                        "progress": progress,
                        "new_alerts": new_alerts,
                        "total_alerts": len(seen_alert_ids),
                    },
                )

                if time_finished:
                    logger.info("ZAP Automation plan %s finished at %s", scan_index, time_finished)
                    break

                await asyncio.sleep(5)

            if cancelled:
                return

            resp = await client.get(
                f"{settings.ZAP_API_URL}/JSON/core/view/alerts/",
                params={"apikey": settings.ZAP_API_KEY, "baseurl": target_url},
            )
            data = resp.json()
            filtered_vulnerabilities = _dedupe_alerts_by_cwe(data.get("alerts", []))

            alerts_data = []

            for vuln_raw in filtered_vulnerabilities:
                try:
                    message_id = vuln_raw.get("messageId")
                    parameter = vuln_raw.get("param")
                    payload = vuln_raw.get("attack")

                    request_text = ""
                    response_text = ""

                    if message_id:
                        try:
                            msg_resp = await client.get(
                                f"{settings.ZAP_API_URL}/JSON/core/view/message/",
                                params={
                                    "apikey": settings.ZAP_API_KEY,
                                    "id": message_id,
                                },
                            )
                            msg_data = msg_resp.json().get("message", {})
                            request_text = msg_data.get("requestHeader", "") + "\n\n" + msg_data.get("requestBody", "")
                            response_text = msg_data.get("responseHeader", "") + "\n\n" + msg_data.get("responseBody", "")
                        except Exception as e:
                            logger.error("Failed to fetch ZAP message ID %s: %s", message_id, e)

                    vuln = VulnerabilitySchema(**vuln_raw)
                    vuln_data = vuln.model_dump()
                    vuln_data["url"] = str(vuln_data["url"])
                    vuln_data["parameter"] = parameter
                    vuln_data["payload"] = payload
                    vuln_data["request"] = request_text
                    vuln_data["response"] = response_text

                    await database_service.create(
                        Vulnerability(**vuln_data, scan_id=scan_id)
                    )
                    alerts_data.append(vuln_data)
                except Exception as ex:
                    logger.error("Error processing vulnerability row: %s", ex, exc_info=True)

            await database_service.update(
                Scan,
                {"scan_id": scan_id},
                {"status": "done"},
            )

            await manager.broadcast(
                str(scan_id),
                {
                    "type": "done",
                    "progress": 100,
                    "alerts_count": len(alerts_data),
                    "total_alerts": len(seen_alert_ids),
                    "alerts": alerts_data,
                },
            )
            logger.info("Scan %s completed successfully. Found %s vulnerabilities.", scan_id, len(alerts_data))

    except Exception as e:
        await database_service.update(
            Scan,
            {"scan_id": scan_id},
            {"status": "error"},
        )
        await manager.broadcast(
            str(scan_id),
            {
                "type": "error",
                "message": str(e),
            },
        )
        logger.error("Error in run_scan for scan_id=%s: %s", scan_id, e, exc_info=True)