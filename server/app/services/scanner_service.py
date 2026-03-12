import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Set
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_cancelled_scans: Set[str] = set()

import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.scan_model import Scan
from models.vulnerability_model import Vulnerability
from schemas.report_schema import Vulnerability as VulnerabilitySchema
from services.database_service import AsyncDatabaseService
from services.websocket_service import manager

# ZAP Confidence mapping: 0=Low, 1=Medium, 2=High
CONFIDENCE_MAP = {
    "Low": "0",
    "Medium": "1",
    "High": "2"
}

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


async def _setup_zap_session(
    client: httpx.AsyncClient,
    cookies: Dict[str, str],
) -> None:
    """Inject authentication cookies into ZAP via Replacer add-on.

    The Replacer add a Cookie header to ALL outgoing ZAP requests,
    ensuring spider and active scanner both work authenticated.
    """
    cookie_string = "; ".join(f"{k}={v}" for k, v in cookies.items())
    rule_description = "AWAST_AUTH_COOKIES"

    # Remove existing rule if present (idempotent)
    try:
        await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/replacer/action/removeRule/",
            {"apikey": settings.ZAP_API_KEY, "description": rule_description},
        )
    except Exception:
        pass

    await _zap_get(
        client,
        f"{settings.ZAP_API_URL}/JSON/replacer/action/addRule/",
        {
            "apikey": settings.ZAP_API_KEY,
            "description": rule_description,
            "enabled": "true",
            "matchType": "REQ_HEADER",
            "matchRegex": "false",
            "matchString": "Cookie",
            "replacement": cookie_string,
        },
    )
    logger.info(f"ZAP Replacer rule set with {len(cookies)} cookie(s)")


async def start_spider(
    target: str, cookies: Optional[Dict[str, str]] = None
) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        if cookies:
            try:
                await _setup_zap_session(client, cookies)
            except Exception as e:
                logger.warning(f"Failed to setup ZAP session for spider: {e}")
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/spider/action/scan/",
            {"apikey": settings.ZAP_API_KEY, "url": target}
        )


async def get_spider_status(scan_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/spider/view/status/",
            {"apikey": settings.ZAP_API_KEY, "scanId": scan_id}
        )


async def stop_spider(scan_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/spider/action/stop/",
            {"apikey": settings.ZAP_API_KEY, "scanId": scan_id}
        )


async def start_scan(
    target: str,
    user_id: str,
    db: AsyncSession,
    cookies: Optional[Dict[str, str]] = None,
) -> dict:
    database_service = AsyncDatabaseService(lambda: db)
    spider_id = 0

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Inject auth cookies into ZAP via Replacer if provided
        if cookies:
            try:
                await _setup_zap_session(client, cookies)
            except Exception as e:
                logger.warning(f"Failed to setup ZAP session for {target}: {e}")

        # Spider the target to discover forms and parameters
        try:
            spider_resp = await _zap_get(
                client,
                f"{settings.ZAP_API_URL}/JSON/spider/action/scan/",
                {"apikey": settings.ZAP_API_KEY, "url": target},
            )
            spider_id = int(spider_resp.get("scan", 0))
            logger.info(f"Spider started for {target} with id={spider_id}")

            for _ in range(120):
                status_resp = await _zap_get(
                    client,
                    f"{settings.ZAP_API_URL}/JSON/spider/view/status/",
                    {"apikey": settings.ZAP_API_KEY, "scanId": spider_id},
                )
                if int(status_resp.get("status", 0)) >= 100:
                    break
                await asyncio.sleep(2)

            logger.info(f"Spider completed for {target}")
        except Exception as e:
            logger.warning(f"Spider failed for {target}: {e}")

    # Active scan is now handled by Nuclei in the background task.
    # We reuse zap_index to store the spider scan ID (satisfies nullable=False).
    scan_data = Scan(
        target=target,
        created_at=datetime.utcnow(),
        zap_index=spider_id,
        user_id=user_id,
    )
    created_scan = await database_service.create(scan_data)
    logger.info(f"Started scan for target {target} with scan_id={created_scan.scan_id}")

    return {
        "scan_id": created_scan.scan_id,
        "scan_index": str(spider_id),
        "zap_index": str(spider_id),
    }


async def get_scan_status(scan_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/ascan/view/status/",
            {"apikey": settings.ZAP_API_KEY, "scanId": scan_id}
        )


async def get_alerts() -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/core/view/alerts/",
            {"apikey": settings.ZAP_API_KEY}
        )


async def get_alerts_with_evidence(baseurl: str = None) -> dict:
    params = {"apikey": settings.ZAP_API_KEY}
    if baseurl:
        params["baseurl"] = baseurl

    async with httpx.AsyncClient(timeout=60.0) as client:
        data = await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/core/view/alerts/",
            params
        )
        alerts = data.get("alerts", [])

        seen = set()
        unique_alerts = []

        for a in alerts:
            key = (a.get("alert"), a.get("url"), a.get("param"))
            if key not in seen:
                seen.add(key)
                unique_alerts.append({
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
                })
        
        # Filter by minimum confidence level
        min_conf = settings.ZAP_MIN_CONFIDENCE
        confidence_threshold = int(CONFIDENCE_MAP.get(min_conf, "1"))
        
        filtered = []
        for a in unique_alerts:
            if not a.get("evidence"):
                continue
            
            # ZAP confidence labels to numeric for comparison
            conf_label = a.get("confidence", "Low")
            conf_val = int(CONFIDENCE_MAP.get(conf_label, "0"))
            
            if conf_val >= confidence_threshold:
                filtered.append(a)

        return {"count": len(filtered), "alerts": filtered}


