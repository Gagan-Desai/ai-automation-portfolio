import os
from pydoc import text
import pdfplumber

def extract_page_content(page):
    tables = page.extract_tables()
    if tables:
        table_text = ""
        for table in tables:
            for row in table:
                clean_row = [str(cell) if cell else "" for cell in row]
                table_text += " | ".join(clean_row) + "\n"
        return table_text
    return page.extract_text() or ""

def extract_all_documents(filenames: list[str]) -> dict:
    document_texts = {}
    for filename in filenames:
        with pdfplumber.open(filename) as pdf:
            text = "\n".join(extract_page_content(page) for page in pdf.pages)
            document_texts[filename] = text
    return document_texts

