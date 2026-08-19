import os
from pydoc import text
import pdfplumber


def extract_text_from_pdfs():
    document_texts = {}
    for filename in os.listdir("resources"):
        if not filename.endswith(".pdf"):
            continue
        filepath = os.path.join("resources", filename)
        with pdfplumber.open(filepath) as pdf:
            text = "\n".join(page.extract_text() for page in pdf.pages)
            document_texts[filename] = text

            

    return document_texts