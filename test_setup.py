"""
Day 1 sanity check — confirms both LLM backends are reachable before building anything.
Run with: python test_setup.py
"""

import os
from dotenv import load_dotenv

load_dotenv()


def test_groq():
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        print("❌ Groq: GROQ_API_KEY not set — check your .env file")
        return

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": "Reply with exactly: Groq is working"}],
    )
    print(f"✅ Groq response: {response.choices[0].message.content.strip()}")


def test_ollama():
    import ollama

    try:
        response = ollama.chat(
            model="llama3.1:8b",
            messages=[{"role": "user", "content": "Reply with exactly: Ollama is working"}],
        )
        print(f"✅ Ollama response: {response['message']['content'].strip()}")
    except Exception as e:
        print(f"❌ Ollama: {e}")
        print("   Make sure Ollama is running and you've pulled the model: ollama pull llama3.1:8b")


if __name__ == "__main__":
    print("Testing Groq...")
    test_groq()
    print("\nTesting Ollama...")
    test_ollama()
