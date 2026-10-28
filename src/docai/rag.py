"""The Q&A assistant: Retrieval-Augmented Generation (RAG).

LESSON: RAG in one picture

   OFFLINE (once):  docs -> chunks -> embeddings -> vector store (index)

   ONLINE (each question):
     question -> embedding -> search index -> top-k chunks
              -> prompt = rules + chunks + question -> LLM -> answer + citations

Why RAG instead of just asking the LLM?
  * The model has never seen YOUR product docs.
  * It may "hallucinate" (confidently make things up).
  * RAG grounds the answer in real text you can cite, and when the docs
    change you just re-run `ingest`; no model training needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .chunking import load_and_chunk
from .config import Settings, load_settings
from .embeddings import get_embedder
from .llm import get_llm
from .prompts import QA_SYSTEM, QA_TEMPLATE
from .vector_store import SearchResult, VectorStore

NOT_FOUND = "I couldn't find that in the documentation."


def ingest(docs_folder: str, settings: Settings | None = None) -> VectorStore:
    """Step 1 (offline): read docs, chunk, embed, save the index."""
    s = settings or load_settings()
    chunks = load_and_chunk(docs_folder, s.chunk_size, s.chunk_overlap)
    embedder = get_embedder(s)
    # Embed the heading too: it adds useful search keywords.
    vectors = embedder.embed([f"{c.heading}\n{c.text}" for c in chunks])
    store = VectorStore(chunks, vectors, embedder.name)
    store.save(s.index_path)
    return store


@dataclass
class Answer:
    question: str
    text: str
    sources: list[SearchResult] = field(default_factory=list)


def build_context(results: list[SearchResult]) -> str:
    """Number each retrieved chunk so the LLM can cite it as [1], [2]..."""
    blocks = []
    for i, r in enumerate(results, start=1):
        blocks.append(f"[{i}] (source: {r.chunk.source} > {r.chunk.heading})\n{r.chunk.text}")
    return "\n\n".join(blocks)


class DocsAssistant:
    """Steps 2-4 (online): retrieve -> augment the prompt -> generate."""

    def __init__(self, settings: Settings | None = None, store: VectorStore | None = None):
        self.settings = settings or load_settings()
        self.store = store or VectorStore.load(self.settings.index_path)
        self.embedder = get_embedder(self.settings)
        if self.embedder.name != self.store.embedder_name:
            raise ValueError(
                f"Index was built with '{self.store.embedder_name}' embeddings but "
                f"EMBEDDING_PROVIDER is '{self.embedder.name}'. Re-run ingest."
            )
        self.llm = get_llm(self.settings)

    def retrieve(self, question: str, top_k: int | None = None) -> list[SearchResult]:
        query_vector = self.embedder.embed([question])[0]
        return self.store.search(query_vector, top_k or self.settings.top_k)

    def ask(self, question: str, min_score: float = 0.05) -> Answer:
        results = self.retrieve(question)
        # Guardrail: if nothing is even slightly relevant, don't call the LLM.
        relevant = [r for r in results if r.score >= min_score]
        if not relevant:
            return Answer(question, NOT_FOUND, [])
        prompt = QA_TEMPLATE.format(context=build_context(relevant), question=question)
        text = self.llm.generate(QA_SYSTEM, prompt, max_tokens=800)
        return Answer(question, text.strip(), relevant)
