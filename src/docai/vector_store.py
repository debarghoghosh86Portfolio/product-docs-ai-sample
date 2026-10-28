"""A tiny vector database built with plain NumPy.

LESSON: A "vector store" keeps (chunk, vector) pairs and answers one question:
"Which stored vectors are closest to this query vector?"

Closeness = cosine similarity = how much two vectors point the same way:
     1.0  -> same direction (very similar text)
     0.0  -> unrelated
Because our vectors are normalised to length 1, cosine similarity is just a
dot product, so searching ALL chunks is a single matrix multiplication.

Real projects use Chroma, FAISS, pgvector, Pinecone, etc. They do the same
thing, plus tricks to stay fast with millions of vectors. Once you
understand these ~60 lines, those tools will feel familiar.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .chunking import Chunk


@dataclass
class SearchResult:
    chunk: Chunk
    score: float


def _normalise(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


class VectorStore:
    def __init__(self, chunks: list[Chunk], vectors: np.ndarray, embedder_name: str):
        assert len(chunks) == len(vectors), "one vector per chunk"
        self.chunks = chunks
        self.vectors = _normalise(vectors.astype(np.float32))
        self.embedder_name = embedder_name

    def search(self, query_vector: np.ndarray, top_k: int = 4) -> list[SearchResult]:
        q = _normalise(query_vector.reshape(1, -1))[0]
        scores = self.vectors @ q                   # cosine similarity with every chunk
        best = np.argsort(scores)[::-1][:top_k]     # indexes of the highest scores
        return [SearchResult(self.chunks[i], float(scores[i])) for i in best]

    # --- saving & loading, so we only embed the docs once ---
    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        meta = {"embedder": self.embedder_name, "chunks": [c.to_dict() for c in self.chunks]}
        path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        np.save(path.with_suffix(".npy"), self.vectors)

    @classmethod
    def load(cls, path: str | Path) -> "VectorStore":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"No index at {path}. Run `python -m docai ingest` first.")
        meta = json.loads(path.read_text(encoding="utf-8"))
        vectors = np.load(path.with_suffix(".npy"))
        chunks = [Chunk(**c) for c in meta["chunks"]]
        return cls(chunks, vectors, meta["embedder"])
