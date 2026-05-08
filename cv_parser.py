from io import BytesIO

import pdfplumber
from docx import Document


def extract_text_from_upload(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    content = uploaded_file.read()

    if name.endswith(".pdf"):
        return _from_pdf(content)
    if name.endswith((".docx", ".doc")):
        return _from_docx(content)
    raise ValueError(
        f"Nepodporovaný formát: {name.split('.')[-1].upper()}. Nahraj prosím PDF nebo DOCX."
    )


def _from_pdf(content: bytes) -> str:
    pages = []
    with pdfplumber.open(BytesIO(content)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    if not pages:
        raise ValueError(
            "Z PDF se nepodařilo extrahovat text. Ujisti se, že soubor není skenovaný obrázek."
        )
    return "\n\n".join(pages)


def _from_docx(content: bytes) -> str:
    doc = Document(BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    if not paragraphs:
        raise ValueError("Z DOCX se nepodařilo extrahovat text. Soubor je pravděpodobně prázdný.")
    return "\n".join(paragraphs)
