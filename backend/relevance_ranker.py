"""Heuristic relevance ranking for files vs. a coding task."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from utils import extract_keywords


PY_DEF = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(", re.MULTILINE)
JS_FN = re.compile(
    r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(|(\w+)\s*:\s*\([^)]*\)\s*=>)",
    re.MULTILINE,
)
JS_CLASS = re.compile(r"class\s+(\w+)", re.MULTILINE)
IMPORT_LINE = re.compile(
    r'^(?:from\s+([\w.]+)\s+import|import\s+([\w.,\s]+))',
    re.MULTILINE,
)


@dataclass
class RankedFile:
    path: str
    score: float
    confidence: float  # 0–100, derived from score
    reasons: list[str]


def _py_defs_classes(content: str) -> set[str]:
    names: set[str] = set()
    try:
        tree = ast.parse(content)
    except SyntaxError:
        for m in PY_DEF.finditer(content):
            names.add(m.group(1))
        return names
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            names.add(node.name)
    return names


def _js_names(content: str) -> set[str]:
    names: set[str] = set()
    for m in JS_FN.finditer(content):
        names.update(g for g in m.groups() if g)
    for m in JS_CLASS.finditer(content):
        names.add(m.group(1))
    return names


def _simple_imports_py(content: str) -> set[str]:
    mods: set[str] = set()
    for m in IMPORT_LINE.finditer(content):
        a, b = m.group(1), m.group(2)
        if a:
            root = a.split(".")[0]
            if root:
                mods.add(root)
        if b:
            for part in b.split(","):
                part = part.strip().split()[0] if part.strip() else ""
                if part:
                    mods.add(part.split(".")[0])
    return mods


def _infer_import_targets(path: str, content: str) -> set[str]:
    """Rough module keys other files might use (for simple boosting)."""
    if path.endswith(".py"):
        return _simple_imports_py(content)
    # JS/TS: from './x' or require('x')
    refs: set[str] = set()
    for m in re.finditer(r"""from\s+['"]([^'"]+)['"]""", content):
        refs.add(Pathish(m.group(1)).stem)
    for m in re.finditer(r"""require\(\s*['"]([^'"]+)['"]\s*\)""", content):
        refs.add(Pathish(m.group(1)).stem)
    return refs


class Pathish:
    """Tiny helper for import path stem."""

    def __init__(self, s: str):
        self.stem = s.split("/")[-1].split("\\")[-1].replace(".js", "").replace(".ts", "")


def _keyword_hits(text: str, keywords: list[str]) -> int:
    tl = text.lower()
    return sum(1 for k in keywords if k in tl)


def _name_keyword_overlap(names: set[str], keywords: list[str]) -> int:
    kw_set = set(keywords)
    return sum(1 for n in names if any(k in n.lower() for k in kw_set))


def rank_files(
    files: dict[str, str],
    task_text: str,
    top_n: int = 5,
) -> list[RankedFile]:
    """
    Score files by filename match, content hits, symbol overlap, simple import boost.
    """
    keywords = extract_keywords(task_text)
    if not keywords:
        keywords = ["code"]

    base: dict[str, float] = {}
    path_stems: dict[str, str] = {}
    reasons_map: dict[str, list[str]] = {}
    for path, content in files.items():
        stem = path.replace("/", " ").replace("_", " ").replace(".", " ").lower()
        path_stems[path] = stem
        score = 0.0
        reasons: list[str] = []
        fn_hits = sum(2.0 for k in keywords if k in stem)
        if fn_hits:
            score += fn_hits
            reasons.append(f"Filename matches task keywords ({int(fn_hits / 2)} hits)")
        content = files[path]
        body_hits = _keyword_hits(content, keywords)
        if body_hits:
            score += min(body_hits, 20) * 0.8
            reasons.append(f"Content keyword matches (~{body_hits})")
        if path.endswith(".py"):
            sym = _py_defs_classes(content)
        elif path.endswith((".js", ".ts", ".tsx", ".jsx")):
            sym = _js_names(content)
        else:
            sym = set()
        sym_ov = _name_keyword_overlap(sym, keywords)
        if sym_ov:
            score += sym_ov * 3.0
            reasons.append(f"Function/class names overlap task ({sym_ov})")
        base[path] = score
        reasons_map[path] = reasons

    # Import boost: if file A imports module name matching high-scoring file B
    avg_score = (sum(base.values()) / len(base)) if base else 0.0
    high_paths = {p for p, s in base.items() if s >= max(avg_score, 3.0)}
    module_to_paths: dict[str, list[str]] = {}
    for path in files:
        stem_key = Path(path).stem.lower()
        module_to_paths.setdefault(stem_key, []).append(path)

    boosted = dict(base)
    boost_reasons: dict[str, list[str]] = {p: [] for p in files}

    for path, content in files.items():
        targets = _infer_import_targets(path, content)
        for t in targets:
            if not t:
                continue
            for other in module_to_paths.get(t.lower(), []):
                if other != path and other in high_paths:
                    boosted[path] = boosted.get(path, 0) + 2.0
                    boost_reasons[path].append(f"Imports or references related file `{other}`")
                    break

    for path in boosted:
        reasons_map[path].extend(boost_reasons[path])

    ranked_paths = sorted(boosted.keys(), key=lambda p: boosted[p], reverse=True)
    if not ranked_paths:
        return []

    max_s = max(boosted[p] for p in ranked_paths) or 1.0
    out: list[RankedFile] = []
    for path in ranked_paths[:top_n]:
        s = boosted[path]
        confidence = min(100.0, round(100.0 * (s / max_s), 1))
        rs = reasons_map.get(path, [])
        if not rs:
            rs = ["Included by default (weak keyword signal)"]
        out.append(RankedFile(path=path, score=s, confidence=confidence, reasons=rs))
    return out
