from pathlib import Path


def extract_text(path):
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(p))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif suffix in (".docx", ".doc"):
        if suffix == ".doc":
            raise ValueError(".doc formatas nepalaikomas; issaugokite kaip .docx")
        from docx import Document
        doc = Document(str(p))
        parts = [para.text for para in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text for cell in row.cells))
        text = "\n".join(parts)
    elif suffix in (".txt", ".md", ".csv"):
        text = p.read_text(encoding="utf-8", errors="replace")
    else:
        raise ValueError(f"Nepalaikomas formatas: {suffix}")
    if not text.strip():
        raise ValueError(
            "Dokumentas tuščias arba be teksto sluoksnio (nuskaitytas vaizdas). "
            "Reikalingas OCR arba tekstinis dokumentas."
        )
    return text