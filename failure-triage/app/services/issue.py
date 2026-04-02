"""Format triage as a paste-ready GitHub / issue markdown block."""

from app.schemas import WhereToLookItem


def build_issue_markdown(
    summary: str,
    hypothesis: list[str],
    where: list[WhereToLookItem],
    fix_plan: list[str],
    repro: list[str],
    confidence: str,
    assumptions: list[str],
    error_excerpt: str,
) -> str:
    hyp = "\n".join(f"- {h}" for h in hypothesis) or "- (none)"
    loc = "\n".join(f"- `{w.path}` — {w.reason}" for w in where) or "- (none)"
    fix = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(fix_plan))
    rep = "\n".join(f"```bash\n{c}\n```" for c in repro)
    asm = "\n".join(f"- {a}" for a in assumptions) or "- (none)"

    return f"""## Summary
{summary}

## Hypothesis
{hyp}

## Where to look
{loc}

## Suggested fix plan
{fix}

## Repro commands
{rep}

## Error excerpt (from log)
```
{error_excerpt[:4000]}
```

## Triage metadata
- **Confidence:** {confidence}
- **Assumptions**
{asm}
"""
