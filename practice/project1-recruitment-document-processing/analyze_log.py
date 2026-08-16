# analyze_log.py
import json

with open("processing.log") as f:
    events = [json.loads(line) for line in f]

resignation_classifications = [e["document_type"] for e in events
                                 if e.get("file") == "resignation_letter_chen.pdf" and "document_type" in e]
print("Resignation letter classified as, across all runs:", resignation_classifications)