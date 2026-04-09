# Context Surgeon

**One messy prompt + a repo** → cleaned task, ranked files, compressed snippets, and a **single block** you paste into Cursor Chat or Composer.

The pipeline is **fully local and deterministic**: heuristics, AST-style parsing where applicable, and **no extra LLM call** inside the tool. You stay in control of what actually reaches the model.

---

## Why it exists

Most pain with coding assistants is not “which model?” but **what context you attach**. Context Surgeon is a **quality gate on context**: it trims noise, picks likely-relevant paths, compresses structure to high-signal excerpts, and wraps everything with rules that reduce invented paths and drift.

---

## What it does (at a glance)

| Stage | What happens |
|--------|----------------|
| **Prompt** | Rule-based cleanup (dedupe, filler) — not an LLM rewrite |
| **Scan** | Repo path or pasted `-----FILE: …-----` bundles |
| **Rank** | Heuristic relevance vs the cleaned task |
| **Compress** | Signatures, key lines, dependencies — not full file dumps |
| **Export** | Cursor-ready message + optional `.md` download |

**Token & cost:** OpenAI-family models use **[tiktoken](https://github.com/openai/tiktoken)** for real tokenizer counts. USD lines use **published list prices for input tokens** (see `backend/token_estimator.py` and links below); they are **estimates** — always confirm on your provider’s pricing page before reconciling invoices. Claude in the catalog uses a **~chars÷4** token estimate unless you extend the backend with Anthropic’s counter.

---

## Repo layout

| Path | Role |
|------|------|
| **`backend/`** | **FastAPI** — analyze API, prompt cleaning, scan, rank, compress |
| **`frontend/`** | **React + Vite + TypeScript + Tailwind** — UI |

---

## Quick start (recommended)

From the **repository root** (`Cursor-Hack/`).

### First time

```powershell
python setup_dev.py
```

This creates `backend/.venv`, installs **Python** deps (including `tiktoken`), and runs `npm install` in `frontend/`.

### Every session

```powershell
python run_dev.py
```

Or double-click **`run_dev.bat`** (Windows).

Then open **http://127.0.0.1:5173** — Vite proxies `/api` to the backend on **port 8000**. **Ctrl+C** stops both processes.

**Requirements:** Python 3.11+ recommended, **Node.js (npm)** on `PATH`.

---

## Single port (production-style)

After a frontend build, the API can serve the UI from **8000** only:

```powershell
cd frontend
npm run build
cd ..\backend
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000** — same origin as `/api`.

---

## Manual two-process setup (optional)

**API**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

On Windows, prefer **`python -m uvicorn`** so the venv is used reliably.

**UI**

```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**.

---

## Using the app

1. Write **your prompt** (task + messy notes in one box).
2. Either set **repository path** (absolute, on the machine where the API runs) **or** paste files with `-----FILE: relative/path-----` markers.
3. Choose **model** — drives tokenizer (OpenAI → tiktoken) and **input list price** for cost lines.
4. **Analyze context** → review steps 1–5 → **Copy for Cursor** or **Download .md**.

**Demos:** **Demo 1 · small repo** / **Demo 2 · large repo** load bundled sample trees under `backend/demo_repo/` and `backend/demo_repo_big/`. Large outputs are preview-truncated in the browser; Copy/Download remain full.

Regenerate the big tree: `python backend/scripts/generate_big_demo.py`

---

## Pricing references (update `token_estimator.py` when rates change)

- [OpenAI API pricing](https://openai.com/api/pricing/)
- [Anthropic API pricing](https://www.anthropic.com/pricing)

---

## Cursor integration

- **Rule (optional):** `.cursor/rules/context-surgeon.mdc` — nudge to run Context Surgeon before huge Composer/Agent dumps.
- **Output:** the generated block tells the model to stick to listed paths/snippets.

---

## Docs

- **`docs/HACKATHON_PRESENTATION.md`** — pitch structure and demo beats.
- **`docs/DEMO_2MIN.md`** — short spoken script + how the pieces fit.

---

## API notes

- `POST /api/analyze` accepts `pricing_model` (alias: `mock_model` for older clients).
- `GET /api/pricing-models` — catalog ids, labels, tokenizer hints, list prices.
