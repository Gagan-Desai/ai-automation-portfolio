
from enum import Enum
from pydantic import BaseModel
import json
from dotenv import  load_dotenv

load_dotenv()
from groq import Groq

client = Groq()

class DocumentType(str, Enum):
    job_application = "job_application"
    reference_letter = "reference_letter"
    offer_acceptance = "offer_acceptance"
    unknown = "unknown"

class Classification(BaseModel):
    document_type: DocumentType

def classify_document(text: str) -> DocumentType:
    schema = Classification.model_json_schema()
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": f"Classify this HR document as one of: job_application, reference_letter, offer_acceptance. If it does not clearly and confidently match one of these three types, classify it as 'unknown' rather than guessing. Respond with JSON matching this schema: {json.dumps(schema)}"},
            {"role": "user", "content": text}
        ],
        response_format={"type": "json_object"}
    )
    parsed = json.loads(response.choices[0].message.content)
    return Classification(**parsed).document_type