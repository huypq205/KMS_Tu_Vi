"""Bảo mật API: CORS theo origin, API key tùy chọn, rate limit endpoint horoscope.

Điểm chính:
- /api/v1/health luôn mở (cần cho health check Render).
- KMS_API_KEY = "" (mặc định) → API mở; khi đặt → mọi /api/v1/* (trừ /health) cần X-API-Key.
- KMS_RATE_LIMIT_PER_MIN áp dụng cho /api/v1/horoscope* (endpoint gọi LLM, tốn chi phí).
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import main
from backend.app.main import app

MOCK_READ_PAYLOAD = {
    "ngay": 15, "thang": 8, "nam": 1995, "chi_gio": 5, "gioi_tinh": 1,
    "duong_lich": True, "provider": "mock",
}


def _reset_rate_buckets(monkeypatch):
    monkeypatch.setattr(main, "_rate_buckets", {})


def test_health_not_blocked_by_api_key(monkeypatch):
    monkeypatch.setattr(main, "_API_KEY", "secret")
    client = TestClient(app)
    assert client.get("/api/v1/health").status_code == 200


def test_api_key_required_when_configured(monkeypatch):
    monkeypatch.setattr(main, "_API_KEY", "secret")
    client = TestClient(app)
    wrong = client.post(
        "/api/v1/horoscope/read", json=MOCK_READ_PAYLOAD,
        headers={"X-API-Key": "sai"},
    )
    assert wrong.status_code == 401
    ok = client.post(
        "/api/v1/horoscope/read", json=MOCK_READ_PAYLOAD,
        headers={"X-API-Key": "secret"},
    )
    assert ok.status_code == 200
    assert ok.json()["status"] == "ok"


def test_api_open_when_key_not_configured(monkeypatch):
    monkeypatch.setattr(main, "_API_KEY", "")
    _reset_rate_buckets(monkeypatch)
    monkeypatch.setattr(main, "_RATE_LIMIT_PER_MIN", 10)
    client = TestClient(app)
    res = client.post("/api/v1/horoscope/read", json=MOCK_READ_PAYLOAD)
    assert res.status_code == 200


def test_rate_limit_blocks_excess_horoscope_calls(monkeypatch):
    monkeypatch.setattr(main, "_API_KEY", "")
    _reset_rate_buckets(monkeypatch)
    monkeypatch.setattr(main, "_RATE_LIMIT_PER_MIN", 2)
    client = TestClient(app)
    assert client.post("/api/v1/horoscope/read", json=MOCK_READ_PAYLOAD).status_code == 200
    assert client.post("/api/v1/horoscope/read", json=MOCK_READ_PAYLOAD).status_code == 200
    third = client.post("/api/v1/horoscope/read", json=MOCK_READ_PAYLOAD)
    assert third.status_code == 429
    # Endpoint không thuộc horoscope không bị rate limit chặn
    assert client.get("/api/v1/stats").status_code in (200, 500)


def test_cors_echoes_configured_origin():
    client = TestClient(app)
    res = client.get("/api/v1/health", headers={"Origin": "http://localhost:8501"})
    assert res.headers.get("access-control-allow-origin") == "http://localhost:8501"


def test_cors_does_not_echo_unknown_origin():
    client = TestClient(app)
    res = client.get("/api/v1/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in res.headers
