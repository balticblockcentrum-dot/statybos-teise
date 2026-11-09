import os
from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def _register_font():
    fonts_dir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    for name in ("arial.ttf", "segoeui.ttf", "calibri.ttf"):
        candidate = fonts_dir / name
        if candidate.exists():
            pdfmetrics.registerFont(TTFont("LexFont", str(candidate)))
            return "LexFont"
    return "Helvetica"


def _save_pdf(text, path):
    font = _register_font()
    body = ParagraphStyle("body", fontName=font, fontSize=11, leading=15, spaceAfter=6)
    heading = ParagraphStyle("heading", fontName=font, fontSize=14, leading=18, spaceBefore=10, spaceAfter=8)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title="Statybos teisės asistento atsakymas",
    )
    story = [Paragraph("Statybos teisės asistento atsakymas", heading), Spacer(1, 4 * mm)]
    for block in text.split("\n"):
        line = block.rstrip()
        if not line:
            continue
        if line.startswith("#"):
            story.append(Paragraph(escape(line.lstrip("# ").strip()), heading))
        else:
            story.append(Paragraph(escape(line), body))
    doc.build(story)
    return path


def save_answer(text, out_base):
    out_base = Path(out_base)
    txt = out_base.with_suffix(".txt")
    txt.write_text(text, encoding="utf-8")

    doc = Document()
    doc.add_heading("Statybos teisės asistento atsakymas", level=0)
    for block in text.split("\n"):
        line = block.rstrip()
        if not line:
            continue
        if line.startswith("#"):
            doc.add_heading(line.lstrip("# ").strip(), level=1)
        else:
            doc.add_paragraph(line)
    docx = out_base.with_suffix(".docx")
    doc.save(str(docx))

    pdf = _save_pdf(text, out_base.with_suffix(".pdf"))
    return txt, docx, pdf