"""Global pytest configuration and fixtures for KMS Tử Vi test suite.

Provides universal test isolation for multi-provider AI keys and configuration,
ensuring local developer .env files do not contaminate unit test expectations.
"""
from __future__ import annotations

import os
import sys
import pytest

# Configure UTF-8 for console output on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


@pytest.fixture(autouse=True)
def isolate_ai_providers(monkeypatch):
    """Isolate multi-provider environment variables and interpreter globals by default.
    
    Prevents developer .env keys (e.g. GROQ_API_KEY, DEEPSEEK_API_KEY, KMS_HOROSCOPE_PROVIDER)
    from polluting legacy test suites that mock Gemini responses or expect a clean environment.
    Tests specifically targeting Groq or DeepSeek explicitly mock or patch these variables.
    """
    # 1. Isolate environment variables
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    monkeypatch.setenv("KMS_HOROSCOPE_PROVIDER", "auto")

    # 2. Isolate module-level imported globals in horoscope_interpreter
    try:
        from backend.app.services import horoscope_interpreter
        monkeypatch.setattr(horoscope_interpreter, "GROQ_API_KEY", "")
        monkeypatch.setattr(horoscope_interpreter, "DEEPSEEK_API_KEY", "")
        monkeypatch.setattr(horoscope_interpreter, "HOROSCOPE_PROVIDER", "auto")
    except ImportError:
        pass

    # 3. Isolate module-level imported globals in core.config
    try:
        from backend.app.core import config
        monkeypatch.setattr(config, "GROQ_API_KEY", "")
        monkeypatch.setattr(config, "DEEPSEEK_API_KEY", "")
        monkeypatch.setattr(config, "HOROSCOPE_PROVIDER", "auto")
    except ImportError:
        pass
