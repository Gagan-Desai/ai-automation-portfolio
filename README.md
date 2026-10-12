# Gagan Desai — AI Automation Engineer Portfolio

**RPA engineer and business analyst (7+ years) moving into AI automation.** I build automation that keeps working when inputs are messy, APIs fail and models are wrong — and I measure and document where it still breaks.


**Looking for:** AI Automation Engineer · AI Engineer (applied / agents) · Intelligent Automation Developer

---

## 60-second tour

| Project | The problem | What I built | Evidence |
|---|---|---|---|
| **[Document Processing Bot](./project1-recruitment-document-processing)** | RPA templates break when a document layout changes | Classify-then-route extraction behind an async FastAPI service with API-key auth and human-review flagging | Same engine ran 6 document types across 2 unrelated domains with zero engine changes |
| **[Financial RAG Assistant](./RAG)** — [**live demo**](https://ai-automation-portfolio-82ggwcuct5xn3hsnvmdagp.streamlit.app) | LLMs invent answers about regulations they never saw | Retrieval over 8 real Central Bank of Ireland documents, with grounded and ungrounded answers shown side by side | Claim-level faithfulness check: grounded answer **1.00**, fabricated answer **0.00** |
| **[FX Rate Tracker](./n8n-workflows)** | Pipelines that only work on the happy path | n8n + Docker + Postgres pipeline with idempotent writes and a central error workflow | Re-running within the same hour produced **zero duplicate rows** |
| **[CRM Agent](./Multi-Tool-Agent)** | Agents act on real systems, so wrong claims have consequences | Tool-calling agent (HubSpot, Gmail, MCP) with a documented faithfulness failure and mitigation | Failure found by testing; deterministic validation gate and measured failure rate in progress |

**If you only open one thing:** try the [live RAG demo](https://ai-automation-portfolio-82ggwcuct5xn3hsnvmdagp.streamlit.app) and compare the grounded and ungrounded answers to the same question.

---

## Why my background matters

Seven years in RPA and business analysis means I already think in triggers, exception paths, audit trails and handover. These projects rebuild those habits on modern, API-first, LLM-enabled tooling: validation before trust, retries only where they are safe, failures that alert a human, and honest documentation of limits.

## Skills demonstrated

**LLM integration:** structured output (JSON mode and strict schema), Pydantic validation with corrective retry, context-window budgeting, evaluation harnesses, claim-level faithfulness scoring
**Retrieval:** embeddings, chunking strategies, ChromaDB, Maximal Marginal Relevance, table-aware PDF extraction
**Agents:** tool calling, MCP client/server, multi-tool loop with iteration cap (LangGraph port planned)
**Orchestration:** n8n, webhooks, OAuth, retries, dead-lettering, idempotency
**Backend:** Python, FastAPI, async jobs, API-key auth, structured logging, Postgres
**Infrastructure:** Docker, custom networks, sidecar containers, Git LFS, Streamlit Cloud deployment

---

<details>
<summary><b>Project details and honest limitations</b></summary>

### Document Processing Bot
A document goes through: text extraction → classification (including an `unknown` option) → registry lookup → generic extraction with Pydantic validation and corrective retry → per-field confidence assessment → status (`success`, `needs_review`, `failed`). Adding a document type means adding one registry entry.
*Findings from stress testing:* the classifier rarely used `unknown` even when permitted; a wrong schema produced a hallucinated field that retries did not fully fix; self-reported confidence changed between runs on identical input.
*Limits:* in-memory job store (a production version needs Redis or a database queue), shared API key, text PDFs only (no OCR).

### Financial RAG Assistant
Eight real Consumer Protection Code documents, two chunking strategies in separate collections, MMR retrieval, a grounded-versus-ungrounded comparison, and a custom faithfulness metric built after a third-party evaluation library failed in four separate ways. A real table-extraction bug was found through a retrieved chunk and fixed.
*Limits:* small hand-picked evaluation set, one preliminary chunk-size test, LLM-judged faithfulness not yet checked for stability, no subject-matter-expert review, local file-based vector store.

### FX Rate Tracker
Hourly fetch → validate response shape → transform → parameterized Postgres upsert → Slack digest, with retries, a dead-letter path and a separate Error Workflow. Runs as three containers resolved by name on a custom Docker network.
*Limits:* manual trigger in the exported version, no automated tests, startup script instead of Docker Compose.

### CRM Agent
Three tools (HubSpot create/search, Gmail send) in a loop with `max_iterations`, plus an MCP bridge that discovers tools at runtime. When a contact already existed, the agent sometimes described it as newly created. Prompt hardening reduced but did not eliminate this, so the fix in progress is a deterministic check before any email is sent.
*Limits:* sandbox CRM, small number of test scenarios, failure rate not yet measured.

</details>

## Repository structure

```
ai-automation-portfolio/
├── README.md
├── n8n-workflows/                              # exported workflows (secrets via environment variables)
├── project1-recruitment-document-processing/   # Document Processing Bot
├── RAG/                                        # Financial RAG Assistant
├── Multi-Tool-Agent/                           # CRM agent
└── practice/                                   # daily experiments
```

Each project folder has its own README with run instructions.

## Running things locally

```bash
conda create -n ai-automation python=3.11
conda activate ai-automation
cp .env.example .env     # add your own keys; .env is git-ignored
```

Install dependencies per project. Run tools through `python3 -m <tool>` so the active environment is used. The RAG vector database uses Git LFS, so run `git lfs install` **before** cloning. Model availability on Groq changes; check the current list (last tested with `openai/gpt-oss-20b`).

## What's next

- [ ] LangGraph port of the CRM agent with a validation gate and a measured before/after failure rate
- [ ] Multi-agent project (planner and executor, memory)
- [ ] n8n AI-agent workflow
- [ ] Automated tests, monitoring and deployment hardening
