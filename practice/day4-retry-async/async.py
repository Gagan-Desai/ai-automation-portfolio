

import requests
import os
from dotenv import  load_dotenv
import json
import logging
import time
import functools
import random
import asyncio
import aiohttp

load_dotenv()


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")



class RetryableError(Exception):
    pass


class NonRetryableError(Exception):
    pass


def read_all_files(folder: str)-> list[tuple[str, str]]:
    """Reads every .txt file in folder. Returns list of (filename, content) pairs."""
    file_data = []
    for filename in os.listdir(folder):
        if filename.endswith(".txt"):
            path = os.path.join(folder, filename)
            with open(path, "r") as f:
                content = f.read()
            file_data.append((filename, content))
    return file_data


def retry_with_backoff(max_attempts=3, base_delay=1):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except RetryableError as e:
                    if attempt == max_attempts - 1:
                        logging.error(f"Giving up after {max_attempts} attempts: {e}")
                        raise
                    wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logging.info(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
        return wrapper
    return decorator



api_key = os.getenv("GROQ_API_KEY")

url = "https://api.groq.com/openai/v1/models"


headers = {
    "Authorization" : f"Bearer {api_key}"
}



@retry_with_backoff(max_attempts=3, base_delay=1)
async def ask_llm(session: aiohttp.ClientSession, prompt: str) -> str:
    """Same job as ask_llm, but via aiohttp and taking a shared session."""
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    async with session.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload) as response:
        if response.status == 200:
            return (await response.json())["choices"][0]["message"]["content"]

        error_msg = (await response.json()).get("error", {}).get("message", "Unknown error")

        if response.status == 429:
            raise RetryableError(f"Status {response.status}: {error_msg}")
        else:
            raise NonRetryableError(f"Status {response.status}: {error_msg}")

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]

    error_msg = response.json().get("error", {}).get("message", "Unknown error")

    if response.status_code in (429, 500, 502, 503):
        raise RetryableError(f"Status {response.status_code}: {error_msg}")
    else:
        raise NonRetryableError(f"Status {response.status_code}: {error_msg}")






async def process_all_files(file_data: list[tuple[str, str]]) -> list:
            async with aiohttp.ClientSession() as session:
                tasks = [ask_llm(session, content) for filename, content in file_data]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                return results
            

def write_all_outputs(file_data: list[tuple[str, str]], results: list, output_folder: str):
    for (filename, content), result in zip(file_data, results):
        if isinstance(result, Exception):
            logging.error(f"Failed to process {filename}: {result}")
            continue

        output_filename = filename.replace(".txt", "_output.txt")
        output_path = os.path.join(output_folder, output_filename)
        with open(output_path, "w") as f:
            f.write(result)

file_data = read_all_files(".")   # your .txt files are sitting right here, per your last output

start = time.perf_counter()
results = asyncio.run(process_all_files(file_data))
elapsed = time.perf_counter() - start

write_all_outputs(file_data, results, ".")
print(f"Processed {len(file_data)} files in {elapsed:.2f}s")