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
    

print(extract_pdf_text("invoice_ironclad_messy.pdf"))