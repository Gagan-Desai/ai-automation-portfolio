import os
import pdfplumber
from classifier import classify_document
from registry import DOCUMENT_REGISTRY
from extractor import extract_document
from confidence import assess_confidence
from logger_setup import setup_logger, log_event

logger = setup_logger()

def process_folder(folder_path: str):
    results = []
    for filename in os.listdir(folder_path):
        if not filename.endswith(".pdf"):
            continue
        filepath = os.path.join(folder_path, filename)
        try:
            with pdfplumber.open(filepath) as pdf:
                text = "\n".join(page.extract_text() for page in pdf.pages)

            doc_type = classify_document(text)
            log_event(logger, "info", "Document classified", file=filename, document_type=doc_type.value)
            #print(f"{filename}: classified as {doc_type.value}")

            if doc_type.value == "unknown":
                log_event(logger, "warning", "Document did not match any registered type", file=filename)
                results.append({"file": filename, "type": "unknown", "data": None, "status": "needs_review", "error": "Document did not match any registered type"})
                continue
            config = DOCUMENT_REGISTRY[doc_type.value]
            result = extract_document(text, config["model"], config["instruction"])
            
            confidence = assess_confidence(text, result.model_dump())
            low_confidence_fields = [fc.field_name for fc in confidence.field_confidences if fc.confidence == "low"]

            if low_confidence_fields:
              log_event(logger, "warning", "Low-confidence fields flagged", file=filename, fields=low_confidence_fields)
            else:
                log_event(logger, "info", "Extraction succeeded cleanly", file=filename, document_type=doc_type.value)
            
            status = "needs_review" if low_confidence_fields else "success"
            results.append({"file": filename, "type": doc_type.value, "data": result, "status": status})

        except Exception as e:
            log_event(logger, "error", "Document processing failed", file=filename, error=str(e))
            results.append({"file": filename, "type": None, "data": None, "status": "failed", "error": str(e)})

    return results


if __name__ == "__main__":
    results = process_folder("inbox")
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results:
        print(f"\n{r['file']} [{r['status']}] -> {r['type']}")
        if r["status"] == "success":
            print(r["data"])
        else:
            print(f"  Error: {r['error']}")