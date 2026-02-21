import asyncio
import os

import httpx
from datetime import datetime

from core.database import async_session
from models.scan_model import Scan
from models.vulnerability_model import Vulnerability
from schemas.report_schema import Vulnerability as VulnerabilitySchema
from services.database_service import AsyncDatabaseService

ZAP_API_KEY = os.getenv("ZAP_API_KEY", "changeme")
ZAP_API_URL = os.getenv("ZAP_API_URL", "http://localhost:8080")

database_service = AsyncDatabaseService(async_session)


async def start_spider(target: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{ZAP_API_URL}/JSON/spider/action/scan/",
            params={"apikey": ZAP_API_KEY, "url": target}
        )
        return resp.json()


async def get_spider_status(scan_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{ZAP_API_URL}/JSON/spider/view/status/",
            params={"apikey": ZAP_API_KEY, "scanId": scan_id}
        )
        return resp.json()


async def start_scan(target: str, user_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{ZAP_API_URL}/JSON/ascan/action/scan/",
            params={"apikey": ZAP_API_KEY, "url": target},
        )
        data = resp.json()

    scan_data = Scan(
        target=target,
        created_at=datetime.utcnow(),
        zap_index=int(data.get("scan")),
        user_id=user_id,
    )
    created_scan = await database_service.create(scan_data)

    return {
        "scan_id": created_scan.scan_id,
        "scan_index": data.get("scan"),
        "zap_index": str(created_scan.zap_index),
    }


async def get_scan_status(scan_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{ZAP_API_URL}/JSON/ascan/view/status/",
            params={"apikey": ZAP_API_KEY, "scanId": scan_id}
        )
        return resp.json()


async def get_alerts() -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{ZAP_API_URL}/JSON/core/view/alerts/",
            params={"apikey": ZAP_API_KEY}
        )
        return resp.json()


async def get_alerts_with_evidence(baseurl: str = None) -> dict:
    params = {"apikey": ZAP_API_KEY}
    if baseurl:
        params["baseurl"] = baseurl

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{ZAP_API_URL}/JSON/core/view/alerts/",
            params=params
        )
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
            f"{ZAP_API_URL}/JSON/core/view/alertsSummary/",
            params={"apikey": ZAP_API_KEY}
        )
        return resp.json()


async def abort_scan(scan_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{ZAP_API_URL}/JSON/ascan/action/stop/",
            params={"apikey": ZAP_API_KEY, "scanId": scan_id}
        )
        return resp.json()


async def run_scan(scan_id: int, target_url: str, scan_index: str):
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            max_retries = 60
            for _ in range(max_retries):
                status_resp = await client.get(
                    f"{ZAP_API_URL}/JSON/ascan/view/status/",
                    params={"apikey": ZAP_API_KEY, "scanId": scan_index}
                )
                status = status_resp.json()
                progress = int(status.get("status", 0))
                if progress >= 100:
                    break
                await asyncio.sleep(5)
            else:
                await database_service.update(
                    Scan,
                    {"scan_id": scan_id},
                    {"status": "error"}
                )
                return

            resp = await client.get(
                f"{ZAP_API_URL}/JSON/core/view/alerts/",
                params={"apikey": ZAP_API_KEY, "baseurl": target_url}
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

    except Exception as e:
        await database_service.update(
            Scan,
            {"scan_id": scan_id},
            {"status": "error"}
        )
        print(f"[!] Ошибка в run_scan: {e}")
