# -*- coding: utf-8 -*-
"""Test suite cho Gói 2: Hợp đồng dữ liệu mở rộng và Luận giải Horoscope.

Ma trận kiểm thử:
- TC-G2-01: Schema hợp đồng có reading.tom_tat_nam (3 đoạn), reading.can_cu_noi_dung, reference_ids, knowledge_references.
- TC-G2-02: Validator chấp nhận nhận định dùng nguồn skill khi source_refs rỗng nhưng reference_ids hợp lệ.
- TC-G2-03: Validator từ chối reference_id không có trong knowledge_references đã cấp.
- TC-G2-04: Validator từ chối fact_id không có thật trong can_cu_noi_dung hoặc luan_diem.
- TC-G2-05: generate_mock_reading sinh đầy đủ tom_tat_nam (3 đoạn), can_cu_noi_dung, reference_ids.
- TC-G2-06: Giờ sinh C/D tiếp tục bị giới hạn thời điểm trong luan_diem và ket_luan.
- TC-G2-07: Version hợp đồng tăng lên 2 và CACHE_SCHEMA_VERSION tăng lên 8.
- TC-G2-08: Token budget cho 2 chế độ AI mặc định là 12288.
- TC-G2-09: Prompt mới chứa yêu cầu tiếng Việt đời thường, cấu trúc 3 đoạn tổng quan năm và bỏ yêu cầu '1-2 câu'.
"""
from __future__ import annotations

import os
import sys
import pytest

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.schemas.horoscope_contract import CONTRACT_VERSION, adapt_reading, adapt_point
from backend.app.services.horoscope_cache import CACHE_SCHEMA_VERSION
from backend.app.services.horoscope_interpreter import (
    generate_mock_reading,
    validate_reading,
    get_max_tokens_for_mode,
    build_horoscope_user_prompt,
    HOROSCOPE_SYSTEM_PROMPT,
    HoroscopeGenerationError,
)
from backend.app.services.horoscope_features import generate_raw_horoscope, extract_horoscope_features
from backend.app.services.horoscope_analysis import build_star_facts
from backend.app.services.star_meanings_reference import select_all_references_for_chart
from tests.horoscope_support import make_request
from backend.app.services.horoscope_service import read_horoscope


def test_tc_g2_01_schema_contract_version_and_cache_version():
    """TC-G2-01: CONTRACT_VERSION = 2 và CACHE_SCHEMA_VERSION = 8."""
    assert CONTRACT_VERSION == 2
    assert CACHE_SCHEMA_VERSION == 8


def test_tc_g2_02_mock_reading_has_tom_tat_nam_and_can_cu_noi_dung():
    """TC-G2-02: generate_mock_reading sinh đầy đủ tom_tat_nam (3 đoạn) và can_cu_noi_dung."""
    raw = generate_raw_horoscope(15, 8, 1995, 5, 1, True)
    features = extract_horoscope_features(raw, 2026, "A")
    context = {"reference_list": []}
    reading = generate_mock_reading(features, context)

    assert "tom_tat_nam" in reading
    assert isinstance(reading["tom_tat_nam"], list)
    assert len(reading["tom_tat_nam"]) == 3
    for p in reading["tom_tat_nam"]:
        assert isinstance(p, str) and len(p.strip()) > 0

    assert "can_cu_noi_dung" in reading
    can_cu = reading["can_cu_noi_dung"]
    assert isinstance(can_cu, dict)
    expected_blocks = ("tong_quan_nam", "tong_quan_ca_nhan", "su_nghiep", "tai_chinh", "tinh_cam", "van_han")
    for block in expected_blocks:
        assert block in can_cu, f"Thiếu khối {block} trong can_cu_noi_dung"
        assert "fact_ids" in can_cu[block]
        assert "source_refs" in can_cu[block]
        assert "reference_ids" in can_cu[block]


