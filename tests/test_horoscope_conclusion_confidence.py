"""T2: bậc tin cậy per kết luận (`muc_tin_cay`) và cấm phần trăm độ tin cậy."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from backend.app.services import horoscope_interpreter as interpreter
from backend.app.services.horoscope_analysis import build_star_facts
from backend.app.services.horoscope_interpreter import (
    CONCLUSION_CONFIDENCE_LEVELS,
    HOROSCOPE_SYSTEM_PROMPT,
    build_horoscope_user_prompt,
    check_conclusion_confidence,
    generate_mock_reading,
    interpret_horoscope,
    response_schema,
)
from backend.app.services.horoscope_rag_bridge import (
    format_context_for_prompt,
    retrieve_horoscope_context,
)
from tests.horoscope_support import gemini_response, make_features, valid_reading


def _reading(features: dict, fact_count: int = 3):
    context = retrieve_horoscope_context(features, 2)
    facts = build_star_facts(features, context)
    return valid_reading(facts, "2026 Bính Ngọ", fact_count=fact_count), facts, context


# 1. Schema / prompt ---------------------------------------------------------

def test_response_schema_requires_confidence_enum():
    schema = response_schema()
    for key in ("luan_diem", "ket_luan"):
        item = schema["properties"][key]["items"]
        assert item["properties"]["muc_tin_cay"]["enum"] == list(CONCLUSION_CONFIDENCE_LEVELS)
        assert "muc_tin_cay" in item["required"]


def test_prompt_defines_four_levels_and_bans_percent():
    for level in CONCLUSION_CONFIDENCE_LEVELS:
        assert level in HOROSCOPE_SYSTEM_PROMPT
    assert "phần trăm" in HOROSCOPE_SYSTEM_PROMPT

    prompt = build_horoscope_user_prompt(make_features(2026), "nguồn thử")
    assert "muc_tin_cay" in prompt
    assert "phần trăm" in prompt


# 2. Validator ---------------------------------------------------------------

def test_valid_reading_with_labels_passes():
    reading, _, _ = _reading(make_features(2026))
    assert check_conclusion_confidence(reading) is None


def test_missing_or_unknown_label_is_rejected():
    reading, _, _ = _reading(make_features(2026))
    reading["luan_diem"][0].pop("muc_tin_cay")
    assert check_conclusion_confidence(reading)
    reading["luan_diem"][0]["muc_tin_cay"] = "kha_nang_cao"
    assert check_conclusion_confidence(reading)


def test_confidence_level_must_match_fact_count():
    reading, facts, _ = _reading(make_features(2026))
    point = reading["luan_diem"][0]
    point["muc_tin_cay"] = "rat_manh"  # mới có 1 fact_id
    assert "fact_id" in check_conclusion_confidence(reading)

    point["fact_ids"] = [f["fact_id"] for f in facts[:3]]
    assert check_conclusion_confidence(reading) is None


def test_confidence_counts_distinct_facts_and_strong_requires_three():
    reading, facts, _ = _reading(make_features(2026))
    point = reading['luan_diem'][0]
    point.update(muc_tin_cay='rat_manh', fact_ids=[facts[0]['fact_id']] * 3)
    assert check_conclusion_confidence(reading)
    point.update(muc_tin_cay='manh', fact_ids=[f['fact_id'] for f in facts[:2]])
    assert check_conclusion_confidence(reading)
    point['fact_ids'] = [f['fact_id'] for f in facts[:3]]
    assert check_conclusion_confidence(reading) is None


def test_percent_confidence_is_rejected():
    reading, _, _ = _reading(make_features(2026))
    for text in ("Có 85% khả năng thuận lợi.", "Có 85 % khả năng thuận lợi.", "Có 12,5% khả năng."):
        reading["luan_diem"][0]["nhan_dinh"] = text
        assert check_conclusion_confidence(reading), text
    reading["luan_diem"][0]["nhan_dinh"] = "Có nhiều dấu hiệu thuận lợi."
    assert check_conclusion_confidence(reading) is None


# 3. Retry flow --------------------------------------------------------------

def test_missing_label_retries_once_with_instruction():
    features = make_features(2026)
    reading, _, context = _reading(features)
    missing = json.loads(json.dumps(reading))
    for point in missing["luan_diem"]:
        point.pop("muc_tin_cay")

    with patch.object(interpreter, "GEMINI_API_KEY", "test-key"), patch.object(
        interpreter, "HOROSCOPE_FALLBACK_MODELS", (),
    ), patch(
        "backend.app.services.horoscope_interpreter.requests.post",
        side_effect=[gemini_response(missing), gemini_response(reading)],
    ) as post:
        result = interpret_horoscope(features, format_context_for_prompt(context), "auto", context)

    assert post.call_count == 2
    assert "muc_tin_cay" in post.call_args_list[1].kwargs["json"]["contents"][0]["parts"][0]["text"]
    assert result["_generation"]["actual_provider"] == "gemini"
    assert check_conclusion_confidence(result) is None


def test_missing_label_after_retry_falls_back_to_mock():
    features = make_features(2026)
    reading, _, context = _reading(features)
    missing = json.loads(json.dumps(reading))
    for point in missing["luan_diem"]:
        point.pop("muc_tin_cay")

    with patch.object(interpreter, "GEMINI_API_KEY", "test-key"), patch.object(
        interpreter, "HOROSCOPE_FALLBACK_MODELS", (),
    ), patch(
        "backend.app.services.horoscope_interpreter.requests.post",
        side_effect=[gemini_response(missing), gemini_response(missing)],
    ) as post:
        result = interpret_horoscope(features, format_context_for_prompt(context), "auto", context)

    assert post.call_count == 2
    assert result["_generation"]["is_mock"] is True
    assert result["_generation"]["reason"] == "invalid_response"


# 4. Mock reading ------------------------------------------------------------

def test_mock_reading_labels_every_conclusion():
    features = make_features(2026)
    reading = generate_mock_reading(features)
    assert reading["ket_luan"]
    assert all(point["muc_tin_cay"] in CONCLUSION_CONFIDENCE_LEVELS for point in reading["ket_luan"])
    assert check_conclusion_confidence(reading) is None


# 5. UI ----------------------------------------------------------------------

def _badge_css(level: str) -> str:
    from frontend.horoscope_view import confidence_badge
    return confidence_badge(level)


def test_badge_maps_levels_to_colors():
    assert "conf-rat-manh" in _badge_css("rat_manh")
    assert "conf-manh" in _badge_css("manh")
    assert "conf-trung-binh" in _badge_css("trung_binh")
    assert "conf-yeu" in _badge_css("yeu")
    assert "conf-yeu" in _badge_css("khong_hop_le")


def test_ui_renders_confidence_badge():
    from streamlit.testing.v1 import AppTest
    from backend.app.main import horoscope_read
    from tests.horoscope_support import make_request

    app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20,
    ).run()
    payload = horoscope_read(make_request(provider="mock"))
    payload["ho_ten"] = "Lê An"
    response = Mock()
    response.iter_lines.return_value = iter([
        json.dumps({"event": "prepared", "report": payload}),
        json.dumps({"event": "result", "report": payload}),
    ])
    with patch("requests.post", return_value=response):
        app.sidebar.button[0].click().run()
    assert not app.exception
    rendered = " ".join(item.value for item in app.markdown)
    assert "conf-badge" in rendered
    assert "Tin cậy:" in rendered
