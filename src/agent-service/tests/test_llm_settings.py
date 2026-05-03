import json
import os
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from app.llm.cache_key import build_cache_key
from app.llm.llm_client import LlmClient, LlmConfigurationError
from app.llm.settings import AgentLlmSettings, default_agent_settings, validate_agent_settings


class LlmSettingsTests(unittest.TestCase):
    def test_default_settings_follow_env_provider(self) -> None:
        with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "GEMINI_MODEL": "gemini-test"}, clear=False):
            settings = default_agent_settings("pm")

        self.assertEqual("gemini", settings.provider)
        self.assertEqual("gemini-test", settings.model)
        self.assertEqual(3_000, settings.token_budget)

    def test_invalid_provider_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_agent_settings(AgentLlmSettings("bad", "model", 3_000))

    def test_invalid_budget_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_agent_settings(AgentLlmSettings("stub", "stub", 10))

    def test_cache_key_includes_provider_model_and_budget(self) -> None:
        base = AgentLlmSettings("stub", "stub", 3_000)
        changed = AgentLlmSettings("stub", "stub-v2", 3_000)

        first = build_cache_key("system", "user", {"stage": "PRD"}, base)
        second = build_cache_key("system", "user", {"stage": "PRD"}, changed)

        self.assertNotEqual(first, second)

    def test_missing_key_is_configuration_error(self) -> None:
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
            with self.assertRaises(LlmConfigurationError):
                LlmClient().complete(
                    "system",
                    "user",
                    {},
                    AgentLlmSettings("gemini", "gemini-test", 3_000),
                    {"Overview"},
                )

    @patch("urllib.request.urlopen")
    def test_openai_adapter_parses_response(self, urlopen: MagicMock) -> None:
        response = MagicMock()
        response.read.return_value = json.dumps(
            {
                "model": "gpt-test",
                "choices": [{"message": {"content": "{\"Overview\":\"ok\"}"}}],
                "usage": {"prompt_tokens": 11, "completion_tokens": 6},
            }
        ).encode("utf-8")
        urlopen.return_value.__enter__.return_value = response

        with patch.dict(os.environ, {"OPENAI_API_KEY": "key"}, clear=False):
            result = LlmClient().complete(
                "system",
                "user",
                {},
                AgentLlmSettings("openai", "gpt-test", 3_000),
                {"Overview"},
            )

        self.assertEqual("{\"Overview\":\"ok\"}", result.text)
        self.assertEqual("openai:gpt-test", result.model)
        self.assertEqual(11, result.input_tokens)

    @patch("urllib.request.urlopen")
    def test_openai_rate_limit_is_non_retryable_configuration_error(self, urlopen: MagicMock) -> None:
        urlopen.side_effect = _http_error(429, "{\"error\":{\"message\":\"rate limited\"}}")

        with patch.dict(os.environ, {"OPENAI_API_KEY": "key"}, clear=False):
            with self.assertRaises(LlmConfigurationError):
                LlmClient().complete(
                    "system",
                    "user",
                    {},
                    AgentLlmSettings("openai", "gpt-test", 3_000),
                    {"Overview"},
                )

    @patch("urllib.request.urlopen")
    def test_gemini_rate_limit_is_non_retryable_configuration_error(self, urlopen: MagicMock) -> None:
        urlopen.side_effect = _http_error(429, "{\"error\":{\"message\":\"rate limited\"}}")

        with patch.dict(os.environ, {"GEMINI_API_KEY": "key"}, clear=False):
            with self.assertRaises(LlmConfigurationError):
                LlmClient().complete(
                    "system",
                    "user",
                    {},
                    AgentLlmSettings("gemini", "gemini-test", 3_000),
                    {"Overview"},
                )

    @patch("urllib.request.urlopen")
    def test_gemini_adapter_parses_response(self, urlopen: MagicMock) -> None:
        response = MagicMock()
        response.read.return_value = json.dumps(
            {
                "candidates": [{"content": {"parts": [{"text": "{\"Overview\":\"ok\"}"}]}}],
                "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 3},
            }
        ).encode("utf-8")
        urlopen.return_value.__enter__.return_value = response

        with patch.dict(os.environ, {"GEMINI_API_KEY": "key"}, clear=False):
            result = LlmClient().complete(
                "system",
                "user",
                {},
                AgentLlmSettings("gemini", "gemini-test", 3_000),
                {"Overview"},
            )

        self.assertEqual("{\"Overview\":\"ok\"}", result.text)
        self.assertEqual("gemini:gemini-test", result.model)
        self.assertEqual(5, result.input_tokens)

    @patch("urllib.request.urlopen")
    def test_claude_adapter_parses_response(self, urlopen: MagicMock) -> None:
        response = MagicMock()
        response.read.return_value = json.dumps(
            {
                "model": "claude-test",
                "content": [{"type": "text", "text": "{\"Overview\":\"ok\"}"}],
                "usage": {"input_tokens": 7, "output_tokens": 4},
            }
        ).encode("utf-8")
        urlopen.return_value.__enter__.return_value = response

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "key"}, clear=False):
            result = LlmClient().complete(
                "system",
                "user",
                {},
                AgentLlmSettings("claude", "claude-test", 3_000),
                {"Overview"},
            )

        self.assertEqual("{\"Overview\":\"ok\"}", result.text)
        self.assertEqual("claude:claude-test", result.model)
        self.assertEqual(7, result.input_tokens)

def _http_error(status_code: int, body: str) -> HTTPError:
    response = MagicMock()
    response.read.return_value = body.encode("utf-8")
    return HTTPError("https://api.openai.com/v1/chat/completions", status_code, "error", {}, response)


if __name__ == "__main__":
    unittest.main()
