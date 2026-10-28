"""The LLM layer: one simple interface, many providers.

LESSON: Every chat-style LLM works the same way at its core:
    (system instructions + user message)  ->  model  ->  generated text

So we define ONE function signature, `generate(system, prompt)`, and write a
small class per provider. The rest of the app never needs to know whether it
is talking to Claude, GPT, a local Llama model, or our fake "mock" model.
This is called the *adapter* (or *strategy*) pattern.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

import requests

from .config import Settings, load_settings


class LLM(ABC):
    """Base class: anything that can turn a prompt into text."""

    name = "base"

    @abstractmethod
    def generate(self, system: str, prompt: str, max_tokens: int = 1500) -> str:
        """Return the model's reply to `prompt`, following `system` instructions."""


# ---------------------------------------------------------------------------
# 1) Mock - no internet, no API key, always the same output.
# ---------------------------------------------------------------------------
class MockLLM(LLM):
    """A pretend LLM for learning and automated tests.

    It does NOT understand language. It just:
      * for Q&A prompts: copies the first sentences of the best source + a citation
      * for anything else: returns a short markdown summary of the input
    This lets you run the full pipeline end-to-end for free.
    """

    name = "mock"

    def generate(self, system: str, prompt: str, max_tokens: int = 1500) -> str:
        # Q&A prompts contain numbered sources like "[1] (source: file.md)".
        match = re.search(r"\[1\] \(source: [^)]+\)\n(.+?)(?:\n\[2\]|\n</context>)", prompt, re.S)
        if match:
            body = "\n".join(ln for ln in match.group(1).splitlines() if not ln.startswith("#"))
            passage = " ".join(body.split())
            sentences = re.split(r"(?<=[.!?])\s+", passage)
            return " ".join(sentences[:2]).strip() + " [1]\n\n_(answer produced by the offline mock model)_"

        # Generator prompts: summarise what we were given.
        lines = [ln for ln in prompt.splitlines() if ln.strip()][:25]
        body = "\n".join(f"- {ln.strip()[:120]}" for ln in lines)
        return (
            "## Draft (offline mock model)\n\n"
            "Switch `LLM_PROVIDER` to `anthropic`, `openai` or `ollama` for real writing.\n"
            "The mock received this material:\n\n" + body
        )


# ---------------------------------------------------------------------------
# 2) Anthropic Claude
# ---------------------------------------------------------------------------
class AnthropicLLM(LLM):
    name = "anthropic"

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is empty. Add it to your .env file.")
        import anthropic  # imported here so the package is only needed if you use it

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate(self, system: str, prompt: str, max_tokens: int = 1500) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        # The reply is a list of content blocks; join the text ones.
        return "".join(block.text for block in response.content if block.type == "text")


# ---------------------------------------------------------------------------
# 3) OpenAI
# ---------------------------------------------------------------------------
class OpenAILLM(LLM):
    name = "openai"

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is empty. Add it to your .env file.")
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, system: str, prompt: str, max_tokens: int = 1500) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# 4) Ollama - free models running on your own computer
# ---------------------------------------------------------------------------
class OllamaLLM(LLM):
    name = "ollama"

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, system: str, prompt: str, max_tokens: int = 1500) -> str:
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "stream": False,
                "options": {"num_predict": max_tokens},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=300,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]


def get_llm(settings: Settings | None = None) -> LLM:
    """Factory: build the LLM chosen by LLM_PROVIDER."""
    s = settings or load_settings()
    if s.llm_provider == "mock":
        return MockLLM()
    if s.llm_provider == "anthropic":
        return AnthropicLLM(s.anthropic_api_key, s.anthropic_model)
    if s.llm_provider == "openai":
        return OpenAILLM(s.openai_api_key, s.openai_model)
    if s.llm_provider == "ollama":
        return OllamaLLM(s.ollama_base_url, s.ollama_model)
    raise ValueError(f"Unknown LLM_PROVIDER '{s.llm_provider}'. Use mock, anthropic, openai or ollama.")
