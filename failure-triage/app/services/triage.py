"""Rule-based triage from extracted signals (no external LLM required for MVP)."""

from typing import Literal

from app.schemas import (
    ExtractedSignals,
    TriageContext,
    TriageRequest,
    TriageResponse,
    WhereToLookItem,
)
from app.services.extract import extract_signals
from app.services.issue import build_issue_markdown


def _confidence(signals: ExtractedSignals, log_len: int) -> Literal["low", "medium", "high"]:
    has_trace = len(signals.file_paths) >= 1
    has_test = len(signals.test_names) >= 1
    has_err = bool(signals.error_type)
    if has_trace and has_err and log_len > 150:
        return "high"
    if (has_trace or has_test) and (has_err or log_len > 80):
        return "medium"
    return "low"


def _summary(signals: ExtractedSignals) -> str:
    if signals.error_type:
        return f"Failure points to: {signals.error_type}"
    if signals.test_names:
        return f"Test failure: {signals.test_names[0]}"
    if signals.file_paths:
        return f"Last referenced file in trace: {signals.file_paths[-1]}"
    return "Could not pinpoint a single cause from this log; see assumptions."


def _hypothesis(signals: ExtractedSignals, ctx: TriageContext | None) -> list[str]:
    out: list[str] = []
    et = (signals.error_type or "").lower()
    if "modulenotfound" in et or "no module named" in et:
        out.append(
            "A Python import failed — the environment may be missing a package "
            "or the package name differs between local and CI."
        )
    elif "importerror" in et:
        out.append(
            "Import failed — circular imports, optional deps, or PYTHONPATH issues "
            "are common causes."
        )
    elif "assertion" in et or "assertionerror" in et:
        out.append(
            "An assertion failed — the code under test returned an unexpected value "
            "or side effect."
        )
    elif "typeerror" in et:
        out.append(
            "A TypeError usually means a wrong type was passed, a missing argument, "
            "or undefined/null where an object was expected."
        )
    elif "referenceerror" in et:
        out.append(
            "A ReferenceError in JS often means a typo, wrong scope, or missing import."
        )
    elif "syntaxerror" in et:
        out.append("A syntax error — check the reported file and line for typos.")
    elif signals.test_names:
        out.append(
            f"The failing test appears to be `{signals.test_names[0]}`. "
            "Focus on recent changes touching that code path."
        )
    else:
        out.append(
            "The log suggests a runtime or test failure; use file paths below "
            "to narrow the fault."
        )
    if ctx and ctx.note:
        out.append(f"User context: {ctx.note.strip()[:300]}")
    return out[:5]


def _where_to_look(signals: ExtractedSignals) -> list[WhereToLookItem]:
    items: list[WhereToLookItem] = []
    for p in signals.file_paths[-8:]:
        items.append(
            WhereToLookItem(
                path=p,
                reason="Appears in stack trace or error location.",
            )
        )
    for t in signals.test_names[:3]:
        items.append(
            WhereToLookItem(
                path=t,
                reason="Reported as failing test or suite.",
            )
        )
    if not items:
        items.append(
            WhereToLookItem(
                path="(search in repo)",
                reason="Search log for your project’s error keywords and file names.",
            )
        )
    return items


def _fix_plan(signals: ExtractedSignals) -> list[str]:
    et = (signals.error_type or "").lower()
    steps: list[str] = [
        "Reproduce locally with the suggested repro command(s); confirm the same error.",
        "Open the top file path from the stack trace and inspect the line referenced.",
    ]
    if "modulenotfound" in et or "no module named" in et:
        steps = [
            "Install the missing package in the same environment CI uses "
            "(check requirements.txt / pyproject.toml / lockfile).",
            "If the package is optional, guard the import or add it to CI install step.",
            "Verify Python version matches CI (some wheels differ per version).",
        ]
    elif "importerror" in et:
        steps = [
            "Check for circular imports and deferred imports inside functions.",
            "Compare PYTHONPATH / working directory between local and CI.",
            "Ensure optional dependencies are installed in CI if the code path needs them.",
        ]
    elif "assertion" in et:
        steps = [
            "Run only the failing test with verbose output to see actual vs expected.",
            "Check recent commits touching the assertion or mocked dependencies.",
            "If flaky, look for time, randomness, or shared global state.",
        ]
    elif "typeerror" in et or "referenceerror" in et:
        steps = [
            "Read the exact line in the stack trace; verify types and null/undefined.",
            "Run the single test file to get a shorter stack trace.",
            "Check for API changes in dependencies (lockfile vs latest).",
        ]
    else:
        steps.extend(
            [
                "Grep the repo for the error message substring to find call sites.",
                "If CI-only: compare env vars and secrets with local `.env`.",
            ]
        )
    return steps[:10]


