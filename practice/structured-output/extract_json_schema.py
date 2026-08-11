from models import TicketTriage 
from groq import Groq
import json
from dotenv import  load_dotenv

load_dotenv()

client = Groq()

def extract_ticket_json_schema(ticket_text: str) -> TicketTriage:
    schema = TicketTriage.model_json_schema()

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a support ticket triage assistant. Analyze the ticket."},
            {"role": "user", "content": ticket_text}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "ticket_triage", "strict": True, "schema": schema}
        }
    )
    parsed = json.loads(response.choices[0].message.content)
    return TicketTriage(**parsed)


# if __name__ == "__main__":
    sample_ticket = "The app crashed again while I was trying to export my invoice for Acme Corp. This is the third time this week and I need it fixed today."
    tricky_ticket = "Hi, I'm reaching out about exploring a potential partnership between our companies for a joint marketing campaign next quarter. Could someone from your business development team get in touch to discuss revenue-sharing terms?"

    result = extract_ticket_json_schema(tricky_ticket)
    print(result)
    print(f"\nCategory: {result.category}")
    print(f"Priority: {result.priority}")
    print(f"Entities: {result.key_entities}")