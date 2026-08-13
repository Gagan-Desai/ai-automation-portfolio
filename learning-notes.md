# Learning Notes — AI Automation Engineer Journey

A running log of what actually happened each day: commands used, problems hit, and *why* each thing matters — not just the roadmap tasks, but the real troubleshooting, since that's where the real learning happens.

---

## Glossary (terms explained as they came up)

- **Homebrew** — a package manager for Mac; lets you install software via `brew install <name>` in Terminal instead of downloading `.dmg` files manually.
- **SSH key** — a cryptographic key pair used to authenticate with GitHub without typing a password every time. Set up once, works forever.
- **Conda environment** — an isolated set of Python packages for one project, so different projects' dependencies never conflict with each other.
- **Dotfiles** — files starting with a `.` (like `.env`, `.gitignore`). Hidden by default in Finder (reveal with `Cmd+Shift+.`) but always visible via `ls -la` in Terminal.
- **PATH** — the list of folders your Terminal searches when you type a command name. If a tool "isn't found," it's often not installed — it's that its location isn't in PATH.
- **Groq** — a cloud API that runs LLMs on fast, specialized hardware. You send a request over the internet, it sends back a response. Fast, free tier, rate-limited.
- **Ollama** — runs LLMs locally on your own Mac. No internet needed after the model's downloaded, no rate limit, but slower and uses your machine's resources.

---

## Day 1 — Environment Setup

**Goal:** Python, VS Code, Git, GitHub repo, Groq API key, Ollama — all working together.

### What was already in place
- Python via Anaconda
- VS Code installed

### Git
```
git --version
git config --global user.name "Gagan Desai"
git config --global user.email "gagann.desai@gmail.com"
```

### GitHub authentication — the real lesson here
HTTPS clone with a password **doesn't work anymore** — GitHub removed password auth for git operations in 2021. Two fixes exist: SSH keys (set up once, permanent) or Personal Access Tokens (need renewing). Went with SSH:
```
ssh-keygen -t ed25519 -C "gagann.desai@gmail.com"
eval "$(ssh-agent -s)"
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
pbcopy < ~/.ssh/id_ed25519.pub
```
Then pasted the key into GitHub → Settings → SSH and GPG keys → New SSH key.

Verify anytime with:
```
ssh -T git@github.com
```
First time you'll get a host-key confirmation prompt ("authenticity of host can't be established") — type `yes`. This is normal, not an error.

**Key lesson:** "Repository not found" over SSH with working auth doesn't mean auth is broken — it means the repo genuinely doesn't exist at that URL yet, or the name/owner is wrong. Confirmed this by checking the GitHub profile page directly, which showed "doesn't have any public repositories yet." **Always create the repo on GitHub's website first** (New → name it → Add README → Create) before trying to clone it.

**Real username turned out to be:** `Gagan-Desai` (capital letters + hyphen — GitHub usernames don't contain spaces, so early guesses with spaces were never going to work).

Correct clone command:
```
cd ~/Documents
git clone git@github.com:Gagan-Desai/ai-automation-portfolio.git
cd ai-automation-portfolio
```

### Conda environment
```
conda create -n ai-automation python=3.11
conda activate ai-automation
```
**Why isolate it:** every project needs its own package versions; a shared environment eventually breaks when two projects need conflicting versions of the same package. `requirements.txt` + a clean environment is also what lets someone else (recruiter, collaborator, future-you on a new machine) reproduce your exact setup.

### Groq API key
console.groq.com → sign up → API Keys → Create API Key → copy immediately (shown once only).

### Ollama
Downloaded from ollama.com, installed via `.dmg`. Then:
```
ollama pull llama3.1:8b
ollama run llama3.1:8b   # test, /bye to exit
ollama list               # confirms model is present
```

### Starter kit files (`.env.example`, `.gitignore`, `requirements.txt`, `README.md`, `test_setup.py`)
**Gotcha hit:** files downloaded without their leading dot (`env.example` instead of `.env.example`, `gitignore` instead of `.gitignore`). Fixed with:
```
mv env.example .env.example
mv gitignore .gitignore
```
Then:
```
cp .env.example .env
```
**Why the `.env` / `.env.example` split exists:** `.env.example` is a safe-to-commit template showing what variables are needed; `.env` holds the real secret and is excluded from Git via `.gitignore`. This pattern exists specifically so a public repo can show its required configuration without ever leaking real credentials — GitHub actively scans public repos for leaked keys.

Edited `.env` via VS Code's **File → Open Folder** (Finder hides dotfiles, VS Code doesn't) and pasted the real Groq key in.

**`code` command gotcha:** running `code .env` in Terminal gave `command not found`. Fixed via VS Code's Command Palette (`Cmd+Shift+P`) → "Shell Command: Install 'code' command in PATH" — then hit a permissions error (`EACCES: permission denied, unlink '/usr/local/bin/code'`) from a leftover file, fixed with:
```
sudo chown -R $(whoami) /usr/local/bin
```
then reran the install command and restarted Terminal.

### Install dependencies + verify
```
pip install -r requirements.txt
python test_setup.py
```
✅ Both Groq and Ollama confirmed working.

```
git add .
git commit -m "Day 1: environment setup, Groq + Ollama verified"
git push
```

### Why Groq *and* Ollama, not just one
- **Groq** = calling a managed cloud service — fast, free tier, rate-limited, needs internet, data leaves your machine.
- **Ollama** = operating your own local inference endpoint — no rate limit, no internet needed after setup, data never leaves your Mac, but slower.
- This maps to a real distinction employers screen for: "using a managed AI service" vs. "managing your own inference endpoint" are different, both-named skills. Week 8's Day 44 (wrapping Ollama behind a FastAPI service) is built specifically to practice the second one.
- Practical reasons to keep both: rate-limit backup, a real latency/cost comparison to run in Week 8, and a genuine answer for "what if a client needs local-only processing for compliance" in an interview.

---

## Day 2 — REST API Fundamentals + First LLM Calls

**Goal:** Understand REST concepts properly, then call the Groq API directly with raw `requests` (not the SDK) — first a GET, then a POST.

### Core REST concepts

