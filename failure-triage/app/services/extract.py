"""Heuristic extraction of stack traces, test names, and error lines from logs."""

import re
from collections import OrderedDict

from app.schemas import ExtractedSignals

# Python traceback: File "path", line 42, in foo
_PY_FILE_LINE = re.compile(r'File "([^"]+)", line (\d+)', re.MULTILINE)

# pytest: FAILED path/to/test.py::test_name - ...
_PYTEST_FAILED = re.compile(
    r"^FAILED\s+(\S+::\S+|\S+\.py::\S+)\s+", re.MULTILINE
)
_PYTEST_FAILED_ALT = re.compile(
    r"^FAILED\s+([^\s]+\.py)\s*-\s", re.MULTILINE
)
# tests/foo.py::test_bar FAILED   [ 12%]
_PYTEST_NODE_LINE = re.compile(
    r"^(\S+\.py::\S+)\s+FAILED\b", re.MULTILINE
)

# Jest / Vitest: ● Suite › test name
_JEST_BULLET = re.compile(r"^\s*●\s+(.+)$", re.MULTILINE)

# file.js:10:5 style (common in Node / TS stacks)
_JS_FILE_COLON = re.compile(
    r"([^\s\"'<>|]+\.(?:js|ts|tsx|jsx|mjs|cjs)):(\d+):(\d+)"
)

# at Object.<anonymous> (/path/file.js:10:5)
_JS_STACK = re.compile(
    r"\(([^()]+\.(?:js|ts|tsx|jsx|mjs|cjs)):(\d+):(\d+)\)|"
    r"\bat\s+(?:async\s+)?(?:\S+\s+)?\(?([^()]+\.(?:js|ts|tsx|jsx|mjs|cjs)):(\d+):(\d+)\)?"
)

_MODULE_NOT_FOUND = re.compile(
    r"ModuleNotFoundError:\s*No module named\s+['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)
_IMPORT_ERROR = re.compile(
    r"ImportError:\s*(.+)", re.IGNORECASE | re.DOTALL
)


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen: OrderedDict[str, None] = OrderedDict()
    for x in items:
        x = x.strip()
        if x and x not in seen:
            seen[x] = None
    return list(seen.keys())


def _guess_framework(text: str, explicit: str) -> str | None:
    if explicit and explicit != "auto":
        return explicit
    lower = text.lower()
    if "pytest" in lower or "=== " in text and "failed" in lower:
        return "pytest"
    if "jest" in lower or "● " in text and ("expect(" in lower or "tests/" in lower):
        return "jest"
    if "vitest" in lower or "⎯⎯⎯⎯" in text:
        return "vitest"
    if "npm err" in lower or "yarn error" in lower:
        return "npm"
    return None


def _extract_error_type(text: str) -> str | None:
    # Prefer last clear Python / JS style error in tail
    tail = text[-8000:] if len(text) > 8000 else text
    lines = tail.split("\n")
    for line in reversed(lines[-40:]):
        line = line.strip()
        m = _MODULE_NOT_FOUND.search(line)
        if m:
            return f"ModuleNotFoundError (missing: {m.group(1)})"
        m = _IMPORT_ERROR.search(line)
        if m:
            return "ImportError"
        if re.match(r"^\w+Error:\s*", line):
            return line.split(":", 1)[0].strip()
        if re.match(r"^\w+Exception:\s*", line):
            return line.split(":", 1)[0].strip()
    return None


def _error_snippet_lines(text: str, max_lines: int = 12) -> list[str]:
    """Collect a few high-signal error lines from the tail."""
    lines = text.split("\n")
    tail = lines[-60:] if len(lines) > 60 else lines
    out: list[str] = []
    for line in tail:
        s = line.rstrip()
        if not s:
            continue
        if any(
            x in s
            for x in (
                "Error",
                "Exception",
                "FAILED",
                "AssertionError",
                "Traceback",
                "expected",
                "Received",
            )
        ):
            out.append(s[:500])
        if len(out) >= max_lines:
            break
    return out if out else ([lines[-1].rstrip()[:500]] if lines else [])


def extract_signals(
    text: str,
    framework: str,
    language: str,
) -> ExtractedSignals:
    file_paths: list[str] = []

    for m in _PY_FILE_LINE.finditer(text):
        file_paths.append(m.group(1))

    for m in _JS_STACK.finditer(text):
        for g in m.groups():
            if g and (g.endswith((".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs"))):
                file_paths.append(g)
                break

    for m in _JS_FILE_COLON.finditer(text):
        file_paths.append(m.group(1))

    test_names: list[str] = []
    for m in _PYTEST_FAILED.finditer(text):
        test_names.append(m.group(1).strip())
    for m in _PYTEST_FAILED_ALT.finditer(text):
        if m.group(1) not in test_names:
            test_names.append(m.group(1).strip())
    for m in _PYTEST_NODE_LINE.finditer(text):
        if m.group(1) not in test_names:
            test_names.append(m.group(1).strip())

    for m in _JEST_BULLET.finditer(text):
        test_names.append(m.group(1).strip())

    error_lines = _error_snippet_lines(text)
    fw = _guess_framework(text, framework)
    err_type = _extract_error_type(text)

    # Language hint
    if language == "python" or fw in ("pytest",):
        pass
    elif language == "javascript" or fw in ("jest", "vitest", "npm"):
        pass

    return ExtractedSignals(
        error_lines=error_lines,
        test_names=_dedupe_keep_order(test_names)[:20],
        file_paths=_dedupe_keep_order(file_paths)[:30],
        error_type=err_type,
        framework_guess=fw,
    )
