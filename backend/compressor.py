"""Compress file contents to high-signal structure for LLM context."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass

from utils import extract_keywords

OMITTED = "    ...  # implementation omitted"


def _end_line(node: ast.AST, fallback: int) -> int:
    return getattr(node, "end_lineno", None) or fallback


@dataclass
class CompressedFile:
    path: str
    text: str
    highlighted_keywords: list[str]


WINDOW = 3  # lines around a keyword hit


def _lines_with_keywords(content: str, keywords: list[str]) -> set[int]:
    lines = content.splitlines()
    hit: set[int] = set()
    for i, line in enumerate(lines):
        low = line.lower()
        if any(k in low for k in keywords):
            for j in range(max(0, i - WINDOW), min(len(lines), i + WINDOW + 1)):
                hit.add(j)
    return hit


def _format_snippet(lines: list[str], indices: set[int]) -> list[str]:
    if not indices:
        return []
    sorted_i = sorted(indices)
    out: list[str] = []
    prev = -2
    for i in sorted_i:
        if i > prev + 1 and out:
            out.append("    ...")
        out.append(lines[i])
        prev = i
    return out


def compress_python(path: str, content: str, keywords: list[str]) -> str:
    lines = content.splitlines()
    kw_set = set(keywords)
    hit_lines = _lines_with_keywords(content, keywords)

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return compress_plain(path, content, keywords)

    parts: list[str] = [f"# {path}", ""]

    # Top-level imports
    imports: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            seg = ast.get_source_segment(content, node)
            if seg:
                imports.append(seg.strip())
    if imports:
        parts.append("\n".join(imports))
        parts.append("")

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            parts.append(f"class {node.name}:")
            doc = ast.get_docstring(node)
            if doc:
                parts.append(f'    """{doc.strip()[:400]}{"..." if len(doc) > 400 else ""}"""')
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    seg = ast.get_source_segment(content, item)
                    if not seg:
                        continue
                    first = seg.split("\n")[0]
                    parts.append(f"    {first.strip()}")
                    idoc = ast.get_docstring(item)
                    if idoc:
                        parts.append(
                            f'        """{idoc.strip()[:300]}{"..." if len(idoc) > 300 else ""}"""'
                        )
                    body_lines = seg.split("\n")[1:]
                    body_has_kw = any(
                        any(k in ln.lower() for k in kw_set) for ln in body_lines if ln.strip()
                    )
                    if body_has_kw:
                        rel_start = item.lineno - 1
                        snippet = _format_snippet(
                            lines,
                            {
                                ln
                                for ln in hit_lines
                                if rel_start <= ln < _end_line(item, len(lines))
                            },
                        )
                        for s in snippet[:12]:
                            parts.append(s)
                        if len(snippet) > 12:
                            parts.append("    ...")
                    else:
                        parts.append(OMITTED)
                elif isinstance(item, ast.Assign | ast.AnnAssign):
                    seg = ast.get_source_segment(content, item)
                    if seg and any(k in seg.lower() for k in kw_set):
                        parts.append("    " + seg.strip().split("\n")[0])
            parts.append("")

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            seg = ast.get_source_segment(content, node)
            if not seg:
                continue
            header = seg.split("\n")[0]
            parts.append(header)
            doc = ast.get_docstring(node)
            if doc:
                parts.append(f'    """{doc.strip()[:400]}{"..." if len(doc) > 400 else ""}"""')
            body_lines = seg.split("\n")[1:]
            body_has_kw = any(
                any(k in ln.lower() for k in kw_set) for ln in body_lines if ln.strip()
            )
            if body_has_kw:
                rel_start = node.lineno - 1
                snippet = _format_snippet(
                    lines,
                    {
                        ln
                        for ln in hit_lines
                        if rel_start <= ln < _end_line(node, len(lines))
                    },
                )
                for s in snippet[:20]:
                    parts.append(s)
                if len(snippet) > 20:
                    parts.append(OMITTED)
            else:
                parts.append(OMITTED)
            parts.append("")

    text = "\n".join(parts).strip()
    if len(text) < 50:
        return compress_plain(path, content, keywords)
    return text


def compress_js_like(path: str, content: str, keywords: list[str]) -> str:
    lines = content.splitlines()
    hit_lines = _lines_with_keywords(content, keywords)
    parts: list[str] = [f"// {path}", ""]

    # Import/export lines
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("import ") or s.startswith("export "):
            parts.append(line)

    if len(parts) > 2:
        parts.append("")

    # Function-ish headers
    hdr = re.compile(
        r"^\s*(?:export\s+)?(?:async\s+)?function\s+\w+|"
        r"^\s*(?:export\s+)?const\s+\w+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>",
    )
    i = 0
    shown_blocks = 0
    while i < len(lines) and shown_blocks < 40:
        line = lines[i]
        if hdr.search(line):
            parts.append(line)
            j = i + 1
            while j < len(lines) and lines[j].startswith((" ", "\t")):
                j += 1
            block_range = set(range(i, j))
            if hit_lines & block_range:
                snippet = _format_snippet(lines, hit_lines & block_range)
                for s in snippet[1:16]:
                    parts.append(s)
                if len(snippet) > 16:
                    parts.append(OMITTED)
            else:
                parts.append(OMITTED)
            parts.append("")
            shown_blocks += 1
            i = j
        else:
            i += 1

    text = "\n".join(parts).strip()
    if len(text) < 40:
        return compress_plain(path, content, keywords)
    return text


def compress_markdown(path: str, content: str, keywords: list[str]) -> str:
    lines = content.splitlines()
    parts: list[str] = [f"<!-- {path} -->", ""]
    if lines:
        parts.append(lines[0])
    kept: list[str] = []
    for line in lines[1:]:
        low = line.lower()
        if any(k in low for k in keywords):
            kept.append(line)
    if not kept:
        kept = lines[1 : min(25, len(lines))]
    parts.extend(kept[:40])
    if len(kept) > 40:
        parts.append("\n... (truncated)")
    return "\n".join(parts)


def compress_plain(path: str, content: str, keywords: list[str]) -> str:
    lines = content.splitlines()
    hit = _lines_with_keywords(content, keywords)
    parts = [f"# {path}", ""]
    if hit:
        parts.extend(_format_snippet(lines, hit)[:50])
    else:
        parts.extend(lines[:30])
        parts.append("...")
    return "\n".join(parts)


def compress_file(path: str, content: str, task_text: str) -> CompressedFile:
    keywords = extract_keywords(task_text, max_keywords=30)
    if not keywords:
        keywords = ["code"]

    if path.endswith(".py"):
        text = compress_python(path, content, keywords)
    elif path.endswith((".js", ".ts", ".tsx", ".jsx")):
        text = compress_js_like(path, content, keywords)
    elif path.endswith(".md"):
        text = compress_markdown(path, content, keywords)
    else:
        text = compress_plain(path, content, keywords)

    # Bold keywords in output for display (markdown-friendly)
    display_kw = [k for k in keywords if k in text.lower()][:12]
    return CompressedFile(path=path, text=text, highlighted_keywords=display_kw)


def compress_selection(
    files: dict[str, str],
    selected_paths: list[str],
    task_text: str,
) -> str:
    chunks: list[str] = []
    for p in selected_paths:
        if p not in files:
            continue
        cf = compress_file(p, files[p], task_text)
        chunks.append(cf.text)
    return "\n\n---\n\n".join(chunks)
