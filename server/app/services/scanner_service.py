import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Set

import httpx
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


# ---------------------------------------------------------------------------
# XSSStrike helpers
# ---------------------------------------------------------------------------

async def _run_xsstrike_scan(target_url: str, cookie_string: str) -> list[dict]:
    logger.info("Starting XSSStrike scan for %s", target_url)
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=600.0)) as client:
            resp = await client.post(
                f"{settings.XSSTRIKE_API_URL}/scan",
                json={"url": target_url, "cookies": cookie_string},
            )
            resp.raise_for_status()
            task_id = resp.json()["task_id"]
            logger.info("XSSStrike task created: %s", task_id)

            while True:
                await asyncio.sleep(5)
                poll = await client.get(f"{settings.XSSTRIKE_API_URL}/scan/{task_id}")
                result = poll.json()
                status = result.get("status")
                if status in ("completed", "error"):
                    break

            if status == "error":
                logger.error("XSSStrike error for %s: %s", target_url, result.get("error"))
                return []

            vulns: list[dict] = []
            for v in result.get("vulnerabilities", []):
                vulns.append({
                    "name": "Cross-Site Scripting (XSS)",
                    "description": v.get("raw", json.dumps(v)),
                    "risk": "High",
                    "cweid": "79",
                    "url": target_url,
                    "method": "GET",
                    "tags": {"source": "xsstrike"},
                    "solution": "Sanitize all user input. Use Content-Security-Policy headers.",
                    "references": ["https://owasp.org/www-community/attacks/xss/"],
                    "parameter": v.get("parameter", ""),
                    "payload": v.get("payload", str(v)),
                    "request": "",
                    "response": "",
                })

            logger.info("XSSStrike found %d vulnerabilities for %s", len(vulns), target_url)
            return vulns

    except Exception as e:
        logger.error("XSSStrike scan failed for %s: %s", target_url, e, exc_info=True)
        return []


# ---------------------------------------------------------------------------
# SQLMap helpers
# ---------------------------------------------------------------------------

async def _run_sqlmap_scan(target_url: str, cookie_string: str) -> list[dict]:
    logger.info("Starting SQLMap scan for %s", target_url)
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=600.0)) as client:
            resp = await client.get(f"{settings.SQLMAP_API_URL}/task/new")
            resp.raise_for_status()
            task_id = resp.json()["taskid"]
            logger.info("SQLMap task created: %s", task_id)

            start_resp = await client.post(
                f"{settings.SQLMAP_API_URL}/scan/{task_id}/start",
                json={"url": target_url, "cookie": cookie_string},
            )
            start_resp.raise_for_status()

            while True:
                await asyncio.sleep(5)
                poll = await client.get(f"{settings.SQLMAP_API_URL}/scan/{task_id}/status")
                poll_data = poll.json()
                if poll_data.get("status") == "terminated":
                    break

            data_resp = await client.get(f"{settings.SQLMAP_API_URL}/scan/{task_id}/data")
            scan_data = data_resp.json()

            vulns: list[dict] = []
            for item in scan_data.get("data", []):
                if item.get("status") == 1:
                    for entry in item.get("value", []):
                        place = entry.get("place", "GET")
                        param = entry.get("parameter", "")
                        title = entry.get("title", "SQL Injection")
                        payload = entry.get("payload", "")
                        dbms = entry.get("dbms", "")
                        vulns.append({
                            "name": f"SQL Injection — {title}",
                            "description": (
                                f"SQLMap detected injection in parameter '{param}' "
                                f"({place}). DBMS: {dbms or 'unknown'}."
                            ),
                            "risk": "High",
                            "cweid": "89",
                            "url": target_url,
                            "method": place,
                            "tags": {"source": "sqlmap", "dbms": dbms},
                            "solution": (
                                "Use parameterized queries / prepared statements. "
                                "Never concatenate user input into SQL."
                            ),
                            "references": ["https://owasp.org/www-community/attacks/SQL_Injection"],
                            "parameter": param,
                            "payload": payload,
                            "request": "",
                            "response": "",
                        })

            logger.info("SQLMap found %d vulnerabilities for %s", len(vulns), target_url)
            return vulns

    except Exception as e:
        logger.error("SQLMap scan failed for %s: %s", target_url, e, exc_info=True)
        return []


# ---------------------------------------------------------------------------
# Public ZAP spider helpers
# ---------------------------------------------------------------------------