def _repro_commands(
    signals: ExtractedSignals,
    framework: str,
    language: str,
) -> list[str]:
    fw = framework if framework != "auto" else (signals.framework_guess or "generic")
    cmds: list[str] = []
    if signals.test_names:
        first = signals.test_names[0]
        if "::" in first and (fw == "pytest" or language == "python"):
            # tests/foo.py::test_bar
            path_part = first.split("::", 1)[0]
            rest = first.split("::", 1)[1] if "::" in first else ""
            if path_part.endswith(".py"):
                cmds.append(f'pytest "{path_part}::{rest}" -vv')
        elif fw in ("jest", "vitest") or language == "javascript":
            cmds.append(f'npm test -- --testNamePattern="{first[:80]}"')
    if not cmds:
        if fw == "pytest" or (language == "python" and "pytest" in (signals.framework_guess or "")):
            cmds.append("pytest -vv --tb=short")
        elif fw in ("jest", "vitest", "npm"):
            cmds.append("npm test")
        else:
            cmds.append("(Re-run the same command shown at the top of your CI job log.)")
    return cmds[:5]


def _assumptions(signals: ExtractedSignals, log_len: int, truncated: bool) -> list[str]:
    a: list[str] = []
    if truncated:
        a.append("Log may be incomplete; root cause might appear earlier than captured.")
    if log_len < 120:
        a.append("Very short log — error context may be missing.")
    if not signals.file_paths and not signals.test_names:
        a.append("No traceback file paths parsed — paste more of the log if possible.")
    if signals.framework_guess:
        a.append(f"Inferred tooling hint: {signals.framework_guess} (verify in CI config).")
    if not a:
        a.append("Triage is based on heuristics; verify against your repo and CI setup.")
    return a[:8]


def build_triage(
    cleaned_log: str,
    signals: ExtractedSignals,
    framework: str,
    language: str,
    context: TriageContext | None,
    truncated_note: str | None,
) -> tuple[str, list[str], list[WhereToLookItem], list[str], list[str], str, list[str], str]:
    """Return fields needed for TriageResponse plus issue markdown."""
    log_len = len(cleaned_log)
    conf = _confidence(signals, log_len)
    summary = _summary(signals)
    hypothesis = _hypothesis(signals, context)
    where = _where_to_look(signals)
    fix = _fix_plan(signals)
    repro = _repro_commands(signals, framework, language)
    assumptions = _assumptions(signals, log_len, bool(truncated_note))

    issue = build_issue_markdown(
        summary=summary,
        hypothesis=hypothesis,
        where=where,
        fix_plan=fix,
        repro=repro,
        confidence=conf,
        assumptions=assumptions,
        error_excerpt="\n".join(signals.error_lines[:8]) if signals.error_lines else "(none parsed)",
    )
    return summary, hypothesis, where, fix, repro, conf, assumptions, issue


def run_triage(
    cleaned_log: str,
    truncated_note: str | None,
    req: TriageRequest,
) -> TriageResponse:
    """End-to-end triage: extract signals, apply rules, build issue export."""
    signals = extract_signals(cleaned_log, req.framework, req.language)
    summary, hypothesis, where, fix, repro, conf, assumptions, issue = build_triage(
        cleaned_log,
        signals,
        req.framework,
        req.language,
        req.context,
        truncated_note,
    )
    return TriageResponse(
        summary=summary,
        hypothesis=hypothesis,
        where_to_look=where,
        fix_plan=fix,
        repro_commands=repro,
        confidence=conf,
        assumptions=assumptions,
        issue_markdown=issue,
        extracted_signals=signals,
        truncated_note=truncated_note,
    )
