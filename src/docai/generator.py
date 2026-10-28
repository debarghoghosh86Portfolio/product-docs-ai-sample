"""The docs generator: let the LLM write first drafts of documentation.

LESSON: LLMs write much better docs when you give them *structured facts*
instead of asking them to "document this". So each generator does two steps:

  1. EXTRACT facts with normal code (no AI): function names, parameters,
     type hints, docstrings, changelog lines...
  2. GENERATE prose with the LLM, using a prompt that contains those facts
     and a strict output format.

Step 1 is cheap, exact and testable; step 2 adds the human-friendly writing.
Always have a person review AI-written docs before publishing.
"""

from __future__ import annotations

import ast
from pathlib import Path

from .config import Settings, load_settings
from .llm import LLM, get_llm
from .prompts import (
    API_REFERENCE_TEMPLATE,
    HOW_TO_TEMPLATE,
    RELEASE_NOTES_TEMPLATE,
    WRITER_SYSTEM,
)


# ---------------------------------------------------------------------------
# Step 1: fact extraction with Python's built-in `ast` (abstract syntax tree)
# ---------------------------------------------------------------------------
def _signature(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Rebuild a readable signature like `create_task(title: str, due: date | None = None) -> Task`."""
    args = fn.args
    defaults = [None] * (len(args.args) - len(args.defaults)) + list(args.defaults)
    parts = []
    for arg, default in zip(args.args, defaults):
        text = arg.arg
        if arg.annotation is not None:
            text += f": {ast.unparse(arg.annotation)}"
        if default is not None:
            text += f" = {ast.unparse(default)}"
        parts.append(text)
    returns = f" -> {ast.unparse(fn.returns)}" if fn.returns is not None else ""
    return f"{fn.name}({', '.join(parts)}){returns}"


def _raises(fn: ast.AST) -> list[str]:
    """Find exception names raised inside a function body."""
    found = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Raise) and node.exc is not None:
            target = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
            found.add(ast.unparse(target))
    return sorted(found)


def extract_structure(source: str) -> list[dict]:
    """Return the public classes/functions of a module as plain dictionaries."""
    tree = ast.parse(source)
    items = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            items.append({
                "kind": "function",
                "signature": _signature(node),
                "docstring": ast.get_docstring(node) or "",
                "raises": _raises(node),
            })
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            methods = [
                {
                    "signature": _signature(m),
                    "docstring": ast.get_docstring(m) or "",
                    "raises": _raises(m),
                }
                for m in node.body
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                and (not m.name.startswith("_") or m.name == "__init__")
            ]
            items.append({
                "kind": "class",
                "name": node.name,
                "docstring": ast.get_docstring(node) or "",
                "methods": methods,
            })
    return items


def format_structure(items: list[dict]) -> str:
    """Render extracted facts as compact text for the prompt."""
    lines = []
    for item in items:
        if item["kind"] == "function":
            lines.append(f"FUNCTION {item['signature']}")
            if item["docstring"]:
                lines.append(f"  doc: {item['docstring']}")
            if item["raises"]:
                lines.append(f"  raises: {', '.join(item['raises'])}")
        else:
            lines.append(f"CLASS {item['name']}")
            if item["docstring"]:
                lines.append(f"  doc: {item['docstring']}")
            for m in item["methods"]:
                lines.append(f"  METHOD {m['signature']}")
                if m["docstring"]:
                    lines.append(f"    doc: {m['docstring']}")
                if m["raises"]:
                    lines.append(f"    raises: {', '.join(m['raises'])}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Step 2: generation with the LLM
# ---------------------------------------------------------------------------
class DocsGenerator:
    def __init__(self, settings: Settings | None = None, llm: LLM | None = None):
        self.settings = settings or load_settings()
        self.llm = llm or get_llm(self.settings)

    def api_reference(self, code_path: str | Path) -> str:
        path = Path(code_path)
        source = path.read_text(encoding="utf-8")
        structure = format_structure(extract_structure(source))
        prompt = API_REFERENCE_TEMPLATE.format(module=path.stem, structure=structure, source=source)
        return self.llm.generate(WRITER_SYSTEM, prompt, max_tokens=3000)

    def release_notes(self, changelog_path: str | Path, version: str, product: str) -> str:
        changelog = Path(changelog_path).read_text(encoding="utf-8")
        prompt = RELEASE_NOTES_TEMPLATE.format(version=version, product=product, changelog=changelog)
        return self.llm.generate(WRITER_SYSTEM, prompt, max_tokens=2000)

    def how_to(self, title: str, notes: str, product: str, audience: str = "new users") -> str:
        prompt = HOW_TO_TEMPLATE.format(title=title, notes=notes, product=product, audience=audience)
        return self.llm.generate(WRITER_SYSTEM, prompt, max_tokens=2000)


def save_markdown(text: str, out_path: str | Path) -> Path:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text.strip() + "\n", encoding="utf-8")
    return out
