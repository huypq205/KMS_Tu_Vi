"""P1 (Plan_Fix_Mai_Anh_v2): hợp đồng dữ liệu ba mức đọc + migration báo cáo cũ.

- reading_mode tách khỏi provider (schema request).
- Cache có chiều reading_mode; CACHE_SCHEMA_VERSION bump lên 7.
- Adapter 6 nhóm: trường thiếu hiển thị là thiếu (MISSING), không suy đoán;
  danh rỗng giữ nguyên (đã kiểm tra, không tìm thấy) — khác MISSING (chưa có dữ liệu).
- Nghiệm thu: response mẫu cho ba mức, báo cáo cũ, fallback.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.app.schemas.horoscope_contract import (
    CONTRACT_VERSION,
    MISSING,
    READING_MODES,
    adapt_point,
    adapt_reading,
    sample_response,
)
from backend.app.services import horoscope_cache
from backend.app.services.horoscope_service import read_horoscope
from tests.horoscope_support import make_request

# --- Báo cáo cũ (schema trước P1): luan_diem/ket_luan không có rule_ids/chu_de ---
OLD_LUAN_DIEM = {
    "nhan_dinh": "Thiên Cơ tại Mệnh (Tý) cần đối chiếu điều kiện trong nguồn.",
    "gioi_han": "Chỉ nêu điều kiện đã có trong dữ kiện lá số.",
    "muc_tin_cay": "trung_binh",
    "loi_chung_cu": ["toa_thu"],
    "phan_chung": "Không ghi nhận phản chứng trong nguồn đã lấy.",
    "fact_ids": ["sao:0:Thien Co:Menh"],
    "source_refs": [3],
    "loai_ket_luan": "cau_truc",
}
OLD_KET_LUAN = {
    "nhan_dinh": "Thiên Cơ tại Mệnh hướng ngoại, cần đọc cùng cung Quan lộc.",
    "giai_thich_thun_viet": "Chính tinh của cung Mệnh; theo từ điển nghĩa cung trong dữ kiện.",
    "gioi_han": "Chưa kiểm tra điều kiện Tuần/Triệt.",
    "muc_tin_cay": "yeu",
    "fact_ids": ["sao:0:Thien Co:Menh"],
    "source_refs": [],
    "loai_ket_luan": "cau_truc",
}


def _reading_with_ket_luan() -> dict:
    return {
        "tieu_de": "Bài đọc kiểm thử",
        "luan_diem": [dict(OLD_LUAN_DIEM)],
        "ket_luan": [dict(OLD_KET_LUAN)],
    }


# --- P1.TC-01: reading_mode trong schema request, tách khỏi provider ---
def test_reading_mode_default_and_valid_values():
    assert make_request(provider="mock").reading_mode == "chuyen_sau"
    for mode in READING_MODES:
        assert make_request(provider="mock", reading_mode=mode).reading_mode == mode


def test_reading_mode_rejects_unknown_value():
    with pytest.raises(ValidationError):
        make_request(provider="mock", reading_mode="level_x")


def test_reading_mode_is_independent_of_provider():
    # Hai khái niệm độc lập: provider là bộ xử lý, reading_mode là lựa chọn người dùng.
    req = make_request(provider="mock", reading_mode="giai_thich")
    assert req.provider == "mock"
    assert req.reading_mode == "giai_thich"


# --- P1.TC-02: cache có chiều reading_mode + bump schema version ---
def test_cache_key_differs_per_reading_mode():
    birth = {"ngay": 1, "thang": 1, "nam": 1990, "chi_gio": "Tý", "gioi_tinh": "Nam"}
    key_a = horoscope_cache.compute_key(birth, "auto", "model", "ctx", "v1", reading_mode="du_lieu")
    key_b = horoscope_cache.compute_key(birth, "auto", "model", "ctx", "v1", reading_mode="chuyen_sau")
    assert key_a != key_b
    # Cùng reading_mode phải cho cùng khóa (trùng lặp vẫn hit).
    assert key_a == horoscope_cache.compute_key(
        birth, "auto", "model", "ctx", "v1", reading_mode="du_lieu"
    )


def test_cache_schema_version_bumped_for_contract():
    assert horoscope_cache.CACHE_SCHEMA_VERSION == 7


# --- P1.TC-03: meta response mang reading_mode + contract_version (trường hợp fallback/mock) ---
def test_meta_carries_reading_mode_and_contract_version_on_mock_fallback():
    report = read_horoscope(make_request(provider="mock", target_year=2026, reading_mode="du_lieu"))
    assert report["status"] == "ok"
    # provider=mock chính là fallback "không gọi AI" của chế độ du_lieu.
    assert report["meta"]["reading_mode"] == "du_lieu"
    assert report["meta"]["contract_version"] == CONTRACT_VERSION
    assert report["meta"]["actual_provider"] == "mock"
    assert report["meta"]["cached"] is False


# --- P1.TC-04: adapter mục luan_diem — thiếu phải hiển thị là thiếu, không suy đoán ---
def test_adapt_point_luan_diem_marks_missing_not_invented():
    item = adapt_point(OLD_LUAN_DIEM, source="luan_diem")
    assert item["nguyen_nhan"] == "luan_diem"
    # Tái dụng từ schema cũ.
    assert item["nhan_dinh"] == OLD_LUAN_DIEM["nhan_dinh"]
    assert item["can_cu"]["fact_ids"] == OLD_LUAN_DIEM["fact_ids"]
    assert item["can_cu"]["source_refs"] == [3]
    assert item["dieu_kien"]["thun"] == ["toa_thu"]
    assert item["dieu_kien"]["nghich"] == OLD_LUAN_DIEM["phan_chung"]
    assert item["pham_vi"]["loai_ket_luan"] == "cau_truc"
    assert item["pham_vi"]["gioi_han"] == OLD_LUAN_DIEM["gioi_han"]
    assert item["muc_can_cu"] == "trung_binh"
    # Trường chưa tồn tại trong schema cũ: phải là MISSING, không được điền.
    assert item["giai_thich"] is MISSING
    assert item["can_cu"]["rule_ids"] is MISSING
    assert item["dieu_kien"]["chua_kiem_tra"] is MISSING
    assert item["pham_vi"]["chu_de"] is MISSING


# --- P1.TC-05: adapter mục ket_luan — giai_thich_thun_viet thuộc ket_luan ---
def test_adapt_point_ket_luan_maps_giai_thich_and_empty_source_refs():
    item = adapt_point(OLD_KET_LUAN, source="ket_luan")
    assert item["nguyen_nhan"] == "ket_luan"
    assert item["giai_thich"] == OLD_KET_LUAN["giai_thich_thun_viet"]
    # Danh rỗng là "đã kiểm tra, không trích dẫn" — phải giữ [], khác MISSING.
    assert item["can_cu"]["source_refs"] == []
    assert item["can_cu"]["rule_ids"] is MISSING
    # ket_luan không có loi_chung_cu/phan_chung/dieu_kien_chua_kiem_tra.
    assert item["dieu_kien"]["thun"] is MISSING
    assert item["dieu_kien"]["nghich"] is MISSING
    assert item["muc_can_cu"] == "yeu"


# --- P1.TC-06: ba mức đọc — du_lieu không bao gồm khối AI (ket_luan) ---
def test_adapt_reading_du_lieu_excludes_ai_sections():
    view = adapt_reading(_reading_with_ket_luan(), mode="du_lieu")
    assert view["mode"] == "du_lieu"
    assert view["contract_version"] == CONTRACT_VERSION
    assert len(view["items"]) == 1
    assert all(item["nguyen_nhan"] == "luan_diem" for item in view["items"])


def test_adapt_reading_deeper_modes_include_both_blocks():
    for mode in ("giai_thich", "chuyen_sau"):
        view = adapt_reading(_reading_with_ket_luan(), mode=mode)
        assert view["mode"] == mode
        assert {item["nguyen_nhan"] for item in view["items"]} == {"luan_diem", "ket_luan"}


def test_adapt_reading_rejects_unknown_mode():
    with pytest.raises(ValueError):
        adapt_reading(_reading_with_ket_luan(), mode="level_x")


# --- P1.TC-07: báo cáo cũ rất cũ (thiếu cả trường T2/T3) vẫn qua adapter ---
def test_adapt_reading_old_report_without_new_fields():
    old = {
        "tieu_de": "Bài cũ",
        "luan_diem": [
            {"nhan_dinh": "x", "fact_ids": ["a"], "source_refs": [1]},
        ],
    }
    item = adapt_reading(old, mode="du_lieu")["items"][0]
    # Nhóm không có trong báo cáo cũ: ghi thiếu, không bịa.
    assert item["muc_can_cu"] is MISSING
    assert item["can_cu"]["rule_ids"] is MISSING
    assert item["dieu_kien"]["thun"] is MISSING
    assert item["dieu_kien"]["nghich"] is MISSING
    assert item["pham_vi"]["loai_ket_luan"] is MISSING
    # Dữ kiện vẫn truy được bằng ID.
    assert item["can_cu"]["fact_ids"] == ["a"]
    assert item["nhan_dinh"] == "x"


# --- P1.TC-08: bài fallback (mock, _generation) không phá adapter ---
def test_fallback_generation_adapts_without_keyerror():
    reading = _reading_with_ket_luan()
    reading["_generation"] = {"actual_provider": "mock", "reason": "timeout", "is_mock": True}
    view = adapt_reading(reading, mode="chuyen_sau")
    assert len(view["items"]) == 2
    assert all(
        item["nhan_dinh"] in (OLD_LUAN_DIEM["nhan_dinh"], OLD_KET_LUAN["nhan_dinh"])
        for item in view["items"]
    )


# --- P1.TC-09: response mẫu cho ba mức (hợp đồng + report gốc) ---
def test_sample_response_for_three_modes():
    base_report = {
        "status": "ok",
        "reading": _reading_with_ket_luan(),
        "meta": {"request_id": "r1"},
    }
    for mode in ("du_lieu", "giai_thich", "chuyen_sau"):
        response = sample_response(mode, base_report)
        # Report gốc không bị adapter sửa.
        assert "reading" in response and "contract" in response
        assert response["contract"]["mode"] == mode
        if mode == "du_lieu":
            assert len(response["contract"]["items"]) == 1
        else:
            assert len(response["contract"]["items"]) == 2
    # Reading gốc vẫn giữ đủ hai khối sau khi tạo response mẫu.
    assert "ket_luan" in base_report["reading"]
