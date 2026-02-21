import uuid
from pathlib import Path

from fastapi import APIRouter
from starlette.responses import FileResponse

from core.database import async_session
from models.scan_model import Scan
from models.vulnerability_model import Vulnerability
from schemas.report_schema import ReportRequest, DownloadReportRequest
from services.database_service import AsyncDatabaseService
from services.report_service import ReportService

router = APIRouter(prefix="/report", tags=["report"])

database_service = AsyncDatabaseService(async_session)
report_service = ReportService()


@router.post("/new")
async def report_new(body: ReportRequest):
    scan_data = await database_service.get(Scan, scan_id=body.scan_id)

    if scan_data.report_id:
        return {"report_id": scan_data.report_id}

    report_id = str(uuid.uuid4())
    await report_service.update_report_status(body.scan_id, "pending")
    vulns = await database_service.get_all(Vulnerability, scan_id=body.scan_id)
    path = report_service.generate_pdf_report(vulns, f"{report_id}.pdf")

    if path:
        await report_service.save_report_db(body.scan_id, report_id)
        await report_service.update_report_status(body.scan_id, "done")
        return {"report_id": report_id}

    return {"message": "Error while generating report.pdf"}


@router.post("/download")
async def report_download(body: DownloadReportRequest):
    scan_data = await database_service.get(Scan, report_id=body.report_id)

    if scan_data.report_id:
        pdf_path = Path(f"static/pdf/{body.report_id}.pdf")
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="vulnerability_report.pdf"
        )

    return {"message": "Error while downloading report.pdf"}
