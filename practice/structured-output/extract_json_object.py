import json
from groq import Groq
from pydantic import ValidationError
from models import TicketTriage 

from dotenv import  load_dotenv

load_dotenv()

client = Groq()

def extract_ticket_json_object(ticket_text: str, max_retries: int = 3) -> TicketTriage:
    schema = TicketTriage.model_json_schema()

    messages = [
        {"role": "system", "content": f"You are a support ticket triage assistant. Respond with a JSON object matching this schema exactly: {json.dumps(schema)}. Respond with JSON only, no other text."},
        {"role": "user", "content": ticket_text}
    ]

    for attempt in range(max_retries):
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            response_format={"type": "json_object"}
        )
        raw = response.choices[0].message.content

        try:
            parsed = json.loads(raw)
            return TicketTriage(**parsed)
        except (json.JSONDecodeError, ValidationError) as e:
           # print(f"\n--- Attempt {attempt + 1} failed ---")
           # print(f"Raw output: {raw}")
           # print(f"Error: {e}\n")
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": f"That response failed validation: {str(e)}. Provide a corrected JSON response matching the schema exactly."})

    raise ValueError(f"Failed to get valid output after {max_retries} attempts")


# if __name__ == "__main__":
    sample_ticket = "The app crashed again while I was trying to export my invoice for Acme Corp. This is the third time this week and I need it fixed today."
    tricky_ticket = "Hi, I'm reaching out about exploring a potential partnership between our companies for a joint marketing campaign next quarter. Could someone from your business development team get in touch to discuss revenue-sharing terms?"

    result = extract_ticket_json_object(tricky_ticket)
    print(result)
    print(f"\nCategory: {result.category}")
    print(f"Priority: {result.priority}")
    print(f"Entities: {result.key_entities}")