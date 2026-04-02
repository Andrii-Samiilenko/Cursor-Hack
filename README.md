# Context Surgeon

Developer tool: **one prompt in** → cleaned text + **minimal relevant repo context** → **ready-to-paste** block for Cursor (deterministic heuristics, **no LLM** in this app).

## Layout

| Folder | Role |
|--------|------|
| **`backend/`** | Python + **FastAPI** — prompt cleaning, repo scan, ranking, compression, token estimates |
| **`frontend/`** | **React + Vite + TypeScript + Tailwind** — UI |

## Run locally (two terminals)

**1) API**

```powershell
cd c:\Users\HP\Desktop\Cursor-Hack\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

On Windows, prefer **`python -m uvicorn`** instead of `uvicorn` — the `uvicorn.exe` shim is often not on `PATH`. Using **`python -m pip install`** ensures packages go into the active `.venv`, not the Store Python user folder.

If you see **`No module named uvicorn`** while `(.venv)` is active, your `pip` may have targeted another Python. Install with the venv interpreter explicitly:

`.\.venv\Scripts\python.exe -m pip install -r requirements.txt` then `.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000`

**2) UI** (proxies `/api` → port 8000)

```powershell
cd c:\Users\HP\Desktop\Cursor-Hack\frontend
npm install
npm run dev
```

Open **http://localhost:5173**

- **Your prompt** — single field (task + messy notes together).
- **Repository path** — absolute path on the **same PC** as the API, or paste files with `-----FILE: path-----` lines.

**Demo:** click **Load demo** then **Analyze context**.

## Production build (optional)

```powershell
cd frontend
npm run build
```

Serve `frontend/dist` with any static host; you must still run the API and configure **CORS** / reverse proxy so the browser can reach `/api` (or set `VITE_API_URL` if you add that to the client later).

## Bundled sample repo

`backend/demo_repo/` — small auth/login example for demos.
