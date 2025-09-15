import asyncio
import os
from dotenv import load_dotenv
import httpx
from fastapi import FastAPI
from plugins.xss_reflected import run as xss_reflected_run
# создаём приложение
load_dotenv()
app = FastAPI()

DVWA_URL = "http://192.168.56.101/dvwa/"  # адрес DVWA
ZAP_API_KEY = os.getenv("ZAP_API_KEY", "changeme")
ZAP_API_URL = os.getenv("ZAP_API_URL", "http://localhost:8080")
# простой маршрут
@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI is working!"}

# пример с параметром
@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"Hello, {name}!"}


@app.post("/api/xss_reflected")
async def run_xss_reflected():
    context = {
        "safe_mode": True,
        # если у тебя есть авторизация — передай cookies: {"PHPSESSID": "..."}
        # "auth": {"cookies": {"PHPSESSID": "abc..."}},
        "param_candidates": ["name", "message", "id", "search"],
        "headers": {"User-Agent": "PTESBot/1.0"}
    }
    return await xss_reflected_run('http://192.168.56.101/vulnerabilities/xss_r/', context)

@app.get("/zap/spider")
async def zap_spider(target: str = "http://192.168.56.101/dvwa/"):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ZAP_API_URL}/JSON/spider/action/scan/",
            params={"apikey": ZAP_API_KEY, "url": target}
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


@app.get("/zap/scan")
async def zap_scan(target: str = "http://192.168.56.101/dvwa/"):
    async with httpx.AsyncClient() as client:
        # запускаем активный скан
        resp = await client.get(
            f"{ZAP_API_URL}/JSON/ascan/action/scan/",
            params={"apikey": ZAP_API_KEY, "url": target}
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


@app.get("/zap/alerts/summary")
async def zap_alerts_summary():
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ZAP_API_URL}/JSON/core/view/alertsSummary/",
            params={"apikey": ZAP_API_KEY}
        )
        return resp.json()
