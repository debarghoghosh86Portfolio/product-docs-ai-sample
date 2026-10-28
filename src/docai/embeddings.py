"""Embeddings: turning text into lists of numbers (vectors).

LESSON: Computers can't compare *meanings* directly, but they can compare
numbers. An embedding model maps a piece of text to a vector such that
similar texts get vectors that point in similar directions.

    "How do I reset my password?"   -> [0.12, -0.40, 0.88, ...]
    "Steps to change login secret"  -> [0.10, -0.38, 0.91, ...]   (close!)
    "Pricing for the Pro plan"      -> [-0.70, 0.22, 0.05, ...]   (far away)

We then measure closeness with *cosine similarity* (see vector_store.py).

Three options here:
  * hashing - offline & free. It matches shared WORDS, not meanings, so it is a
              "keyword" search. Perfect for learning; weaker on synonyms.
  * openai  - real semantic embeddings via API.
  * ollama  - real semantic embeddings on your own machine, free.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
import requests

from .config import Settings, load_settings


class Embedder(ABC):
    name = "base"

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray:
        """Return an array of shape (len(texts), dimensions)."""


class HashingEmbedder(Embedder):
    """Offline embeddings using scikit-learn's HashingVectorizer.

    Each word (and each pair of neighbouring words) is hashed into one of
    `n_features` buckets; the vector counts how often each bucket appears.
    No training, no downloads, and the same text always gives the same vector.
    """

    name = "hashing"

    def __init__(self, n_features: int = 2**14):
        from sklearn.feature_extraction.text import HashingVectorizer

        self.vectorizer = HashingVectorizer(
            n_features=n_features,
            ngram_range=(1, 2),
            stop_words="english",   # ignore "the", "and", "is"...
            alternate_sign=False,
            norm="l2",
        )

    def embed(self, texts: list[str]) -> np.ndarray:
        return self.vectorizer.transform(texts).toarray().astype(np.float32)


class OpenAIEmbedder(Embedder):
    name = "openai"

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is empty but EMBEDDING_PROVIDER=openai.")
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def embed(self, texts: list[str]) -> np.ndarray:
        response = self.client.embeddings.create(model=self.model, input=texts)
        return np.array([item.embedding for item in response.data], dtype=np.float32)


class OllamaEmbedder(Embedder):
    name = "ollama"

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def embed(self, texts: list[str]) -> np.ndarray:
        response = requests.post(
            f"{self.base_url}/api/embed",
            json={"model": self.model, "input": texts},
            timeout=300,
        )
        response.raise_for_status()
        return np.array(response.json()["embeddings"], dtype=np.float32)


def get_embedder(settings: Settings | None = None) -> Embedder:
    s = settings or load_settings()
    if s.embedding_provider == "hashing":
        return HashingEmbedder()
    if s.embedding_provider == "openai":
        return OpenAIEmbedder(s.openai_api_key, s.openai_embedding_model)
    if s.embedding_provider == "ollama":
        return OllamaEmbedder(s.ollama_base_url, s.ollama_embedding_model)
    raise ValueError(
        f"Unknown EMBEDDING_PROVIDER '{s.embedding_provider}'. Use hashing, openai or ollama."
    )
