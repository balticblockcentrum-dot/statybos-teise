from docx import Document

from lex import draft


def test_save_answer_three_formats(tmp_path):
    text = "# Antraštė\nĄČĘĖĮŠŲŪŽ ąčęėįšųūž\nCK 6.644 str. rangos sutartis."
    txt, docx, pdf = draft.save_answer(text, tmp_path / "atsakymas")
    assert txt.exists() and docx.exists() and pdf.exists()
    assert txt.read_text(encoding="utf-8") == text
    assert pdf.read_bytes()[:5] == b"%PDF-"
    assert docx.stat().st_size > 0


def test_pdf_embeds_lithuanian_font(tmp_path):
    _, _, pdf = draft.save_answer("Lietuviškos raidės ąčęėįšųūž", tmp_path / "a")
    data = pdf.read_bytes()
    assert b"Arial" in data or b"LexFont" in data


def test_docx_contains_body(tmp_path):
    _, docx, _ = draft.save_answer("# Title\nBody text", tmp_path / "a")
    doc = Document(str(docx))
    full = "\n".join(p.text for p in doc.paragraphs)
    assert "Body text" in full