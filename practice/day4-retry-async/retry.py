

import requests
import os
from dotenv import  load_dotenv
import json
import logging
import time
import functools
import random

load_dotenv()


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")



class RetryableError(Exception):
    pass


class NonRetryableError(Exception):
    pass


def retry_with_backoff(max_attempts=3, base_delay=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except RetryableError as e:
                    if attempt == max_attempts - 1:
                        logging.error(f"Giving up after {max_attempts} attempts: {e}")
                        raise
                    wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logging.info(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
        return wrapper
    return decorator



api_key = os.getenv("GROQ_API_KEY")

url = "https://api.groq.com/openai/v1/models"


headers = {
    "Authorization" : f"Bearer {api_key}"
}

files = os.listdir('.')
print(files)

@retry_with_backoff(max_attempts=3, base_delay=1)
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

    error_msg = response.json().get("error", {}).get("message", "Unknown error")

    if response.status_code in (429, 500, 502, 503):
        raise RetryableError(f"Status {response.status_code}: {error_msg}")
    else:
        raise NonRetryableError(f"Status {response.status_code}: {error_msg}")

start = time.perf_counter()

for file in files:
    if file.endswith(".txt"):
        with open(file, "r") as f:
            content = f.read()
        reply = ask_llm(content)
        print("Response from LLM:", reply)


elapsed = time.perf_counter() - start
print(f"Sequential processing took {elapsed:.2f}s for {len([f for f in files if f.endswith('.txt')])} files")