async def get_alerts_summary() -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/core/view/alertsSummary/",
            {"apikey": settings.ZAP_API_KEY}
        )


async def get_alert_by_id(alert_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/core/view/alert/",
            {"apikey": settings.ZAP_API_KEY, "id": alert_id}
        )


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
                f"{settings.ZAP_API_URL}/JSON/ascan/action/stop/",
                {"apikey": settings.ZAP_API_KEY, "scanId": zap_index},
            )
        except Exception as e:
            logger.warning(f"ZAP active scan stop failed for {scan_id}: {e}")

        try:
            await _zap_get(
                client,
                f"{settings.ZAP_API_URL}/JSON/spider/action/stop/",
                {"apikey": settings.ZAP_API_KEY, "scanId": zap_index},
            )
        except Exception:
            pass

    async with async_session() as db:
        database_service = AsyncDatabaseService(lambda: db)
        await database_service.update(
            Scan, {"scan_id": scan_id}, {"status": "stopped"}
        )

    await manager.broadcast(str(scan_id), {
        "type": "stopped",
        "message": "Scan was stopped by user",
    })
    logger.info(f"Scan {scan_id} stopped by user")
    return {"status": "stopped", "scan_id": str(scan_id)}


async def get_spider_urls(target_url: str) -> list[str]:
    """Fetch all URLs discovered by ZAP spider for the given target."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await _zap_get(
                client,
                f"{settings.ZAP_API_URL}/JSON/spider/view/allUrls/",
                {"apikey": settings.ZAP_API_KEY},
            )
        all_urls: list[str] = resp.get("urls", [])
        parsed_target = urlparse(target_url)
        target_host = parsed_target.netloc

        filtered = [u for u in all_urls if urlparse(u).netloc == target_host]
        logger.info(f"ZAP spider found {len(filtered)} URLs for {target_url}")
        return filtered
    except Exception as e:
        logger.warning(f"Failed to retrieve spider URLs from ZAP: {e}. Falling back to target URL only.")
        return []


async def run_scan(scan_id: int, target_url: str, scan_index: str):
    from core.database import async_session
    async with async_session() as db:
        await _run_scan_internal(scan_id, target_url, db)


async def _run_scan_internal(scan_id: int, target_url: str, db: AsyncSession):
    import services.nuclei_service as nuclei_service

    database_service = AsyncDatabaseService(lambda: db)
    logger.info(f"Starting Nuclei scan for scan_id={scan_id}, target={target_url}")

    try:
        # Fetch URLs discovered by ZAP spider to feed Nuclei
        urls = await get_spider_urls(target_url)

        alerts_data: list[dict] = []
        total_count = 0
        scan_id_str = str(scan_id)

        async for finding in nuclei_service.run_nuclei_scan(target_url, urls or None):
            if scan_id_str in _cancelled_scans:
                _cancelled_scans.discard(scan_id_str)
                logger.info(f"Scan {scan_id} cancelled by user during Nuclei run")
                await database_service.update(Scan, {"scan_id": scan_id}, {"status": "stopped"})
                await manager.broadcast(scan_id_str, {
                    "type": "stopped",
                    "message": "Scan was stopped by user",
                })
                return

            try:
                vuln_schema = VulnerabilitySchema(**finding)
                vuln_data = vuln_schema.model_dump()
                vuln_data["url"] = str(vuln_data["url"])

                await database_service.create(Vulnerability(**vuln_data, scan_id=scan_id))
                alerts_data.append(vuln_data)
                total_count += 1

                await manager.broadcast(scan_id_str, {
                    "type": "progress",
                    "progress": -1,  # Nuclei has no percentage progress
                    "new_alerts": [{
                        "name": vuln_data.get("name", "Unknown"),
                        "risk": vuln_data.get("risk", "Info"),
                        "url": vuln_data.get("url", ""),
                    }],
                    "total_alerts": total_count,
                })
            except Exception as ex:
                logger.error(f"Error saving Nuclei finding: {ex}", exc_info=True)

        if scan_id_str in _cancelled_scans:
            _cancelled_scans.discard(scan_id_str)
            return

        await database_service.update(Scan, {"scan_id": scan_id}, {"status": "done"})
        await manager.broadcast(scan_id_str, {
            "type": "done",
            "progress": 100,
            "alerts_count": len(alerts_data),
            "total_alerts": total_count,
            "alerts": alerts_data,
        })
        logger.info(f"Nuclei scan {scan_id} completed. Found {len(alerts_data)} vulnerabilities.")

    except Exception as e:
        await database_service.update(Scan, {"scan_id": scan_id}, {"status": "error"})
        await manager.broadcast(str(scan_id), {
            "type": "error",
            "message": str(e),
        })
        logger.error(f"Error in run_scan for scan_id={scan_id}: {e}", exc_info=True)
