"""Assemble the final ready-to-paste assistant prompt."""

from __future__ import annotations


def build_ready_prompt(cleaned_task: str, compressed_context: str) -> str:
    task = (cleaned_task or "").strip()
    ctx = (compressed_context or "").strip()
    return (
        "You are helping with the following task:\n\n"
        f"{task}\n\n"
        "Here is the minimal relevant repository context:\n\n"
        f"{ctx}\n\n"
        "Please focus only on this task and this context.\n"
        "If an assumption is required, state it explicitly."
    )


def build_markdown_export(
    cleaned_task: str,
    compressed_context: str,
    ready_prompt: str,
    stats_lines: list[str],
) -> str:
    lines = [
        "# Context Surgeon export",
        "",
        "## Cleaned task",
        "",
        cleaned_task,
        "",
        "## Compressed context",
        "",
        "```text",
        compressed_context,
        "```",
        "",
        "## Stats",
        "",
    ]
    lines.extend(f"- {s}" for s in stats_lines)
    lines.extend(["", "## Ready-to-paste prompt", "", "```text", ready_prompt, "```", ""])
    return "\n".join(lines)
