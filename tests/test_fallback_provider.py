# -*- coding: utf-8 -*-
"""Unit test cho FallbackLLMProvider và cơ chế Gemini chính, Groq dự phòng trong KMS RAG."""
import sys
import unittest
from unittest.mock import patch, Mock

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.services.llm_provider import (
    LLMProvider,
    LLMResponse,
    LLMError,
    FallbackLLMProvider,
    GeminiLLMProvider,
    GroqLLMProvider,
    get_llm_provider,
)


class TestFallbackLLMProvider(unittest.TestCase):
    """Kiểm thử FallbackLLMProvider: Gemini làm chính, Groq làm dự phòng."""

    def test_tc01_primary_gemini_success_skips_fallback(self):
        """TC-FB-01: Provider chính (Gemini) thành công -> Trả về kết quả, không gọi fallback."""
        mock_gemini = Mock(spec=LLMProvider)
        mock_gemini.name = "gemini"
        mock_gemini.model = "gemini-3.6-flash"
        mock_gemini.generate.return_value = LLMResponse(
            text="Theo Bửu Đình [1]...",
            provider="gemini",
            model="gemini-3.6-flash",
        )

        mock_groq = Mock(spec=LLMProvider)
        mock_groq.name = "groq"
        mock_groq.model = "openai/gpt-oss-20b"

        provider = FallbackLLMProvider(primary=mock_gemini, fallback=mock_groq)
        res = provider.generate("System prompt", "User prompt")

        self.assertEqual(res.provider, "gemini")
        self.assertIn("Bửu Đình", res.text)
        mock_gemini.generate.assert_called_once_with("System prompt", "User prompt")
        mock_groq.generate.assert_not_called()

    def test_tc02_primary_gemini_fails_calls_groq_fallback(self):
        """TC-FB-02: Provider chính (Gemini) gặp lỗi -> Tự động chuyển sang Groq dự phòng."""
        mock_gemini = Mock(spec=LLMProvider)
        mock_gemini.name = "gemini"
        mock_gemini.model = "gemini-3.6-flash"
        mock_gemini.generate.side_effect = LLMError("Lỗi Gemini API: 429 ResourceExhausted")

        mock_groq = Mock(spec=LLMProvider)
        mock_groq.name = "groq"
        mock_groq.model = "openai/gpt-oss-20b"
        mock_groq.generate.return_value = LLMResponse(
            text="Theo Nguyễn Phát Lộc [2]...",
            provider="groq",
            model="openai/gpt-oss-20b",
        )

        provider = FallbackLLMProvider(primary=mock_gemini, fallback=mock_groq)
        res = provider.generate("System prompt", "User prompt")

        self.assertEqual(res.provider, "groq")
        self.assertIn("Nguyễn Phát Lộc", res.text)
        mock_gemini.generate.assert_called_once_with("System prompt", "User prompt")
        mock_groq.generate.assert_called_once_with("System prompt", "User prompt")

    def test_tc03_both_fail_raises_fallback_error(self):
        """TC-FB-03: Cả Gemini và Groq đều lỗi -> Ném ngoại lệ LLMError của fallback."""
        mock_gemini = Mock(spec=LLMProvider)
        mock_gemini.name = "gemini"
        mock_gemini.generate.side_effect = LLMError("Gemini 429")

        mock_groq = Mock(spec=LLMProvider)
        mock_groq.name = "groq"
        mock_groq.generate.side_effect = LLMError("Groq 500 Server Error")

        provider = FallbackLLMProvider(primary=mock_gemini, fallback=mock_groq)
        with self.assertRaises(LLMError) as ctx:
            provider.generate("System prompt", "User prompt")
        self.assertIn("Groq 500", str(ctx.exception))

    def test_tc04_get_llm_provider_auto_returns_fallback_provider(self):
        """TC-FB-04: get_llm_provider('auto') trả về FallbackLLMProvider khi cả 2 key đều có."""
        with patch("backend.app.services.llm_provider.GEMINI_API_KEY", "test-gemini-key"), \
             patch("backend.app.services.llm_provider.GROQ_API_KEY", "test-groq-key"), \
             patch("backend.app.core.config.GEMINI_API_KEY", "test-gemini-key"), \
             patch("backend.app.core.config.GROQ_API_KEY", "test-groq-key"):
            provider = get_llm_provider("auto")
            self.assertIsInstance(provider, FallbackLLMProvider)
            self.assertIsInstance(provider.primary, GeminiLLMProvider)
            self.assertIsInstance(provider.fallback, GroqLLMProvider)


if __name__ == "__main__":
    unittest.main()
