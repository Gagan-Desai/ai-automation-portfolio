import json
from typing import Type, TypeVar
from dotenv import  load_dotenv
from logger_setup import setup_logger, log_event
load_dotenv()
from groq import Groq
from pydantic import BaseModel, ValidationError

logger = setup_logger()

client = Groq()

T = TypeVar("T", bound=BaseModel)

def extract_document(text: str, model_class: Type[T], instruction: str, max_retries: int = 3) -> T:
    schema = model_class.model_json_schema()

    messages = [
        {"role": "system", "content": f"{instruction} Respond with a JSON object matching this schema exactly: {json.dumps(schema)}. Respond with JSON only, no other text."},
        {"role": "user", "content": text}
    ]

    for attempt in range(max_retries):
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            response_format={"type": "json_object"}
        )
        raw = response.choices[0].message.content

        try:
            parsed = json.loads(raw)
            return model_class(**parsed)
        except (json.JSONDecodeError, ValidationError) as e:
            log_event(logger, "warning", "Extraction attempt failed", attempt=attempt + 1, model_class=model_class.__name__, error=str(e))
            print(f"\n--- Attempt {attempt + 1} failed ---\n{e}\n")
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": f"That response failed validation: {str(e)}. Provide a corrected JSON response matching the schema exactly."})

    raise ValueError(f"Failed to extract valid {model_class.__name__} after {max_retries} attempts")