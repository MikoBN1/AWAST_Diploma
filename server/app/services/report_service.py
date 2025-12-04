import uuid

from core.database import async_session
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

from models.scan_model import Scan
from services.database_service import AsyncDatabaseService

styles = getSampleStyleSheet()
styles['Normal'].fontName = 'Times-Roman'
styles['Heading2'].fontName = 'Times-Bold'

database_service = AsyncDatabaseService(async_session)

class ReportService:
    @staticmethod
    def generate_pdf_report(vulns, filename="vulnerability_report.pdf"):
        output_dir = "static/pdf"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)

        story = [Paragraph("Vulnerabilities Report", styles["Title"]), Spacer(1, 20)]

        for idx, v in enumerate(vulns, start=1):
            story.append(Paragraph(f"<b>{idx}. {v.name}</b>", styles["Heading2"]))
            story.append(Spacer(1, 5))

            story.append(Paragraph(f"<b>Description:</b> {v.description}", styles["BodyText"]))
            story.append(Spacer(1, 5))

            story.append(Paragraph("Tags:", styles['Heading2']))
            for tag, link in v.tags.items():
                if link:  # если ссылка не пустая
                    story.append(Paragraph(f'<a href="{link}">{tag}</a>', styles['Normal']))
                    story.append(Spacer(1, 5))

            if v.references:
                for ref in v.references:
                    story.append(Paragraph(str(ref), styles["BodyText"]))

            story.append(Spacer(1, 5))
            story.append(Paragraph(f"<b>Risk:</b> {v.risk}", styles["BodyText"]))
            story.append(Paragraph(f"<b>URL:</b> {v.url}", styles["BodyText"]))
            story.append(Paragraph(f"<b>Method:</b> {v.method}", styles["BodyText"]))

            story.append(Spacer(1, 20))

        pdf = SimpleDocTemplate(output_path, pagesize=A4)
        pdf.build(story)

        return output_path


    @staticmethod
    async def save_report_db(scan_id:str, report_id:str):
        await database_service.update(Scan, {"scan_id": scan_id}, {"report_id": report_id})

    @staticmethod
    async def update_report_status(scan_id: str, status: str):
        await database_service.update(Scan, {"scan_id": scan_id}, {"report_status": status})
