"""Chunking: cutting long documents into small, searchable pieces.

LESSON: Why not give the LLM the whole manual?
  * Models have a limited context window (and you pay per token).
  * Smaller, focused pieces make search more precise.
  * The model answers better when it sees only the relevant parts.

Strategy used here (simple but effective for Markdown docs):
  1. Split the file at headings (#, ##, ###) so each piece stays on one topic.
  2. If a section is still too long, pack its paragraphs into chunks of about
     `chunk_size` characters, repeating the last `overlap` characters at the
     start of the next chunk so a sentence cut in half isn't lost.
  3. Remember where each chunk came from (file + heading) for citations.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

HEADING = re.compile(r"^(#{1,3})\s+(.*)$", re.M)


@dataclass
class Chunk:
    id: str        # e.g. "billing.md#2"
    source: str    # file name
    heading: str   # nearest heading, for nicer citations
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def split_by_headings(markdown: str) -> list[tuple[str, str]]:
    """Return a list of (heading, section_text) pairs."""
    matches = list(HEADING.finditer(markdown))
    if not matches:
        return [("", markdown)]
    sections = []
    if matches[0].start() > 0:  # text before the first heading
        sections.append(("", markdown[: matches[0].start()]))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        sections.append((m.group(2).strip(), markdown[m.start():end]))
    return sections


def pack_paragraphs(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Group paragraphs into chunks no longer than ~chunk_size characters."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, current = [], ""
    for para in paragraphs:
        if current and len(current) + len(para) + 2 > chunk_size:
            chunks.append(current)
            tail = current[-overlap:] if overlap else ""
            current = (tail + "\n\n" + para).strip()
        else:
            current = (current + "\n\n" + para).strip()
        # A single giant paragraph: hard-split it.
        while len(current) > chunk_size * 1.5:
            chunks.append(current[:chunk_size])
            current = current[chunk_size - overlap:]
    if current:
        chunks.append(current)
    return chunks


def chunk_document(source: str, markdown: str, chunk_size: int = 800, overlap: int = 150) -> list[Chunk]:
    chunks: list[Chunk] = []
    for heading, section in split_by_headings(markdown):
        for piece in pack_paragraphs(section, chunk_size, overlap):
            # Skip pieces that are only a heading with no content.
            if len(HEADING.sub("", piece).strip()) < 20:
                continue
            chunks.append(Chunk(id=f"{source}#{len(chunks)}", source=source, heading=heading, text=piece))
    return chunks


def load_and_chunk(folder: str | Path, chunk_size: int = 800, overlap: int = 150) -> list[Chunk]:
    """Read every .md / .txt file in a folder (recursively) and chunk it."""
    folder = Path(folder)
    files = sorted(p for p in folder.rglob("*") if p.suffix.lower() in {".md", ".txt"})
    if not files:
        raise FileNotFoundError(f"No .md or .txt files found in {folder}")
    all_chunks: list[Chunk] = []
    for path in files:
        rel = path.relative_to(folder).as_posix()
        all_chunks.extend(chunk_document(rel, path.read_text(encoding="utf-8"), chunk_size, overlap))
    return all_chunks
