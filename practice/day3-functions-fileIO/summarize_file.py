

import requests
import os
from dotenv import  load_dotenv
import json

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

url = "https://api.groq.com/openai/v1/models"


headers = {
    "Authorization" : f"Bearer {api_key}"
}

files = os.listdir('.')
print(files)



def ask_llm(prompt:str)->str :
    """Sends a prompt to the language model and returns the response."""
    payload = {
    "model": "llama-3.1-8b-instant",
    "messages": [
        {"role": "user", "content": prompt}
    ]
}

    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)


    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return "Error: " + response.json().get("error", {}).get("message", "Unknown error")
    



for file in files:
    if file.endswith(".txt"):
        with open(file, "r") as f:
            content = f.read()
        reply = ask_llm(content)
        print("Response from LLM:", reply)