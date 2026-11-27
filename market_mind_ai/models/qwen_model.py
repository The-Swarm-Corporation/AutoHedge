"""
Qwen2.5-1.5B Instruct model wrapper for swarms Agent compatibility.

Wraps :class:`market_mind_ai.models.qwen_client.QwenClient` so it can be
passed as the ``llm`` argument to a swarms ``Agent``. When Qwen is not
configured (no ``QWEN_API_KEY``), all calls return ``None`` so callers can
detect unavailability and degrade gracefully.

Configuration is read entirely from environment variables — no credentials
or endpoints are hardcoded.
"""

from __future__ import annotations

from typing import Any, Optional

from market_mind_ai.models.qwen_client import QwenClient


class QwenModel:
    """
    Swarms-compatible LLM wrapper for Qwen2.5-1.5B Instruct.

    The swarms Agent calls ``llm(system_prompt, user_prompt, ...)`` or
    accesses ``llm.call(...)`` depending on version. This wrapper implements
    both ``__call__`` and ``call`` so it works with either path.

    Returns ``None`` when the Qwen client is not available, allowing the
    pipeline to fall back gracefully instead of crashing.
    """

    def __init__(
        self,
        client: Optional[QwenClient] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> None:
        self.client = client or QwenClient()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @property
    def is_available(self) -> bool:
        """True when Qwen is configured and can serve requests."""
        return self.client.is_available

    def _to_optional(self, text: str) -> Optional[str]:
        """Convert empty-string responses to None for cleaner semantics."""
        return text if text else None

    def __call__(
        self,
        system_prompt: str,
        user_prompt: str,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[str]:
        """
        Swarms-style invocation: ``llm(system_prompt, user_prompt)``.

        Returns the assistant's text, or ``None`` when Qwen is unavailable.
        """
        return self._to_optional(
            self.client.complete(
                prompt=user_prompt,
                system=system_prompt,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        )

    def call(
        self,
        prompt: str,
        system: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[str]:
        """
        Alternative invocation: ``llm.call(prompt, system=...)``.

        Returns the assistant's text, or ``None`` when Qwen is unavailable.
        """
        return self._to_optional(
            self.client.complete(
                prompt=prompt,
                system=system,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self.client.close()
