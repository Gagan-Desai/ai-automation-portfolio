# FX Rate Tracker — Orchestration Without AI

**Portfolio Piece #0 — the deliberately AI-free build.**

Before building anything with an LLM in it, I wanted to prove something more fundamental first: that I can design and ship a production-shaped automation pipeline — proper service architecture, idempotent writes, input validation, centralized error handling — with zero AI involved anywhere in the stack. Everything that follows this piece adds AI on top of this foundation. Nothing here is covering for the absence of real engineering underneath it.

## What it does

An hourly pipeline that fetches live foreign exchange rates, validates the response, transforms and filters it down to the currencies that matter, writes it to a real database without ever creating duplicate records, and posts a digest to Slack — with a fully separate, centralized failure path for anything that goes wrong along the way.

## Architecture

The stack is three Docker containers on a custom network, not one monolithic service:

- **n8n** — the orchestration engine, running the actual workflow
- **PostgreSQL** — the system of record for historical rate data
- **A Python task runner sidecar** — a separate container that executes the workflow's Python transform steps, communicating with n8n over an internal broker connection

These containers don't find each other via hardcoded IP addresses, which would break every time a container restarts and gets reassigned a new one. Instead, they sit on a custom Docker network with an embedded DNS resolver, so n8n reaches Postgres simply by the name `postgres-fx`, and the Python runner reaches n8n as `n8n` — the same name-based service discovery pattern Kubernetes Services provide at cluster scale, just running on a single Docker host. Getting this working end to end meant understanding, precisely, why containers are isolated by default, why `-p` port publishing solves a completely different problem than container-to-container DNS does, and why Docker Desktop on a Mac adds an extra layer (a hidden Linux VM) that makes naive `--network host` setups behave unexpectedly.

## The failure modes I deliberately designed for — and actually tested

Anyone can write a happy-path workflow. The point of this piece was building for what happens when things don't go to plan, and then proving each defense actually works rather than just claiming it does.

**Idempotent writes.** The `fx_rates` table enforces a `UNIQUE(currency, fetched_at)` constraint, with `fetched_at` truncated to the hour rather than stored to the microsecond — a subtlety that matters: without the truncation, a retried run minutes later would generate a different timestamp and the uniqueness constraint would never actually catch the duplicate, silently defeating its own purpose. The insert uses `ON CONFLICT DO NOTHING`, a deliberate choice over an upsert — I wanted strict "this was already handled, do nothing" semantics rather than "always overwrite with the latest value," and documented that tradeoff rather than picking one by default. I proved this works by manually re-running the pipeline within the same clock hour and confirming zero duplicate rows landed in the table.

**Input validation against API contract drift.** The pipeline doesn't trust a `200 OK` response to mean the data is actually usable. A dedicated check confirms the response body actually contains a `rates` field of the expected type before anything downstream touches it — a real, different failure category from a request simply erroring out, since an API can return a perfectly successful response that's still the wrong shape to safely process.

**SQL injection safety.** Every database write uses parameterized queries (`$1`, `$2` placeholders with a separate parameters list), not string-concatenated values — the database compiles the query's structure before any data arrives, so nothing a value contains can ever be reinterpreted as a second command.

**Centralized error handling, tested against its actual trigger conditions.** Beyond local error branches on individual nodes, a completely separate Error Workflow — built around n8n's Error Trigger node — catches any unhandled failure across the whole pipeline and posts an alert automatically, with no per-node wiring required. I learned, by hitting it directly, that this trigger only fires for genuine production executions, never manual test runs — meaning I had to deliberately activate the workflow and submit through its real production trigger to actually prove the alert fires, rather than trusting it worked from editor testing alone.

**Reproducible infrastructure.** The entire three-container stack comes back up from a single script rather than a sequence of commands re-typed from memory — with the network created idempotently, persistent containers (Postgres, the Python runner) resumed rather than recreated, and the one container that must be rebuilt fresh each time (n8n) started cleanly. Secrets — the Slack webhook URL, the runner's auth token — are never hardcoded into the script itself; they're loaded from a separate file that's explicitly excluded from version control.

## What I'd improve with more time

Worth being honest about the current limitations rather than presenting this as finished:

- The running-total query does a full `COUNT(*)` over the table on every run — fine at this scale, but a known scaling concern on a large table that I'd address with a maintained counter or periodic materialized count before this saw real production volume.
- The trigger is currently a Manual Trigger for testing convenience; a real deployment needs it swapped to the Schedule Trigger with a genuine hourly cron expression.
- The startup script is a reasonable stopgap, but Docker Compose would be the more standard, more maintainable way to express this same multi-container dependency graph.
- There's no automated test suite — verification so far has been manual, deliberate failure injection, which is a reasonable start but not a substitute for real test coverage.

## Why this piece exists

The next pieces in this portfolio add large language models into pipelines shaped exactly like this one — document extraction, retrieval-augmented answering, multi-step agents. Building this one first, with zero AI in it, was deliberate: it's the baseline that makes the AI-powered work that follows a genuine addition of capability, not a substitute for engineering that was never there to begin with.
