"""Heuristic prompt audit: shorten and dedupe while preserving intent."""

from __future__ import annotations

import re
from dataclasses import dataclass

from utils import normalize_whitespace, split_sentences, unique_preserve_order


FILLER_PHRASES = [
    (re.compile(r"\bplease note that\b", re.I), ""),
    (re.compile(r"\bit is important to\b", re.I), ""),
    (re.compile(r"\bi would like you to\b", re.I), " "),
    (re.compile(r"\bkindly\b", re.I), ""),
    (re.compile(r"\bas soon as possible\b", re.I), ""),
    (re.compile(r"\bat your earliest convenience\b", re.I), ""),
    (re.compile(r"\bmake sure to\b", re.I), ""),
    (re.compile(r"\btry to\b", re.I), ""),
    (re.compile(r"\bessentially\b", re.I), ""),
    (re.compile(r"\bbasically\b", re.I), ""),
    (re.compile(r"\bactually\b", re.I), ""),
    (re.compile(r"\bjust wanted to\b", re.I), ""),
    (re.compile(r"\bi need you to\b", re.I), ""),
]

REPEAT_INSTRUCTION = re.compile(
    r"\b(remember|note|don't forget|do not forget)\b[^.!?]*[.!?]",
    re.I,
)


@dataclass
class PromptCleanResult:
    cleaned_prompt: str
    removed_or_reduced: list[str]


def _dedupe_sentences(sentences: list[str], log: list[str]) -> list[str]:
    seen_norm: set[str] = set()
    kept: list[str] = []
    for s in sentences:
        n = normalize_whitespace(s.lower())
        if len(n) < 8:
            if n and n not in seen_norm:
                seen_norm.add(n)
                kept.append(s)
            continue
        if n in seen_norm:
            log.append(f"Removed duplicate sentence: {s[:80]}{'…' if len(s) > 80 else ''}")
            continue
        seen_norm.add(n)
        kept.append(s)
    return kept


def _collapse_repeated_instructions(text: str, log: list[str]) -> str:
    """Remove redundant 'remember / note' style clauses (first kept)."""
    found = list(REPEAT_INSTRUCTION.finditer(text))
    if len(found) <= 1:
        return text
    # Remove all but first
    for m in reversed(found[1:]):
        log.append(f"Reduced repeated instruction: {m.group(0)[:70]}…")
        text = text[: m.start()] + text[m.end() :]
    return normalize_whitespace(text)


def clean_prompt(raw_prompt: str) -> PromptCleanResult:
    """Single user prompt: task + details + optional verbose text in one field."""
    log: list[str] = []
    raw = normalize_whitespace(raw_prompt or "")

    if not raw:
        return PromptCleanResult(cleaned_prompt="", removed_or_reduced=[])

    # Filler removal
    working = raw
    for pat, repl in FILLER_PHRASES:
        new_t, n = pat.subn(repl, working)
        if n:
            log.append(f"Trimmed filler phrase ({n}×): {pat.pattern[:50]}…")
        working = new_t
    working = normalize_whitespace(working)

    working = _collapse_repeated_instructions(working, log)

    sentences = split_sentences(working)
    if len(sentences) > 1:
        before = len(sentences)
        sentences = _dedupe_sentences(sentences, log)
        if len(sentences) < before:
            pass
    cleaned = normalize_whitespace(" ".join(sentences))

    # Collapse triple+ newlines to double (already single-space from sentences)
    cleaned = re.sub(r"\s{3,}", " ", cleaned)

    if len(cleaned) < len(raw) * 0.95:
        log.append("Shortened verbose phrasing / whitespace")

    # If still very long, keep first 2 sentences + last sentence heuristic
    s2 = split_sentences(cleaned)
    if len(s2) > 6:
        kept = s2[:3] + s2[-2:]
        dropped = s2[3:-2]
        for d in dropped:
            log.append(f"Omitted middle sentence (length cap): {d[:60]}…")
        cleaned = normalize_whitespace(" ".join(kept))

    log = unique_preserve_order(log)
    return PromptCleanResult(cleaned_prompt=cleaned, removed_or_reduced=log)
