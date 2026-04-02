"""Lightweight token and cost estimates (clearly labeled as approximate)."""

from __future__ import annotations

import math
from dataclasses import dataclass


def estimate_tokens(char_count: int) -> int:
    """Rough heuristic: ~4 characters per token for English/code mix."""
    if char_count <= 0:
        return 0
    return int(math.ceil(char_count / 4.0))


# Mock USD per 1M input tokens (illustrative only)
MOCK_PRICING = {
    "gpt-4o-mini (mock)": 0.15,
    "gpt-4o (mock)": 2.50,
    "claude-3.5 (mock)": 3.00,
}


@dataclass
class TokenStats:
    original_chars: int
    compressed_chars: int
    original_tokens: int
    compressed_tokens: int
    reduction_pct: float
    model_label: str
    estimated_original_cost_usd: float
    estimated_compressed_cost_usd: float
    cost_saved_usd: float


def compute_stats(
    original_text: str,
    compressed_text: str,
    model_key: str = "gpt-4o-mini (mock)",
) -> TokenStats:
    oc = len(original_text)
    cc = len(compressed_text)
    ot = estimate_tokens(oc)
    ct = estimate_tokens(cc)
    if ot == 0:
        reduction = 0.0
    else:
        reduction = round(100.0 * (1.0 - ct / max(ot, 1)), 1)
    rate = MOCK_PRICING.get(model_key, 0.15)
    orig_cost = (ot / 1_000_000.0) * rate
    comp_cost = (ct / 1_000_000.0) * rate
    return TokenStats(
        original_chars=oc,
        compressed_chars=cc,
        original_tokens=ot,
        compressed_tokens=ct,
        reduction_pct=reduction,
        model_label=model_key,
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
