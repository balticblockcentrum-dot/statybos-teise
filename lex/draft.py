from pathlib import Path

from docx import Document


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
    return txt, docx