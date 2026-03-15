import logging
import uuid
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from starlette.responses import FileResponse

from core.database import async_session
from models.scan_model import Scan
from models.vulnerability_model import Vulnerability
from schemas.report_schema import ReportRequest, DownloadReportRequest
from services.database_service import AsyncDatabaseService
from services.report_service import ReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/report", tags=["report"])

database_service = AsyncDatabaseService(async_session)
report_service = ReportService()


@router.post("/new")
async def report_new(body: ReportRequest):
    logger.info("report/new: scan_id=%s", body.scan_id)
    scan_data = await database_service.get(Scan, scan_id=body.scan_id)

    # Защита от AttributeError
    if not scan_data:
        logger.warning("report/new: scan_id=%s not found", body.scan_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    if scan_data.report_id:
        logger.info("report/new: returning existing report_id=%s", scan_data.report_id)
        return {"report_id": scan_data.report_id}

    report_id = str(uuid.uuid4())
    await report_service.update_report_status(body.scan_id, "pending")
    
    vulns = await database_service.get_all(Vulnerability, scan_id=body.scan_id)
    logger.info("report/new: vulns list count=%d", len(vulns))
    
    # Защита от блокировки Event Loop: выполняем синхронную генерацию PDF в пуле потоков
    safe_filename = f"{report_id}.pdf"
    path = await run_in_threadpool(report_service.generate_pdf_report, vulns, safe_filename)

    if path:
        await report_service.save_report_db(body.scan_id, report_id)
        await report_service.update_report_status(body.scan_id, "done")
        logger.info("report/new: created report_id=%s path=%s", report_id, path)
        return {"report_id": report_id}

    await report_service.update_report_status(body.scan_id, "failed")
    logger.error("report/new: PDF generation failed for scan_id=%s", body.scan_id)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error while generating report")


@router.post("/download")
async def report_download(body: DownloadReportRequest):
    logger.info("report/download: report_id=%s", body.report_id)
    scan_data = await database_service.get(Scan, report_id=body.report_id)

    # Защита от AttributeError
    if not scan_data or not scan_data.report_id:
        logger.warning("report/download: scan not found for report_id=%s", body.report_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    # Строгая защита от Path Traversal: извлекаем только имя (на случай инъекции в report_id)
    secure_filename = os.path.basename(f"{body.report_id}.pdf")
    pdf_path = Path("static/pdf") / secure_filename

    # Проверка физического наличия файла на диске перед отдачей
    if not pdf_path.is_file():
        logger.error("report/download: file missing on disk path=%s", pdf_path)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report file not found on server")

    logger.info("report/download: serving path=%s", pdf_path)
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename="vulnerability_report.pdf"
    )