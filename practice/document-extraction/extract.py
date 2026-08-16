invoice_1 = """
INVOICE

Acme Office Supplies Ltd.
Invoice #: INV-2026-0472
Date: January 5, 2026

Bill To: Riverside Consulting

Description                Qty    Unit Price    Total
Ergonomic Office Chair       3        150.00      450.00
Standing Desk                 2        320.00      640.00
Wireless Keyboard             5         45.00      225.00

Subtotal: 1315.00
Tax (8%): 105.20
Total: 1420.20
"""

invoice_2 = """
BRIGHT PATH LOGISTICS

Bill to: Coastal Retail Group
Date: 15/02/202

Item                          Qty    Rate      Amount
Freight Handling - Zone A       1    890.00     890.00
Warehouse Storage (monthly)     2    210.00     420.00
Fuel Surcharge                  1     75.50      75.50

Subtotal: 1385.50
Tax: 0.00
Total Due: 1385.50
"""

invoice_3 = """
G R E E N F I E L D   M A T E R I A L S   C O

Invoice No:  GM-88231
Dat e: 3rd  March,2026

Descrlption                    Qty     Unit Prlce    Llne Total
Steel  Beams  (10ft)              12        85.00        1020.00
Concrete  Mix  (50lb bags)        40         9.75         390.00
Safety  Harnesses                  6        34.50         207.00

Sub-total :  1617.00
Tax  (7%)  :   113.19
TOTAL    :   1730.19
"""


from pydoc import doc
import pdfplumber
import json
from groq import Groq
from pydantic import ValidationError
from invoice_models import Invoice
from dotenv import  load_dotenv

load_dotenv()


client = Groq()

def extract_pdf_text(path: str) -> str:
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages)

def extract_invoice(document_text: str, max_retries: int = 3) -> Invoice:
    schema = Invoice.model_json_schema()

    messages = [
        {"role": "system", "content": f"Extract invoice data from the following document. Respond with a JSON object matching this schema exactly: {json.dumps(schema)}. Extract the date exactly as it appears in the document — do not reformat it yourself. Respond with JSON only, no other text."},
        {"role": "user", "content": document_text}
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
            return Invoice(**parsed)
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"\n--- Attempt {attempt + 1} failed ---\n{e}\n")
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": f"That response failed validation: {str(e)}. Provide a corrected JSON response matching the schema exactly."})

    raise ValueError(f"Failed to extract valid invoice after {max_retries} attempts")


if __name__ == "__main__":
    # for i, doc in enumerate([invoice_1, invoice_2, invoice_3], 1):
    #     print(f"\n=== Invoice {i} ===")
    #     result = extract_invoice(doc)
    #     print(result)
        


    result = extract_invoice(extract_pdf_text("invoice_ironclad_messy.pdf"))
    print(result)