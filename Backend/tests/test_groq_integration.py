"""
Phase B.3 — Groq AI Integration Tests (mocked).

Validates the response sanitization, error handling, retry behavior,
and fallback mechanisms of the Groq client module.
"""

import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from services.groq_client import (
    get_fallback,
    sanitize_and_parse_response,
    generate_ai_chat_async,
    CRISIS_RESOURCES,
)


class TestSanitizeAndParseResponse(unittest.TestCase):
    """Unit tests for sanitize_and_parse_response()."""

    def test_valid_json_response(self):
        raw = json.dumps({
            "text": "Hello, how are you?",
            "severity": "low",
            "suggestions": ["Breathe deeply", "Take a walk"],
        })
        result = sanitize_and_parse_response(raw)
        self.assertEqual(result["text"], "Hello, how are you?")
        self.assertEqual(result["severity"], "low")
        self.assertIsInstance(result["suggestions"], list)

    def test_markdown_fenced_json(self):
        raw = '```json\n{"text": "I hear you.", "severity": "medium", "suggestions": ["Rest"]}\n```'
        result = sanitize_and_parse_response(raw)
        self.assertEqual(result["text"], "I hear you.")
        self.assertEqual(result["severity"], "medium")

    def test_plain_text_no_json(self):
        raw = "I understand you're going through a tough time. It's okay to feel this way."
        result = sanitize_and_parse_response(raw)
        # Should salvage the text since it's > 20 chars and not JSON
        self.assertIn("tough time", result["text"])
        self.assertEqual(result["severity"], "low")

    def test_empty_string(self):
        result = sanitize_and_parse_response("")
        # Should return service_error fallback
        self.assertIn("text", result)
        self.assertEqual(result["severity"], "low")

    def test_malformed_json(self):
        raw = '{"text": "incomplete json'
        result = sanitize_and_parse_response(raw)
        self.assertIn("text", result)

    def test_crisis_flag_prevents_downgrade(self):
        raw = json.dumps({
            "text": "Things will be okay.",
            "severity": "low",
            "suggestions": ["Relax"],
        })
        result = sanitize_and_parse_response(raw, is_crisis=True)
        self.assertEqual(result["severity"], "crisis")

    def test_crisis_flag_adds_helpline_resources(self):
        raw = json.dumps({
            "text": "Please reach out for help.",
            "severity": "crisis",
            "suggestions": ["Call a friend"],
        })
        result = sanitize_and_parse_response(raw, is_crisis=True)
        self.assertEqual(result["severity"], "crisis")
        self.assertTrue(any("14416" in s for s in result["suggestions"]))

    def test_suggestions_stripped_and_capped(self):
        raw = json.dumps({
            "text": "Response",
            "severity": "low",
            "suggestions": ["  tip 1  ", "", "tip 2", "tip 3", "tip 4", "tip 5 (should be dropped)"],
        })
        result = sanitize_and_parse_response(raw)
        # Empty strings filtered, max 4 suggestions
        self.assertTrue(len(result["suggestions"]) <= 4)
        self.assertNotIn("", result["suggestions"])

    def test_json_embedded_in_text(self):
        raw = 'Here is my response:\n{"text": "Embedded JSON", "severity": "low", "suggestions": []}\nEnd.'
        result = sanitize_and_parse_response(raw)
        self.assertEqual(result["text"], "Embedded JSON")


class TestGenerateAiChatAsync(unittest.TestCase):
    """Tests for the async Groq client wrapper."""

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    @patch("services.groq_client.GROQ_API_KEY", "")
    def test_missing_api_key_returns_fallback(self):
        result = self._run(generate_ai_chat_async("hello"))
        self.assertIn("text", result)
        # Should be missing_config fallback
        self.assertIn("offline", result["text"].lower())

    @patch("services.groq_client.GROQ_API_KEY", "gsk_test_key")
    @patch("services.groq_client.get_async_client")
    def test_successful_response(self, mock_get_client):
        mock_client = AsyncMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps({
            "text": "Hello! How are you?",
            "severity": "low",
            "suggestions": ["Take care"],
        })
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        mock_get_client.return_value = mock_client

        result = self._run(generate_ai_chat_async("hello"))
        self.assertEqual(result["text"], "Hello! How are you?")
        self.assertEqual(result["severity"], "low")

    @patch("services.groq_client.GROQ_API_KEY", "gsk_test_key")
    @patch("services.groq_client.get_async_client")
    def test_timeout_returns_fallback(self, mock_get_client):
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=asyncio.TimeoutError)
        mock_get_client.return_value = mock_client

        result = self._run(generate_ai_chat_async("hello"))
        self.assertIn("text", result)
        # Should be timeout fallback
        self.assertIn("longer than expected", result["text"].lower())

    @patch("services.groq_client.GROQ_API_KEY", "gsk_test_key")
    @patch("services.groq_client.get_async_client")
    def test_rate_limit_returns_fallback(self, mock_get_client):
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("rate_limit exceeded (429)")
        )
        mock_get_client.return_value = mock_client

        result = self._run(generate_ai_chat_async("hello"))
        self.assertIn("text", result)

    @patch("services.groq_client.GROQ_API_KEY", "gsk_test_key")
    @patch("services.groq_client.get_async_client")
    def test_auth_error_returns_fallback(self, mock_get_client):
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("401 Unauthorized: Invalid auth credentials")
        )
        mock_get_client.return_value = mock_client

        result = self._run(generate_ai_chat_async("hello"))
        self.assertIn("text", result)
        # Should be missing_config (auth-related) fallback
        self.assertIn("offline", result["text"].lower())

    @patch("services.groq_client.GROQ_API_KEY", "gsk_test_key")
    @patch("services.groq_client.get_async_client")
    def test_server_error_returns_fallback(self, mock_get_client):
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("500 Internal Server Error")
        )
        mock_get_client.return_value = mock_client

        result = self._run(generate_ai_chat_async("hello"))
        self.assertIn("text", result)

    @patch("services.groq_client.GROQ_API_KEY", "gsk_test_key")
    @patch("services.groq_client.get_async_client")
    def test_empty_response_handled(self, mock_get_client):
        mock_client = AsyncMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = ""
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        mock_get_client.return_value = mock_client

        result = self._run(generate_ai_chat_async("hello"))
        self.assertIn("text", result)
        # Should have some fallback text, not crash

    @patch("services.groq_client.GROQ_API_KEY", "gsk_test_key")
    @patch("services.groq_client.get_async_client")
    def test_crisis_preserved_on_timeout(self, mock_get_client):
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=asyncio.TimeoutError)
        mock_get_client.return_value = mock_client

        result = self._run(generate_ai_chat_async("hello", is_crisis=True))
        self.assertEqual(result["severity"], "crisis")
        self.assertTrue(any("14416" in s for s in result["suggestions"]))


if __name__ == "__main__":
    unittest.main()
