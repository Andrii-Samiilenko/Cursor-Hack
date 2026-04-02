"""Normalize and bound raw CI / terminal output."""

import re

_MAX_CHARS = 200_000

# ANSI escape sequences (colors, cursor) — strip for consistent parsing.
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\]8;;.*?\x1b\\")


def strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def preprocess_log(raw: str) -> tuple[str, str | None]:
    """
    Return cleaned text and an optional note if input was truncated.

    Caller should enforce max length before calling; this function also
    defensively truncates if needed.
    """
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = strip_ansi(text)
    if len(text) > _MAX_CHARS:
        return text[:_MAX_CHARS], (
            f"Log was truncated to {_MAX_CHARS} characters for processing; "
            "earlier lines may be missing."
        )
    return text, None
