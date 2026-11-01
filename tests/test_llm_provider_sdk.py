"""KMS RAG phải dùng SDK google-genai (thay google-generativeai deprecated)."""
from __future__ import annotations

import pytest

import google.genai as genai
from backend.app.services.llm_provider import GeminiLLMProvider, LLMError


def _fake_response():
    usage = type("Usage", (), {"prompt_token_count": 11, "candidates_token_count": 7})()
    return type("Resp", (), {"text": "Trả lời thử", "usage": usage})()


def test_gemini_provider_uses_new_sdk(monkeypatch):
    captured: dict = {}

    def fake_generate_content(model, contents, config=None, **kwargs):
        captured["model"] = model
        captured["contents"] = contents
        captured["config"] = config
        return _fake_response()

    class FakeModels:
        generate_content = staticmethod(fake_generate_content)

    class FakeClient:
        models = FakeModels()

    monkeypatch.setattr(genai, "Client", lambda api_key=None, **kw: FakeClient())

    provider = GeminiLLMProvider(api_key="fake-key", model="gemini-3.6-flash")
    resp = provider.generate("system prompt", "user question")

    assert resp.text == "Trả lời thử"
    assert resp.provider == "gemini"
    assert resp.prompt_tokens == 11
    assert resp.completion_tokens == 7
    assert captured["model"] == "gemini-3.6-flash"
    assert captured["contents"] == "user question"
    assert captured["config"].system_instruction == "system prompt"


def test_gemini_provider_caches_client(monkeypatch):
    class FakeClient:
        instances = 0

        def __init__(self, **kwargs):
            type(self).instances += 1

    calls = []

    def fake_generate_content(model, contents, config=None, **kwargs):
        calls.append(1)
        return _fake_response()

    FakeClient.models = type("M", (), {"generate_content": staticmethod(fake_generate_content)})()
    monkeypatch.setattr(genai, "Client", FakeClient)

    provider = GeminiLLMProvider(api_key="fake-key", model="gemini-3.6-flash")
    provider.generate("s", "u")
    provider.generate("s", "u")
    assert len(calls) == 2
    assert FakeClient.instances == 1


def test_gemini_provider_requires_key(monkeypatch):
    import backend.app.services.llm_provider as lp

    monkeypatch.setattr(lp, "GEMINI_API_KEY", "")
    with pytest.raises(LLMError):
        lp.GeminiLLMProvider()
