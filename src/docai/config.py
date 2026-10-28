"""Settings for the whole project, read from environment variables / .env.

LESSON: Keep secrets (API keys) and tunable values OUT of your code.
Reading them from the environment means you can switch from the free
"mock" model to Claude or OpenAI without changing a single line of code.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Reads the .env file (if it exists) into os.environ.
load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


@dataclass
class Settings:
    llm_provider: str = "mock"
    embedding_provider: str = "hashing"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_embedding_model: str = "nomic-embed-text"

    chunk_size: int = 800
    chunk_overlap: int = 150
    top_k: int = 4
    index_path: str = "output/index.json"


def load_settings() -> Settings:
    """Build a Settings object from the current environment."""
    return Settings(
        llm_provider=_get("LLM_PROVIDER", "mock").lower(),
        embedding_provider=_get("EMBEDDING_PROVIDER", "hashing").lower(),
        anthropic_api_key=_get("ANTHROPIC_API_KEY"),
        anthropic_model=_get("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
        openai_api_key=_get("OPENAI_API_KEY"),
        openai_model=_get("OPENAI_MODEL", "gpt-4o-mini"),
        openai_embedding_model=_get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        ollama_base_url=_get("OLLAMA_BASE_URL", "http://localhost:11434"),
        ollama_model=_get("OLLAMA_MODEL", "llama3.2"),
        ollama_embedding_model=_get("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
        chunk_size=int(_get("CHUNK_SIZE", "800")),
        chunk_overlap=int(_get("CHUNK_OVERLAP", "150")),
        top_k=int(_get("TOP_K", "4")),
        index_path=_get("INDEX_PATH", "output/index.json"),
    )
