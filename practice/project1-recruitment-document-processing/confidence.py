# confidence.py
import json
from typing import List
from pydantic import BaseModel
from dotenv import  load_dotenv

load_dotenv()
from groq import Groq

client = Groq()

class FieldConfidence(BaseModel):
    field_name: str
    confidence: str  # "high", "medium", "low"
    reason: str

class ConfidenceAssessment(BaseModel):
    field_confidences: List[FieldConfidence]

def assess_confidence(text: str, extracted_data: dict) -> ConfidenceAssessment:
    schema = ConfidenceAssessment.model_json_schema()
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": f"Given the original document and the extracted data, rate your confidence in each field as high/medium/low, with a brief reason. Respond with JSON matching this schema: {json.dumps(schema)}"},
            {"role": "user", "content": f"Original document:\n{text}\n\nExtracted data:\n{json.dumps(extracted_data)}"}
        ],
        response_format={"type": "json_object"}
    )
    parsed = json.loads(response.choices[0].message.content)
    return ConfidenceAssessment(**parsed)