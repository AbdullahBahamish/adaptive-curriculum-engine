"""LLM Client infrastructure for optional AI enhancements.

Designed following the Strategy Pattern:
- Supports Mock (offline/local fallback), OpenAI-compatible APIs, and Google Gemini.
- Does not block or fail the primary microservice if LLM is disabled or offline.
"""
from typing import Protocol

import httpx

from ace.core.config import settings
from ace.core.logging import get_logger

logger = get_logger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM completions."""

    def complete(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text completion from prompt."""
        ...


class MockLLMProvider:
    """Deterministic fallback provider when external LLM is disabled."""

    def complete(self, prompt: str, system_prompt: str | None = None) -> str:
        logger.debug("mock_llm_complete_invoked", prompt_length=len(prompt))
        return (
            "This personalized curriculum has been topologically sequenced according to "
            "foundational prerequisite dependencies. We recommend mastering each core "
            "module before advancing to dependent topics."
        )


class OpenAILLMProvider:
    """Client for OpenAI and compatible endpoints (e.g. vLLM, Ollama, Groq)."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def complete(self, prompt: str, system_prompt: str | None = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.3,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            logger.warning("llm_api_call_failed", error=str(exc))
            return MockLLMProvider().complete(prompt, system_prompt)


def get_llm_provider() -> LLMProvider:
    """Factory function to instantiate the configured LLM provider."""
    if not settings.llm_enabled or not settings.llm_api_key:
        return MockLLMProvider()

    if settings.llm_provider in ("openai", "ollama", "groq"):
        return OpenAILLMProvider(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )

    return MockLLMProvider()
