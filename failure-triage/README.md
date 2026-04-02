# Failure Triage Bot (MVP)

Turn pasted CI or test logs into structured triage: summary, hypothesis, where to look, fix plan, repro commands, confidence, assumptions, and a GitHub-ready issue markdown block.

## Requirements

- Python 3.10+

## Setup

```bash
cd failure-triage
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run
- One-command dev run (recommended):
```bash
cd failure-triage
make dev
```

By default this starts on `http://127.0.0.1:8001/`.

- **Web UI:** http://127.0.0.1:8001/
- **OpenAPI docs:** http://127.0.0.1:8001/docs
- **Health:** `GET /health`

## API (summary)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/triage` | Body: `log`, optional `framework`, `language`, `context` → triage JSON |
| `GET` | `/api/fixtures` | List demo fixture ids and titles |
| `GET` | `/api/fixtures/{id}` | Full fixture `log` + metadata |
| `GET` | `/api/demo/{id}` | Run triage on embedded demo log (same response as `/api/triage`) |

No API keys are required; triage uses on-server heuristics and rule-based templates.

## Project layout

```
failure-triage/
  app/
    main.py           # FastAPI app, routes, static mount
    schemas.py        # Pydantic request/response models
    fixtures.py       # Embedded sample logs
    services/
      preprocess.py   # ANSI strip, newline normalize, length bound
      extract.py      # Traceback / test name / error heuristics
      triage.py       # Rule-based triage + orchestration
      issue.py        # Issue markdown export
  static/
    index.html
    style.css
    app.js
  requirements.txt
  README.md
```
