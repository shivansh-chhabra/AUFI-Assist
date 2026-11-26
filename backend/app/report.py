"""Server-side PDF of a finished case: ranking, answers, per-disease summary, recommended tests, sources."""
import datetime as dt
import io
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .conditions import condition_name
from .pipeline import ANSWER_LABEL
from .session import Session

_FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/dejavu",
    "/Library/Fonts",
    "C:/Windows/Fonts",
]


def _register_fonts() -> tuple[str, str]:
    """Prefer DejaVu (full Unicode); fall back to Helvetica."""
    for d in _FONT_DIRS:
        reg, bold = Path(d) / "DejaVuSans.ttf", Path(d) / "DejaVuSans-Bold.ttf"
        if reg.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont("AUFI", str(reg)))
            pdfmetrics.registerFont(TTFont("AUFI-Bold", str(bold)))
            return "AUFI", "AUFI-Bold"
    return "Helvetica", "Helvetica-Bold"


def _clean(text: str, unicode_ok: bool) -> str:
    text = escape(text or "")
    if not unicode_ok:
        text = text.encode("cp1252", "replace").decode("cp1252")
    return text


def build_pdf(s: Session) -> bytes:
    font, bold = _register_fonts()
    uni = font == "AUFI"
    c = lambda t: _clean(t, uni)  # noqa: E731

    ss = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=ss["BodyText"], fontName=font, fontSize=10, leading=14)
    small = ParagraphStyle("small", parent=body, fontSize=8.5, leading=11, textColor=colors.HexColor("#555555"))
    h1 = ParagraphStyle("h1", parent=body, fontName=bold, fontSize=18, leading=22, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=body, fontName=bold, fontSize=13, leading=17, spaceBefore=14, spaceAfter=6)
    h3 = ParagraphStyle("h3", parent=body, fontName=bold, fontSize=10.5, leading=14, spaceBefore=8, spaceAfter=2)

    sources = {x["id"]: x for x in (s.evidence or {}).get("sources", [])}

    def rich(text: str) -> str:
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", c(text))
        t = re.sub(r"(?m)^- ", "&bull; ", t)
        return t.replace("\n\n", "<br/><br/>").replace("\n", "<br/>")

    def cited(text: str, cites: list[int]) -> str:
        return rich(text) + " " + "".join(f"<super>[{n}]</super>" for n in cites)

    story = [
        Paragraph("AUFI Assist: case summary", h1),
        Paragraph(c(f"Generated {dt.datetime.now():%d %b %Y, %H:%M}. Decision support only, not a diagnosis."), small),
        Spacer(1, 6),
        Paragraph(
            c("This summary ranks possible causes of acute undifferentiated fever from the patient's answers and "
              "lists the recommended confirmatory tests and a short summary of the likely conditions. It must be reviewed by a doctor."),
            body,
        ),
    ]

    # ranking
    story.append(Paragraph("Most likely conditions", h2))
    rows = [["Condition", "Probability"]]
    for cid, p in sorted(s.posterior.items(), key=lambda kv: kv[1], reverse=True):
        mark = "  (shortlisted)" if cid in s.shortlist else ""
        rows.append([c(condition_name(cid)) + mark, f"{round(p * 100)}%" if p >= 0.01 else "<1%"])
    t = Table(rows, colWidths=[110 * mm, 30 * mm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font), ("FONTNAME", (0, 0), (-1, 0), bold),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))
    story.append(t)

    # recommended tests (pulled out so they are easy to find)
    tests = []
    for e in s.explanation or []:
        for sec in e["sections"]:
            if sec["contentType"] == "confirmatory_tests":
                tests.append((e["disease"], sec))
    story.append(Paragraph("Recommended tests", h2))
    if tests:
        for disease, sec in tests:
            story.append(Paragraph(c(disease), h3))
            story.append(Paragraph(cited(sec["text"], sec["citations"]), body))
    else:
        story.append(Paragraph("No guideline-backed test recommendation was available for this case.", body))

    # per-disease detail (the shortlisted conditions; the fixed summaries)
    detail = [e for e in (s.explanation or []) if e.get("info") and e["diseaseId"] in s.shortlist]
    if detail:
        story.append(Paragraph("Summary by condition", h2))
        for e in detail:
            i = e["info"]
            story.append(Paragraph(c(e["disease"]), h3))
            story.append(Paragraph(c(i["summary"]), body))
            story.append(Spacer(1, 3))
            story.append(Paragraph(f"<b>Caused by.</b> {c(i['causativeAgent'])}", body))
            story.append(Paragraph(f"<b>How it spreads.</b> {c(i['transmission'])}", body))
            story.append(Paragraph("<b>Prevention.</b>", body))
            for m in i["preventiveMethods"]:
                story.append(Paragraph("&bull; " + c(m), body))
            story.append(Spacer(1, 3))

    # answers
    story.append(Paragraph("Patient's answers", h2))
    story.append(Paragraph(c("Initial description: " + (s.initial_text or "(none)")), body))
    if s.asked:
        arows = [["Question", "Answer"]] + [[Paragraph(c(a["text"]), body), ANSWER_LABEL.get(a["answer"], a["answer"])] for a in s.asked]
        at = Table(arows, colWidths=[130 * mm, 30 * mm])
        at.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), font), ("FONTNAME", (0, 0), (-1, 0), bold),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5), ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
        ]))
        story += [Spacer(1, 4), at]

    # sources
    if sources:
        story.append(Paragraph("Guideline sources", h2))
        for n, src in sources.items():
            tag = f" ({src['body']})" if src.get("body") else ""
            story.append(Paragraph(c(f"[{n}] {src['title']}{tag}, {src['location']}"), small))

    buf = io.BytesIO()
    SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
        title="AUFI Assist case summary",
    ).build(story)
    return buf.getvalue()
