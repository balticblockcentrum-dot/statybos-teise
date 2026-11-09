import pytest
from docx import Document

from lex import ingest


def test_txt_unicode(tmp_path):
    p = tmp_path / "doc.txt"
    p.write_text("Sutartis dėl rangos darbų. ĄČĘĖĮŠŲŪŽ", encoding="utf-8")
    assert ingest.extract_text(p) == "Sutartis dėl rangos darbų. ĄČĘĖĮŠŲŪŽ"


@pytest.mark.parametrize("suffix", [".txt", ".md", ".csv"])
def test_text_formats(tmp_path, suffix):
    p = tmp_path / ("doc" + suffix)
    p.write_text("tekstas", encoding="utf-8")
    assert ingest.extract_text(p) == "tekstas"


def test_docx_paragraphs_and_table(tmp_path):
    p = tmp_path / "doc.docx"
    doc = Document()
    doc.add_paragraph("Pirmas sakinys.")
    doc.add_paragraph("Antras sakinys.")
    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "A"
    table.cell(0, 1).text = "B"
    doc.save(str(p))
    out = ingest.extract_text(p)
    assert "Pirmas sakinys." in out
    assert "Antras sakinys." in out
    assert "A | B" in out


def test_doc_rejected(tmp_path):
    p = tmp_path / "doc.doc"
    p.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="doc"):
        ingest.extract_text(p)


def test_unknown_format(tmp_path):
    p = tmp_path / "doc.xyz"
    p.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="Nepalaikomas"):
        ingest.extract_text(p)


def test_pdf(tmp_path):
    from reportlab.pdfgen import canvas

    p = tmp_path / "doc.pdf"
    c = canvas.Canvas(str(p))
    c.drawString(72, 720, "Rangos sutartis CK 6.644")
    c.save()
    assert "Rangos" in ingest.extract_text(p)