"""Command-line interface.

Examples:
    python -m docai ingest sample_product/docs
    python -m docai ask "How do I reset my password?"
    python -m docai chat
    python -m docai gen-api sample_product/code/tasks.py
    python -m docai gen-release sample_product/CHANGELOG.md --version 2.4.0
"""

from __future__ import annotations

import argparse
import sys

from .config import load_settings
from .generator import DocsGenerator, save_markdown
from .rag import DocsAssistant, ingest


def _print_answer(answer, show_sources: bool = True) -> None:
    print("\n" + answer.text + "\n")
    if show_sources and answer.sources:
        print("Sources:")
        for i, r in enumerate(answer.sources, start=1):
            print(f"  [{i}] {r.chunk.source} > {r.chunk.heading}  (score {r.score:.2f})")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="docai", description="GenAI for product documentation")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest", help="Index a folder of .md/.txt docs for Q&A")
    p.add_argument("folder")

    p = sub.add_parser("ask", help="Ask one question about the indexed docs")
    p.add_argument("question")

    sub.add_parser("chat", help="Interactive Q&A (type 'exit' to quit)")

    p = sub.add_parser("gen-api", help="Generate an API reference from a Python file")
    p.add_argument("code_file")
    p.add_argument("--out", default=None)

    p = sub.add_parser("gen-release", help="Generate release notes from a changelog")
    p.add_argument("changelog")
    p.add_argument("--version", required=True)
    p.add_argument("--product", default="TaskFlow")
    p.add_argument("--out", default=None)

    p = sub.add_parser("gen-howto", help="Generate a how-to guide from rough notes")
    p.add_argument("title")
    p.add_argument("notes_file")
    p.add_argument("--product", default="TaskFlow")
    p.add_argument("--audience", default="new users")
    p.add_argument("--out", default=None)

    args = parser.parse_args(argv)
    settings = load_settings()
    print(f"[docai] LLM={settings.llm_provider}  embeddings={settings.embedding_provider}")

    if args.command == "ingest":
        store = ingest(args.folder, settings)
        sources = sorted({c.source for c in store.chunks})
        print(f"Indexed {len(store.chunks)} chunks from {len(sources)} files -> {settings.index_path}")

    elif args.command == "ask":
        _print_answer(DocsAssistant(settings).ask(args.question))

    elif args.command == "chat":
        assistant = DocsAssistant(settings)
        print("Ask about the docs. Type 'exit' to quit.")
        while True:
            try:
                q = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if q.lower() in {"exit", "quit"}:
                break
            if q:
                _print_answer(assistant.ask(q))

    else:
        gen = DocsGenerator(settings)
        if args.command == "gen-api":
            text = gen.api_reference(args.code_file)
            out = args.out or "output/api_reference.md"
        elif args.command == "gen-release":
            text = gen.release_notes(args.changelog, args.version, args.product)
            out = args.out or f"output/release_notes_{args.version}.md"
        else:  # gen-howto
            with open(args.notes_file, encoding="utf-8") as f:
                notes = f.read()
            text = gen.how_to(args.title, notes, args.product, args.audience)
            out = args.out or "output/how_to.md"
        print(f"Saved -> {save_markdown(text, out)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