async def start_spider(target: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
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
) -> dict:
    database_service = AsyncDatabaseService(lambda: db)

    async with httpx.AsyncClient(timeout=60.0) as client:
        data = await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/ascan/action/scan/",
            {"apikey": settings.ZAP_API_KEY, "url": target},
        )

    scan_raw = data.get("scan")
    if scan_raw is None:
        msg = data.get("message", str(data))
        logger.error("ZAP ascan failed for %s: %s", target, msg)
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
        scan_type="ascan",
    )
    created_scan = await database_service.create(scan_data)

    has_cookies = bool(cookies)
    logger.info(
        "Started scan for %s — ZAP runner_id=%s, auth_tools=%s",
        target, runner_id, has_cookies,
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
            f"{settings.ZAP_API_URL}/JSON/ascan/view/status/",
            {"apikey": settings.ZAP_API_KEY, "scanId": scan_id},
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


async def run_scan(
    scan_id: int,
    target_url: str,
    scan_index: str,
    cookies: Optional[Dict[str, str]] = None,
):
    from core.database import async_session

    async with async_session() as db:
        await _run_scan_internal(scan_id, target_url, scan_index, db, cookies)


async def _run_scan_internal(
    scan_id: int,
    target_url: str,
    scan_index: str,
    db: AsyncSession,
    cookies: Optional[Dict[str, str]] = None,
) -> None:
    database_service = AsyncDatabaseService(lambda: db)

    scan = await database_service.get(Scan, scan_id=scan_id)
    if not scan:
        logger.error("Scan record not found for scan_id=%s", scan_id)
        return

    zap_runner_id = str(scan.zap_index if scan.zap_index is not None else scan_index)
    has_cookies = bool(cookies)
    cookie_string = ""
    if has_cookies:
        cookie_string = "; ".join(f"{k}={v}" for k, v in cookies.items())

    logger.info(
        "Tracking scan_id=%s, target=%s, zap_runner_id=%s, auth_tools=%s",
        scan_id, target_url, zap_runner_id, has_cookies,
    )

    xsstrike_task = None
    sqlmap_task = None

    try:
        seen_alert_ids: set = set()

        if has_cookies:
            xsstrike_task = asyncio.create_task(
                _run_xsstrike_scan(target_url, cookie_string)
            )
            sqlmap_task = asyncio.create_task(
                _run_sqlmap_scan(target_url, cookie_string)
            )

        async with httpx.AsyncClient(timeout=60.0) as client:
            cancelled = False

            while True:
                scan_id_str = str(scan_id)
                if scan_id_str in _cancelled_scans:
                    _cancelled_scans.discard(scan_id_str)
                    cancelled = True
                    logger.info("Scan %s cancelled by user", scan_id)
                    break

                ascan_status = await _zap_get(
                    client,
                    f"{settings.ZAP_API_URL}/JSON/ascan/view/status/",
                    {"apikey": settings.ZAP_API_KEY, "scanId": zap_runner_id},
                )
                zap_progress = int(ascan_status.get("status", 0))

                xss_done = xsstrike_task.done() if xsstrike_task else True
                sql_done = sqlmap_task.done() if sqlmap_task else True

                if has_cookies:
                    combined = (
                        int(zap_progress * 0.5)
                        + (25 if xss_done else 0)
                        + (25 if sql_done else 0)
                    )
                else:
                    combined = zap_progress

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
                        "progress": combined,
                        "new_alerts": new_alerts,
                        "total_alerts": len(seen_alert_ids),
                    },
                )

                zap_finished = zap_progress >= 100
                all_done = zap_finished and xss_done and sql_done
                if all_done:
                    break

                await asyncio.sleep(5)

            if cancelled:
                if xsstrike_task:
                    xsstrike_task.cancel()
                if sqlmap_task:
                    sqlmap_task.cancel()
                return

            # ---- Collect ZAP results ----
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
                            request_text = (
                                msg_data.get("requestHeader", "")
                                + "\n\n"
                                + msg_data.get("requestBody", "")
                            )
                            response_text = (
                                msg_data.get("responseHeader", "")
                                + "\n\n"
                                + msg_data.get("responseBody", "")
                            )
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
                    logger.error("Error processing ZAP vulnerability: %s", ex, exc_info=True)

            # ---- Collect XSSStrike + SQLMap results ----
            xsstrike_vulns: list[dict] = []
            sqlmap_vulns: list[dict] = []

            if xsstrike_task:
                try:
                    xsstrike_vulns = await xsstrike_task
                except Exception as e:
                    logger.error("XSSStrike task failed: %s", e)

            if sqlmap_task:
                try:
                    sqlmap_vulns = await sqlmap_task
                except Exception as e:
                    logger.error("SQLMap task failed: %s", e)

            for vuln_data in xsstrike_vulns + sqlmap_vulns:
                try:
                    await database_service.create(
                        Vulnerability(**vuln_data, scan_id=scan_id)
                    )
                    alerts_data.append(vuln_data)
                except Exception as ex:
                    logger.error("Error saving tool vulnerability: %s", ex, exc_info=True)

            # ---- Finalize ----
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
            logger.info(
                "Scan %s completed. Found %d vulnerabilities (ZAP: %d, XSSStrike: %d, SQLMap: %d).",
                scan_id, len(alerts_data),
                len(alerts_data) - len(xsstrike_vulns) - len(sqlmap_vulns),
                len(xsstrike_vulns), len(sqlmap_vulns),
            )

    except Exception as e:
        if xsstrike_task:
            xsstrike_task.cancel()
        if sqlmap_task:
            sqlmap_task.cancel()
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
