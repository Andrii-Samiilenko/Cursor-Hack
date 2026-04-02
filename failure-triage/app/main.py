"""
Failure Triage Bot — FastAPI entrypoint.

Serves the REST API under /api and static assets from / (index.html, css, js).
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.fixtures import FIXTURES, get_fixture_log, list_fixture_meta
from app.schemas import TriageRequest, TriageResponse
from app.services.preprocess import preprocess_log
from app.services.triage import run_triage

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="Failure Triage Bot",
    description="Turn CI/test logs into structured triage and issue-ready exports.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/triage", response_model=TriageResponse)
def triage(req: TriageRequest) -> TriageResponse:
    cleaned, truncated_note = preprocess_log(req.log)
    return run_triage(cleaned, truncated_note, req)


@app.get("/api/fixtures")
def fixtures_list() -> list[dict[str, str]]:
    return list_fixture_meta()


@app.get("/api/fixtures/{fixture_id}")
def fixture_detail(fixture_id: str) -> dict[str, str]:
    if fixture_id not in FIXTURES:
        raise HTTPException(status_code=404, detail="Unknown fixture id")
    return {
        "id": fixture_id,
        "title": FIXTURES[fixture_id]["title"],
        "log": get_fixture_log(fixture_id),
    }


@app.get("/api/demo/{fixture_id}", response_model=TriageResponse)
def triage_demo(fixture_id: str) -> TriageResponse:
    try:
        log = get_fixture_log(fixture_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Unknown fixture id") from e
    cleaned, truncated_note = preprocess_log(log)
    req = TriageRequest(
        log=cleaned,
        framework="auto",
        language="auto",
        context=None,
    )
    return run_triage(cleaned, truncated_note, req)


if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
