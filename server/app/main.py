import asyncio
import os
from dotenv import load_dotenv
import httpx
from fastapi import FastAPI

from schemas.zap_scanner_schema import RequestBody

load_dotenv()
app = FastAPI()

DVWA_URL = "http://192.168.56.101/dvwa/"  # адрес DVWA
ZAP_API_KEY = os.getenv("ZAP_API_KEY", "changeme")
ZAP_API_URL = os.getenv("ZAP_API_URL", "http://localhost:8080")

@app.post("/zap/spider")
async def zap_spider(target: RequestBody):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ZAP_API_URL}/JSON/spider/action/scan/",
            params={"apikey": ZAP_API_KEY, "url": target.target}
        )
        return resp.json()

@app.get("/zap/spider_status/{scan_id}")
async def zap_spider_status(scan_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ZAP_API_URL}/JSON/spider/view/status/",
            params={"apikey": ZAP_API_KEY, "scanId": scan_id}
        )
        return resp.json()


@app.post("/zap/scan")
async def zap_scan(target: RequestBody):
    async with httpx.AsyncClient() as client:
        # запускаем активный скан
        resp = await client.get(
            f"{ZAP_API_URL}/JSON/ascan/action/scan/",
            params={"apikey": ZAP_API_KEY, "url": target.target}
        )
        return resp.json()

@app.get("/zap/scan_status/{scan_id}")
async def zap_scan_status(scan_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ZAP_API_URL}/JSON/ascan/view/status/",
            params={"apikey": ZAP_API_KEY, "scanId": scan_id}
        )
        return resp.json()

@app.get("/zap/alerts")
async def zap_alerts():
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ZAP_API_URL}/JSON/core/view/alerts/",
            params={"apikey": ZAP_API_KEY}
        )
        return resp.json()


@app.get("/zap/alerts/target")
async def zap_alerts_with_evidence(baseurl: str = None):
    params = {"apikey": ZAP_API_KEY}
    if baseurl:
        params["baseurl"] = baseurl

    async with httpx.AsyncClient() as client:
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


@app.get("/zap/alerts/summary")
async def zap_alerts_summary():
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ZAP_API_URL}/JSON/core/view/alertsSummary/",
            params={"apikey": ZAP_API_KEY}
        )
        return resp.json()
