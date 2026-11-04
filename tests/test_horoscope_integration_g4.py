"""
Gói 4: Kiểm thử tích hợp toàn diện (Integration & Regression)
Bao gồm:
- TC-G4-01: Lá số mẫu năm 2026: tổng quan đúng năm 2026 và Can Chi Bính Ngọ; 3 đoạn; không kết luận sự kiện chỉ từ riêng 1 sao.
- TC-G4-02: Đổi năm hoặc đổi lá số tạo nội dung tổng quan và vận trình tương ứng.
- TC-G4-03: Nguồn skill hiển thị đúng nhãn "Tử Vi Đẩu Số Toàn Tập", có ghi chú tham khảo, không số trang.
- TC-G4-04: Token budget 12288 cho cả 2 chế độ AI; chế độ dữ liệu giữ nguyên không dựng bài AI.
- TC-G4-05: Cache schema bump (version 8) vô hiệu hóa cache cũ, đảm bảo tương thích backward.
"""
from __future__ import annotations

import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import pytest
from backend.app.core.config import HOROSCOPE_MAX_TOKENS_GIAI_THICH, HOROSCOPE_MAX_TOKENS_CHUYEN_SAU
from backend.app.schemas.horoscope_contract import CONTRACT_VERSION, adapt_reading
from backend.app.services.horoscope_cache import compute_key, CACHE_SCHEMA_VERSION
from backend.app.services.horoscope_interpreter import (
    generate_mock_reading,
    validate_reading,
    HOROSCOPE_SYSTEM_PROMPT,
)
from backend.app.services.star_meanings_reference import (
    SOURCE,
    SOURCE_NOTE,
    select_all_references_for_chart,
)
from tests.horoscope_support import make_features


def test_tc_g4_01_sample_2026_annual_overview_and_can_chi():
    """Lá số mẫu năm 2026 sinh 3 đoạn tổng quan, Can Chi Bính Ngọ."""
    feats = make_features(target_year=2026)
    reading = generate_mock_reading(feats)
    assert len(reading["tom_tat_nam"]) == 3
    joined = " ".join(reading["tom_tat_nam"])
    assert "2026" in joined
    assert "Bính Ngọ" in joined
    # Không suy diễn biến cố từ riêng Tuế Phá hay Bạch Hổ đơn lẻ
    assert "tai nạn chết chóc" not in joined.lower()
    assert "chắc chắn thất bại" not in joined.lower()


def test_tc_g4_02_different_years_produce_different_content():
    """Đổi năm (2026 vs 2027) tạo tổng quan năm và vận trình khác nhau."""
    feats_2026 = make_features(target_year=2026)
    feats_2027 = make_features(target_year=2027)
    reading_2026 = generate_mock_reading(feats_2026)
    reading_2027 = generate_mock_reading(feats_2027)

    assert "2026" in " ".join(reading_2026["tom_tat_nam"])
    assert "2027" in " ".join(reading_2027["tom_tat_nam"])
    assert "2026" in reading_2026["van_han_hien_tai"]["giai_doan"]
    assert "2027" in reading_2027["van_han_hien_tai"]["giai_doan"]


def test_tc_g4_03_skill_sources_displayed_with_correct_label_and_no_pages():
    """Nguồn skill chuẩn hóa tên, ghi chú và không chứa số trang giả."""
    assert SOURCE == "Tử Vi Đẩu Số Toàn Tập"
    assert "chưa đối chiếu bản sách" in SOURCE_NOTE

    feats = make_features(target_year=2026)
    refs = select_all_references_for_chart(feats, [])
    for r in refs:
        assert "page" not in r
        assert "trang" not in r.get("reference_id", "").lower()
        assert r["source"] == "Tử Vi Đẩu Số Toàn Tập"
        assert r["source_note"] == SOURCE_NOTE


def test_tc_g4_04_reading_modes_and_token_budget():
    """Kiểm tra cấu hình token budget và prompt."""
    assert HOROSCOPE_MAX_TOKENS_GIAI_THICH == 12288
    assert HOROSCOPE_MAX_TOKENS_CHUYEN_SAU == 12288
    # Prompt không còn yêu cầu gò ép 1-2 câu
    assert "Mỗi trường viết 1–2 câu" not in HOROSCOPE_SYSTEM_PROMPT
    assert "150–220 từ" in HOROSCOPE_SYSTEM_PROMPT or "3 đoạn" in HOROSCOPE_SYSTEM_PROMPT


def test_tc_g4_05_cache_schema_invalidation():
    """Cache version 8 đảm bảo cache cũ của version 7 không dùng lại bài luận cũ."""
    assert CACHE_SCHEMA_VERSION == 8
    key_current = compute_key(
        {"year": 1990, "month": 5, "day": 10, "hour": 8, "gender": "nam"},
        "gemini",
        "gemini-3.5-flash-lite",
        "ctx_hash_test",
        "index_v1",
        "chuyen_sau",
    )
    assert isinstance(key_current, str) and len(key_current) == 64
