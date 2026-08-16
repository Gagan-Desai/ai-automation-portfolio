# debug_confidence.py
import pdfplumber
from confidence import assess_confidence
from extractor import extract_document
from registry import DOCUMENT_REGISTRY
from classifier import classify_document

with pdfplumber.open("inbox/reference_letter_osei.pdf") as pdf:
    text = "\n".join(page.extract_text() for page in pdf.pages)

doc_type = classify_document(text)
config = DOCUMENT_REGISTRY[doc_type.value]
result = extract_document(text, config["model"], config["instruction"])

confidence = assess_confidence(text, result.model_dump())

for fc in confidence.field_confidences:
    print(f"{fc.field_name}: {fc.confidence}")
    print(f"  reason: {fc.reason}\n")