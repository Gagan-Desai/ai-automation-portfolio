# pip install fastapi uvicorn python-multipart

import uuid
import io
import pdfplumber
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from rpds import List

from classifier import classify_document
from registry import DOCUMENT_REGISTRY
from extractor import extract_document
from confidence import assess_confidence

app = FastAPI()
jobs: dict = {}  # in-memory job store — see limitation note below

def process_document_job(job_id: str, text: str):
    try:
        doc_type = classify_document(text)

        if doc_type.value == "unknown":
            jobs[job_id] = {"status": "needs_review", "document_type": "unknown", "error": "Document did not match any registered type"}
            return

        config = DOCUMENT_REGISTRY[doc_type.value]
        result = extract_document(text, config["model"], config["instruction"])

        confidence = assess_confidence(text, result.model_dump())
        low_conf = [fc.field_name for fc in confidence.field_confidences if fc.confidence == "low"]

        jobs[job_id] = {
            "status": "needs_review" if low_conf else "success",
            "document_type": doc_type.value,
            "data": result.model_dump(),
             "confidence_details": [fc.model_dump() for fc in confidence.field_confidences]
        }
    except Exception as e:
        jobs[job_id] = {"status": "failed", "error": str(e)}


@app.post("/extract", status_code=202)
async def extract(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    contents = await file.read()
    with pdfplumber.open(io.BytesIO(contents)) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages)

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing"}
    background_tasks.add_task(process_document_job, job_id, text)

    return {"job_id": job_id, "status": "processing"}

@app.post("/extract-batch")
async def extract_batch(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    job_ids = []
    for file in files:
        contents = await file.read()
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            text = "\n".join(page.extract_text() for page in pdf.pages)
        job_id = str(uuid.uuid4())
        jobs[job_id] = {"status": "processing", "filename": file.filename}
        background_tasks.add_task(process_document_job, job_id, text)
        job_ids.append(job_id)
    return {"job_ids": job_ids}


@app.get("/status/{job_id}")
async def status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **jobs[job_id]}