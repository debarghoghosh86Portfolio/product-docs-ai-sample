"""Automated tests. Run with:  pytest

They use the offline mock LLM + hashing embeddings, so they are free,
fast, and run the same on every machine (including GitHub Actions).
"""

from pathlib import Path

import pytest

from docai.chunking import chunk_document, load_and_chunk
from docai.config import Settings
from docai.generator import DocsGenerator, extract_structure, format_structure
from docai.rag import NOT_FOUND, DocsAssistant, ingest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "sample_product" / "docs"


@pytest.fixture
def settings(tmp_path):
    return Settings(llm_provider="mock", embedding_provider="hashing",
                    index_path=str(tmp_path / "index.json"))


@pytest.fixture
def assistant(settings):
    ingest(str(DOCS), settings)
    return DocsAssistant(settings)


# --- chunking ---------------------------------------------------------------
def test_chunks_keep_source_and_heading():
    md = "# Title\n\nIntro text that is long enough.\n\n## Part A\n\nDetails about part A go here."
    chunks = chunk_document("x.md", md, chunk_size=200, overlap=20)
    assert [c.heading for c in chunks] == ["Title", "Part A"]
    assert all(c.source == "x.md" for c in chunks)


def test_long_sections_are_split():
    md = "# Big\n\n" + "\n\n".join(f"Paragraph {i} " + "word " * 40 for i in range(10))
    chunks = chunk_document("big.md", md, chunk_size=300, overlap=50)
    assert len(chunks) > 3
    assert all(len(c.text) <= 450 for c in chunks)


def test_sample_docs_load():
    chunks = load_and_chunk(DOCS)
    assert len({c.source for c in chunks}) == 6


# --- retrieval (the most important part of RAG to test!) --------------------
@pytest.mark.parametrize("question, expected_file", [
    ("How do I reset my password?", "account-and-security.md"),
    ("How much does the Business plan cost?", "billing.md"),
    ("What is the API rate limit?", "integrations.md"),
    ("Why can't I move a task to Done?", "troubleshooting.md"),
    ("How many members can I invite on the free plan?", "projects-and-tasks.md"),
])
def test_retrieval_finds_right_file(assistant, question, expected_file):
    top_files = [r.chunk.source for r in assistant.retrieve(question, top_k=3)]
    assert expected_file in top_files


def test_answer_has_citation(assistant):
    answer = assistant.ask("How long is the password reset link valid?")
    assert "[1]" in answer.text
    assert answer.sources


def test_unrelated_question_is_refused(assistant):
    answer = assistant.ask("zebra quantum lasagna")
    assert answer.text == NOT_FOUND


# --- generator --------------------------------------------------------------
def test_extract_structure_from_code():
    source = (ROOT / "sample_product" / "code" / "tasks.py").read_text()
    text = format_structure(extract_structure(source))
    assert "CLASS TaskClient" in text
    assert "complete_task(self, task_id: str) -> Task" in text
    assert "raises: TaskBlockedError" in text


def test_generator_runs_with_mock(settings):
    gen = DocsGenerator(settings)
    out = gen.release_notes(ROOT / "sample_product" / "CHANGELOG.md", "2.4.0", "TaskFlow")
    assert "mock" in out.lower()
