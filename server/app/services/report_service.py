import logging
import os
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.pdfgen import canvas

from core.database import async_session
from models.scan_model import Scan
from services.database_service import AsyncDatabaseService

logger = logging.getLogger(__name__)

# Risk level to hex color (for badges and table rows)
RISK_COLORS = {
    "critical": colors.HexColor("#8B0000"),   # dark red
    "high": colors.HexColor("#C0392B"),       # red
    "medium": colors.HexColor("#D4A017"),     # amber/gold
    "low": colors.HexColor("#2980B9"),        # blue
    "info": colors.HexColor("#7F8C8D"),      # gray
}

# Light backgrounds for table cells
RISK_BG = {
    "critical": colors.HexColor("#FFEBEE"),
    "high": colors.HexColor("#FFCDD2"),
    "medium": colors.HexColor("#FFF8E1"),
    "low": colors.HexColor("#E3F2FD"),
    "info": colors.HexColor("#ECEFF1"),
}

database_service = AsyncDatabaseService(async_session)


def _risk_key(risk: str) -> str:
    """Normalize risk string for color lookup."""
    if not risk:
        return "info"
    r = str(risk).strip().lower()
    for k in ("critical", "high", "medium", "low", "info"):
        if k in r:
            return k
    return "info"


def _get_risk_color(risk: str, bg: bool = False):
    d = RISK_BG if bg else RISK_COLORS
    return d.get(_risk_key(risk), d["info"])


class NumberedCanvas(canvas.Canvas):
    """Canvas that draws page numbers in the footer."""

    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._page_num = 0

    def showPage(self):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#666666"))
        self.drawRightString(A4[0] - 0.75 * inch, 0.5 * inch, f"Page {self._page_num + 1}")
        self.restoreState()
        self._page_num += 1
        canvas.Canvas.showPage(self)


