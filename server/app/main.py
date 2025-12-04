import asyncio
import os
import uuid
from datetime import datetime
from controllers import user_controller, auth_controller
from dotenv import load_dotenv
import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from starlette.responses import FileResponse
from pathlib import Path

from core.security import get_current_user
from models.users_model import User
from schemas.exploiter_schema import ExploiterRequestBody
from schemas.report_schema import VulnerabilityReport, ReportRequest, DownloadReportRequest
from schemas.zap_scanner_schema import RequestBody
from services.database_service import AsyncDatabaseService
from services.exploiter_service import ExploiterService
from services.llm_service import LLMService
from services.playwright_service import login_and_save_session
from services.report_service import ReportService
from fastapi.middleware.cors import CORSMiddleware
from core.database import init_models, async_session
from models.scan_model import Scan
from models.vulnerability_model import Vulnerability
from schemas.report_schema import Vulnerability as VulnerabilitySchema
load_dotenv()
app = FastAPI()

llm_service = LLMService()
exploiter_service = ExploiterService()
report_service = ReportService()
database_service = AsyncDatabaseService(async_session)

ZAP_API_KEY = os.getenv("ZAP_API_KEY", "changeme")
ZAP_API_URL = os.getenv("ZAP_API_URL", "http://localhost:8080")

@app.on_event("startup")
async def startup_event():
    await init_models()

origins = (["http://localhost:5173", "http://127.0.0.1:5173"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def zap_scan(target: RequestBody, background_tasks: BackgroundTasks, user: User=Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ZAP_API_URL}/JSON/ascan/action/scan/",
            params={"apikey": ZAP_API_KEY, "url": target.target},
        )
        data = resp.json()

    scan_data = Scan(target=target.target, created_at=datetime.utcnow(), zap_index=int(data.get("scan")), user_id=user.user_id)
    created_scan = await database_service.create(scan_data)
    background_tasks.add_task(run_scan, created_scan.scan_id, target.target, str(created_scan.zap_index))

    return {"scan_id": created_scan.scan_id, "scan_index": data.get("scan")}

async def run_scan(scan_id: int, target_url: str, scan_index: str):
    try:
        async with httpx.AsyncClient() as client:
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

@app.get("/zap/abort/scan/{scan_id}")
async def zap_abort(scan_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ZAP_API_URL}/JSON/ascan/action/stop/",
            params={"apikey": ZAP_API_KEY, "scanId": scan_id}
        )
        return resp.json()

@app.post("/exploiter/run")
async def exploiter_run(body: ExploiterRequestBody):
    try:
        payloads_task = asyncio.create_task(
            llm_service.ask_for_payloads(body.target, body.vuln_type, body.params)
        )

        print(f"[+] Логинимся в {body.login_url} как {body.username}...")
        cookies = login_and_save_session(
            login_url=body.login_url.rsplit("/", 1)[0] + "/login.php",
            username=body.username,
            password=body.password,
            headless=True,
            slow_mo=1
        )
        print("[+] Успешно залогинен!")

        payloads = await payloads_task
        if not payloads:
            payloads = ["<script>alert(1)</script>", "\"'><img src=x onerror=alert(1)>"]

        print(f"[+] Получено {len(payloads)} payload'ов от ИИ")

        for payload in payloads:
            success, message, curl_command = exploiter_service.try_exploit(
                vuln_type=body.vuln_type,
                url=body.target,
                method=body.method,
                param=body.params,
                data={"payloads": payload},
                cookies=cookies,
            )
            print(message)
            if success:
                return {
                    "status": "confirmed",
                    "vuln_type": body.vuln_type,
                    "target": body.target,
                    "parameter": body.params,
                    "working_payload": payload,
                    "proof": message,
                    "curl": curl_command,
                    "message": "Уязвимость успешно подтверждена и эксплуатирована!"
                }

        return {
            "status": "potential",
            "message": "Ни один payload не сработал. Возможно, нужна ручная проверка.",
            "tried_payloads": payloads[:10]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при эксплуатации: {str(e)}")

@app.post("/report/new")
async def report_new(body: ReportRequest):
    scan_data = await database_service.get(Scan, scan_id=body.scan_id)

    if scan_data.report_id:
        return {"report_id":scan_data.report_id}

    report_id = str(uuid.uuid4())
    await report_service.update_report_status(body.scan_id, "pending")
    vulns = await database_service.get_all(Vulnerability, scan_id=body.scan_id)
    path = report_service.generate_pdf_report(vulns, f"{report_id}.pdf")

    if path:
        await report_service.save_report_db(body.scan_id, report_id)
        await report_service.update_report_status(body.scan_id, "done")
        return {"report_id": report_id}

    return {"message": "Error while generating report.pdf"}

@app.post("/report/download")
async def report_new(body: DownloadReportRequest):
    scan_data = await database_service.get(Scan, report_id=body.report_id)

    if scan_data.report_id:
        pdf_path = Path(f"static/pdf/{body.report_id}.pdf")
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="vulnerability_report.pdf"
        )

    return {"message":"Error while downloading report.pdf"}

app.include_router(user_controller.router, prefix="/api")
app.include_router(auth_controller.router, prefix="/api")