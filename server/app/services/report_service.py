import logging
import os
import uuid
from xml.sax.saxutils import escape

from core.database import async_session
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from models.scan_model import Scan
from services.database_service import AsyncDatabaseService

logger = logging.getLogger(__name__)

styles = getSampleStyleSheet()
styles['Normal'].fontName = 'Times-Roman'
styles['Heading2'].fontName = 'Times-Bold'

database_service = AsyncDatabaseService(async_session)


class ReportService:
    @staticmethod
    def generate_pdf_report(vulns, filename="vulnerability_report.pdf"):
        logger.debug("Starting PDF report generation", extra={"filename": filename, "vulns_count": len(vulns)})

        output_dir = "static/pdf"
        os.makedirs(output_dir, exist_ok=True)

        # 1. Защита от Path Traversal: извлекаем только имя файла, игнорируя пути
        secure_filename = os.path.basename(filename)
        output_path = os.path.join(output_dir, secure_filename)
        logger.debug("Resolved secure output path for report", extra={"output_path": output_path})

        # Отфильтруем дубликаты по cweid
        unique_vulns = []
        seen_keys = set()

        for v in vulns:
            # Уязвимости без cweid (None) сохраняем всегда, чтобы не потерять данные
            cwe_clean = str(v.cweid).strip().upper() if v.cweid else None
            name_clean = str(v.name).strip().upper() if v.name else "UNKNOWN"
            filter_key = cwe_clean if cwe_clean else name_clean
            if filter_key in seen_keys:
                continue  # Пропускаем дубликат
                
            seen_keys.add(filter_key)
            unique_vulns.append(v)

        logger.debug(
            "Finished filtering vulnerabilities for report",
            extra={
                "original_count": len(vulns),
                "unique_count": len(unique_vulns),
                "unique_cweids": list(seen_keys),
            },
        )

        story = [Paragraph("Vulnerabilities Report", styles["Title"]), Spacer(1, 20)]

        # Используем отфильтрованный список unique_vulns
        for idx, v in enumerate(unique_vulns, start=1):
            logger.debug(
                "Adding vulnerability to PDF story",
                extra={
                    "index": idx,
                    "name": getattr(v, "name", None),
                    "cweid": getattr(v, "cweid", None),
                    "risk": getattr(v, "risk", None),
                },
            )

            # 2. Защита от XML/HTML Injection: экранируем все данные из БД
            safe_name = escape(str(v.name))
            safe_desc = escape(str(v.description))
            safe_risk = escape(str(v.risk))
            safe_url = escape(str(v.url))
            safe_method = escape(str(v.method))

            story.append(Paragraph(f"<b>{idx}. {safe_name}</b>", styles["Heading2"]))
            story.append(Spacer(1, 5))

            story.append(Paragraph(f"<b>Description:</b> {safe_desc}", styles["BodyText"]))
            story.append(Spacer(1, 5))

            story.append(Paragraph("Tags:", styles['Heading2']))
            for tag, link in v.tags.items():
                if link:
                    safe_tag = escape(str(tag))
                    # Дополнительно экранируем кавычки для атрибута внутри тега
                    safe_link = escape(str(link), entities={'"': "&quot;"})

                    # Защита от вредоносных ссылок (например, javascript:...)
                    if safe_link.startswith(('http://', 'https://')):
                        story.append(Paragraph(f'<a href="{safe_link}">{safe_tag}</a>', styles['Normal']))
                        story.append(Spacer(1, 5))

            if v.references:
                for ref in v.references:
                    safe_ref = escape(str(ref))
                    story.append(Paragraph(safe_ref, styles["BodyText"]))

            story.append(Spacer(1, 5))
            story.append(Paragraph(f"<b>Risk:</b> {safe_risk}", styles["BodyText"]))
            story.append(Paragraph(f"<b>URL:</b> {safe_url}", styles["BodyText"]))
            story.append(Paragraph(f"<b>Method:</b> {safe_method}", styles["BodyText"]))

            story.append(Spacer(1, 20))

        pdf = SimpleDocTemplate(output_path, pagesize=A4)
        pdf.build(story)

        logger.debug("PDF report successfully generated", extra={"output_path": output_path})
        return output_path

    @staticmethod
    async def save_report_db(scan_id: str, report_id: str):
        logger.debug(
            "Saving report reference in database",
            extra={"scan_id": scan_id, "report_id": report_id},
        )
        await database_service.update(Scan, {"scan_id": scan_id}, {"report_id": report_id})

    @staticmethod
    async def update_report_status(scan_id: str, status: str):
        logger.debug(
            "Updating report status in database",
            extra={"scan_id": scan_id, "status": status},
        )
        await database_service.update(Scan, {"scan_id": scan_id}, {"report_status": status})