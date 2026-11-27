"""
Qwen2.5-1.5B Instruct client for OpenCode v2 compatibility.

Provides a modular, fault-tolerant HTTP client for the Qwen-AI-compatible
model API (OpenAI-style chat completions). Configuration is read entirely
from environment variables — no credentials or endpoints are hardcoded.

Environment variables:
    QWEN_API_KEY      Bearer token for Qwen API authentication (required)
    QWEN_API_BASE     Base URL of the Qwen-compatible API endpoint
                      (default: https://dashscope.aliyuncs.com/api/v1)
    QWEN_MODEL        Model name to use (default: qwen2.5-1.5b-instruct)
    QWEN_TIMEOUT      Request timeout in seconds (default: 30)
    QWEN_MAX_TOKENS   Maximum tokens per response (default: 4096)
    QWEN_TEMPERATURE  Sampling temperature (default: 0.7)

Research-only: this client is used for research / analysis tasks. It never
submits orders, connects to brokers, or handles real-money trading.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

import httpx
from loguru import logger

_DEFAULT_API_BASE = "https://dashscope.aliyuncs.com/api/v1"
_DEFAULT_MODEL = "qwen2.5-1.5b-instruct"
_DEFAULT_TIMEOUT = 30.0
_DEFAULT_MAX_TOKENS = 4096
_DEFAULT_TEMPERATURE = 0.7


def _env_str(
    name: str, default: Optional[str] = None
) -> Optional[str]:
    """Read a string env var, returning default when unset or empty."""
    value = os.getenv(name)
    return value if value else default


def _env_float(name: str, default: float) -> float:
    """Read a float env var, returning default on parse failure."""
    try:
        return float(os.getenv(name, ""))
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    """Read an int env var, returning default on parse failure."""
    try:
        return int(os.getenv(name, ""))
    except (TypeError, ValueError):
        return default


class QwenConfig:
    """Configuration for the Qwen2.5 client, sourced from environment."""

    def __init__(self) -> None:
        self.api_key = _env_str("QWEN_API_KEY")
        api_base = _env_str("QWEN_API_BASE", _DEFAULT_API_BASE)
        self.api_base = (
            api_base.rstrip("/") if api_base else _DEFAULT_API_BASE
        )
        self.model = _env_str("QWEN_MODEL", _DEFAULT_MODEL)
        self.timeout = _env_float("QWEN_TIMEOUT", _DEFAULT_TIMEOUT)
        self.max_tokens = _env_int(
            "QWEN_MAX_TOKENS", _DEFAULT_MAX_TOKENS
        )
        self.temperature = _env_float(
            "QWEN_TEMPERATURE", _DEFAULT_TEMPERATURE
        )

    @property
    def is_configured(self) -> bool:
        """True when an API key is present."""
        return bool(self.api_key)

    @property
    def chat_url(self) -> str:
        """Full chat-completions endpoint URL."""
        return f"{self.api_base}/chat/completions"

    def validate(self) -> List[str]:
        """Return a list of configuration problems (empty when valid)."""
        problems: List[str] = []
        if not self.is_configured:
            problems.append("QWEN_API_KEY is not set")
        if not self.api_base.startswith(("http://", "https://")):
            problems.append("QWEN_API_BASE must be an http(s) URL")
        if self.timeout <= 0:
            problems.append("QWEN_TIMEOUT must be positive")
        if self.max_tokens <= 0:
            problems.append("QWEN_MAX_TOKENS must be positive")
        if not 0 <= self.temperature <= 2:
            problems.append("QWEN_TEMPERATURE must be between 0 and 2")
        return problems


class QwenClient:
    """
    Fault-tolerant Qwen2.5 chat-completions client.

    Usage::

        client = QwenClient()
        if client.is_available():
            text = client.complete("Analyze NVDA sentiment", system="...")
    """

    def __init__(self, config: Optional[QwenConfig] = None) -> None:
        self.config = config or QwenConfig()
        self._client: Optional[httpx.Client] = None

    @property
    def is_available(self) -> bool:
        """True when the client has an API key and can make requests."""
        return self.config.is_configured

    def _get_client(self) -> httpx.Client:
        """Lazily create a shared httpx client with sensible defaults."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.config.timeout,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def check_availability(self) -> Tuple[bool, str]:
        """
        Probe whether the configured model endpoint is reachable.

        Returns ``(available, reason)``. Never raises. A missing key or an
        invalid configuration short-circuits before any network call.
        """
        problems = self.config.validate()
        if problems:
            return False, "; ".join(problems)
        try:
            client = self._get_client()
            response = client.get(
                f"{self.config.api_base}/models",
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            return True, "available"
        except Exception as exc:
            logger.warning("Qwen availability probe failed: {}", exc)
            return False, str(exc)

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """
        Send a chat-completion request and return the assistant's text.

        Returns an empty string (and logs the error) when the model is
        unavailable or the request fails — callers should treat an empty
        response as "model unavailable" and degrade gracefully.
        """
        problems = self.config.validate()
        if problems or not self.is_available:
            logger.warning(
                "Qwen client unavailable: {}", "; ".join(problems)
            )
            return ""
        if not isinstance(prompt, str) or not prompt.strip():
            logger.warning("Qwen completion rejected: empty prompt")
            return ""
        if timeout is not None and timeout <= 0:
            logger.warning("Qwen completion rejected: invalid timeout")
            return ""

        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": model or self.config.model,
            "messages": messages,
            "temperature": (
                temperature
                if temperature is not None
                else self.config.temperature
            ),
            "max_tokens": (
                max_tokens
                if max_tokens is not None
                else self.config.max_tokens
            ),
            "stream": False,
        }

        try:
            client = self._get_client()
            response = client.post(
                self.config.chat_url,
                json=payload,
                timeout=(
                    timeout
                    if timeout is not None
                    else self.config.timeout
                ),
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.error("Qwen completion failed: {}", exc)
            return ""

        try:
            choices = data.get("choices", [])
            if not choices:
                logger.error("Qwen response contained no choices")
                return ""
            message = choices[0].get("message", {})
            return str(message.get("content", ""))
        except (AttributeError, TypeError, ValueError) as exc:
            logger.error("Failed to parse Qwen response: {}", exc)
            return ""

    def complete_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        *,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Send a chat-completion request expecting a JSON object in the response.

        Returns the parsed dict, or None when the model is unavailable or
        the response is not valid JSON.
        """
        json_system = (
            (system + "\n\n" if system else "")
            + "Return ONLY a single valid JSON object. No markdown fences, "
            "no prose before or after, and no commentary."
        )
        text = self.complete(
            prompt,
            system=json_system,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        if not text:
            return None
        try:
            return json.loads(text)
        except (ValueError, TypeError):
            # Try to extract JSON from markdown fences or prose
            import re

            fence = re.search(
                r"```(?:json)?\s*(.*?)```", text, re.DOTALL
            )
            if fence:
                try:
                    return json.loads(fence.group(1).strip())
                except (ValueError, TypeError):
                    pass
            return None

    def complete_research(
        self,
        entity: str,
        context: str,
        *,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Model-assisted research analysis with validated structured output.

        The response must be a JSON object containing ``summary`` (str),
        ``sentiment`` (str), and ``confidence`` (0..1). Any other shape is
        rejected. Returns None when the model is unavailable or the output
        fails validation. Never performs network calls without a key.
        """
        prompt = (
            f"Research entity: {entity}\n"
            f"Source context: {context[:1200] or 'none provided'}\n"
            "Return JSON with keys: summary (string), "
            "sentiment (string), confidence (number 0-1)."
        )
        data = self.complete_json(
            prompt,
            system="You are a research analyst. Respond with JSON only.",
            model=model,
            timeout=timeout,
        )
        if not isinstance(data, dict):
            return None
        summary = data.get("summary")
        sentiment = data.get("sentiment")
        confidence = data.get("confidence")
        if not isinstance(summary, str) or not isinstance(sentiment, str):
            return None
        if not isinstance(confidence, (int, float, str)):
            return None
        try:
            score = float(confidence)
        except (TypeError, ValueError):
            return None
        if not 0.0 <= score <= 1.0:
            return None
        return {
            "summary": summary[:1000],
            "sentiment": sentiment[:64],
            "confidence": score,
        }

    def __enter__(self) -> "QwenClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
