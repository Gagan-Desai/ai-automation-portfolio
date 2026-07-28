# AI Automation Portfolio

My portfolio of projects for the RPA → AI Automation Engineer transition, built following a 53-day roadmap.

## Setup (Day 1)

1. Create the conda environment:
   ```
   conda create -n ai-automation python=3.11
   conda activate ai-automation
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in your real Groq API key:
   ```
   cp .env.example .env
   ```
3. Make sure Ollama is installed and you've pulled a model:
   ```
   ollama pull llama3.1:8b
   ```
4. Verify both LLM backends work:
   ```
   python test_setup.py
   ```
   You should see a successful response from both Groq and Ollama.

## Structure (will grow week by week)

```
ai-automation-portfolio/
├── README.md
├── requirements.txt
├── .env.example        # copy to .env, never commit .env itself
├── .gitignore
├── test_setup.py        # Day 1 sanity check
├── project-1-document-bot/     # Week 3-4
├── project-2-rag-assistant/    # Week 5-6
└── project-3-multistep-agent/  # Week 7
```

## Projects

- **Project 1 — Document Understanding Bot:** RPA-to-AI bridge, extracts structured data from messy documents.
- **Project 2 — RAG Knowledge Assistant:** Answers questions grounded in real documents.
- **Project 3 — Multi-Step AI Agent:** Plans, uses tools, and maintains memory across a task — built both in code and in n8n.
