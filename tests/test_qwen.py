"""
Tests for Qwen2.5-1.5B Instruct integration.

All model-inference tests use mocked HTTP (httpx) so no real Qwen API
credentials or network calls are required. Actual Qwen inference is never
claimed in these tests.
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from market_mind_ai.env_loader import (
    qwen_is_configured,
    require_qwen_key,
)
from market_mind_ai.models.qwen_client import QwenClient, QwenConfig
from market_mind_ai.models.qwen_model import QwenModel


class QwenConfigTests(unittest.TestCase):
    """Configuration is read entirely from environment variables."""

    def test_defaults_when_no_env(self):
        with patch.dict(os.environ, {}, clear=True):
            # Remove Qwen-related vars if present
            for k in (
                "QWEN_API_KEY",
                "QWEN_API_BASE",
                "QWEN_MODEL",
                "QWEN_TIMEOUT",
                "QWEN_MAX_TOKENS",
                "QWEN_TEMPERATURE",
            ):
                os.environ.pop(k, None)
            config = QwenConfig()
            self.assertIsNone(config.api_key)
            self.assertFalse(config.is_configured)
            self.assertIn("api/v1", config.api_base)
            self.assertEqual(config.model, "qwen2.5-1.5b-instruct")
            self.assertEqual(config.timeout, 30.0)
            self.assertEqual(config.max_tokens, 4096)
            self.assertEqual(config.temperature, 0.7)

    def test_custom_env_values(self):
        env = {
            "QWEN_API_KEY": "test-key-123",
            "QWEN_API_BASE": "https://custom.qwen.api/v1",
            "QWEN_MODEL": "qwen2.5-1.5b-instruct",
            "QWEN_TIMEOUT": "60",
            "QWEN_MAX_TOKENS": "2048",
            "QWEN_TEMPERATURE": "0.2",
        }
        with patch.dict(os.environ, env, clear=True):
            config = QwenConfig()
            self.assertEqual(config.api_key, "test-key-123")
            self.assertTrue(config.is_configured)
            self.assertEqual(
                config.api_base, "https://custom.qwen.api/v1"
            )
            self.assertEqual(config.model, "qwen2.5-1.5b-instruct")
            self.assertEqual(config.timeout, 60.0)
            self.assertEqual(config.max_tokens, 2048)
            self.assertEqual(config.temperature, 0.2)

    def test_chat_url(self):
        with patch.dict(
            os.environ,
            {
                "QWEN_API_KEY": "key",
                "QWEN_API_BASE": "https://api.example.com",
            },
            clear=True,
        ):
            config = QwenConfig()
            self.assertEqual(
                config.chat_url,
                "https://api.example.com/chat/completions",
            )


class QwenClientAvailabilityTests(unittest.TestCase):
    """Client availability and graceful degradation."""

    def test_not_available_without_key(self):
        with patch.dict(os.environ, {}, clear=True):
            client = QwenClient()
            self.assertFalse(client.is_available)

    def test_available_with_key(self):
        with patch.dict(
            os.environ, {"QWEN_API_KEY": "test-key"}, clear=True
        ):
            client = QwenClient()
            self.assertTrue(client.is_available)

    def test_complete_returns_empty_when_not_configured(self):
        with patch.dict(os.environ, {}, clear=True):
            client = QwenClient()
            result = client.complete("Say hello")
            self.assertEqual(result, "")

    def test_complete_json_returns_none_when_not_configured(self):
        with patch.dict(os.environ, {}, clear=True):
            client = QwenClient()
            result = client.complete_json('{"x": 1}')
            self.assertIsNone(result)

    def test_close_is_safe_when_never_used(self):
        with patch.dict(os.environ, {}, clear=True):
            client = QwenClient()
            client.close()  # should not raise


class QwenClientMockedHTTPSessionTests(unittest.TestCase):
    """Mocked HTTP session tests — no real Qwen API calls."""

    def _make_mock_response(
        self, text: str, status: int = 200
    ) -> MagicMock:
        mock = MagicMock()
        mock.status_code = status
        mock.json.return_value = {
            "choices": [{"message": {"content": text}}],
        }
        mock.raise_for_status.return_value = None
        return mock

    def test_complete_success(self):
        with patch.dict(
            os.environ, {"QWEN_API_KEY": "test-key"}, clear=True
        ):
            client = QwenClient()
            mock_response = self._make_mock_response(
                "The answer is 42"
            )
            mock_http_client = MagicMock()
            mock_http_client.post.return_value = mock_response
            with patch.object(
                client, "_get_client", return_value=mock_http_client
            ):
                result = client.complete("What is 2+2?")
            self.assertEqual(result, "The answer is 42")

    def test_complete_http_error(self):
        with patch.dict(
            os.environ, {"QWEN_API_KEY": "test-key"}, clear=True
        ):
            import httpx

            client = QwenClient()
            mock_client = MagicMock()
            mock_client.post.side_effect = httpx.HTTPError("boom")
            with patch.object(
                client, "_get_client", return_value=mock_client
            ):
                result = client.complete("What is 2+2?")
            self.assertEqual(result, "")

    def test_complete_no_choices(self):
        with patch.dict(
            os.environ, {"QWEN_API_KEY": "test-key"}, clear=True
        ):
            client = QwenClient()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"choices": []}
            mock_response.raise_for_status.return_value = None
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            with patch.object(
                client, "_get_client", return_value=mock_client
            ):
                result = client.complete("What is 2+2?")
            self.assertEqual(result, "")

    def test_complete_json_parses(self):
        with patch.dict(
            os.environ, {"QWEN_API_KEY": "test-key"}, clear=True
        ):
            client = QwenClient()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"ticker": "NVDA", "score": 0.8}'
                            )
                        }
                    }
                ],
            }
            mock_response.raise_for_status.return_value = None
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            with patch.object(
                client, "_get_client", return_value=mock_client
            ):
                result = client.complete_json("Analyze NVDA")
            self.assertIsNotNone(result)
            self.assertEqual(result["ticker"], "NVDA")

    def test_complete_json_invalid(self):
        with patch.dict(
            os.environ, {"QWEN_API_KEY": "test-key"}, clear=True
        ):
            client = QwenClient()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [
                    {"message": {"content": "not json at all"}}
                ],
            }
            mock_response.raise_for_status.return_value = None
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            with patch.object(
                client, "_get_client", return_value=mock_client
            ):
                result = client.complete_json("Analyze NVDA")
            self.assertIsNone(result)


class QwenModelTests(unittest.TestCase):
    """QwenModel wrapper tests."""

    def test_not_available_without_key(self):
        with patch.dict(os.environ, {}, clear=True):
            model = QwenModel()
            self.assertFalse(model.is_available)

    def test_call_returns_none_when_not_available(self):
        with patch.dict(os.environ, {}, clear=True):
            model = QwenModel()
            result = model("system prompt", "user prompt")
            self.assertIsNone(result)

    def test_call_returns_none_on_unavailable(self):
        with patch.dict(os.environ, {}, clear=True):
            model = QwenModel()
            result = model.call("prompt", system="system")
            self.assertIsNone(result)

    def test_call_success_when_available(self):
        with patch.dict(
            os.environ, {"QWEN_API_KEY": "test-key"}, clear=True
        ):
            model = QwenModel()
            # Mock the client's complete method
            with patch.object(
                model.client, "complete", return_value="Qwen response"
            ):
                result = model("system", "user")
            self.assertEqual(result, "Qwen response")

    def test_call_success_via_call_method(self):
        with patch.dict(
            os.environ, {"QWEN_API_KEY": "test-key"}, clear=True
        ):
            model = QwenModel()
            with patch.object(
                model.client, "complete", return_value="call result"
            ):
                result = model.call(
                    "user prompt", system="system prompt"
                )
            self.assertEqual(result, "call result")


class WorkersQwenTests(unittest.TestCase):
    """create_agents respects Qwen configuration."""

    def test_create_agents_without_qwen_uses_default_models(self):
        with patch.dict(os.environ, {}, clear=True):
            from market_mind_ai.workers import create_agents

            agents = create_agents(enable_trading=False)
            self.assertIn("director", agents)
            self.assertIn("sentiment", agents)
            self.assertIn("quant", agents)
            self.assertIn("risk", agents)
            self.assertIn("execution", agents)
            # When Qwen is not configured, agents should use model_name
            # (not a custom llm)
            self.assertIsNotNone(agents["director"].model_name)

    def test_create_agents_with_qwen_uses_qwen_model(self):
        env = {"QWEN_API_KEY": "test-key-123"}
        with patch.dict(os.environ, env, clear=True):
            # Reset cached Qwen model
            import market_mind_ai.workers as w

            w._QWEN_MODEL = None
            from market_mind_ai.workers import create_agents

            agents = create_agents(enable_trading=False)
            self.assertIn("director", agents)
            # When Qwen is configured, agents should have llm set
            self.assertIsNotNone(agents["director"].llm)


class EnvLoaderQwenTests(unittest.TestCase):
    """env_loader Qwen helpers."""

    def test_require_qwen_key_false_without_env(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(require_qwen_key())

    def test_require_qwen_key_true_with_env(self):
        with patch.dict(
            os.environ, {"QWEN_API_KEY": "key"}, clear=True
        ):
            self.assertTrue(require_qwen_key())

    def test_qwen_is_configured_matches_require_qwen_key(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(qwen_is_configured(), require_qwen_key())


class QwenHardeningTests(unittest.TestCase):
    """Config validation, availability probe and structured research output."""

    def test_config_validate_reports_missing_key_and_bad_values(self):
        with patch.dict(
            os.environ,
            {
                "QWEN_API_BASE": "not-a-url",
                "QWEN_TIMEOUT": "-1",
                "QWEN_MAX_TOKENS": "0",
                "QWEN_TEMPERATURE": "5",
            },
            clear=True,
        ):
            problems = QwenConfig().validate()
        self.assertTrue(any("API_KEY" in p for p in problems))
        self.assertTrue(any("http" in p for p in problems))
        self.assertTrue(any("TIMEOUT" in p for p in problems))
        self.assertTrue(any("MAX_TOKENS" in p for p in problems))
        self.assertTrue(any("TEMPERATURE" in p for p in problems))

    def test_config_validate_ok_with_valid_env(self):
        with patch.dict(
            os.environ,
            {"QWEN_API_KEY": "k", "QWEN_API_BASE": "https://api.test/v1"},
            clear=True,
        ):
            self.assertEqual(QwenConfig().validate(), [])

    def test_check_availability_short_circuits_without_key(self):
        with patch.dict(os.environ, {}, clear=True):
            available, reason = QwenClient().check_availability()
        self.assertFalse(available)
        self.assertIn("API_KEY", reason)

    def test_check_availability_success_with_mocked_probe(self):
        env = {"QWEN_API_KEY": "k", "QWEN_API_BASE": "https://api.test/v1"}
        with patch.dict(os.environ, env, clear=True):
            client = QwenClient()
            mock_client = MagicMock()
            mock_client.get.return_value.raise_for_status.return_value = None
            with patch.object(
                client, "_get_client", return_value=mock_client
            ):
                available, reason = client.check_availability()
        self.assertTrue(available)
        self.assertEqual(reason, "available")
        client.close()

    def test_check_availability_handles_probe_failure(self):
        import httpx

        env = {"QWEN_API_KEY": "k", "QWEN_API_BASE": "https://api.test/v1"}
        with patch.dict(os.environ, env, clear=True):
            client = QwenClient()
            mock_client = MagicMock()
            mock_client.get.side_effect = httpx.ConnectError("offline")
            with patch.object(
                client, "_get_client", return_value=mock_client
            ):
                available, reason = client.check_availability()
        self.assertFalse(available)
        self.assertIn("offline", reason)

    def test_complete_rejects_empty_prompt(self):
        with patch.dict(os.environ, {"QWEN_API_KEY": "k"}, clear=True):
            client = QwenClient()
            self.assertEqual(client.complete("   "), "")

    def test_complete_research_validates_structured_output(self):
        with patch.dict(os.environ, {"QWEN_API_KEY": "k"}, clear=True):
            client = QwenClient()
            with patch.object(
                client,
                "complete_json",
                return_value={
                    "summary": "Mocked bullish outlook",
                    "sentiment": "bullish",
                    "confidence": 0.75,
                },
            ):
                result = client.complete_research("NVDA", "mock context")
            self.assertIsNotNone(result)
            self.assertEqual(result["confidence"], 0.75)

    def test_complete_research_rejects_bad_confidence(self):
        with patch.dict(os.environ, {"QWEN_API_KEY": "k"}, clear=True):
            client = QwenClient()
            with patch.object(
                client,
                "complete_json",
                return_value={
                    "summary": "x",
                    "sentiment": "y",
                    "confidence": 4.2,
                },
            ):
                self.assertIsNone(client.complete_research("NVDA", "ctx"))


class QwenFailureRegressionTests(unittest.TestCase):
    """Timeouts, malformed payloads and secret-leak regressions."""

    def _client(self):
        with patch.dict(
            os.environ,
            {"QWEN_API_KEY": "test-key", "QWEN_API_BASE": "https://api.test/v1"},
            clear=True,
        ):
            return QwenClient()

    def test_timeout_returns_empty_not_raise(self):
        import httpx

        client = self._client()
        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.TimeoutException("timed out")
        with patch.object(client, "_get_client", return_value=mock_client):
            result = client.complete("prompt", timeout=0.001)
        self.assertEqual(result, "")

    def test_malformed_json_response_returns_empty(self):
        client = self._client()
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.side_effect = ValueError("not json")
        mock_client = MagicMock()
        mock_client.post.return_value = response
        with patch.object(client, "_get_client", return_value=mock_client):
            self.assertEqual(client.complete("prompt"), "")

    def test_message_without_content_returns_empty(self):
        client = self._client()
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"choices": [{"message": {}}]}
        mock_client = MagicMock()
        mock_client.post.return_value = response
        with patch.object(client, "_get_client", return_value=mock_client):
            self.assertEqual(client.complete("prompt"), "")

    def test_api_key_is_not_logged_on_failure(self):
        from loguru import logger

        client = self._client()
        sink = []
        handler_id = logger.add(sink.append, level="ERROR")
        self.addCleanup(lambda: logger.remove(handler_id))
        mock_client = MagicMock()
        mock_client.post.side_effect = RuntimeError("network down")
        with patch.object(client, "_get_client", return_value=mock_client):
            client.complete("prompt")
        logged = "".join(str(entry) for entry in sink)
        self.assertNotIn("test-key", logged)


if __name__ == "__main__":
    unittest.main()
