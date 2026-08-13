import os
import pdfplumber
from classifier import classify_document
from registry import DOCUMENT_REGISTRY
from extractor import extract_document

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
            print(f"{filename}: classified as {doc_type.value}")

            config = DOCUMENT_REGISTRY[doc_type.value]
            result = extract_document(text, config["model"], config["instruction"])
            results.append({"file": filename, "type": doc_type.value, "data": result, "status": "success"})

        except Exception as e:
            print(f"FAILED: {filename} — {e}")
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