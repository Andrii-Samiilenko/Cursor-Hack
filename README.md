# Context Surgeon



Developer tool: **one prompt in** → cleaned text + **minimal relevant repo context** → **ready-to-paste** block for Cursor (deterministic heuristics, **no LLM** in this app).



## Layout



| Folder | Role |

|--------|------|

| **`backend/`** | Python + **FastAPI** — prompt cleaning, repo scan, ranking, compression, token estimates |

| **`frontend/`** | **React + Vite + TypeScript + Tailwind** — UI |



## Easiest: one terminal (dev)



From the **repo root** (`Cursor-Hack/`):



**First time only**



```powershell

python setup_dev.py

```



**Every time**



```powershell

python run_dev.py

```



Or double-click **`run_dev.bat`** (Windows).



Then open **http://127.0.0.1:5173** — Vite proxies `/api` to the API on port 8000. **Ctrl+C** stops API + UI together.



Requirements: **Python 3** and **Node.js (npm)** on `PATH`.



---



## One URL, one process (demo / no hot reload)



After a frontend build, the API can serve the UI from **port 8000** only:



```powershell

cd frontend

npm run build

cd ..\backend

.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000

```



Open **http://127.0.0.1:8000** — same origin as `/api` (no second port).



---



## Manual two-process setup (optional)



**API**



```powershell

cd backend

python -m venv .venv

.\.venv\Scripts\python.exe -m pip install -r requirements.txt

.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

```



On Windows, if `uvicorn` is not on `PATH`, always use **`python -m uvicorn`** (or the `.venv\Scripts\python.exe` path above).



**UI**



```powershell

cd frontend

npm install

npm run dev

```



Open **http://localhost:5173**



---



## Using the app



- **Your prompt** — task + notes in one field.

- **Repository path** — absolute path on the **same PC** as the API, or paste files with `-----FILE: path-----` lines.



**Demo:** **Demo 1 · small repo** or **Demo 2 · large repo** → **Analyze context**.



## Bundled sample repos



- `backend/demo_repo/` — compact smoke test.

- `backend/demo_repo_big/` — stress demo for judges (strong token / $ delta). Regenerate: `python backend/scripts/generate_big_demo.py`

In the UI use **Demo 2 · large repo** for the big numbers (long outputs are preview-truncated in the browser; Copy/Download are full).



## 3-minute pitch (hackathon)

See **`docs/HACKATHON_PRESENTATION.md`** — problem, Review + QA main road, side quests, demo script.

**Short demo (EN):** **`docs/DEMO_2MIN.md`** — how the code works in plain language + ~2 min spoken script (problem, solution, benefit).

## Cursor integration



- **Rule (optional):** `.cursor/rules/context-surgeon.mdc` — reminds you to run Context Surgeon before huge Composer/Agent tasks.

- **Output:** the generated block tells the model to use **only** listed paths/snippets (reduces invented files and drift).



The UI shows **mock** $/day and **illustrative** Wh/day sliders — for demo storytelling only, not real billing or carbon data.

