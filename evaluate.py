"""Measure how good retrieval is.   Run:  python evaluate.py

LESSON: "It looks right" is not a measurement. A tiny labelled test set lets
you compare settings objectively (chunk size, top_k, hashing vs. OpenAI
embeddings...). We measure "hit rate @k": for what % of questions is the
correct document in the top k results?
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from docai.config import load_settings  # noqa: E402
from docai.rag import DocsAssistant, ingest  # noqa: E402

# (question, file that contains the answer)
TEST_SET = [
    ("How do I reset my password?", "account-and-security.md"),
    ("Is SMS supported for two-factor authentication?", "account-and-security.md"),
    ("Which plan includes SSO?", "account-and-security.md"),
    ("How much is the Pro plan?", "billing.md"),
    ("Can I get a refund on a monthly plan?", "billing.md"),
    ("Who can change the subscription plan?", "billing.md"),
    ("How do I create a task from Slack?", "integrations.md"),
    ("How do I verify a webhook request?", "integrations.md"),
    ("What happens when I exceed the API rate limit?", "integrations.md"),
    ("How deep can subtasks be nested?", "projects-and-tasks.md"),
    ("Can a deleted project be restored?", "projects-and-tasks.md"),
    ("How long do invitations last?", "getting-started.md"),
    ("Which browsers are supported?", "getting-started.md"),
    ("I am not receiving notification emails", "troubleshooting.md"),
    ("Why was I logged out?", "troubleshooting.md"),
]


def main() -> None:
    settings = load_settings()
    ingest("sample_product/docs", settings)
    assistant = DocsAssistant(settings)
    k = settings.top_k
    hits = 0
    for question, expected in TEST_SET:
        results = assistant.retrieve(question, top_k=k)
        files = [r.chunk.source for r in results]
        ok = expected in files
        hits += ok
        print(f"{'PASS' if ok else 'MISS'}  {question:<50} -> {files[0]}")
    print(f"\nHit rate @{k}: {hits}/{len(TEST_SET)} = {hits / len(TEST_SET):.0%}"
          f"   (embeddings: {settings.embedding_provider})")


if __name__ == "__main__":
    main()
