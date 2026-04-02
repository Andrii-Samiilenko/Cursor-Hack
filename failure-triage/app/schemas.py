"""Pydantic models for API request and response bodies."""

from typing import Literal

from pydantic import BaseModel, Field


class TriageContext(BaseModel):
    """Optional hints from the user (branch, recent change, etc.)."""

    branch: str | None = Field(default=None, max_length=256)
    note: str | None = Field(default=None, max_length=2000)


class TriageRequest(BaseModel):
    """POST /api/triage body."""

    log: str = Field(..., min_length=1, max_length=200_000)
    framework: Literal["auto", "pytest", "jest", "vitest", "generic"] = "auto"
    language: Literal["auto", "python", "javascript"] = "auto"
    context: TriageContext | None = None


class WhereToLookItem(BaseModel):
    """A file, module, or search hint."""

    path: str
    reason: str


class ExtractedSignals(BaseModel):
    """Structured signals parsed from raw log text."""

    error_lines: list[str] = Field(default_factory=list)
    test_names: list[str] = Field(default_factory=list)
    file_paths: list[str] = Field(default_factory=list)
    error_type: str | None = None
    framework_guess: str | None = None


class TriageResponse(BaseModel):
    """Structured triage returned to the client."""

    summary: str
    hypothesis: list[str]
    where_to_look: list[WhereToLookItem]
    fix_plan: list[str]
    repro_commands: list[str]
    confidence: Literal["low", "medium", "high"]
    assumptions: list[str]
    issue_markdown: str
    extracted_signals: ExtractedSignals
    truncated_note: str | None = None
