"""T1: độ tin cậy dữ liệu giờ sinh (input_confidence A–D) end-to-end."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from backend.app.schemas.horoscope import HoroscopeAskRequest, HoroscopeRequest
from backend.app.services import horoscope_interpreter as interpreter
from backend.app.services.horoscope_analysis import build_star_facts
from backend.app.services.horoscope_confidence import (
    LOW_CONFIDENCE_CAVEAT,
    check_ask_input_confidence,
    check_input_confidence,
)
from backend.app.services.horoscope_features import extract_horoscope_features
from backend.app.services.horoscope_interpreter import (
    build_horoscope_user_prompt,
    generate_mock_reading,
    interpret_horoscope,
)
from backend.app.services.horoscope_rag_bridge import (
    format_context_for_prompt,
    retrieve_horoscope_context,
)
from tests.horoscope_support import (
    gemini_response,
    make_features,
    make_raw,
    make_request,
    valid_reading,
)


def _reading_with_caveat(features: dict, fact_count: int = 3, top_k: int = 2) -> dict:
    context = retrieve_horoscope_context(features, top_k)
    facts = build_star_facts(features, context)
    reading = valid_reading(facts, "2026 Bính Ngọ", fact_count=fact_count)
    for point in reading["luan_diem"]:
        point["gioi_han"] += " " + LOW_CONFIDENCE_CAVEAT
    return reading


# 1. Schema -----------------------------------------------------------------

def test_request_defaults_and_enum_validation():
    req = HoroscopeRequest(ngay=15, thang=8, nam=1995, chi_gio=5)
    assert req.input_confidence == "A"
    assert req.gio_sinh_source == "memory"
    assert req.gio_sinh_error_phut is None

    ask = HoroscopeAskRequest(ngay=15, thang=8, nam=1995, chi_gio=5, question="Năm nay thế nào?")
    assert ask.input_confidence == "A"
    assert ask.gio_sinh_source == "memory"
    assert ask.gio_sinh_error_phut is None

    with pytest.raises(ValidationError):
        HoroscopeRequest(ngay=15, thang=8, nam=1995, chi_gio=5, input_confidence="E")
    with pytest.raises(ValidationError):
        HoroscopeRequest(ngay=15, thang=8, nam=1995, chi_gio=5, gio_sinh_error_phut=-1)
    with pytest.raises(ValidationError):
        HoroscopeAskRequest(ngay=15, thang=8, nam=1995, chi_gio=5, question="x", gio_sinh_source="forum")


# 2. Feature propagation ----------------------------------------------------

def test_features_propagate_confidence_metadata():
    features = extract_horoscope_features(make_raw(), 2026, "C", "estimate", 90)
    basic = features["thong_tin_co_ban"]
    assert basic["input_confidence"] == "C"
    assert basic["gio_sinh_source"] == "estimate"
    assert basic["gio_sinh_error_phut"] == 90

    default = extract_horoscope_features(make_raw(), 2026)
    assert default["thong_tin_co_ban"]["input_confidence"] == "A"
    assert default["thong_tin_co_ban"]["gio_sinh_source"] == "memory"
    assert default["thong_tin_co_ban"]["gio_sinh_error_phut"] is None


# 3. Prompt -----------------------------------------------------------------

def test_prompt_carries_confidence_and_cd_constraint():
    features = make_features(
        2026, input_confidence="C", gio_sinh_source="estimate", gio_sinh_error_phut=90,
    )
    prompt = build_horoscope_user_prompt(features, "nguồn thử")
    assert "Độ tin cậy giờ sinh: C" in prompt
    assert "±90 phút" in prompt
    assert "RÀNG BUỘC DỮ LIỆU" in prompt
    assert LOW_CONFIDENCE_CAVEAT in prompt

    prompt_a = build_horoscope_user_prompt(make_features(2026), "nguồn thử")
    assert "Độ tin cậy giờ sinh: A" in prompt_a
    assert "RÀNG BUỘC DỮ LIỆU" not in prompt_a


def test_ask_prompt_carries_confidence():
    from backend.app.services.horoscope_ask import build_ask_user_prompt

    features = make_features(2026, input_confidence="D")
    req = HoroscopeAskRequest(ngay=15, thang=8, nam=1995, chi_gio=5, question="Năm nay thế nào?")
    prompt = build_ask_user_prompt(features, [], [], req, "tong_quan")
    assert "Độ tin cậy giờ sinh: D" in prompt
    assert LOW_CONFIDENCE_CAVEAT in prompt


# 4. Validation C/D ---------------------------------------------------------

def test_check_input_confidence_only_blocks_cd():
    features_a = make_features(2026)
    with_timing = _reading_with_caveat(features_a)
    with_timing["van_han_hien_tai"]["co_hoi_nen_nam_bat"] = "Năm 2026 sẽ kết hôn."
    assert check_input_confidence(with_timing, features_a) is None

    features_d = make_features(2026, input_confidence="D")
    assert check_input_confidence(with_timing, features_d)

    clean = _reading_with_caveat(features_d)
    assert check_input_confidence(clean, features_d) is None

    missing_caveat = _reading_with_caveat(features_d)
    missing_caveat["luan_diem"][0]["gioi_han"] = "Chưa xác minh điều kiện tổ hợp."
    assert check_input_confidence(missing_caveat, features_d)


def test_check_ask_input_confidence_rejects_timing_claim():
    features = make_features(2026, input_confidence="C")
    answer = {
        "tra_loi": "Năm 2026 sẽ kết hôn.",
        "muc_do_can_cu": "dau_hieu_ro",
        "giai_thich_thun_viet": "Cung Phu thê nói về quan hệ tình cảm.",
        "fact_ids": ["1"],
        "source_refs": [1],
        "gioi_han": LOW_CONFIDENCE_CAVEAT,
    }
    assert check_ask_input_confidence(answer, features)
    answer["tra_loi"] = "Cấu trúc cho thấy xu hướng thận trọng khi chọn người đồng hành."
    assert check_ask_input_confidence(answer, features) is None
    answer["gioi_han"] = "Chưa kiểm duyệt thủ công."
    assert check_ask_input_confidence(answer, features)


# 5. Mock reading / mock ask ------------------------------------------------

def test_mock_reading_marks_cd_limits():
    features = make_features(2026, input_confidence="C")
    reading = generate_mock_reading(features)
    assert reading["ket_luan"]
    assert all(LOW_CONFIDENCE_CAVEAT in p["gioi_han"] for p in reading["ket_luan"])
    assert LOW_CONFIDENCE_CAVEAT in reading["van_han_hien_tai"]["thach_thuc_can_can_trong"]
    assert check_input_confidence(reading, features) is None


def test_mock_ask_marks_cd_limit():
    from backend.app.services.horoscope_ask import mock_ask_answer

    features = make_features(2026, input_confidence="D")
    answer = mock_ask_answer(features, [], [], "tinh_cam", "Năm nay có người tìm hiểu không?")
    assert LOW_CONFIDENCE_CAVEAT in answer["gioi_han"]
    assert check_ask_input_confidence(answer, features) is None


# 6. Retry flow -------------------------------------------------------------

def test_interpret_retries_when_cd_reading_has_timing_claim():
    features = make_features(2026, input_confidence="C")
    context = retrieve_horoscope_context(features, 2)
    facts = build_star_facts(features, context)
    bad = valid_reading(facts, "2026 Bính Ngọ", fact_count=3)
    for point in bad["luan_diem"]:
        point["gioi_han"] += " " + LOW_CONFIDENCE_CAVEAT
    bad["van_han_hien_tai"]["co_hoi_nen_nam_bat"] = "Năm 2026 sẽ kết hôn."
    good = _reading_with_caveat(features)

    with patch.object(interpreter, "GEMINI_API_KEY", "test-key"), patch(
        "backend.app.services.horoscope_interpreter.requests.post",
        side_effect=[gemini_response(bad), gemini_response(good)],
    ) as post:
        reading = interpret_horoscope(features, format_context_for_prompt(context), "auto", context)

    assert post.call_count == 2
    assert reading["_generation"]["attempts"] == 2
    assert reading["_generation"]["specificity_low"] is False
    assert check_input_confidence(reading, features) is None


def test_cd_timing_claim_after_retry_is_never_returned_as_low_specificity():
    features = make_features(2026, input_confidence='D')
    bad = _reading_with_caveat(features)
    bad['van_han_hien_tai']['co_hoi_nen_nam_bat'] = 'Năm 2026 sẽ kết hôn.'
    context = retrieve_horoscope_context(features, 2)
    with patch.object(interpreter, 'GEMINI_API_KEY', 'test-key'), patch.object(
        interpreter, 'HOROSCOPE_FALLBACK_MODELS', (),
    ), patch('backend.app.services.horoscope_interpreter.requests.post',
             side_effect=[gemini_response(bad), gemini_response(bad)]):
        result = interpret_horoscope(features, format_context_for_prompt(context), 'auto', context)
    assert result['_generation']['is_mock'] is True
    assert check_input_confidence(result, features) is None


def test_cd_rejects_explicit_temporal_conclusion_type():
    features = make_features(2026, input_confidence='C')
    reading = _reading_with_caveat(features)
    reading['luan_diem'][0]['loai_ket_luan'] = 'thoi_diem'
    assert check_input_confidence(reading, features)


# 7. Cache isolation --------------------------------------------------------

def test_cache_does_not_mix_confidence_levels():
    from backend.app.services import horoscope_cache
    from backend.app.services.horoscope_service import read_horoscope

    horoscope_cache.clear()
    req_a = make_request(provider="auto", target_year=2026, top_k_per_topic=4)
    req_c = make_request(
        provider="auto", target_year=2026, top_k_per_topic=4,
        input_confidence="C", gio_sinh_source="estimate", gio_sinh_error_phut=90,
    )
    reading_a = _reading_with_caveat(make_features(2026), top_k=4)
    reading_c = _reading_with_caveat(make_features(2026, input_confidence="C"), top_k=4)
    try:
        with patch.object(interpreter, "GEMINI_API_KEY", "test-key"), patch(
            "backend.app.services.horoscope_interpreter.requests.post",
            side_effect=[gemini_response(reading_a), gemini_response(reading_c)],
        ) as post:
            first = read_horoscope(req_a)
            second = read_horoscope(req_c)
        assert post.call_count == 2
        assert first["meta"]["cached"] is False
        assert second["meta"]["cached"] is False
        assert second["thong_tin_co_ban"]["input_confidence"] == "C"
    finally:
        horoscope_cache.clear()


# 8. UI ---------------------------------------------------------------------

def test_ui_sends_confidence_and_shows_cd_warning():
    from streamlit.testing.v1 import AppTest
    from backend.app.main import horoscope_read

    app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20,
    ).run()
    assert not app.exception

    app.selectbox(key="input_confidence").set_value("C")
    app.selectbox(key="gio_sinh_source").set_value("estimate")
    app.number_input(key="gio_sinh_error").set_value(90)

    payload = horoscope_read(make_request(
        provider="mock", input_confidence="C", gio_sinh_source="estimate", gio_sinh_error_phut=90,
    ))
    payload["ho_ten"] = "Lê An"
    response = Mock()
    response.iter_lines.return_value = iter([
        json.dumps({"event": "prepared", "report": payload}),
        json.dumps({"event": "result", "report": payload}),
    ])
    with patch("requests.post", return_value=response) as post:
        app.sidebar.button[0].click().run()
        assert post.call_count == 1
        sent = post.call_args.kwargs["json"]

    assert sent["input_confidence"] == "C"
    assert sent["gio_sinh_source"] == "estimate"
    assert sent["gio_sinh_error_phut"] == 90
    warnings = " ".join(item.value for item in app.warning)
    assert "Dữ liệu giờ sinh chưa chắc chắn (mức C)" in warnings
    assert not app.exception
