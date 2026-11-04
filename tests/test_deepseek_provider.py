# -*- coding: utf-8 -*-
"""Unit test cho DeepSeek Provider và Horoscope DeepSeek Integration."""
import sys
import unittest
from unittest.mock import patch, Mock

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.services.llm_provider import (
    DeepSeekLLMProvider,
    get_llm_provider,
    LLMError,
)
from backend.app.services.horoscope_interpreter import (
    _request_deepseek,
    HoroscopeGenerationError,
)


class TestDeepSeekIntegration(unittest.TestCase):
    """Kiểm thử tích hợp DeepSeek API."""

    def test_provider_initialization(self):
        p = DeepSeekLLMProvider(api_key="sk-test", model="deepseek-chat")
        self.assertEqual(p.name, "deepseek")
        self.assertEqual(p.model, "deepseek-chat")

    def test_get_llm_provider_deepseek(self):
        p = get_llm_provider("deepseek")
        self.assertIsInstance(p, DeepSeekLLMProvider)

    @patch("requests.post")
    def test_deepseek_generate_success(self, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Theo Bửu Đình [1]..."}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }
        mock_post.return_value = mock_resp

        p = DeepSeekLLMProvider(api_key="sk-test")
        res = p.generate("System prompt", "User prompt")
        self.assertIn("Bửu Đình", res.text)
        self.assertEqual(res.provider, "deepseek")

    @patch("requests.post")
    def test_deepseek_insufficient_balance_llm_error(self, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 402
        mock_resp.text = '{"error":{"message":"Insufficient Balance"}}'
        mock_post.return_value = mock_resp

        p = DeepSeekLLMProvider(api_key="sk-test")
        with self.assertRaises(LLMError) as ctx:
            p.generate("System prompt", "User prompt")
        self.assertIn("402 Insufficient Balance", str(ctx.exception))

    @patch("requests.post")
    def test_horoscope_request_deepseek_402_raises_specific_error(self, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 402
        mock_post.return_value = mock_resp

        with self.assertRaises(HoroscopeGenerationError) as ctx:
            _request_deepseek("prompt", "sk-test")
        self.assertEqual(ctx.exception.code, "deepseek_insufficient_balance")
        self.assertIn("DeepSeek chưa đủ số dư", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

