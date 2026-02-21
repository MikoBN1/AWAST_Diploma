import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.scan_model import Scan
from models.vulnerability_model import Vulnerability
from schemas.report_schema import Vulnerability as VulnerabilitySchema
from services.database_service import AsyncDatabaseService
from services.websocket_service import manager

async def start_spider(target: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{settings.ZAP_API_URL}/JSON/spider/action/scan/",
            params={"apikey": settings.ZAP_API_KEY, "url": target}
        )
        resp.raise_for_status()
        return resp.json()


async def get_spider_status(scan_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{settings.ZAP_API_URL}/JSON/spider/view/status/",
            params={"apikey": settings.ZAP_API_KEY, "scanId": scan_id}
        )
        resp.raise_for_status()
        return resp.json()


async def start_scan(target: str, user_id: str, db: AsyncSession) -> dict:
    database_service = AsyncDatabaseService(lambda: db)
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{settings.ZAP_API_URL}/JSON/ascan/action/scan/",
            params={"apikey": settings.ZAP_API_KEY, "url": target},
        )
        resp.raise_for_status()
        data = resp.json()

    scan_data = Scan(
        target=target,
        created_at=datetime.utcnow(),
        zap_index=int(data.get("scan")),
        user_id=user_id,
    )
    created_scan = await database_service.create(scan_data)
    logger.info(f"Started scan for target {target} with scan_id={created_scan.scan_id}")

    return {
        "scan_id": created_scan.scan_id,
        "scan_index": data.get("scan"),
        "zap_index": str(created_scan.zap_index),
    }


async def get_scan_status(scan_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{settings.ZAP_API_URL}/JSON/ascan/view/status/",
            params={"apikey": settings.ZAP_API_KEY, "scanId": scan_id}
        )
        resp.raise_for_status()
        return resp.json()


async def get_alerts() -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{settings.ZAP_API_URL}/JSON/core/view/alerts/",
            params={"apikey": settings.ZAP_API_KEY}
        )
        resp.raise_for_status()
        return resp.json()


async def get_alerts_with_evidence(baseurl: str = None) -> dict:
    params = {"apikey": settings.ZAP_API_KEY}
    if baseurl:
        params["baseurl"] = baseurl

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{settings.ZAP_API_URL}/JSON/core/view/alerts/",
            params=params
        )
        resp.raise_for_status()
        data = resp.json()
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
        filtered = [a for a in unique_alerts if a.get("evidence")]

        return {"count": len(filtered), "alerts": filtered}


async def get_alerts_summary() -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{settings.ZAP_API_URL}/JSON/core/view/alertsSummary/",
            params={"apikey": settings.ZAP_API_KEY}
        )
        resp.raise_for_status()
        return resp.json()


async def abort_scan(scan_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{settings.ZAP_API_URL}/JSON/ascan/action/stop/",
            params={"apikey": settings.ZAP_API_KEY, "scanId": scan_id}
        )
        resp.raise_for_status()
        return resp.json()


async def run_scan(scan_id: int, target_url: str, scan_index: str, db: AsyncSession):
    database_service = AsyncDatabaseService(lambda: db)
    logger.info(f"Starting run_scan for scan_id={scan_id}, target={target_url}, zap_scan_index={scan_index}")
    try:
        seen_alert_ids = set()
        async with httpx.AsyncClient(timeout=60.0) as client:
            max_retries = 60
            for _ in range(max_retries):
                status_resp = await client.get(
                    f"{settings.ZAP_API_URL}/JSON/ascan/view/status/",
                    params={"apikey": settings.ZAP_API_KEY, "scanId": scan_index}
                )
                status = status_resp.json()
                progress = int(status.get("status", 0))
                
                alerts_ids_resp = await client.get(
                    f"{settings.ZAP_API_URL}/JSON/ascan/view/alertsIds/",
                    params={"apikey": settings.ZAP_API_KEY, "scanId": scan_index}
                )
                current_alert_ids = alerts_ids_resp.json().get("alertsIds", [])
                
                new_alerts = []
                if isinstance(current_alert_ids, list):
                    for aid in current_alert_ids:
                        aid_str = str(aid)
                        if aid_str not in seen_alert_ids:
                            alert_detail_resp = await client.get(
                                f"{settings.ZAP_API_URL}/JSON/core/view/alert/",
                                params={"apikey": settings.ZAP_API_KEY, "id": aid_str}
                            )
                            alert_detail = alert_detail_resp.json().get("alert", {})
                            if alert_detail:
                                logger.debug(f"Scan {scan_id} found new alert: {alert_detail.get('alert')} on {alert_detail.get('url')}")
                                new_alerts.append({
                                    "id": aid_str,
                                    "name": alert_detail.get("alert", "Unknown"),
                                    "risk": alert_detail.get("risk", "Info"),
                                    "url": alert_detail.get("url", "")
                                })
                            seen_alert_ids.add(aid_str)
                
                await manager.broadcast(str(scan_id), {
                    "type": "progress",
                    "progress": progress,
                    "new_alerts": new_alerts,
                    "total_alerts": len(seen_alert_ids)
                })

                if progress >= 100:
                    break
                await asyncio.sleep(5)
            else:
                await database_service.update(
                    Scan,
                    {"scan_id": scan_id},
                    {"status": "error"}
                )
                await manager.broadcast(str(scan_id), {
                    "type": "error",
                    "message": "Scan timeout"
                })
                return

            resp = await client.get(
                f"{settings.ZAP_API_URL}/JSON/core/view/alerts/",
                params={"apikey": settings.ZAP_API_KEY, "baseurl": target_url}
            )
            data = resp.json()
            vulnerabilities = [VulnerabilitySchema(**v) for v in data.get("alerts", [])]

            for vuln in vulnerabilities:
                vuln_data = vuln.model_dump()
                vuln_data["url"] = str(vuln_data["url"])
                await database_service.create(Vulnerability(**vuln_data, scan_id=scan_id))

            await database_service.update(
                Scan,
                {"scan_id": scan_id},
                {"status": "done"}
            )
            
            await manager.broadcast(str(scan_id), {
                "type": "done",
                "progress": 100,
                "alerts_count": len(vulnerabilities),
                "total_alerts": len(seen_alert_ids)
            })
            logger.info(f"Scan {scan_id} completed successfully. Found {len(vulnerabilities)} vulnerabilities.")

    except Exception as e:
        await database_service.update(
            Scan,
            {"scan_id": scan_id},
            {"status": "error"}
        )
        await manager.broadcast(str(scan_id), {
            "type": "error",
            "message": str(e)
        })
        logger.error(f"Error in run_scan for scan_id={scan_id}: {e}", exc_info=True)
