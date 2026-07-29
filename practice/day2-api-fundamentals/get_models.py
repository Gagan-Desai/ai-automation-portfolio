import os
import requests
from dotenv import  load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

url = "https://api.groq.com/openai/v1/models"


headers = {
    "Authorization" : f"Bearer {api_key}"
}

print("Key loaded:", api_key is not None)

response = requests.get(url, headers=headers)   
print ("Status Code : "  , response.status_code)
print(response.json())

models_List = response.json()["data"]
print("Available Models:", len(models_List))

for model in models_List:
    print("Model ID:", model["id"])
    print("Model Name:", model["name"])
    print("---")


payload = {
    "model": "llama-3.1-8b-instant",
    "messages": [
        {"role": "user", "content": "Explain what a REST API is in one sentence."}
    ]
}

response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)

print("Response Status Code:", response.status_code)
print("Response JSON:", response.json())