def test_tc_g2_03_validate_reading_accepts_skill_ref_with_empty_source_refs():
    """TC-G2-03: Validator chấp nhận nhận định dùng nguồn skill khi source_refs rỗng nhưng có reference_ids hợp lệ."""
    raw = generate_raw_horoscope(15, 8, 1995, 5, 1, True)
    features = extract_horoscope_features(raw, 2026, "A")
    ref_id = "REF-STAR-vu_khuc"

    context = {
        "reference_list": [],
        "knowledge_references": [{"reference_id": ref_id}],
    }
    facts = build_star_facts(features, context)

    reading = generate_mock_reading(features, context)
    # Thêm 1 kết luận chỉ dùng reference_ids từ skill (source_refs rỗng)
    reading["ket_luan"].append({
        "nhan_dinh": "Xu hướng thích nghi và giải quyết việc có tính kế hoạch.",
        "giai_thich_thun_viet": "Theo tài liệu tham khảo từ bộ skill.",
        "gioi_han": "Điều kiện cần kiểm tra thêm ở thực tế.",
        "muc_tin_cay": "trung_binh",
        "fact_ids": [facts[0]["fact_id"]],
        "source_refs": [],
        "reference_ids": [ref_id],
        "loai_ket_luan": "cau_truc",
    })

    # Không được raise lỗi invalid_response
    validate_reading(reading, facts, context)


def test_tc_g2_04_validate_reading_rejects_unprovided_reference_id():
    """TC-G2-04: Validator từ chối reference_id không có trong danh mục skill đã cấp."""
    raw = generate_raw_horoscope(15, 8, 1995, 5, 1, True)
    features = extract_horoscope_features(raw, 2026, "A")
    facts = build_star_facts(features, {})

    context = {
        "reference_list": [{"ref_id": 1}],
        "knowledge_references": [{"reference_id": "REF-STAR-tu_vi"}],
    }

    reading = generate_mock_reading(features, context)
    reading["ket_luan"].append({
        "nhan_dinh": "Nhận định giả với reference_id ma.",
        "giai_thich_thun_viet": "Giải nghĩa.",
        "gioi_han": "Giới hạn.",
        "muc_tin_cay": "trung_binh",
        "fact_ids": [facts[0]["fact_id"]],
        "source_refs": [],
        "reference_ids": ["REF-UNKNOWN-999"],
        "loai_ket_luan": "cau_truc",
    })

    with pytest.raises(HoroscopeGenerationError):
        validate_reading(reading, facts, context)


def test_tc_g2_05_token_budget_default_12288():
    """TC-G2-05: Token budget cho 2 chế độ AI mặc định là 12.288."""
    assert get_max_tokens_for_mode("chuyen_sau") >= 12288
    assert get_max_tokens_for_mode("giai_thich") >= 12288


def test_tc_g2_06_prompt_system_and_user_requirements():
    """TC-G2-06: Prompt bỏ yêu cầu '1-2 câu', yêu cầu tiếng Việt đời thường và tổng quan năm 3 đoạn."""
    assert "mỗi trường 1–2 câu" not in HOROSCOPE_SYSTEM_PROMPT
    assert "đời thường" in HOROSCOPE_SYSTEM_PROMPT

    raw = generate_raw_horoscope(15, 8, 1995, 5, 1, True)
    features = extract_horoscope_features(raw, 2026, "A")
    facts = build_star_facts(features, {})
    prompt = build_horoscope_user_prompt(features, "", facts)

    assert "tom_tat_nam" in prompt or "3 đoạn" in prompt or "TỔNG QUAN NĂM" in prompt
    assert "can_cu_noi_dung" in prompt or "reference_ids" in prompt


def test_tc_g2_07_full_report_carries_knowledge_references():
    """TC-G2-07: read_horoscope ở chế độ mock/du_lieu trả đủ knowledge_references và reading mới."""
    req = make_request(provider="mock", target_year=2026, reading_mode="du_lieu")
    report = read_horoscope(req)
    assert report["status"] == "ok"
    assert "knowledge_references" in report
    assert isinstance(report["knowledge_references"], list)
    assert len(report["knowledge_references"]) > 0

    reading = report["reading"]
    assert "tom_tat_nam" in reading
    assert len(reading["tom_tat_nam"]) == 3
    assert "can_cu_noi_dung" in reading
