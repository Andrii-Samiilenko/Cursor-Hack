"""Scan a repository for relevant source files; parse pasted multi-file blobs."""

from __future__ import annotations

import os
import re
from pathlib import Path

ALLOWED_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".md"}

SKIP_DIR_NAMES = {
    "node_modules",
    ".git",
    "dist",
    "build",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".idea",
    ".vscode",
}

MAX_FILE_BYTES = 512 * 1024  # 512 KB

PASTE_FILE_MARKER = re.compile(
    r"^-----FILE:\s*(.+?)\s*-----$", re.MULTILINE
)


def _is_probably_text(sample: bytes) -> bool:
    if not sample:
        return True
    if b"\x00" in sample[:8192]:
        return False
    return True


def scan_repo(root: str | Path) -> dict[str, str]:
    """
    Recursively read allowed files under root.
    Returns relative posix paths -> utf-8 content (skipped files omitted).
    """
    root = Path(root).resolve()
    if not root.is_dir():
        return {}

    out: dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        for name in filenames:
            p = Path(dirpath) / name
            try:
                rel = p.relative_to(root).as_posix()
            except ValueError:
                continue
            if p.suffix.lower() not in ALLOWED_SUFFIXES:
                continue
            try:
                size = p.stat().st_size
            except OSError:
                continue
            if size > MAX_FILE_BYTES:
                continue
            try:
                raw = p.read_bytes()
            except OSError:
                continue
            if not _is_probably_text(raw[: min(len(raw), 8192)]):
                continue
            try:
                text = raw.decode("utf-8", errors="replace")
            except Exception:
                continue
            out[rel] = text
    return out


def parse_pasted_files(blob: str) -> dict[str, str]:
    """
    Parse pasted content with lines like:
    -----FILE: src/foo.py-----
    <content>
    If no markers, returns {"pasted_context.txt": blob} when non-empty.
    """
    blob = blob.strip()
    if not blob:
        return {}

    matches = list(PASTE_FILE_MARKER.finditer(blob))
    if not matches:
        return {"pasted_context.txt": blob}

    out: dict[str, str] = {}
    for i, m in enumerate(matches):
        path = m.group(1).strip().replace("\\", "/")
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(blob)
        content = blob[start:end].strip("\n")
        if path:
            out[path] = content
    return out
