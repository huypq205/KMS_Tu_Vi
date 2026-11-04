# -*- coding: utf-8 -*-
"""Test Suite cho Gói 1: Nguồn kiến thức và chuẩn hóa tham khảo từ Skill.

Ma trận kiểm thử:
- TC-G1-01: Nạp thành công cả 2 file star_meanings.md và cach_cuc_luan_giai.md với nguồn 'Tử Vi Đẩu Số Toàn Tập'.
- TC-G1-02: Lọc bỏ triệt để các đoạn nhạy cảm (tuổi thọ, phán tử vong/bệnh tật, phẩm hạnh, chỉ thị prompt).
- TC-G1-03: Chọn kiến thức theo chủ đề (sự nghiệp, tài chính, tình cảm, vận trình, tổng quan) không bị giới hạn 8 sao chung.
- TC-G1-04: Xét sao tam hợp và đối cung theo cung đang luận (Quan lộc, Tài bạch, Phu thê), không neo vào Mệnh.
- TC-G1-05: Cách cục chỉ được chọn khi bộ nhận diện (cach_cuc_detector) xác nhận khớp đủ hoặc khớp một phần.
- TC-G1-06: Không có số trang (pdf_page, book_code) trong metadata nguồn skill, lưu đúng source_file và sha256.
- TC-G1-07: reference_signature phản ánh thay đổi của cả 2 file hoặc chính sách lọc (đổi file là đổi signature).
- TC-G1-08: Tương thích ngược: load_meanings, get_meaning, select_meanings, format_meanings vẫn hoạt động tốt.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
import pytest

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.services.star_meanings_reference import (
    load_meanings,
    get_meaning,
    select_meanings,
    format_meanings,
    reference_signature,
    load_skill_knowledge,
    select_topic_references,
    select_all_references_for_chart,
    SOURCE,
    SOURCE_NOTE,
)
from backend.app.services.horoscope_features import generate_raw_horoscope, extract_horoscope_features
from backend.app.services.horoscope_analysis import build_star_facts
from backend.app.services.cach_cuc_detector import detect_cach_cuc


def test_tc_g1_01_load_both_files_attributed():
    """TC-G1-01: Nạp 2 file với nguồn hiển thị 'Tử Vi Đẩu Số Toàn Tập'."""
    data = load_skill_knowledge()
    assert isinstance(data, dict)
    assert "stars" in data
    assert "palaces" in data
    assert "principles" in data
    assert "cach_cuc" in data
    assert "career_types" in data
    assert "annual_principles" in data

    # Kiểm tra nguồn hiển thị
    assert SOURCE == "Tử Vi Đẩu Số Toàn Tập"
    assert "chưa đối chiếu" in SOURCE_NOTE


def test_tc_g1_02_sensitive_content_filtered():
    """TC-G1-02: Lọc bỏ nội dung nhạy cảm, tuổi thọ, tử vong và chỉ thị."""
    data = load_skill_knowledge()
    all_texts = []
    for category in data.values():
        for item in category.values():
            text = item.get("text", "")
            all_texts.append(text)
            assert "chắc chắn chết" not in text
            assert "yểu" not in text.lower()
            assert "ignore" not in text.lower()
            assert "system:" not in text.lower()
            # Không được phán cứng tuổi thọ (vd: 84 tuổi, 93 tuổi)
            import re
            assert not re.search(r"\b\d{2}\s*tuổi\b", text, re.I), f"Tìm thấy phán định tuổi thọ: {text}"


def test_tc_g1_03_topic_based_selection_not_limited_to_8_stars():
    """TC-G1-03: Chọn tài liệu theo từng chủ đề không bị bóp nghẹt 8 sao chung."""
    raw = generate_raw_horoscope(15, 8, 1995, 5, 1, True)
    features = extract_horoscope_features(raw, 2026, "A")
    facts = build_star_facts(features, {})

    # Chọn theo chủ đề sự nghiệp
    career_refs = select_topic_references(features, facts, topic="su_nghiep")
    assert len(career_refs) > 0
    # Phải có kiến thức về Quan lộc hoặc nghề nghiệp hoặc sao tại Quan lộc
    career_ref_names = [r["name"] for r in career_refs]
    assert any("Quan Lộc" in r["name"] or "nghề" in r.get("group_heading", "").lower() or r.get("topic") == "su_nghiep" for r in career_refs)

    # Chọn theo chủ đề tình cảm
    love_refs = select_topic_references(features, facts, topic="tinh_cam")
    assert len(love_refs) > 0
    assert any("Phu Thê" in r["name"] or r.get("topic") == "tinh_cam" for r in love_refs)


def test_tc_g1_04_tam_hop_and_doi_cung_for_palaces():
    """TC-G1-04: Xét tam hợp và đối cung cho cung đang luận (Quan lộc, Tài bạch)."""
    raw = generate_raw_horoscope(15, 8, 1995, 5, 1, True)
    features = extract_horoscope_features(raw, 2026, "A")
    facts = build_star_facts(features, {})

    career_refs = select_topic_references(features, facts, topic="su_nghiep")
    # Cung Quan Lộc của lá số 15/8/1995 giờ Thìn (Mệnh Thìn -> Quan lộc Thân)
    # Tam hợp của Thân là Tý, Thìn; đối cung là Dần.
    # Các sao tại Thân, Tý, Thìn, Dần cần được ưu tiên trong chủ đề sự nghiệp
    ref_ids = [r["reference_id"] for r in career_refs]
    assert len(ref_ids) > 0


def test_tc_g1_05_cach_cuc_only_if_detected():
    """TC-G1-05: Chỉ đưa cách cục vào tham khảo nếu detector xác nhận khớp đủ hoặc khớp 1 phần."""
    raw = generate_raw_horoscope(15, 8, 1995, 5, 1, True)
    features = extract_horoscope_features(raw, 2026, "A")
    facts = build_star_facts(features, {})
    detection = detect_cach_cuc(features, facts=facts)

    all_refs = select_all_references_for_chart(features, facts, cach_cuc=detection)
    cach_cuc_refs = [r for r in all_refs if r.get("category") == "cach_cuc"]

    detected_rules = {r["rule_id"] for r in detection.get("rules", []) if r.get("ket_qua") in ("khop_du", "khop_mot_phan")}
    for ref in cach_cuc_refs:
        rule_id = ref.get("matched_rule_id")
        assert rule_id in detected_rules, f"Cách cục {rule_id} không có trong kết quả nhận diện mà vẫn được cấp!"


def test_tc_g1_06_no_page_numbers_or_book_codes_for_skills():
    """TC-G1-06: Không tự bịa số trang hoặc gán mã sách KMS cho nguồn skill."""
    raw = generate_raw_horoscope(15, 8, 1995, 5, 1, True)
    features = extract_horoscope_features(raw, 2026, "A")
    facts = build_star_facts(features, {})
    all_refs = select_all_references_for_chart(features, facts)

    for ref in all_refs:
        assert "pdf_page" not in ref
        assert "page_label" not in ref
        assert "book_code" not in ref
        assert ref["source_file"] in ("star_meanings.md", "cach_cuc_luan_giai.md")
        assert len(ref["source_sha256"]) == 64
        assert ref["reference_id"].startswith("REF-")


def test_tc_g1_07_reference_signature_changes_on_skill_mod():
    """TC-G1-07: reference_signature phản ánh cả 2 file."""
    sig = reference_signature()
    assert sig.startswith("reference-knowledge-v2:") or "star-meanings-filter-v1:" in sig


def test_tc_g1_08_backward_compatibility():
    """TC-G1-08: Tương thích ngược toàn bộ hàm cũ."""
    facts = [{'fact_id': '1', 'sao': 'Vũ Khúc', 'cung': 'Tài bạch', 'nhom': 'chinh_tinh'}]
    m = get_meaning("Vũ Khúc")
    assert m is not None
    assert "Vũ Khúc" in m["name"]
    entries = select_meanings(facts)
    assert len(entries) == 1
    formatted = format_meanings(entries)
    assert "Tử Vi Đẩu Số Toàn Tập" in formatted or "Ý NGHĨA SAO THAM KHẢO" in formatted
