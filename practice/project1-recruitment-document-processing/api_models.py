
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel

class JobStatus(str, Enum):
    processing = "processing"
    success = "success"
    needs_review = "needs_review"
    failed = "failed"

class ExtractResponse(BaseModel):
    job_id: str
    status: JobStatus

class StatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    document_type: Optional[str] = None
    data: Optional[dict] = None
    low_confidence_fields: Optional[List[str]] = None
    error: Optional[str] = None