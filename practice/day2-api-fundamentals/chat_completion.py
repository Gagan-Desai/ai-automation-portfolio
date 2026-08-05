import os
import requests
from dotenv import  load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

url = "https://api.groq.com/openai/v1/models"


headers = {
    "Authorization" : f"Bearerqs {api_key}"
}

print("Key loaded:", api_key is not None)



payload = {
    "model": "llama-3.1-8b-instant",
    "messages": [
        {"role": "user", "content": "Explain what a REST API is in one sentence."}
    ]
}

response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)

print("Response Status Code:", response.status_code)
print("Response JSON:", response.json())

print("Usage:", response.json()["usage"]["total_tokens"])