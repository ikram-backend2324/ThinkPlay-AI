"""
Extracts plain text from an uploaded .docx or .pdf file so it can be handed
to either the strict template parser or the AI parser.
"""

import io

import docx
from pypdf import PdfReader


class ExtractionError(Exception):
    pass


def extract_text(uploaded_file):
    name = (uploaded_file.name or "").lower()
    data = uploaded_file.read()

    if name.endswith(".docx"):
        document = docx.Document(io.BytesIO(data))
        text = "\n".join(p.text for p in document.paragraphs if p.text.strip())
    elif name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    else:
        raise ExtractionError("Please upload a .docx or .pdf file.")

    if not text.strip():
        raise ExtractionError("Couldn't find any text in that file.")
    return text
