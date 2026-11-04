# -*- coding: utf-8 -*-
"""Unit test cho Groq Provider và Horoscope Groq Integration."""
import sys
import unittest
from unittest.mock import patch, Mock

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.services.llm_provider import (
    GroqLLMProvider,
    get_llm_provider,
    LLMError,
)
from backend.app.services.horoscope_interpreter import (
    _request_groq,
    HoroscopeGenerationError,
)


class TestGroqIntegration(unittest.TestCase):
    """Kiểm thử tích hợp Groq API."""

    def test_provider_initialization(self):
        p = GroqLLMProvider(api_key="gsk-test", model="openai/gpt-oss-20b")
        self.assertEqual(p.name, "groq")
        self.assertEqual(p.model, "openai/gpt-oss-20b")

    def test_get_llm_provider_groq(self):
        p = get_llm_provider("groq")
        self.assertIsInstance(p, GroqLLMProvider)

    @patch("requests.post")
    def test_groq_generate_success(self, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Theo Nguyễn Phát Lộc [1]..."}}],
            "usage": {"prompt_tokens": 15, "completion_tokens": 30},
        }
        mock_post.return_value = mock_resp

        p = GroqLLMProvider(api_key="gsk-test")
        res = p.generate("System prompt", "User prompt")
        self.assertIn("Nguyễn Phát Lộc", res.text)
        self.assertEqual(res.provider, "groq")

    @patch("requests.post")
    def test_groq_api_error(self, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_post.return_value = mock_resp

        p = GroqLLMProvider(api_key="gsk-test")
        with self.assertRaises(LLMError) as ctx:
            p.generate("System prompt", "User prompt")
        self.assertIn("Lỗi Groq API", str(ctx.exception))

    @patch("requests.post")
    def test_horoscope_request_groq_rate_limit(self, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 429
        mock_post.return_value = mock_resp

        with self.assertRaises(HoroscopeGenerationError) as ctx:
            _request_groq("prompt", "gsk-test")
        self.assertEqual(ctx.exception.code, "quota")


if __name__ == "__main__":
    unittest.main()