class ReportService:
    @staticmethod
    def _build_styles():
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="ReportTitle",
            parent=styles["Heading1"],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor("#1A237E"),
            alignment=1,
        ))
        styles.add(ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            fontSize=14,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor("#283593"),
        ))
        styles.add(ParagraphStyle(
            name="Body",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=6,
        ))
        styles.add(ParagraphStyle(
            name="Caption",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#555555"),
            spaceAfter=4,
        ))
        styles["Normal"].fontName = "Helvetica"
        styles["Heading2"].fontName = "Helvetica-Bold"
        return styles

    @staticmethod
    def generate_pdf_report(vulns, filename="vulnerability_report.pdf"):
        logger.debug("Starting PDF report generation", extra={"filename": filename, "vulns_count": len(vulns)})

        output_dir = "static/pdf"
        os.makedirs(output_dir, exist_ok=True)
        secure_filename = os.path.basename(filename)
        output_path = os.path.join(output_dir, secure_filename)
        logger.debug("Resolved secure output path for report", extra={"output_path": output_path})

        unique_vulns = []
        seen_keys = set()
        for v in vulns:
            cwe_clean = str(v.cweid).strip().upper() if v.cweid else None
            name_clean = str(v.name).strip().upper() if v.name else "UNKNOWN"
            filter_key = cwe_clean if cwe_clean else name_clean
            if filter_key in seen_keys:
                continue
            seen_keys.add(filter_key)
            unique_vulns.append(v)

        logger.debug(
            "Finished filtering vulnerabilities for report",
            extra={"original_count": len(vulns), "unique_count": len(unique_vulns), "unique_cweids": list(seen_keys)},
        )

        styles = ReportService._build_styles()
        story = []

        # ----- Cover / Title -----
        story.append(Spacer(1, 1.5 * inch))
        story.append(Paragraph("Vulnerability Assessment Report", styles["ReportTitle"]))
        story.append(Paragraph(
            f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            styles["Caption"],
        ))
        story.append(Spacer(1, 0.3 * inch))

        # Summary table (counts by risk)
        risk_counts = {}
        for v in unique_vulns:
            k = _risk_key(str(v.risk))
            risk_counts[k] = risk_counts.get(k, 0) + 1
        for rk in ("critical", "high", "medium", "low", "info"):
            risk_counts.setdefault(rk, 0)

        summary_data = [
            ["Total vulnerabilities", str(len(unique_vulns))],
            ["Critical", str(risk_counts["critical"])],
            ["High", str(risk_counts["high"])],
            ["Medium", str(risk_counts["medium"])],
            ["Low", str(risk_counts["low"])],
            ["Info", str(risk_counts["info"])],
        ]
        summary_table = Table(summary_data, colWidths=[3 * inch, 1.5 * inch])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E8EAF6")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1A237E")),
            ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#283593")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9FA8DA")),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ]))
        story.append(summary_table)
        story.append(PageBreak())

        # ----- Executive summary -----
        story.append(Paragraph("Executive Summary", styles["SectionTitle"]))
        story.append(Paragraph(
            "This report lists unique findings from the security scan, grouped by severity. "
            "Address critical and high severity issues first.",
            styles["Body"],
        ))
        story.append(Spacer(1, 12))

        exec_data = [["Severity", "Count", "Description"]]
        for label, key in [("Critical", "critical"), ("High", "high"), ("Medium", "medium"), ("Low", "low"), ("Info", "info")]:
            count = risk_counts[key]
            desc = {
                "critical": "Immediate action required.",
                "high": "Fix as soon as possible.",
                "medium": "Plan remediation.",
                "low": "Consider in next release.",
                "info": "Informational only.",
            }[key]
            exec_data.append([label, str(count), desc])

        exec_table = Table(exec_data, colWidths=[1.2 * inch, 0.8 * inch, 3.5 * inch])
        exec_styles = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3949AB")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9FA8DA")),
        ]
        for i, (label, _, _) in enumerate(exec_data[1:], start=1):
            key = label.lower()
            exec_styles.append(("BACKGROUND", (0, i), (0, i), _get_risk_color(key, bg=True)))
            exec_styles.append(("TEXTCOLOR", (0, i), (0, i), _get_risk_color(key)))
        exec_styles.append(("ROWBACKGROUNDS", (1, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]))
        exec_table.setStyle(TableStyle(exec_styles))
        story.append(exec_table)
        story.append(Spacer(1, 24))

        # ----- Findings -----
        story.append(Paragraph("Findings", styles["SectionTitle"]))
        story.append(Spacer(1, 8))

        for idx, v in enumerate(unique_vulns, start=1):
            safe_name = escape(str(v.name))
            safe_desc = escape(str(v.description))
            safe_risk = escape(str(v.risk))
            safe_url = escape(str(v.url))
            safe_method = escape(str(v.method))
            risk_k = _risk_key(str(v.risk))
            badge_color = _get_risk_color(str(v.risk))
            bg_color = _get_risk_color(str(v.risk), bg=True)

            # Risk badge + title row
            badge_table = Table(
                [[Paragraph(f"<b>{safe_risk.upper()}</b>", ParagraphStyle(name="Badge", fontSize=9, textColor=badge_color, fontName="Helvetica-Bold"))]],
                colWidths=[1.2 * inch],
            )
            badge_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), bg_color),
                ("BOX", (0, 0), (-1, -1), 1, badge_color),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))

            story.append(Paragraph(f"<b>{idx}. {safe_name}</b>", styles["Heading2"]))
            story.append(Spacer(1, 4))
            story.append(badge_table)
            story.append(Spacer(1, 6))

            if getattr(v, "cweid", None):
                safe_cwe = escape(str(v.cweid))
                story.append(Paragraph(f"<b>CWE:</b> {safe_cwe}", styles["Caption"]))
                story.append(Spacer(1, 4))

            story.append(Paragraph("<b>Description</b>", styles["Caption"]))
            story.append(Paragraph(safe_desc, styles["Body"]))
            story.append(Spacer(1, 6))

            # URL, Method in a small table
            meta_data = [
                ["URL", safe_url[:80] + ("..." if len(safe_url) > 80 else "")],
                ["Method", safe_method],
            ]
            meta_table = Table(meta_data, colWidths=[0.9 * inch, 4.6 * inch])
            meta_table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEEEEE")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#BDBDBD")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(meta_table)
            story.append(Spacer(1, 6))

            if getattr(v, "solution", None) and str(v.solution).strip():
                safe_sol = escape(str(v.solution))
                story.append(Paragraph("<b>Recommendation</b>", styles["Caption"]))
                story.append(Paragraph(safe_sol, styles["Body"]))
                story.append(Spacer(1, 6))

            if getattr(v, "tags", None) and v.tags:
                story.append(Paragraph("<b>Tags</b>", styles["Caption"]))
                for tag, link in v.tags.items():
                    if link:
                        safe_tag = escape(str(tag))
                        safe_link = escape(str(link), entities={'"': "&quot;"})
                        if safe_link.startswith(("http://", "https://")):
                            story.append(Paragraph(f'<a href="{safe_link}" color="#1565C0">{safe_tag}</a>', styles["Body"]))
                story.append(Spacer(1, 6))

            if getattr(v, "references", None) and v.references:
                story.append(Paragraph("<b>References</b>", styles["Caption"]))
                for ref in v.references:
                    story.append(Paragraph(escape(str(ref)), styles["Body"]))
                story.append(Spacer(1, 6))

            story.append(Spacer(1, 16))

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=1.0 * inch,
        )
        doc.build(story, canvasmaker=NumberedCanvas)

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
