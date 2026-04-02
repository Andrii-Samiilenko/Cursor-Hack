"""Shared helpers for Context Surgeon."""

from __future__ import annotations

import re
from typing import Iterable


STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "as",
        "is",
        "was",
        "are",
        "be",
        "by",
        "with",
        "from",
        "this",
        "that",
        "it",
        "if",
        "then",
        "so",
        "we",
        "you",
        "i",
        "me",
        "my",
        "please",
        "just",
        "also",
        "very",
        "really",
        "can",
        "could",
        "would",
        "should",
        "need",
        "want",
        "like",
        "make",
        "sure",
        "all",
        "any",
        "some",
        "into",
        "about",
        "when",
        "how",
        "what",
        "which",
        "who",
        "there",
        "here",
        "do",
        "does",
        "did",
        "have",
        "has",
        "had",
        "not",
        "no",
        "yes",
        "ok",
        "thanks",
    }
)

WORD_RE = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")


def extract_keywords(text: str, max_keywords: int = 24) -> list[str]:
    """Lowercase keywords from text, excluding common stopwords."""
    if not text:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for m in WORD_RE.finditer(text.lower()):
        w = m.group(0)
        if len(w) < 2 or w in STOPWORDS:
            continue
        if w not in seen:
            seen.add(w)
            out.append(w)
            if len(out) >= max_keywords:
                break
    return out


def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def truncate_middle(s: str, max_len: int = 120) -> str:
    if len(s) <= max_len:
        return s
    half = (max_len - 3) // 2
    return s[:half] + "..." + s[-half:]


def unique_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out
