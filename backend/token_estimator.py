"""Token counts via tiktoken (OpenAI) and cost from published API list prices.

Input-token USD uses each vendor's public price sheet (input only). Confirm current
rates on the provider site before reconciling invoices — we do not call billing APIs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

try:
    import tiktoken
except ImportError:  # pragma: no cover
    tiktoken = None


# Legacy UI/API values → current catalog ids
LEGACY_MODEL_IDS: dict[str, str] = {
    "gpt-4o-mini (mock)": "gpt-4o-mini",
    "gpt-4o (mock)": "gpt-4o",
    "claude-3.5 (mock)": "claude-sonnet-3.5",
}


# Published list prices: USD per 1M input tokens. Cite provider pricing pages in README.
# Last reviewed: 2026-04 (see README for links).
MODEL_REGISTRY: dict[str, dict[str, Any]] = {
    "gpt-4o-mini": {
        "label": "GPT-4o mini",
        "usd_per_million_input_tokens": 0.15,
        "tiktoken_model": "gpt-4o-mini",
    },
    "gpt-4o": {
        "label": "GPT-4o",
        "usd_per_million_input_tokens": 2.50,
        "tiktoken_model": "gpt-4o",
    },
    "claude-sonnet-3.5": {
        "label": "Claude 3.5 Sonnet",
        "usd_per_million_input_tokens": 3.00,
        "tiktoken_model": None,
    },
}


def normalize_model_id(requested: str | None) -> str:
    if not requested or not str(requested).strip():
        return "gpt-4o-mini"
    s = str(requested).strip()
    s = LEGACY_MODEL_IDS.get(s, s)
    if s in MODEL_REGISTRY:
        return s
    return "gpt-4o-mini"


def list_pricing_models() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for mid, spec in MODEL_REGISTRY.items():
        tok = spec["tiktoken_model"]
        if tok:
            note = f"tiktoken ({tok})"
        else:
            note = "~chars÷4 (approx.; use Anthropic API for exact Claude counts)"
        out.append(
            {
                "id": mid,
                "label": spec["label"],
                "usd_per_million_input_tokens": spec["usd_per_million_input_tokens"],
                "tokenizer_note": note,
            }
        )
    return out


def _chars_div4_tokens(text: str) -> int:
    if not text:
        return 0
    return int(math.ceil(len(text) / 4.0))


def count_tokens(text: str, model_id: str) -> tuple[int, str]:
    """
    Returns (token_count, short description of method).
    OpenAI-family models use tiktoken when installed; otherwise chars÷4 fallback.
    """
    if not text:
        return 0, "empty"
    mid = normalize_model_id(model_id)
    spec = MODEL_REGISTRY.get(mid, MODEL_REGISTRY["gpt-4o-mini"])
    tmodel = spec.get("tiktoken_model")
    if tmodel and tiktoken is not None:
        try:
            enc = tiktoken.encoding_for_model(tmodel)
            n = len(enc.encode(text))
            return n, f"tiktoken · {enc.name}"
        except Exception:
            pass
    n = _chars_div4_tokens(text)
    if tmodel:
        return n, "chars÷4 (tiktoken unavailable — pip install tiktoken)"
    return n, "~chars÷4 (Claude estimate)"


@dataclass
class TokenStats:
    original_chars: int
    compressed_chars: int
    original_tokens: int
    compressed_tokens: int
    reduction_pct: float
    model_id: str
    model_label: str
    tokenizer_note: str
    estimated_original_cost_usd: float
    estimated_compressed_cost_usd: float
    cost_saved_usd: float


def compute_stats(
    original_text: str,
    compressed_text: str,
    model_id: str = "gpt-4o-mini",
) -> TokenStats:
    mid = normalize_model_id(model_id)
    spec = MODEL_REGISTRY.get(mid, MODEL_REGISTRY["gpt-4o-mini"])
    rate = float(spec["usd_per_million_input_tokens"])
    label = f"{spec['label']} · ${rate}/M input tok (list)"

    oc = len(original_text)
    cc = len(compressed_text)
    ot, note_o = count_tokens(original_text, mid)
    ct, note_c = count_tokens(compressed_text, mid)
    note_combined = note_o if note_o == note_c else f"before: {note_o}; after: {note_c}"

    if ot == 0:
        reduction = 0.0
    else:
        reduction = round(100.0 * (1.0 - ct / max(ot, 1)), 1)

    orig_cost = (ot / 1_000_000.0) * rate
    comp_cost = (ct / 1_000_000.0) * rate
    return TokenStats(
        original_chars=oc,
        compressed_chars=cc,
        original_tokens=ot,
        compressed_tokens=ct,
        reduction_pct=reduction,
        model_id=mid,
        model_label=label,
        tokenizer_note=note_combined,
        estimated_original_cost_usd=round(orig_cost, 6),
        estimated_compressed_cost_usd=round(comp_cost, 6),
        cost_saved_usd=round(orig_cost - comp_cost, 6),
    )


def hallucination_risk_note(reduction_pct: float) -> str:
    """Informal label based on how much context was removed."""
    if reduction_pct < 20:
        return "Low removal — full context retained."
    if reduction_pct < 50:
        return "Moderate compression — review that key paths stayed included."
    return "Heavy compression — double-check nothing critical was dropped."
