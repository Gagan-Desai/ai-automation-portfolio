from extract_json_object import extract_ticket_json_object
from extract_json_schema import extract_ticket_json_schema
from groq import Groq

if __name__ == "__main__":
    ambiguous_ticket = "Hi, I'm reaching out about exploring a potential partnership between our companies for a joint marketing campaign next quarter. Could someone from your business development team get in touch to discuss revenue-sharing terms?"

    print("=" * 70)
    print(f"{'RUN':<6}{'json_object (category)':<28}{'json_schema (category)':<28}")
    print("=" * 70)

    for i in range(5):
        result_a = extract_ticket_json_object(ambiguous_ticket)
        result_b = extract_ticket_json_schema(ambiguous_ticket)
        print(f"Run {i+1}:")
        print(f"  category:  {result_a.category.value:<12} | {result_b.category.value}")
        print(f"  priority:  {result_a.priority.value:<12} | {result_b.priority.value}")
        print(f"  sentiment: {result_a.sentiment.value:<12} | {result_b.sentiment.value}")
        print(f"  entities (json_object): {[e.entity for e in result_a.key_entities]}")
        print(f"  entities (json_schema): {[e.entity for e in result_b.key_entities]}")
        print()

    print("=" * 70)