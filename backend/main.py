"""
Context Surgeon API — run: uvicorn main:app --reload --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import AliasChoices, BaseModel, Field, field_validator

from compressor import compress_file, compress_selection
from demo_data import DEMO_BIG_USER_PROMPT, DEMO_USER_PROMPT, demo_repo_big_path, demo_repo_path
from prompt_builder import build_markdown_export, build_ready_prompt
from prompt_cleaner import clean_prompt
from relevance_ranker import rank_files
from repo_scanner import parse_pasted_files, scan_repo
from token_estimator import (
    compute_stats,
    count_tokens,
    hallucination_risk_note,
    list_pricing_models,
    normalize_model_id,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Context Surgeon", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _pick_top_k(n_files: int) -> int:
    if n_files <= 0:
        return 0
    if n_files <= 3:
        return n_files
    return min(5, max(3, n_files))


def _gather_files(repo_path: str, pasted: str) -> tuple[dict[str, str], str]:
    rp = (repo_path or "").strip()
    if rp:
        p = Path(rp).expanduser()
        if p.is_dir():
            scanned = scan_repo(p)
            if scanned:
                return scanned, f"Repository: `{p}`"
            return {}, "empty_repo"
        return {}, "bad_repo"
    pasted = (pasted or "").strip()
    if pasted:
        parsed = parse_pasted_files(pasted)
        if parsed:
            return parsed, "Pasted files"
    return {}, "none"


def _original_bundle_text(user_prompt: str, files: dict[str, str]) -> str:
    head = (user_prompt or "").strip()
    body = "\n\n".join(f"## {path}\n{content}" for path, content in sorted(files.items()))
    return f"{head}\n\n---\n\n{body}" if body else head


def _highlight_md(text: str, keywords: list[str]) -> str:
    out = text
    for k in sorted(set(keywords), key=len, reverse=True):
        if not k:
            continue
        pat = re.compile(re.escape(k), re.I)
        out = pat.sub(lambda m: f"**{m.group(0)}**", out)
    return out


class AnalyzeRequest(BaseModel):
    prompt: str = Field(..., description="Full user prompt (task + any verbose context)")
    repo_path: str = ""
    pasted: str = ""
    pricing_model: str = Field(
        default="gpt-4o-mini",
        validation_alias=AliasChoices("pricing_model", "mock_model"),
        description="Catalog id for tokenizer + published input list price",
    )

    @field_validator("pricing_model", mode="before")
    @classmethod
    def _normalize_pricing_model(cls, v: object) -> str:
        return normalize_model_id(str(v) if v is not None else "")


class RankedFileOut(BaseModel):
    path: str
    score: float
    confidence: float
    reasons: list[str]


class StatsOut(BaseModel):
    original_tokens: int
    compressed_tokens: int
    tokens_saved: int
    reduction_pct: float
    original_chars: int
    compressed_chars: int
    ready_message_tokens: int
    risk_note: str
    tokenizer_note: str


class CostOut(BaseModel):
    model_label: str
    estimated_original_cost_usd: float
    estimated_compressed_cost_usd: float
    cost_saved_usd: float


class AnalyzeResponse(BaseModel):
    ok: bool
    error: str | None = None
    cleaned_prompt: str = ""
    audit_log: list[str] = []
    source_label: str = ""
    files_scanned: int = 0
    files_selected: int = 0
    ranked_files: list[RankedFileOut] = []
    compressed_context: str = ""
    compressed_context_md: str = ""
    ready_prompt: str = ""
    stats: StatsOut | None = None
    cost: CostOut | None = None
    raw_bundle_preview: str = ""
    export_markdown: str = ""
    stats_before_label: str = ""
    stats_after_label: str = ""


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/demo")
def get_demo(variant: str = "small"):
    if variant == "big":
        return {
            "prompt": DEMO_BIG_USER_PROMPT,
            "repo_path": str(demo_repo_big_path()),
            "pasted": "",
            "variant": "big",
            "hint": "Demo 2: 16 noisy files — expect a large token cut; UI preview is clipped for speed.",
        }
    return {
        "prompt": DEMO_USER_PROMPT,
        "repo_path": str(demo_repo_path()),
        "pasted": "",
        "variant": "small",
        "hint": "Demo 1: small repo — quick smoke test.",
    }


@app.get("/api/pricing-models")
def pricing_models():
    return {
        "models": list_pricing_models(),
        "pricing_note": "USD per 1M input tokens from public list prices; confirm on the provider site.",
        "token_note": "OpenAI picks use tiktoken; Claude uses a chars÷4 estimate unless you extend the backend.",
    }


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(body: AnalyzeRequest) -> AnalyzeResponse:
    prompt = (body.prompt or "").strip()
    if not prompt:
        return AnalyzeResponse(ok=False, error="empty_prompt")

    try:
        return _run_analyze(body, prompt)
    except Exception:
        logger.exception("analyze failed")
        return AnalyzeResponse(ok=False, error="analysis_failed")


def _run_analyze(body: AnalyzeRequest, prompt: str) -> AnalyzeResponse:
    files, src_label = _gather_files(body.repo_path, body.pasted)
    if src_label == "bad_repo":
        return AnalyzeResponse(ok=False, error="bad_repo")
    if src_label == "empty_repo":
        return AnalyzeResponse(ok=False, error="empty_repo")
    if src_label == "none":
        return AnalyzeResponse(ok=False, error="no_source")

    clean = clean_prompt(prompt)
    task_for_rank = clean.cleaned_prompt or prompt
    ranked = rank_files(files, task_for_rank, top_n=12)
    k = _pick_top_k(len(ranked))
    top = ranked[:k]
    selected_paths = [r.path for r in top]
    compressed = compress_selection(files, selected_paths, task_for_rank)
    ready = build_ready_prompt(task_for_rank, compressed)

    raw_bundle = _original_bundle_text(prompt, files)
    # Compare worst-case paste (whole repo) vs what actually matters: task + compressed excerpts.
    # The full Cursor paste (`ready`) adds safety instructions — reported separately.
    payload_for_stats = f"{task_for_rank}\n\n{compressed}"
    stats = compute_stats(raw_bundle, payload_for_stats, model_id=body.pricing_model)
    tokens_saved = max(0, stats.original_tokens - stats.compressed_tokens)
    reduction_pct = max(0.0, stats.reduction_pct)
    risk = hallucination_risk_note(reduction_pct)
    ready_message_tokens, _ready_note = count_tokens(ready, body.pricing_model)

    all_kw: list[str] = []
    for p in selected_paths:
        if p in files:
            all_kw.extend(compress_file(p, files[p], task_for_rank).highlighted_keywords)
    uniq_kw = list(dict.fromkeys(all_kw))[:15]
    compressed_md = _highlight_md(compressed, uniq_kw)

    export_md = build_markdown_export(
        task_for_rank,
        compressed,
        ready,
        [
            f"Original ~tokens (prompt + all files): {stats.original_tokens}",
            f"Core payload ~tokens (task + compressed context): {stats.compressed_tokens}",
            f"Reduction vs full-repo paste: {reduction_pct:.1f}%",
            f"Full Cursor-ready message ~tokens: {ready_message_tokens}",
            f"Files: {len(files)} scanned, {len(selected_paths)} selected",
            f"Tokens saved (est.): {tokens_saved}",
            f"Token counting: {stats.tokenizer_note}",
        ],
    )

    preview = raw_bundle[:12000] + ("\n\n… (truncated)" if len(raw_bundle) > 12000 else "")

    return AnalyzeResponse(
        ok=True,
        cleaned_prompt=clean.cleaned_prompt,
        audit_log=clean.removed_or_reduced[:40],
        source_label=src_label,
        files_scanned=len(files),
        files_selected=len(selected_paths),
        ranked_files=[
            RankedFileOut(
                path=r.path,
                score=round(r.score, 2),
                confidence=r.confidence,
                reasons=r.reasons[:6],
            )
            for r in top
        ],
        compressed_context=compressed,
        compressed_context_md=compressed_md,
        ready_prompt=ready,
        stats=StatsOut(
            original_tokens=stats.original_tokens,
            compressed_tokens=stats.compressed_tokens,
            tokens_saved=tokens_saved,
            reduction_pct=reduction_pct,
            original_chars=stats.original_chars,
            compressed_chars=stats.compressed_chars,
            ready_message_tokens=ready_message_tokens,
            risk_note=risk,
            tokenizer_note=stats.tokenizer_note,
        ),
        cost=CostOut(
            model_label=stats.model_label,
            estimated_original_cost_usd=stats.estimated_original_cost_usd,
            estimated_compressed_cost_usd=stats.estimated_compressed_cost_usd,
            cost_saved_usd=stats.cost_saved_usd,
        ),
        raw_bundle_preview=preview,
        export_markdown=export_md,
        stats_before_label="Worst case: your prompt + every scanned file pasted into the model",
        stats_after_label="Core signal: cleaned task + compressed excerpts from only the top-ranked files",
    )


# Optional: serve built UI from the same port (after `npm run build` in frontend/)
_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _FRONTEND_DIST.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=str(_FRONTEND_DIST), html=True),
        name="spa",
    )