- **Stateless:** every request must carry everything needed to be understood on its own (e.g., the auth header) — the server remembers nothing between calls.
- **Safe** methods (GET) never change server state. **Idempotent** methods (GET, PUT, DELETE) give the same end state no matter how many times you call them with the same input. **POST is neither** — this is why blindly auto-retrying a failed POST is risky (could create duplicates / double-charge / generate a duplicate LLM completion). Matters directly for retry logic in n8n later.
- **Status code categories** (the category matters more than memorizing individual codes):
  - `2xx` success
  - `4xx` — *you* did something wrong (400 malformed request, 401 not authenticated, 403 authenticated but not authorized, 404 resource doesn't exist, 429 rate limited)
  - `5xx` — the *server* did something wrong
  - **Rule of thumb for later retry logic:** 401/404/400 → don't retry, alert a human (retrying an invalid request just fails again). 429/5xx → often worth retrying, ideally with a delay.
- **Headers used constantly:** `Content-Type` = what you're sending; `Authorization` = who you are. Groq (like most modern APIs) uses **Bearer token** auth: `Authorization: Bearer <key>`.

### GET request (Challenge 1 — list models)

```python
headers = {"Authorization": f"Bearer {api_key}"}
response = requests.get(url, headers=headers)
```
`response` is a `Response` **object**, not the data itself — `.status_code`, `.json()`, `.text` are things you pull off it.

**Key lesson — always print the raw response before extracting anything.** The model list wasn't at the top level of the JSON — it was nested under a `"data"` key:
```python
models_list = response.json()["data"]      # dict → list
for model in models_list:
    print(model["id"])                      # each item is a dict
```
Never guess the shape of a JSON response — print it first, then write extraction code against what you actually see.

### POST request (Challenge 2 — chat completion)

**`requests.post()` — `data=` vs `json=` is not a stylistic choice:**
- `data=my_dict` sends it as a raw form-encoded string, does **not** set `Content-Type` for you — a common real bug (server receives garbage, you get a confusing 400).
- `json=my_dict` correctly serializes the dict to JSON text **and** sets `Content-Type: application/json` automatically. **This is the correct one for JSON APIs.**

```python
response = requests.post(url, headers=headers, json=payload)
```

**Response shape** (again — nested, don't assume):
```python
reply = response.json()["choices"][0]["message"]["content"]
```
`choices` is a **list** (API can return multiple alternative completions), so index `[0]` before drilling into `message` → `content`.

The `usage` block in every response (`prompt_tokens`, `completion_tokens`, `total_tokens`) is the raw data source for cost/token tracking — this is exactly what Week 8's monitoring work builds on top of.

### Error handling — seen firsthand, not just theory

Triggered both failure types on purpose:
- **Bad model name → 404**, not 400. REST convention: the request was *structurally* valid, it just pointed at a resource that doesn't exist — same category as a bad URL. 400 is reserved for a malformed request itself.
- **Bad API key → 401** (authentication failure) — clearly distinct from 404.

**Real crash hit and fixed:** code that assumed `response.json()["choices"]` always exists threw a `KeyError` on failure, because error responses have an `"error"` key instead, not `"choices"`. Fixed with a status-code branch:
```python
if response.status_code == 200:
    reply = response.json()["choices"][0]["message"]["content"]
    print(reply)
else:
    error_info = response.json()["error"]
    print(f"Request failed ({response.status_code}): {error_info['message']}")
```
**The real lesson:** never write extraction code assuming the happy-path shape — check status first, branch accordingly.

---

### Deep dive: environments, interpreters, and how it all fits production

**What an interpreter actually is:** a literal binary file on disk (e.g., `/opt/anaconda3/envs/ai-automation/bin/python3.11`). A Mac has several installed at once (system Python, conda `base`, conda `ai-automation`, maybe Homebrew's) — each fully independent, with its own separate installed packages. Installing a package into one does nothing for the others.

**What `conda activate` actually does:** temporarily rewrites the shell's `PATH` (the ordered list of folders the shell searches for commands) to put that environment's `bin/` folder first. That's the entire mechanism — no magic, just search-order manipulation.

**Why VS Code's interpreter picker and the terminal's active env can disagree:** they're two *separate* settings that both happen to point at Python — VS Code's picker is only used by the editor's own analysis/Run button; it doesn't read your terminal's `conda activate` state. **Terminal output is always the ground truth** — a squiggly warning in the editor is just VS Code's own static analysis guessing, and can be safely ignored if the terminal run actually works.

**Practical fix when VS Code's interpreter picker won't "stick":** use the integrated terminal (`` Ctrl+` ``) inside VS Code instead of fighting the dropdown — write code in the editor pane, run it in the terminal pane below, same window. Sidesteps the whole issue.

**Is conda "the standard"?** No — it's popular specifically in data science because it handles complex non-Python dependencies well. In general software engineering / production, more common tools are: **`venv`** (built into Python itself, no install needed, the lightweight default most companies use), **Poetry** (manages environment + produces a lockfile for exact reproducibility), or just plain **`pip install -r requirements.txt`** (universal, works inside any of the above). Conda is a fine choice for this roadmap since Anaconda was already installed — just good to know it's not universal.

**What `.env` / `load_dotenv()` actually do:** every running process has OS-level environment variables (a simple key-value dictionary — `PATH` is one, `HOME` is another). `os.getenv("KEY")` just reads from that dictionary. `.env` is **not** read automatically — `load_dotenv()` is a small library that opens the file and manually injects each `KEY=value` line into that same OS-level dictionary at the start of your script. A `.env` file is a **local development convenience only** — it should never exist in real production.

**How production actually differs — the real target of this roadmap:**
1. A **Dockerfile** bakes the interpreter + packages + code into one frozen, portable image — no more "environment" on a host machine to mismatch.
2. Conda mostly disappears in production images — plain `pip install` inside a slim Docker image is lighter and more standard, since Docker itself now provides the isolation conda gave you locally.
3. **Secrets are never baked into the image** — they're injected at container/pod startup by whatever platform runs it (Kubernetes Secrets, AWS Lambda environment config, Docker Compose `environment:` block). The code doesn't change (`os.getenv("GROQ_API_KEY")` stays identical) — only *where the value comes from* changes.

**The progression to keep in mind:** `.env` file (now, local) → Docker image with runtime-injected secrets (Week 8) → Kubernetes Secrets doing the same job at cluster scale (Week 9). Same underlying concept the whole way — just moving further from a laptop toward real infrastructure.

### Gotchas hit and fixed today
- `code` command not found in a fresh terminal → PATH change from a previous session doesn't carry to new terminal windows; fully quit and reopen, or just use VS Code's sidebar "New File" instead of the `code` command.
- Printed `response.json` instead of `response.json()` → forgetting `()` prints a reference to the method itself, not its result. Parentheses are what actually *call* a function.

---

## Day 3 — Functions, File I/O, and the Multi-File Processing Pattern

**Goal:** Move from flat one-off scripts to reusable functions, learn to read/write files, and build the actual "process every file in a folder" pattern Project 1 is built on.

### Functions — syntax broken down

```python
def ask_llm(prompt: str) -> str:
    """Docstring — shows up in help() and editor tooltips."""
    ...
    return result
```
- `def name(...):` registers the function; nothing inside runs until it's *called*.
- `(prompt: str)` — `prompt` is a parameter name (a local variable that only exists inside the function); `: str` is a **type hint**, not enforced at runtime by Python itself — it's for tooling/readability (matters more once FastAPI in Week 4 *does* enforce these strictly).
- `-> str` — a type hint for the return value, same non-enforcement caveat.
- **`return` vs `print()`:** `return` hands a value back to whoever called the function, silently — you still need an explicit `print()` elsewhere to actually see it. Assigning a function's result to a variable (`reply = ask_llm(...)`) produces no visible output on its own.

### `.get()` for safe dict access

Cleaner alternative to yesterday's `if/else` branch for handling missing keys — never raises `KeyError`, returns a default instead:
```python
error_msg = response.json().get("error", {}).get("message", "Unknown error")
```

### File I/O

```python
with open("filename.txt", "r") as f:
    content = f.read()
```
**Always use `with`** — guarantees the file closes automatically even if an exception happens mid-read, preventing resource leaks. Mode `"r"` = read, `"w"` = write (overwrites — be careful).

Reading/writing actual JSON *files* on disk (different from `response.json()`, which parses JSON that arrived over the network):
```python
import json
with open("data.json", "w") as f:
    json.dump(my_dict, f)
with open("data.json", "r") as f:
    loaded = json.load(f)
```

### Real bugs hit and fixed today (all worth remembering)
1. **Called the function but never printed the result** — `reply = ask_llm(...)` alone shows nothing; needed `print(reply)` after.
2. **Function body ignored its own parameter** — payload had a hardcoded string instead of using `prompt`, so the function always asked the same question regardless of input. Lesson: when refactoring a working script into a function, double-check every hardcoded value that *should* become a parameter reference actually got swapped in.
3. **Typo in the auth header** (`"Bearerqs"` instead of `"Bearer"`) — caused a 401 by accident, same failure mode triggered on purpose yesterday. Auth scheme keywords are exact strings the server checks for; a typo silently produces an auth failure, not a Python error.

### Multi-file loop — Project 1's actual structure, in miniature

```python
import os

for filename in os.listdir("inputs"):
    if filename.endswith(".txt"):          # filters out macOS's hidden .DS_Store file
        input_path = os.path.join("inputs", filename)
        with open(input_path, "r") as f:
            prompt = f.read()

        reply = ask_llm(prompt)

        output_filename = filename.replace(".txt", "_output.txt")
        output_path = os.path.join("outputs", output_filename)
        with open(output_path, "w") as f:
            f.write(reply)
```
- **`os.listdir("folder")`** returns just filenames (strings), not full paths and not contents.
- **`os.path.join(folder, filename)`** builds a correct path for whatever OS runs the code (Mac/Linux use `/`, Windows uses `\`) — always prefer this over manually concatenating strings with `+`, especially since this exact code will later run inside a Linux Docker container (Week 8) regardless of what it was built on.
- This loop — read every file in a folder, process each through the LLM, write a matching output — **is Project 1's core structure.** Everything from Week 3–4 builds directly on top of this exact pattern, just with real documents instead of placeholder `.txt` files.

---

## Day 4 — Decorators, Custom Exceptions, Async Concurrency, Retry with Backoff

**Goal:** Make LLM calls resilient (retry on transient failures) and fast (concurrent instead of sequential). Result: **1.2s (concurrent) vs. 4.2s (sequential)** for the same batch of files — ~3.5x speedup, proven with real timing, not assumed.

### Decorators — the mechanism

A decorator is a function that takes a function and returns a new one wrapping it. `@decorator` above `def f(): ...` is exactly equivalent to `f = decorator(f)`.

```python
def retry_with_backoff(max_attempts=3, base_delay=1):   # "decorator factory" — accepts config
    def decorator(func):                                  # receives the function being wrapped
        @functools.wraps(func)                             # preserves func's real name/docstring
        def wrapper(*args, **kwargs):                      # *args/**kwargs = works on any signature
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except RetryableError as e:
                    if attempt == max_attempts - 1:
                        raise                                # out of attempts — let it propagate
                    wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(wait_time)
        return wrapper
    return decorator
```
- **Three levels deep (config → decorator → wrapper)** specifically because `@retry_with_backoff(max_attempts=3)` needs to accept *your own* arguments, not just the function being wrapped — a plain decorator only ever receives one argument (the function itself).
- **`functools.wraps(func)` is not optional** — without it, the wrapped function's `__name__`/docstring get silently replaced by the wrapper's, breaking debugging and introspection.
- **Why wrap instead of inlining retry logic into every function:** retry (like logging, caching, timing) is a *cross-cutting concern* — the same policy needed across many otherwise-unrelated functions (Groq today, HubSpot/Ollama/Calendar in later weeks). Inlining means N copies of the same logic that will inevitably drift out of sync. Decorators are the wrong call, though, when the policy genuinely differs per-function, when you need context from inside the function to decide how to retry, or when something's only ever called once.
- **Other real production wrapper patterns, same shape, different job:** caching (`functools.lru_cache`, or Redis-backed in production), timing/profiling, circuit breakers (stop calling a service entirely after too many failures, instead of retrying into a dead service — `pybreaker`), rate limiting outgoing calls, cost/usage metering, distributed tracing (OpenTelemetry). Decorators can also be written as **classes** (`__init__` + `__call__`) instead of nested functions — preferred when the wrapper needs to persist state across calls (a running count, a cache dict).

### Custom exceptions — why the classes are empty

```python
class RetryableError(Exception):
    pass

class NonRetryableError(Exception):
    pass
```
- `pass` exists purely because Python requires *something* indented under a `:` — it means "do nothing."
- **The empty body is deliberate, not lazy** — inheriting from `Exception` already provides everything needed (storing a message, `str()`, working with `raise`/`except`). You're not adding behavior, you're creating a distinct **type** so `except RetryableError` and `except NonRetryableError` can tell failures apart. The name/identity of the type *is* the information (matching on type is more robust than string-parsing a message, which breaks the moment the message wording changes).
- **`raise RetryableError("some message")` works with no `__init__` defined** because it inherits `Exception`'s constructor.
- `except RetryableError` internally checks `isinstance(raised_thing, RetryableError)` — a sibling type (`NonRetryableError`) does **not** match, so it passes straight through the retry wrapper untouched, uncaught — exactly why a bad API key or bad model name never gets retried, only 429/5xx do.

### The critical design fork this required

Retry logic needs failures to be **exceptions**, not string return values disguised as success. Had to go back and change `ask_llm`'s failure branch from `return "Error: ..."` to actually `raise RetryableError(...)` / `raise NonRetryableError(...)` — otherwise the decorator has nothing to catch, since nothing's ever thrown.

### Async/await + aiohttp — the concurrency layer

**The core mechanism:** Python's `asyncio` runs on one thread with an event loop. `await some_io_call()` doesn't block the program — it tells the loop "I'm waiting on external I/O (network), go advance something else while you wait." This only works for I/O-bound waiting (network calls), not CPU computation — during the wait, the CPU is genuinely idle, and asyncio uses that idle time for other pending requests.

**`requests` is synchronous and cannot participate in this — needed `aiohttp` instead.**

```python
async def ask_llm_async(session: aiohttp.ClientSession, prompt: str) -> str:
    payload = {"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": prompt}]}
    async with session.post(url, headers=headers, json=payload) as response:
        if response.status == 200:                        # NOTE: .status, not .status_code (aiohttp vs requests naming)
            data = await response.json()                    # NOTE: needs await — body may still be streaming in
            return data["choices"][0]["message"]["content"]
        error_body = await response.json()
        ...
```

**Orchestration:**
```python
async def process_all_files(file_data: list[tuple[str, str]]) -> list:
    async with aiohttp.ClientSession() as session:            # one shared connection pool for every call
        tasks = [ask_llm_async(session, content) for filename, content in file_data]   # list of UNRUN coroutine objects
        results = await asyncio.gather(*tasks, return_exceptions=True)                  # actually schedules all concurrently
        return results
```
- **`[fn(x) for x in items]` where `fn` is `async def` creates a list of coroutine *objects*, none running yet** — same "unexecuted reference" trap as `response.json` without `()` from Day 2. `asyncio.gather(*tasks)` is what actually drives them all forward concurrently.
- **`return_exceptions=True` is essential for a batch job.** Without it, one failing file crashes `gather()` entirely and cancels every other still-running task, discarding results that had already succeeded. With it, a failed task's exception object lands *in the results list itself*, at the position it would've held — checked afterward with `isinstance(result, Exception)`.
- **`asyncio.gather()` preserves input order in its results** — this is what makes `zip(file_data, results)` a safe way to re-pair each file with its own outcome afterward, with no extra bookkeeping needed.
- **Async retry wrapper needs three changes from the sync version:** `wrapper` itself must be `async def` (since it calls an `async def` function); `return await func(...)` instead of `return func(...)` (awaiting is what actually drives the coroutine and lets its exception surface); `await asyncio.sleep(...)` instead of `time.sleep(...)` — using blocking `time.sleep` inside an async wrapper freezes the *entire event loop*, silently killing concurrency for every other in-flight request during that wait.

### Exponential backoff + jitter — the actual reasoning

`wait = base_delay * (2 ** attempt)` — grows the delay each retry (1s, 2s, 4s...). **Fixed-interval retries are a real, named failure mode at scale ("thundering herd"):** if many clients get rate-limited at the same moment, retrying after an identical fixed delay makes them all hammer the server again in perfect sync, repeating the failure. **Jitter** (`+ random.uniform(0, 1)`) spreads retries out so they don't cluster.

### Sync vs. async — where each is actually the right call

- **Read-everything-first / batch approach** (what Project 1 uses): input is a fixed, known, memory-sized set that already exists on disk. Read all, then process concurrently.
- **Stream-and-process-as-you-go instead, when:** the input is too big for memory (huge log files — read in chunks), or files/events arrive continuously rather than as a fixed batch (a live-watched folder, a message queue) — no fixed "everything" to read upfront.
- **Real-world stretch noted for later:** live folder-watching (`watchdog` library — fires an event the instant a file appears, rather than re-scanning on a timer) is a natural upgrade to Project 1 once the batch version is solid — planned for after Week 2 (triggers/orchestration) or around Week 7, not now, to avoid stacking a new hard concept on top of ones not yet proven solid.

### Logging over print()

```python
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.info("...")
logging.error("...")
```
Structured (timestamps, severity levels), filterable/routable — unlike `print()`, which is a dead end once you need to redirect output to a file or monitoring system (Week 8's territory).

### Gotchas hit and fixed today
- Timed the whole script including `os.listdir()` and setup — should scope timers around just the comparable work (the actual LLM-calling loop) for a fair sync-vs-async comparison.
- Left dead/leftover sync loop code in the same file as the new async pipeline — decorated functions accept `*args, **kwargs` (anything), so calling the old loop against the new async-decorated function silently created an unawaited coroutine instead of erroring loudly (`RuntimeWarning: coroutine was never awaited`).
- Included `404` in the retryable-status tuple by mistake — contradicts Day 2's own lesson (404 = resource doesn't exist, retrying the identical request won't change that; only 429/5xx are worth retrying).
- Real result once fixed: **sequential ~4.2s vs. concurrent ~1.2s, same files — ~3.5x speedup**, proof this actually works, not just runs without crashing.

---

## Day 5 — *(buffer/research day — used for catch-up, folded into Day 6 prep)*

## Day 6 — Docker Fundamentals + n8n (Webhook → LLM → Response, end to end)

**Goal:** Run n8n via Docker, understand containers/volumes properly, then rebuild the "call an LLM" pipeline visually in n8n instead of Python — full round trip, real dynamic data in, real dynamic reply out.

### Docker — why n8n needs it, and the persistence problem

A Docker image bakes an app + all its dependencies into one portable, frozen unit — same "reproducible environment" idea as Day 3's `requirements.txt` discussion, just packaged one level further so nothing (not even the interpreter or OS libraries) needs to be separately installed on the host.

**Containers are ephemeral by default** — a container's filesystem is normally wiped when it stops. Fine for stateless jobs, catastrophic for n8n, which needs to remember every workflow forever. Solved with a **volume**: storage that lives outside the container's disposable filesystem and gets mounted in.

```
docker run -it --rm --name n8n -p 5678:5678 -e N8N_SECURE_COOKIE=false -v n8n_data:/home/node/.n8n docker.n8n.io/n8nio/n8n
```

- **`-it`** = interactive (`-i`, keeps STDIN open) + pseudo-terminal (`-t`) — lets you see live logs and `Ctrl+C` cleanly.
- **`--rm`** = auto-delete the *container* on stop. Does **not** touch volumes — a named volume is a separate Docker object with its own lifecycle, specifically designed to outlive any single container (that's the entire point of using one for something like n8n).
- **`-p HOST:CONTAINER`** (`5678:5678` here) — port mapping. A container's internal ports are invisible to the host until explicitly mapped; left number = what you type into your Mac's browser, right number = what the app inside is actually listening on. They don't have to match.
- **`-v n8n_data:/home/node/.n8n`** — a **named volume** (Docker manages where it physically lives, you reference it only by name) vs. a **bind mount** (`-v ~/some-folder:/path`, where you choose and can directly browse the folder). Named volumes suit "app state I don't need to touch myself" (databases, n8n's workflow storage); bind mounts suit "I need direct file access" (mounting real project code for live development).
- **`-e KEY=VALUE`** — sets an environment variable *inside* the container. **Same underlying mechanism as `load_dotenv()` from Day 3**, just injected by Docker at container startup instead of a Python library reading a file — this is the second step in the progression: `.env` file (local Python) → Docker `-e` flag (here) → Kubernetes Secrets (Week 9), same concept, different point on the path to real infrastructure.

**`docker stop <name>` vs. `Ctrl+C`:** if `Ctrl+C` doesn't stop a container (some images don't forward the interrupt signal properly to the process inside), open a *separate* terminal and run `docker stop n8n` instead — targets the container from outside via Docker's own control channel rather than relying on the signal reaching the right place. `docker ps` lists running containers only; `docker ps -a` includes stopped ones too.

**Real gotcha hit:** Safari + secure cookies. n8n's session cookie is marked `Secure` by default, which browsers only send over HTTPS — except for the literal hostname `localhost` (not `127.0.0.1`), and Safari enforces this exception more strictly than Chrome/Firefox. Fixed with `-e N8N_SECURE_COOKIE=false` (fine for a local-only, non-internet-facing instance) or just switching to Chrome and using `localhost` instead of `127.0.0.1`.

### n8n concepts — the real translation from a week of Python

**Triggers** — every workflow starts from an event. **Manual Trigger** ("When clicking 'Execute workflow'") is the default starter node n8n adds automatically — only fires from inside n8n's own UI, no external URL, can't be reached by `curl`. Needed a real **Webhook** node instead for anything external-facing — swapped it in explicitly (delete Manual Trigger, add Webhook, rewire the connection; a node merely sitting near another on the canvas doesn't mean it's wired in — the actual connecting line is what matters, and only one line was truly "live" even though two looked visually close).

**Expressions (`{{ }}`)** — n8n's mechanism for pulling dynamic data from previous nodes into a field, conceptually identical to Python dict access (`response.json()["choices"][0]["message"]["content"]`), just UI syntax instead of code:
```
{{ $json.body.prompt }}                    # pulling incoming webhook data into the request body
{{ $json.choices[0].message.content }}     # pulling the reply text back out of Groq's response
```
**Fixed vs. Expression mode** on any field (toggled via the small `fx` icon) — Expression mode is for values that genuinely change per-request (the prompt); Fixed mode is for constants (an API key). Accidentally leaving a field in Expression mode with nothing valid typed in showed n8n's internal placeholder `__n8n_BLANK_VALUE_...` — not an error message, just what an empty expression evaluates to; the actual fix was toggling back to Fixed mode.

**Credentials, not External Secrets** — "External Secrets" (pulling from an outside vault like AWS Secrets Manager) is Enterprise-only. The free, correct mechanism on Community Edition is the node's own **Credential** system: HTTP Request → Authentication → Generic Credential Type → Header Auth → store `Authorization: Bearer <key>` as a named, reusable credential. Stored encrypted in n8n's own database (inside the Docker volume — why the volume mattered beyond just workflows). **Same underlying reason as `.gitignore`/`.env` from Day 1** — paste the raw key directly into a node field instead, and it becomes part of the workflow's exported JSON, leaking with any share/export/version-control of that workflow.

**Body Content Type = JSON, "Using JSON" mode (not "Using Fields Below")** — same `json=` vs `data=` distinction from Day 2's `requests.post()`; JSON mode is what correctly serializes and sets `Content-Type` for a nested payload like `messages: [{role, content}]`, which the fields-based UI handles awkwardly.

**Test URL vs. Production URL, and test-mode's one-shot listening:** the Test URL only exists once a real Webhook node is present, and only actually listens *after* clicking "Test workflow" (or "Execute workflow") — it captures exactly one real external call per click, then stops. Sending a `curl` request without arming it first returns a 404 ("webhook is not registered"), with n8n's own error hinting at the fix. Production URL goes live once the workflow is activated (a separate toggle), and doesn't need re-arming per call.

**Respond to Webhook — needed two separate fixes, not just adding the node:**
1. The **Webhook node itself** has a "Respond" setting defaulting to "Immediately" — meaning it auto-acknowledges the moment it receives a request and never actually waits for the rest of the workflow to finish, so a Respond to Webhook node downstream never runs (n8n flags it "unused" on execution). Had to change this to "Using 'Respond to Webhook' Node."
2. Even with that fixed, the Respond to Webhook node's own **"Respond With"** setting defaulted to sending everything it received — the *entire* raw Groq response object. Had to explicitly set it to "Text" and add the extraction expression (`{{ $json.choices[0].message.content }}`) to get back just the clean reply text, mirroring exactly what `ask_llm`'s `return` statement does in Python.

### The full debugging sequence, in order (worth remembering the *pattern*, not just each fix)
1. Secure cookie blocked Safari → fixed with `N8N_SECURE_COOKIE=false` env var.
2. Tried "External Secrets" for the API key → wrong feature (Enterprise-only) → used node Credentials instead.
3. Left the credential's Value field in Expression mode by accident → saw `__n8n_BLANK_VALUE` placeholder → toggled to Fixed mode.
4. First real test replied generically ("Is there something I can help you with?") → traced to the workflow still being wired to the old Manual Trigger, not the new Webhook node, despite both being visually near the HTTP Request node.
5. `curl` returned 404 "webhook not registered" → test-mode webhooks only listen after clicking "Test workflow," one call at a time.
6. First successful call returned `{"message":"Workflow was started"}` → Webhook node's "Respond" setting was on "Immediately," never waiting for the rest of the flow.
7. Next call returned the *entire* raw Groq JSON object instead of just the reply → Respond to Webhook node's "Respond With" wasn't set to extract just the text field.
8. Final call: clean plain-text reply only — fully working.

**The real lesson in that sequence:** almost every step *looked* like a new, unrelated bug, but each was actually "n8n has an extra layer of explicit configuration (routing, response mode, listening state) that Python's plain `return`/`print()` never required" — worth remembering that visual/no-code tools trade code-level control for UI-level settings that are just as easy to misconfigure, not easier by default.

### Supplement — how n8n's engine actually works, and API vs. webhook

**The full request trace, layer by layer:**
1. `curl` sends a real HTTP POST over TCP → Docker's `-p 5678:5678` routes it into the container's network namespace.
2. n8n (a Node.js/Express server) matches the URL against its internal routing table. **Test mode registers that route dynamically, for exactly one call, when "Test workflow" is clicked** — which is precisely why re-running `curl` without re-clicking it returns a 404 "not registered." This is a deliberate debugging/UX choice (capture one clean example's data per test click, not a technical ceiling) — the **Production URL**, live once the workflow is activated, has no such one-shot limit and can handle many concurrent executions.
3. The raw request gets converted into n8n's internal `{ json: {...} }` items format — same role as `response.json()`, just automatic.
4. The workflow engine walks the node graph in order, resolving `{{ }}` expressions against whatever data is currently available at each node's input, then running that node's logic.
5. **The one genuinely new concept vs. anything built in plain Python:** with Webhook's "Respond" set to "Using Respond to Webhook Node," the engine holds the original HTTP connection open in memory across every node in between — it does not reply until execution physically reaches the Respond to Webhook node. This is exactly why "Respond: Immediately" caused a premature reply earlier in the day, and it's a mechanic with no equivalent in a single Python script (it only shows up once you're running a real server, e.g. FastAPI in Week 4).
6. The credential (Groq key) gets decrypted and injected as a real header only at the moment the HTTP Request node actually runs — transient, in-memory, never written into the workflow's exported JSON.

**Direct link back to Day 4:** Node.js (what n8n runs on) is built on the same single-threaded, non-blocking-I/O event loop model as Python's `asyncio`. Traced through with real numbers: when 3 concurrent `ask_llm_async` calls hit `await session.post(...)`, each one suspends (hands control back to the loop) rather than blocking; the loop starts the next one instead of waiting idle; all 3 requests end up in flight simultaneously; whichever response arrives first gets resumed first. Nothing runs literally at the same instant (one thread, one thing at a time) — the entire speedup comes from never sitting idle waiting on I/O when other work could start instead. n8n's server does the exact same thing if two people call an activated webhook near-simultaneously: interleaved, not blocked, not truly parallel.

**API vs. webhook — the actual distinction (not two technologies, one pattern flip):**
- **API call = you initiate** ("pull"). All of Days 1–4's `requests.post()`/`aiohttp` work — you decide when to ask, the server just waits to be asked.
- **Webhook = they initiate** ("push"). Today's Webhook node registers a URL and passively waits for someone else to decide when to call it — n8n has zero control over timing.
- Mechanically a webhook *is* just an HTTP endpoint, same as an API — the difference is entirely about who calls whom and why, not the underlying protocol.
- **Why it matters practically:** polling an API on a timer (n8n's Schedule Trigger) to check "anything new yet?" wastes calls and adds latency; a webhook gets called the instant something actually happens, zero wasted checks. Same conceptual upgrade as the `watchdog` live-folder-watching idea flagged earlier (event-driven) vs. Day 3's batch script (poll-on-demand).

---

## Day 7 — Schedule Trigger, IF Node, OAuth, and a Real Multi-Service Pipeline

**Goal:** Form submission → Google Sheets (OAuth) → Slack alert (webhook-as-credential). Plus: Schedule Trigger (the "pull" pattern made concrete) and an IF node doing real input validation.

### Real-world grounding for today's pattern (asked for explicitly — keep doing this every day going forward)
**Form → Sheet → Slack alert** is one of the most common first automations built in real companies: sales lead capture (speed-to-lead is a measured, revenue-relevant metric — a webhook beats polling here because immediacy has real dollar value), recruiting/HR intake, IT helpdesk requests, event signups, expense/approval audit trails. Built with a tool like n8n instead of paid SaaS specifically because it's free, fast to stand up, and maintainable by a non-engineer afterward — this is the actual "citizen developer" trend driving demand for this role.
**Schedule Trigger's real niche is separate:** uptime/health monitoring (how tools like UptimeRobot work internally), scheduled report digests, nightly reminder/nudge checks. **Interview-ready rule of thumb: webhook when reacting instantly to something that just happened; cron/schedule when the value is a predictable recurring check.**

### Schedule Trigger — the "pull" pattern, made concrete
Built a separate test workflow: Schedule Trigger (every 30s, for testing only) → HTTP Request (fixed hardcoded prompt, no `{{ }}` needed since nothing triggered this except time itself).
- **Gotcha:** clicking "Execute workflow" always runs once, immediately, manually — regardless of trigger type. It does **not** start the trigger's own timing logic. The schedule only actually runs on its own once the workflow is genuinely published/active.
- **n8n 2.0 changed how activation works** — the old simple on/off "Active" toggle is gone, replaced by a **Save & Publish** model: every edit autosaves as a new version, but nothing goes live in production until you explicitly click **Publish**. This was a deliberate n8n redesign specifically to stop people from accidentally pushing live changes to a running production workflow while debugging — a real production-safety lesson, not just a UI change. Real lesson: **when a tool's UI doesn't match what you expect from memory/older tutorials, verify against current docs rather than assume — tools change versions fast.**
- **To inspect a scheduled run's data:** the live Editor canvas always shows "No input connected / No output data" for an idle node — that's just the blueprint view. Real data only exists inside the **Executions** tab → click a specific timestamped row → click the node *within that snapshot*.
- Deactivated/unpublished after confirming it worked — a 30s interval left running burns free-tier API limits for no further benefit.

### IF node — real input validation, not a toy example
Inserted between Webhook and HTTP Request (click the connecting line → **+** appears mid-line to insert a node). Condition: is `{{ $json.body.prompt }}` non-empty? **True** output → HTTP Request (existing path). **False** output → a second Respond to Webhook node returning a fixed error message, Groq never gets called.
- This is the visual, no-code equivalent of `if response.status_code == 200:` from Day 2/4 — same reasoning, just on the *input* side instead of the *output* side, and directly matches the roadmap's "validate AI outputs... implement error handling" line.
- Confirmed by checking execution history: on the invalid-input test, the HTTP Request node genuinely never ran at all.

### OAuth — the second authentication model (vs. Groq's Bearer-token key)
**Why Google needs a different model than Groq:** an API key just proves "this app has a valid key." Google Sheets needs something stronger — proof that a *specific human* explicitly, revocably consented to let this app touch *their* account.
**The flow, traced through for real:**
1. App redirects to Google's own login page — password never touches the third-party app (n8n).
2. Google shows a consent screen ("Allow n8n to access your Sheets?").
3. On approval, Google redirects back to a pre-registered **redirect URI** with a temporary code.
4. That code gets exchanged for an **access token** (short-lived) + a **refresh token** (long-lived, silently gets new access tokens later without re-login).
- The redirect URI must be registered in advance specifically so a malicious site can't intercept the consent code — this is *why* OAuth needs more upfront setup than "paste a key."

**Real setup sequence (Google Cloud Console):**
1. Create a project → enable the specific API needed (Google Sheets API).
2. Configure the OAuth consent screen (**"Google Auth Platform"** in the current UI — same thing, renamed) — App type External, add your own account under **Audience → Test users** (not under "Overview," which is just an analytics dashboard — easy wrong-tab mistake).
3. Create OAuth Client ID, type **Web application**. Skip "Authorized JavaScript origins" (that's for client-side browser JS, not a server like n8n). **Authorized redirect URIs** is the field that matters — copy the exact callback URL n8n's own credential screen displays (`http://localhost:5678/rest/oauth2-credential/callback`) rather than guessing it.
4. Get Client ID + Client Secret, paste into n8n's Google Sheets credential, click "Connect my account" — this triggers the real login/consent flow just described.

**Real error hit: "Access blocked: n8n has not completed the Google verification process," Error 403 access_denied.** Any OAuth app that hasn't gone through Google's full public verification starts in **Testing mode** — it refuses login for *any* account, including your own, unless explicitly whitelisted under Test users first. Not a bug — a real security default preventing a half-configured app from being usable by strangers. Fixed by adding the exact login email under Audience → Test users, then retrying the connection.

**Once connected:** Google Sheets node, operation **Append Row**, columns mapped via `{{ $json.FieldName }}` — same expression mechanism as Day 6's `{{ $json.body.prompt }}`, now pulling from the Form Trigger node's output shape instead of a raw webhook body.

**Gotcha, same pattern as Day 6:** an expression field showing red/"undefined" almost always means no real test data has flowed through yet (submit the actual form once via its real URL, not just click the node's own test button) — or, second cause, a field-name mismatch between what the Form Trigger actually outputs (check its Output tab for the *exact*, case-sensitive key) and what the expression references.

### Slack Incoming Webhook — a third, different secrecy model
Slack's Incoming Webhook is the same push pattern as n8n's own Webhook node, just flipped: Slack hands *you* a URL to send requests *to*, and posts whatever JSON you send as a message in a chosen channel.
- Setup: api.slack.com/apps (the developer console — a completely different site from slack.com/the Slack client itself, easy first mix-up) → Create New App → From scratch → pick the target workspace → enable **Incoming Webhooks** → Add New Webhook to Workspace → pick a channel → copy the generated URL.
- **Auth model, worth contrasting explicitly with the other two used this week:** Groq = Bearer token in a header (key proves identity). Google Sheets = OAuth (a specific human's revocable consent). Slack's Incoming Webhook = **the URL itself *is* the credential** — no separate header or token needed; anyone holding the exact URL can post to that channel. Wired via a plain HTTP Request node (POST, JSON body `{"text": "..."}`, Authentication: None) — deliberately not n8n's dedicated Slack node, to reinforce that a "Slack integration" is just another HTTP Request underneath, same as everything else built this week.
- Final confirmed result: real form submission → row appended to Google Sheet → Slack message "New form submission from [Name]" posted automatically, full chain working end to end.

---

### Follow-up (a few days after Day 7) — the secret leak scare, in plain language

Tried to commit the exported n8n workflows to GitHub, and the push got **rejected**. GitHub scans everything pushed to it for things that look like secret keys or tokens, and it recognized the real Slack webhook URL sitting in plain text inside the exported Sheets+Slack workflow file. GitHub blocked the push before it ever landed in the repo — so nothing actually leaked publicly, but it was a real close call, not a false alarm.

**Why it happened:** back on Day 7, the Slack webhook was set up by pasting the real URL straight into the HTTP Request node's URL field — unlike Groq's key, which went through n8n's proper Credential system. That was fine while just clicking around locally, but the moment the workflow got exported to a file (to put it in git), that raw URL came along with it, in plain readable text.

**Quick fix:** swap the real URL out for a placeholder in the file, then `git commit --amend` before pushing again — since GitHub never actually accepted the bad version, there's no messy history to clean up, just a straight swap and recommit.

**Proper fix:** instead of hardcoding secrets into a workflow at all, n8n can pull values from environment variables set on the Docker container — same idea as Python's `os.getenv()` reading a `.env` file back on Day 1, just done through Docker's `-e` flag instead. So the container got restarted with an extra `-e SLACK_WEBHOOK_URL="..."` flag, and the node was pointed at `{{ $env.SLACK_WEBHOOK_URL }}` instead of the raw pasted URL.

**Two extra snags hit along the way, both worth remembering:**
1. n8n 2.0 actually **blocks access to environment variables by default now** as a security measure — so `{{ $env.SLACK_WEBHOOK_URL }}` threw an "access denied" error until one more flag got added to the docker command: `-e N8N_BLOCK_ENV_ACCESS_IN_NODE=false`.
2. Editing the exported JSON file by hand to add that expression broke the file — because n8n doesn't store `{{ }}` expressions as plain text in its JSON, it stores them as a quoted string starting with an equals sign, like `"={{ $env.SLACK_WEBHOOK_URL }}"`. Typing the expression into n8n's actual UI (instead of hand-editing the exported file afterward) avoids this entirely, since n8n formats it correctly on its own before it's ever exported.

Also rotated the real Slack webhook URL afterward, just to be safe, since it briefly touched GitHub's servers during the failed push even though it was never actually stored there.

**The big real-world lesson:** any secret value needs to go through a proper credential or environment-variable mechanism from the very start — not "whatever gets it working right now" — because the moment something gets version-controlled, exported, or shared, whatever was hardcoded travels along with it. Same exact `.env`/`.gitignore` lesson from Day 1, just showing up again inside n8n instead of Python.

---

## Day 8 — Production-Grade Error Handling: Retry, Dead-Lettering, Centralized Alerting

**Goal:** move past "a workflow that works when everything goes right." Real production systems have three distinct failure-handling layers — most self-taught builds only ever implement the first one. Built and proved all three today, on the real Day 6/7 workflow.

### The three layers, and where each shows up in real companies
1. **Retry** — transient failures self-heal without a human noticing.
2. **Alerting** — failures that aren't transient need to reach a human fast (this is literally what PagerDuty/Opsgenie/Sentry exist to do at scale).
3. **Dead-lettering** — once retries are exhausted, the failed data needs to land somewhere reviewable, not vanish into a log nobody reads (the same concept behind AWS SQS's dead-letter queue, or Airflow's `on_failure_callback`).

### Layer 1 — Node-level retry
Node → **Settings** tab (separate from Parameters) → **Retry On Fail** (toggle) → **Max Tries** (set 3, matching the Day 4 Python default) → **Wait Between Tries** (fixed delay in ms, e.g. 2000).
**Real limitation, confirmed by testing, not just assumed:** n8n's built-in retry does **not** distinguish a hopeless failure (bad URL, bad auth — will fail identically every time) from one worth retrying (429/5xx) — it retries blindly on any failure. This is a real, specific gap vs. the `RetryableError`/`NonRetryableError` split hand-built in Python on Day 4. **Good, concrete interview line:** *"n8n's native retry doesn't distinguish retryable from non-retryable failures — for that, I'd wrap the call in a Code node reusing the same exception-based logic I built by hand."*
Also confirmed: n8n's retry is **fixed-interval**, not exponential-with-jitter like the hand-built Python version — another real, nameable gap.

### Layer 2 — Dead-lettering (local, per-node)
Node Settings → **"On Error" → "Continue Using Error Output"** creates a second output connector (**Error**, alongside **Success**) on that node. This is different from the Continue-on-Fail flag alone — it actually routes failed items to a separate path with the error data attached, rather than just letting execution limp forward.
**Real captured error shape** (from a genuine Slack webhook failure): original submission data (`Name`, `Email`, etc.) **plus** an appended `error` object — `error.message` (human-readable, e.g. `404 - "no_team"`), `error.status` (the real HTTP code), `error.name` (`"AxiosError"` — confirms n8n's HTTP Request node runs on Axios, Node's equivalent of Python's `requests`), and a full `error.stack` trace (Node.js internal file paths — useful for live debugging, but deliberately **excluded** from the dead-letter sheet since it's unreadable noise for a human reviewing a tracking spreadsheet later; that level of detail belongs in real logging/monitoring, Week 8's territory, not a spreadsheet).
Built chain: **Edit Fields node** (Manual Mapping mode — maps `error.message`/`error.status` plus the original fields, renaming the original `Timestamp` to `submitted_at` to avoid clashing with a new `failed_at: {{ $now }}`) → **Google Sheets Append Row**, pointed at a dedicated **`Failed_Submissions`** tab, not the main data tab.

### Layer 3 — Centralized Error Workflow (the genuinely new concept today)
A *separate* workflow whose only job is reacting to failures from *other* workflows — catches anything unhandled anywhere, not just the specific failure points a builder remembered to wire local error paths for.
**Build:** new workflow → **Error Trigger** node (no configuration needed — it only ever fires when n8n itself invokes it) → HTTP Request → Slack webhook.
**Wiring it up:** main workflow's own **Settings → Error Workflow** dropdown → select the error-handler workflow.

**Real gotchas hit, each one genuinely instructive:**
- **The Error Workflow dropdown was disabled/greyed out at first.** Cause: the target error-handler workflow hadn't been Published yet — n8n requires the target to be a valid, live workflow before it can be selected as an error handler.
- **After fixing that and triggering a real failure, the Error Workflow still never fired — "No executions found."** Root cause, confirmed via n8n's own docs: **the Error Trigger only fires for genuine production executions, never for manual test runs** — even if a real HTTP request was involved and the node genuinely failed. Submitting via the Form Trigger's **Test URL** (or clicking "Execute workflow" in the editor) is *always* classified as a manual test internally, regardless of how "real" the request looks. **Same Test-URL-vs-Production-URL distinction from Day 6/7's Webhook node, just resurfacing here in a less obvious spot.** Fix required three things simultaneously: (1) the main workflow itself genuinely Published/Active, not just the error handler, (2) the error handler actually *selected and saved* in the dropdown, not just unlocked, (3) the form submitted through its real **Production URL**, not the Test URL.
- **Once it finally fired, the Slack alert itself failed with `no_text`.** Cause: "Specify Body" was left on **"Using Fields Below"** instead of **"Using JSON"** — in fields mode, no `text` key was ever actually populated, so Slack correctly rejected the payload for missing its one required field. Switched to "Using JSON" with an explicit `{"text": "..."}` body, referencing the real field paths confirmed directly from the Error Trigger's own Input panel (`execution.error.description`, `context.name`, etc.) rather than guessed.
- **A `[ERROR: not accessible via UI, please run node]` message under the `{{ $env.SLACK_WEBHOOK_URL }}` field turned out to be purely cosmetic** — n8n's live expression *preview* genuinely cannot resolve `$env` values for on-screen display, but the value resolves correctly at actual execution time regardless. Confirmed this wasn't a real problem by checking the Output panel: a real, structured JSON error response came back *from Slack's own servers*, proof the request truly reached Slack — a broken URL substitution would have shown a connection-level error instead, not a proper API response.

**Final confirmed result:** a genuine, unprompted Slack message — *"🚨 Workflow failed: Requested entity was not found. :: Sheets+Slack"* — fired entirely by the separate Error Handler workflow after a real production form submission hit a deliberately broken Google Sheets node, with zero manual intervention. Two structurally different kinds of Slack alerts now exist side by side in the same channel: one from the **known, locally-handled** dead-letter path (Layer 2), one from the **unanticipated, centrally-caught** failure (Layer 3) — genuine layered defense, not just one catch-all.

### Idempotency risk — flagged, then actually solved with a real fix

**The risk (Day 8):** Google Sheets "Append Row" is a POST-like operation and is **not idempotent** (same Day 2 lesson). If a retry fires *after* a row was actually successfully written but the confirmation response merely timed out or got lost, the retry would append a **duplicate row**, silently corrupting the data.

**The fix, built and proven working (follow-up session):**

**Key insight worth remembering above all else: where the key gets generated matters more than how.** Generating a random ID *inside* the write node itself would produce a *different* ID on every retry — solving nothing, since the whole point is recognizing "this exact submission was already attempted." The key must be generated **once, upstream**, right after the trigger, *before* anything risky — because n8n's retry re-runs a failed node with its *existing* input, it never regenerates data from earlier nodes. That's what makes the key stay constant across retries.

**Step 1 — generate the key once, in a Code node right after the trigger:**
```javascript
for (const item of $input.all()) {
  item.json.idempotency_key = `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
}
return $input.all();
```
**Gotcha:** the Code node defaults to (or can be switched to) Python mode, which threw `"Python runner unavailable: Python 3 is missing from this system"` — the standard self-hosted n8n Docker image is Node.js-based and has no Python runtime at all. Switched the node's language dropdown to **JavaScript**, which runs natively inside n8n's own process with no external dependency, and it worked immediately. Used plain `Date`/`Math` (no `crypto` module) specifically to sidestep any chance of hitting another n8n 2.0 sandbox permission wall like the `$env` one from Day 8's incident.

**Step 2 — check-before-write, instead of blind-append:**
Added a **Google Sheets "Get row(s)"** node before the real append, filtering `Column: Key` equals `{{ $json.idempotency_key }}`, with **"Return only First Matching Row"** enabled to keep output predictable.

**Real gotcha — zero matches means zero items, not one empty item.** By default, when the filter matches nothing, the node emits *nothing at all* downstream — which would silently kill the whole chain for every genuinely new (non-duplicate) submission, the common case. **Fix: node's own Settings tab (not Parameters — same tab as Day 8's Retry On Fail) → toggle "Always Output Data" on.** This forces exactly one item to flow through either way, with fields like `row_number` simply absent on a non-match.

**The actual signal to branch on:** `row_number` — this field only exists at all when a real matching row was found by Google Sheets, making it a cleaner check than testing `Key` directly.

**Step 3 — the IF node:** `{{ $json.row_number }}` **is empty** →
- **true** (no match — genuinely new) → proceeds to the real Google Sheets append (writes to the dedicated `Idempotency` tracking tab) → then the Slack alert
- **false** (match found — duplicate) → routed to a **No Operation, do nothing** node — fully silent, no write, no alert at all (a deliberate choice: duplicates should be invisible, not generate a misleading "new submission" alert for something that already happened)

**Real gotcha — data reference after the branch point.** Past the IF node, `{{ $json.X }}` refers to whatever the *immediately preceding* node output (Get row(s), possibly an empty `{}`), **not** the original submission data from several nodes back. Fixed by referencing the Code node **by name** instead of relying on the implicit immediate-predecessor `$json`:
```
{{ $('Code in JavaScript1').item.json.Name }}
```
This node-by-name reference works regardless of what sits directly upstream, and is the correct general pattern any time a workflow branches and you need data from further back than the immediately preceding node.

**Real proof, not just a working diagram:** submitted a genuine new entry through the Production URL — one row appended, one Slack alert fired. Then, from that same execution in the Executions tab, **manually re-ran just the Get row(s) node** — the exact real-world scenario being defended against (a retry hitting an item that was already fully processed). Confirmed: the IF node correctly routed to `false` → No Operation, **no duplicate row appeared, no second Slack alert fired.** The original Day 8 risk is now genuinely, provably closed — not just described.

---

## Day 9 (in progress) — Docker Networking Fundamentals (Postgres + n8n)

**Goal:** wire up a real Postgres database alongside n8n, as infrastructure for a bigger "API → transform → database, with fallback" workflow (Portfolio Piece #0). Before building the workflow itself, had to actually understand Docker networking — genuinely new territory, distinct from anything from Day 6.

### What a Docker network actually is
Not physical — a **software-defined virtual network** built from Linux kernel features (network namespaces, virtual ethernet interfaces, a virtual bridge). `docker network create automation-net` does three concrete things: creates a private virtual subnet, gives every attached container its own private IP on it, and runs an **embedded DNS resolver** scoped to just that network.

**The core isolation fact:** every container gets its own private network namespace — its own private `localhost`, invisible to every other container and to the Mac itself. Two containers not attached to the *same* Docker network cannot reach each other at all, not by name, not even by raw IP — genuinely separate virtual subnets with no route between them.

### The two separate problems this creates, and their two separate fixes — don't merge these
1. **Container ↔ container** (n8n needs to reach Postgres): container IPs on a custom network are dynamically assigned and **can change** between restarts — relying on a hardcoded IP would be fragile. Fixed by the custom network's **embedded DNS**: containers resolve each other **by name** (`postgres-fx`) instead of by IP. No `-p` flag involved anywhere in this path.
2. **Host ↔ container** (the Mac's browser needs to reach n8n): solved entirely differently, by **`-p 5678:5678`** — a direct port mapping, `HOST:CONTAINER`. Nothing to do with DNS or changing IPs — it's a completely separate mechanism for a completely separate problem. **Easy mistake to make: thinking `-p` is "how containers find each other" — it isn't; it's specifically the host-to-container bridge.**

**Real trace of what happens when n8n's Postgres node fires** (host `postgres-fx`, port `5432`):
1. n8n's container asks Docker's embedded DNS server (not a real internet DNS lookup) "what IP is `postgres-fx`?"
2. That DNS server keeps a live registry of every container on `automation-net`, keyed by container name, and returns the current internal IP (e.g. `172.19.0.3`).
3. n8n's container opens a direct TCP connection to that IP on port 5432, entirely inside Docker's private virtual world — the Mac's actual network hardware is never involved.

**Why the default bridge network wouldn't have worked as cleanly:** without an explicit `--network`, Docker places containers on its default bridge — which allows raw IP-to-IP reachability but does **not** run the name-resolution DNS service. Would have meant manually running `docker inspect` to find Postgres's ever-changing IP and hardcoding it — fragile, exactly what a custom network avoids.

### Why not just use `--network host` for Postgres (a genuinely surprising, Mac-specific answer)
`--network host` removes network isolation entirely, sharing the real host's network stack directly — no `-p` needed, in theory. **But Docker Desktop on Mac doesn't run containers on macOS at all** — macOS lacks the Linux kernel features Docker needs, so Docker Desktop silently runs a hidden Linux VM in the background, and *every* container this whole week has actually been running *inside that VM*, not literally on the Mac. `--network host` would make a container share *that hidden VM's* network — reachable at `localhost` *inside the VM*, which the real Mac terminal has no direct access to. This is a well-known Docker Desktop limitation, and it's exactly why `-p` (which Docker Desktop specially bridges from the VM back to the real Mac) is the standard way to reach a container from the actual machine.

Separately, even without the Mac VM quirk, host networking is generally the wrong default choice: no isolation (broader blast radius if compromised), port collisions become manual to manage, and it forfeits the embedded-DNS name resolution that made this setup clean.

**Forward link to Week 9:** Kubernetes Pods are the same underlying idea — each isolated, each needing to be found. Kubernetes **Services** solve the identical problem via the cluster's own internal DNS, just distributed across many physical machines instead of one Docker host (that's what the `overlay` network driver — for multi-host container networking — is a stepping stone toward). Understanding *why* the custom bridge network was necessary today is most of the conceptual work for understanding Kubernetes Services later.

**Practical proof, worth running rather than trusting blindly:**
```
docker exec -it n8n ping -c 2 postgres-fx
```
Runs a command *inside* the live n8n container, confirming the name genuinely resolves and a response comes back — the DNS mechanism observed directly, not just described.

---

## Day 9 (continued) — Postgres Credential, JSON Escaping, Python Task Runner Sidecar

### Postgres credential setup — the same networking bug recurring
n8n Postgres credential: Host `postgres-fx`, Database `automation`, User `postgres`, Password matching `POSTGRES_PASSWORD`, **SSL disabled** (the local container has no SSL certs configured at all — a real, common gotcha with any quick local Postgres setup, worth checking for on any fresh credential form).

**Real gotcha, twice in one day:** "Host not found, please check your host name." `docker network inspect automation-net` showed only `postgres-fx` registered — **n8n itself was never attached to the network**, despite the network existing. Root cause: n8n had been restarted at some point using an older command that predated `--network automation-net` being added — Docker does **not** retroactively add a running container to a network created after it started; the flag has to be present at `docker run` time, or added live afterward. Fixed live, without restarting, with:
```
docker network connect automation-net n8n
```
**This exact same "container exists but isn't on the network" gap recurred a second time later the same day** with the Python runner sidecar — turned out n8n itself had actually crashed/never started that time (see below), a different root cause producing the identical symptom. **General lesson: "container not found on the network" can mean either "forgot the `--network` flag" or "the container isn't running at all" — always check `docker ps` first, don't assume which one it is.**

### JSON escaping — "Using JSON" mode isn't always safe with dynamic values
Building a Slack alert body referencing a real captured error message (`error.message` containing its own literal quote marks, e.g. `404 - "no_team"`) broke n8n's JSON parser: *"Expected ',' or '}' after property value."* Cause: substituting a dynamic value straight into hand-written JSON text doesn't escape anything inside that value — if the value itself contains `"`, it prematurely closes the JSON string, corrupting the structure.
**Two valid fixes, opposite of Day 8's Slack bug (worth holding both in mind, not just one):**
- Switch **"Specify Body"** to **"Using Fields Below"** instead of "Using JSON" — n8n's fields UI escapes values automatically.
- Or, stay in "Using JSON" mode but wrap the dynamic parts in `JSON.stringify(...)` inside the expression — this returns a fully-escaped, self-quoting string, so no manual quote marks are needed around the `{{ }}` at all: `{{ JSON.stringify('text: ' + $('Node').item.json.error.message) }}`.
**The real rule to remember:** "Using JSON" is fine for fixed, known structure with simple embedded values; the moment a value's *contents* are unpredictable (a real error message, a user's free-text input), either switch modes or wrap it in `JSON.stringify()` — don't hand-splice unknown text into raw JSON syntax.

### Real Python transform, JavaScript vs. Python side by side
```javascript
// JavaScript
const rates = $input.first().json.rates;
const currencyPairs = Object.entries(rates).map(([currency, rate]) => ({ json: { currency, rate } }));
return currencyPairs;
```
```python
# Python
rates = _input.first()["json"]["rates"]
currency_pairs = [{"json": {"currency": currency, "rate": rate}} for currency, rate in rates.items()]
return currency_pairs
```
- `_input` not `$input` — Python doesn't allow variable names starting with `$`.
- `["json"]["rates"]` not `.json.rates` — n8n's Python data arrives as real Python `dict`s, which use bracket key access; there's no dot-notation shorthand for dict keys in Python the way JS objects have it.
- List comprehension replaces `.map()` — Python's native syntax for "transform every item," built into the language rather than a method call.
- `.items()` replaces `Object.entries()` — Python dicts have this built in natively.
- **The `{"json": {...}}` wrapping requirement is identical in both languages** — that's n8n's own rule, unrelated to which language runs the code.

### Setting up a real Python task runner — genuine multi-container infrastructure, not a toggle
**Confirmed via n8n's own docs, not assumed:** Python in the Code node requires **external mode** — a separate sidecar container (`n8nio/runners` image) running alongside n8n, communicating over a shared auth token. This is real infrastructure, the same "two containers, one custom network, resolved by name" pattern as Postgres earlier today — deliberately reused rather than learning a new concept.

**Setup:**
1. Generate a shared secret: `openssl rand -hex 32`.
2. Restart n8n with task-runner env vars added: `N8N_RUNNERS_ENABLED=true`, `N8N_RUNNERS_MODE=external`, `N8N_RUNNERS_BROKER_LISTEN_ADDRESS=0.0.0.0`, `N8N_RUNNERS_AUTH_TOKEN=<the generated secret>` — alongside the existing flags, on `automation-net`.
   - **`N8N_RUNNERS_BROKER_LISTEN_ADDRESS=0.0.0.0` is the genuinely important one** — by default, n8n's internal task broker only listens on its own container's private `localhost`, invisible to anything else even on the same custom network. Setting it to `0.0.0.0` makes it listen on all interfaces so a *separate* sidecar container can actually reach it. **Same "isolated localhost per container" concept from earlier today, resurfacing in a third spot.**
3. Run the runner sidecar on the same network, pointed at n8n by container name: `docker run -d --name n8n-runners --network automation-net -e N8N_RUNNERS_AUTH_TOKEN=<same secret> -e N8N_RUNNERS_TASK_BROKER_URI=http://n8n:5679 n8nio/runners:latest`.

**Real gotcha:** the first restart attempt of n8n (with the new task-runner flags) silently produced **no running container at all** — `docker network connect automation-net n8n` failed with `"No such container: n8n"`, and `docker ps`/`docker ps -a` showed nothing, because **`--rm` deletes a container immediately if it crashes on startup**, leaving zero trace to debug from. Root cause: the long `docker run` command had been pasted across multiple lines with `\` continuations, and — matching a pattern that had already happened twice earlier this week (a mangled `git push`/`git add` paste, an earlier truncated `docker run`) — the multi-line paste likely got mangled in the terminal. **Fix: always run long Docker commands as a single unbroken line** rather than trusting multi-line continuation in this terminal setup.

**Confirmed working:** three containers now resolving each other by name on `automation-net` (`n8n`, `postgres-fx`, `n8n-runners`), Python Code node executing real Python instead of throwing "Python 3 is missing" — genuine sidecar architecture built and proven, not just a settings toggle flipped.

---

## Day 10 — Portfolio Piece #0 Write-Up
Written as a standalone README (`PORTFOLIO-PIECE-0.md`) documenting the FX rate tracker's architecture, deliberate failure-mode design, and honest limitations — full content lives in that file, not duplicated here. Core framing: build one genuinely production-shaped pipeline with **zero AI in it** first, so later AI-powered pieces read as an addition to real engineering, not a substitute for it.

---

## Project A — Dependency Health & Security Monitor

**Goal:** three genuinely different external APIs (PyPI, GitHub, OSV.dev), each with a different messy real-world shape, merged and scored into one composite signal per package — deliberately harder than the FX tracker's single clean API.

### PyPI extraction — messy real-world data, not a clean API
`releases[version]` is a **list** of file records (wheel + sdist etc.), not one record — earliest `upload_time_iso_8601` via `min()` gives the true release date.
**The GitHub-link extraction problem, solved in layers, each validated against real broken cases:**
- Naive "grab any `project_urls` value containing github.com" fails hard — real data showed `Funding` (a GitHub *Sponsors* page) and `Changelog` (a file link) sorting before the real `Source`/`Homepage` entries for `pydantic` and `httpx`, and `CI: GitHub Actions`/`issues` sorting first for `aiohttp`/`ollama`.
- Fix layer 1: priority-sort candidates by trustworthy key names (`source`, `repository`, `homepage`) before trusting any of them.
- Fix layer 2: trim every candidate URL down to just its first two path segments (`owner/repo`), which also incidentally cleans up trailing junk like `/actions?query=...` or `/blob/master/...`.
- Fix layer 3 (a real remaining gap layer 2 alone can't catch): a blocklist for reserved GitHub path segments (`sponsors`, `orgs`, `marketplace`) that structurally *look* like a valid `owner/repo` pair but aren't — `github.com/sponsors/username` passes every prior check and still needs an explicit reject.

### Two confirmed n8n platform bugs, not user error — verified via official docs and GitHub issue trackers, not assumed
1. **Python Code nodes cannot reference another node by name at all.** No equivalent of JavaScript's `$('NodeName')` exists in native Python — confirmed directly by n8n's own docs ("Native Python supports only `_items`/`_item`") and matched by an independent community bug report hitting the identical `name '_' is not defined` error.
2. **The external Python task runner's stdlib import allowlist is currently broken.** `N8N_RUNNERS_STDLIB_ALLOW=*` — the documented way to permit standard library imports like `datetime` — is reported ignored across multiple separate GitHub issues, on multiple n8n versions, including nightly builds. Not a config mistake; a currently-open upstream bug.

**Resolution pattern, applied consistently once both were confirmed real:** use JavaScript specifically for the two things Python's native Code node genuinely can't do right now — cross-node references and date/time math (`Date` is a JS language built-in, not an import, so immune to the stdlib-blocking bug entirely) — and keep Python for everything else. A deliberate, explainable hybrid-language architecture, not an inconsistency.

### Merge by position, not by matching field — the actual fix for the cross-node reference gap
Rather than fight the broken node-reference mechanism further, restructured so the OSV branch never needs to recover `package` at all: switched the Merge node to **Combine by Position** instead of matching fields, relying on the GitHub branch (which already reliably carries `package` forward via explicit per-node returns) to supply it in the final merged record.
**Hard requirement for this to stay correct:** both branches must process the same items, in the same order, with nothing filtered or dropped — verified by checking both Merge inputs show identical item counts (15/15) before trusting the output. A branch that silently drops items on a dead-end IF path would misalign every position-based pairing without any visible error.

### Composite health score — three normalized signals, an honest missing-data policy
Recency (PyPI), activity (GitHub), security (OSV historical vuln count) each normalized to 0–100 before combining — raw values on different scales can't be meaningfully weighted together otherwise.
**Archived repos are a hard override to 0** for the activity score, regardless of how recent the last push looks — a maintainer's explicit "this is dead" signal beats any date-based inference.
**Missing GitHub data doesn't get defaulted to "average" (50)** — that would be presenting a guess as a real signal. Instead its weight (0.3) is proportionally redistributed across the two signals that *do* exist, so a package's score stays fair and comparable even when computed from incomplete evidence.
**All three sub-scores are stored alongside the composite, not just the final number** — a bare `62` tells a reviewer nothing actionable; `recency: 95, activity: 40, security: 100` tells them exactly what's dragging the score down. Real production monitoring practice: always store the breakdown.

### OSV.dev — a genuine design decision about what question to ask, confirmed via OSV's own maintainers
Querying **without** a `version` field returns every vulnerability ever recorded for a package name, across its entire history — confirmed directly from an OSV maintainer's own GitHub reply, not assumed. Querying **with** the specific current `version` scopes the answer to "is what I'm using right now actually affected."
**Deliberately chose the version-less (full history) query** for this build, and — the more important lesson — **renamed every field to say `historical_vuln_count`/`historical_vuln_ids` rather than a generic `vuln_count`**, so the stored data can never be misread as "these are current, unpatched risks" when they're actually a broader historical record. Precise labeling matters as much as the underlying logic.
Also worth remembering: **mostly-empty vulnerability results are the correct, desired outcome** for well-maintained packages — not a sign the pipeline is broken. Proved the non-empty path genuinely worked by deliberately testing against a known old, vulnerable version before trusting the empty results on everything else.

### Real bugs hit and fixed along the way
- **A field-name swap** (`github_open_issues` and `github_archived` assigned to each other's keys) silently broke the activity score for nearly every package — a real open-issues count like `76`, sitting under the `archived` key, is truthy in JavaScript, so `if (data.github_archived)` incorrectly treated almost every active repo as archived. Fixed, and hardened further with an explicit `=== true` check so a missing/undefined value can never be confused with a genuine `false`.
- **Run Once for All Items vs. Run Once for Each Item** return-shape mismatch recurred here too (same lesson as Day 4's async work): all-items mode needs a list of `{"json": {...}}`; per-item mode needs one bare `{"json": {...}}` — mixing them produces a nested, confusing "'json' property isn't a dictionary" error rather than an obvious one.
- **`{{ }}` expression syntax has no meaning inside a Code node's actual script** — it's only evaluated in UI parameter fields (URL boxes, JSON body fields configured through Parameters). Writing `{{ $('Node').item.json.x }}` inside Python or JS code just produces that literal string, not a resolved value — a mistake made more than once before it fully stuck.

### Idempotent Postgres storage
Same `UNIQUE` constraint pattern as the FX tracker, this time genuinely using an **upsert** (`ON CONFLICT ... DO UPDATE`) rather than `DO NOTHING` — a deliberate choice, since repeatedly re-running during active development needs fresh results each time, unlike the FX tracker's stricter "first write wins" design. `historical_vuln_ids` stored as `JSONB` (via `$N::jsonb` casting on insert) rather than flattened text, so the array stays real, structured, queryable data rather than a string to re-parse later.

---

## Day 12 (raised bar) — Context Window Management, Measured Not Assumed

**Goal, deliberately upgraded from the original roadmap scope:** don't just "know context windows exist" — build real token counting, a real budget calculator, two competing context-management strategies, and a genuine measured test proving one strategy preserves a planted critical fact that the other loses. Real script, standalone Python (not n8n — see below for why that matters), living in `practice/context-management/`.

### Token counting — real, not estimated
`tiktoken` (`cl100k_base` encoding) used as an honest approximation for Groq's Llama models — different tokenizer under the hood, but standard, accepted industry practice rather than chasing an exact per-provider match. Confirmed real number worth remembering: `llama-3.1-8b-instant` has a **131,072 token (128K) context window**.

### The budget calculator — why it has to run on every single turn, not once
```
available = model_context_window - system_tokens - reserved_output_tokens - formatting_overhead
```
**`reserved_output_tokens` is the one people skip and regret** — fill the entire window with input and the model has zero room left to actually respond. `formatting_overhead` is a small defensive buffer for per-message role-marker tokens that exist but aren't precisely knowable from outside the provider's own tokenizer.
**Real industry scope, not a niche concern:** this has to run fresh before *every* API call for the life of a conversation, not once at the start — the budget available for history shrinks as the conversation grows. Directly relevant to customer support bots, coding assistants, RAG systems (retrieved chunks compete for the same budget as history — Week 5 territory), and agent tool-loops (Week 6–7) alike.

### Two strategies, actually built and actually tested against each other

**Sliding window** — keep the most recent turns, drop the oldest first-by-first until it fits. Simple, but optimizes purely for **recency**, with zero regard for **importance**.

**Hierarchical summarization** — compress older turns into a running summary via a real LLM call, recursively re-summarizing the summary itself if it's still too large after compression. Built with `_depth`/`_max_depth` as a **hard recursion safety cap** — genuine production practice, not just a patch: never trust recursion to terminate purely because the budget math is supposed to work out, since a real misconfiguration (window smaller than the reserved-output default, for instance) can make the target mathematically unreachable.

**Two real bugs hit and fixed, both genuinely instructive:**
1. **The impossible-budget bug** — testing with `model_context_window=200` but leaving `reserved_output_tokens` at its default (1024) made the computed budget permanently `0`, since `max(negative, 0) = 0` — meaning the recursion could never terminate (no non-empty conversation ever has 0 tokens), and every failed iteration burned a real Groq API call. **General lesson: an infinite loop hitting a real paid API is a genuine cost/rate-limit incident, not just a local annoyance — always add a hard depth/iteration cap as a last line of defense, independent of how correct your own math seems.**
2. **The summarize-of-a-summary collapse** — once `to_keep` (the last 4 messages) stopped shrinking round to round, `to_summarize` degenerated into just the *single previous summary message* on every subsequent round. The summarization prompt's own wording ("summarize this **conversation**") caused the model to reasonably respond "there is no conversation to summarize" when handed something that no longer looked like one — silently discarding the planted fact in the process. **Fixed by rewording the prompt to explicitly handle both a full conversation and an already-compressed statement, with an explicit instruction never to bail out with "nothing to summarize."** A genuinely non-obvious failure mode that only a multi-round, real-budget-pressure test would surface — a shallow one-round test would never have caught it.

### The measured proof (Part 4) — the actual deliverable, not the code alone
Planted a specific fact (`"X7829-Q"`, a fake account ID) early in a 12-message test conversation, buried under filler, then ran both strategies against the **identical computed budget** (same `calculate_available_budget()` call, same parameters, for a fair test rather than two separately-tuned scenarios). Automated the check itself (`contains_fact()` using `any(...)`) rather than eyeballing printed output.

**Real result:**
```
STRATEGY                 RESULT         MESSAGES KEPT
Sliding Window           LOST           7
Hierarchical Summary     PRESERVED      5
```
**The genuinely sharp finding, worth being able to state precisely in an interview:** sliding window kept *more* raw messages (7 vs. 5) and still lost the fact — because it optimizes purely for recency, with no concept of importance. Summarization kept fewer messages but preserved more actual information, by compressing intelligently rather than discarding outright. **More messages preserved ≠ more information preserved** — a real, measured, non-obvious distinction, not a talking point taken on faith.

### Engineering hygiene along the way
- **Module separation**: core functions (`summarization.py`) vs. test/check logic (`fact_check.py`) split into separate files, importing cleanly via `from summarization import (...)` — required first fixing `summarization.py` to wrap its runnable test code in `if __name__ == "__main__":`, since without that guard, importing the file would have silently executed its entire test conversation (including real API calls) the instant the import line ran. Same production-code-vs-test-code separation principle Week 8's real `pytest` suite will formalize later.
- **Environment correction**: this exercise was briefly, incorrectly attempted inside an n8n Code node, which hard-blocks all external package imports (`tiktoken` included) by default — same restrictive-sandbox posture already confirmed broken/limited twice in Project A. Corrected by recognizing this was always meant to be a standalone script, run directly via `python3` in the `ai-automation` conda environment — no n8n involved at all.

---

## Day 13 — Structured Output Prompting: json_object vs. json_schema, Measured Not Assumed

**Goal:** move past "ask the model nicely for JSON" — understand and build against the real reliability hierarchy Groq actually offers, and prove the difference between the approaches with real, comparable evidence rather than just reading about it.

### The reliability hierarchy
1. **Plain prompt instructions** — weakest, unreliable (markdown fences, preamble text, malformed syntax).
2. **`json_object` mode** — guarantees syntactically valid JSON, never guarantees it matches any particular schema.
3. **`json_schema` mode, `strict: true`** — constrained decoding at the token level; genuinely cannot produce a schema-violating response. **Real, current limitation confirmed via docs, not assumed: only supported on `openai/gpt-oss-20b` / `openai/gpt-oss-120b` on Groq right now — not on `llama-3.1-8b-instant`, which this whole roadmap has used since Day 1.** Hit this directly as a real 400 error before finding the actual supported models.
4. **Pydantic + manual validation + corrective retry loop** — the practical, ergonomic pattern for models/modes that don't offer a server-side guarantee: catch `json.JSONDecodeError` (not valid JSON at all) and `pydantic.ValidationError` (valid JSON, wrong shape) as two genuinely separate failure categories, and feed the specific validation error back to the model on retry rather than blindly repeating the identical prompt — different in kind from Day 4's transient-failure retry decorator, since this one is *corrective*, not just persistent.

### Composed Pydantic schema — small named pieces assembled into a whole
`Category`, `Priority`, `Sentiment`, `EntityType` as enums (closed, fixed vocabularies — makes "only these exact values are valid" an enforced rule, not a hopeful instruction); `Entity` as a small nested shape (free-text + a constrained type); `TicketTriage` as the top-level composition, including `key_entities: List[Entity]` — a list where every item must itself satisfy a nested shape. **Real distinction worth remembering: "required" (the field must be present) and "non-empty" (a list must have ≥1 item) are different rules — Pydantic only enforces the first by default; use `Field(min_length=1)` for the second if genuinely needed.**

### Real gotcha — strict mode's stricter schema requirements
`additionalProperties: false` must be set on **every** object in the schema tree, or Groq rejects the schema outright before ever calling the model — including nested submodels like `Entity`, not just the top-level class. Fixed via `model_config = ConfigDict(extra="forbid")` on every `BaseModel` in the schema, which Pydantic then correctly reflects in its generated JSON Schema output.

### Real evidence, not just theory — same ambiguous ticket through both approaches
A deliberately category-less ticket (a partnership/marketing proposal, not cleanly fitting `urgent`/`billing`/`technical`/`general`) run through both:
- **`json_object` + retry (llama-3.1-8b-instant):** failed on attempt 1 — invented `type: "department"` for an entity, a value that doesn't exist in the `EntityType` enum. Correctly self-corrected to `"organization"` on attempt 2 after the validation error was fed back.
- **`json_schema` strict (gpt-oss-20b):** succeeded in **one** attempt — structurally incapable of producing an invalid enum value in the first place.
**The real, concrete lesson from this comparison, not just a stated principle:** structured output guarantees **shape**, never **content correctness**. Running the same ambiguous ticket 5 times through both approaches showed `category`/`priority` perfectly stable across both, but `sentiment` genuinely wobbled — 100% consistent `positive` on the Llama/retry path, split between `neutral`/`positive` on the strict/gpt-oss path. **Worth stating precisely: the more rigorously schema-constrained approach was not the more content-consistent one** — strict mode's guarantee never touches which value the model judges correct, only which values are syntactically permitted. Two different model families being compared, not just two API parameters on the same model — worth remembering as a real nuance if this comes up in an interview.

### Engineering hygiene
Same module-separation pattern as Day 12: `models.py` (single shared schema — both approaches import the identical class, preventing silent schema drift between them), `extract_json_object.py`, `extract_json_schema.py`, `compare.py` — each approach genuinely independent and separately testable before being compared side by side.

---

## Day 14 — Classifier Evaluation: Measuring "Is It Actually Right," Not Just "Is It Valid JSON"

**Goal, deliberately built as the natural complement to Day 13, not a repeat of it:** Day 13 proved format reliability. It never once asked whether the classification was *correct*. Reused the existing `TicketTriage` classifier as-is (`category`→category, `priority`→urgency, `requires_immediate_attention`→action_required — same shape as the roadmap's original Day 14 spec, no need to rebuild from scratch) and built a real, measured evaluation harness on top.

### Ground truth — 9 hand-labeled real examples, deliberately including genuine ambiguity
Built with intentional edge cases, not just easy wins: a bug report where urgency and actionability plausibly diverge (low urgency, but still a real fix needed), a ticket genuinely unclear between two categories (its own text admits the ambiguity). **Worth remembering as a real methodology point: ground truth is a human judgment call, not an objective fact — disagreeing with your own earlier labels while reviewing results is a normal, expected part of building an eval set, not a sign of doing it wrong.**

### Real bugs hit while building the harness — both about incomplete data flowing into the report
- First version's `print_report()` only ever displayed *category* mismatches, silently hiding the far more informative urgency/action-required misses — fixed by adding all three mismatch sections.
- `evaluate()` computed `urgency_correct`/`action_correct` booleans but never stored the underlying `true_urgency`/`true_action_required` values themselves needed to *display* those mismatches — a real `KeyError`, and a good general lesson: a correctness flag is only useful for reporting if the two raw values it was computed from are also kept around, not just the boolean result.

### Real, measured results — and a specific, non-random pattern in the errors, not just a percentage
```
Category accuracy: 89%
Urgency accuracy: 67%
Action-required accuracy: 78%
```
**Every single urgency miss was off by exactly one adjacent step** (`predicted high, actual medium` — twice; `predicted medium, actual low` — once), never wildly wrong (`low` vs `high`). **Real finding, not just a number: the model has a systematic bias toward over-escalating urgency by one notch, not random noise** — a materially more specific and useful insight than "67% accuracy" alone communicates, and a direct illustration of why urgency (an *ordinal* field) deserves a different evaluation lens than a plain categorical field like `category` — exact-match accuracy treats "off by one" and "maximally wrong" identically, which can understate how reasonable a model's judgment actually is.
**Both action-required misses predicted `False` when the true label was `True`, on tickets that were either low-urgency or genuinely ambiguous** — a real, explainable pattern: the model appears to conflate "low urgency" with "no action needed," even though the schema treats them as independent judgments. **Concrete, testable next step identified from this, not just filed away:** add an explicit sentence to the system prompt distinguishing the two ("action_required should be True for any confirmed issue regardless of urgency"), then re-run the identical labeled set to see whether the specific misses actually resolve — a real, falsifiable prompt-improvement hypothesis, generated directly from measured evidence rather than guessed at.

---

## Day 15 — Document Data Extraction: Normalization, Not Just Classification

**Goal, deliberately upgraded beyond the roadmap's original "extract fields" scope:** apply Days 13–14's structured-output machinery to real documents, but layer in genuine data-cleaning challenges dates alone never test — currency parsing, informal-text-to-enum normalization, arithmetic cross-validation, and eventually real PDF text extraction (not just plain strings).

### The real design decision — where should normalization happen?
Two legitimate options: ask the model to normalize directly (simple, but only as reliable as the model's compliance), or **extract raw text exactly as it appears and normalize deterministically in code afterward** — chosen deliberately, since it makes normalization testable independent of the LLM's mood that day. System prompt explicitly instructs the model *not* to reformat dates itself, preserving that separation of concerns.

### New Pydantic tools, each solving a genuinely different problem
- **`field_validator`** (`mode="before"`) — runs *before* Pydantic's own type coercion, needed when the raw value isn't naturally the target type yet (e.g., `"$1,264.50"` isn't a `float` until stripped of `$`/`,` first — without `mode="before"`, Pydantic would try to coerce the string directly and fail before your cleanup code ever ran).
- **`model_validator`** (`mode="after"`) — a genuinely different tool from `field_validator`: runs once *all* individual fields have already validated, checking relationships **across multiple fields together** (line items summing to subtotal; subtotal − discount + tax = total) — something no single-field validator can structurally do. Real floating-point lesson: use `abs(a - b) > tolerance`, never `!=`, when comparing computed sums.
- **`Optional[X] = None`** — the correct way to express "this field may legitimately be absent" (e.g., no invoice number printed anywhere), distinct from Day 13's "required means present, not non-empty" lesson.

### Real PDF extraction — genuinely new foundational skill
`pdfplumber` used to pull raw text out of an actual PDF file for the first time this roadmap (`page.extract_text()`), rather than a hardcoded Python string. **Two separate, real failure modes discovered and tested deliberately, not stumbled into:**
- **No detectable table structure** — a hand-typeset invoice (no reportlab `Table`/grid lines, just individually positioned text) makes `extract_tables()` return an empty list entirely; `pdfplumber`'s table detection relies on finding ruling lines or consistent whitespace gutters, which many real small-vendor invoices simply don't have.
- **A rotated diagonal watermark corrupting the text stream itself** — not just visually, but literally: individual watermark letters bled into real content lines (`"ATax (7%): $136.67"` — a stray `A` glued onto `Tax`). **Real, valuable finding: the LLM extraction pipeline correctly parsed `tax=136.67` despite this character-level corruption** — genuine evidence that LLM-based extraction is materially more resilient to noisy input than a fixed-position or regex-anchored parser would be (a regex matching literal `"Tax"` would have missed `"ATax"` entirely).

---

## Day 16 — Project 1: Document-Processing Bot, Classify-Then-Route Architecture

**Goal, deliberately reframed from the roadmap's literal wording:** old RPA needs a separate fixed template per document type. A genuinely AI-native system shouldn't. Built a two-stage pipeline — classify the document type first, then route to the correct extraction schema — rather than one hardcoded schema, directly foreshadowing Week 6–7's agent routing patterns.

### Architecture — three genuinely reusable pieces
- **`document_models.py`** — multiple, structurally distinct Pydantic schemas (one set built for invoices/POs/receipts, a second fresh set built for an HR-document domain: `JobApplication`, `ReferenceLetter`, `OfferAcceptance` — genuinely different shapes, not relabeled copies, to make classification meaningfully necessary rather than trivial).
- **`classifier.py`** — a lightweight, separate LLM call using a tiny schema (just a `DocumentType` enum), reusing the exact `json_object` structured-output pattern from Day 13, applied to a much simpler classification task rather than full extraction.
- **`registry.py`** — a dict mapping each classified type to its `{model, instruction}` pair. Adding a fourth document type later means adding one registry entry, not rewriting the pipeline.

### `generic_extractor.py` — the real engineering challenge, genuine code reuse proven, not just claimed
Genericized Day 13–15's hardcoded `extract_ticket_json_schema`/`extract_invoice` functions into one: `extract_document(text, model_class: Type[T], instruction) -> T`. **New Python tool: `TypeVar`/`Type[T]`** — declares "whatever class is passed in, the same class comes back out," giving real type-safety across a genuinely generic function, rather than the function body needing to know which specific schema it's working with. Same `json_object` + validation + corrective-retry loop underneath, completely unchanged — only the schema and prompt are now parameters instead of hardcoded.

### `process_folder.py` — real production batch-processing pattern
Loops a real folder of mixed PDFs, classifying and extracting each independently, with the entire per-file body wrapped in `try/except`. **The genuinely important production requirement this enforces: one malformed or misclassified document must never crash the whole batch** — a failure is caught, logged with its filename and error, and added to the results list as a `"failed"` entry, while every other file in the folder still completes normally. Directly reuses the failure-isolation instinct from the n8n dead-lettering work earlier in the roadmap, expressed in plain Python.

### Real, complete proof — same infrastructure, two unrelated domains, zero code changes
Ran the identical `generic_extractor.py`/`process_folder.py` against **six different document schemas across two structurally unrelated domains** (invoices/purchase orders/receipts, then job applications/reference letters/offer forms) with no changes to the extraction engine itself — only new schema files and a new registry. **The single hardest, most convincing result:** `ReferenceLetter.recommendation_strength` correctly inferred as `"strong"` from a letter that never once uses that literal word anywhere in its text — synthesized from tone and intensity across a full paragraph ("strongest possible recommendation," "without reservation"), a categorically harder task than any explicit-value extraction from Days 13–15. Currency parsing, dual-date normalization, and enum classification all confirmed working correctly on the same document in the same run.

### Engineering hygiene
Hit a real, instructive import mismatch after manually removing a naming prefix (`hr_`) from several files: confirmed via `python3 -c "import classifier; print(classifier.__file__)"` that Python's actual runtime import and VS Code's Cmd+click "Go to Definition" can resolve differently — the editor's static analysis is not proof of what will actually execute. **Real lesson: when editor navigation and runtime behavior disagree, trust `__file__`, not the IDE.**

---

## Day 17 — *(not started yet — buffer/research, deliberately breaking Project 1 on messy documents)*
