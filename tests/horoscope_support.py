"""Fixture dùng chung cho các test Horoscope (không gọi mạng, không gọi Gemini thật)."""
from __future__ import annotations

import json
from unittest.mock import Mock

from backend.app.schemas.horoscope import HoroscopeRequest

BIRTH = {"ngay": 15, "thang": 8, "nam": 1995, "chi_gio": 5, "gioi_tinh": 1}
# Additive T5 response contract; make_features() derives these from the selected
# table rather than hardcoding a school into every report fixture.
TU_HOA_TABLE_FIELDS = {"id", "school", "source", "verification_status", "signature"}


def make_request(provider: str = "mock", target_year: int | None = None, **extra) -> HoroscopeRequest:
    return HoroscopeRequest(**BIRTH, provider=provider, target_year=target_year, **extra)


def make_raw() -> dict:
    from backend.app.services.horoscope_features import generate_raw_horoscope
    return generate_raw_horoscope(
        BIRTH["ngay"], BIRTH["thang"], BIRTH["nam"], BIRTH["chi_gio"], BIRTH["gioi_tinh"],
        duong_lich=True,
    )


def make_features(target_year: int | None = None, **extra) -> dict:
    from backend.app.services.horoscope_features import extract_horoscope_features
    return extract_horoscope_features(make_raw(), target_year, **extra)


def valid_reading(facts: list[dict], year_text: str = "2026 Bính Ngọ",
                  fact_count: int = 3, include_year: bool = True) -> dict:
    """Bài đọc hợp lệ theo schema, dẫn các fact có source_refs thật."""
    usable = [f for f in facts if f.get("source_refs")][:fact_count]
    points = [{
        "nhan_dinh": f"{f['sao']} tại {f['cung']} ({f['dia_chi']}) cần đối chiếu điều kiện trong nguồn.",
        "gioi_han": "Chỉ nêu điều kiện đã có trong dữ kiện lá số.",
        "muc_tin_cay": "trung_binh",
        "fact_ids": [f["fact_id"]],
        "source_refs": [f["source_refs"][0]],
    } for f in usable]
    period = (f"Năm {year_text}: vận trình cần đọc cùng đại hạn và tiểu hạn."
              if include_year else "Giai đoạn hiện tại cần đọc cùng đại hạn và tiểu hạn.")
    return {
        "tieu_de": "Bài đọc kiểm thử",
        "tong_quan": {
            "ban_sac": "Dữ kiện thử.", "diem_manh": ["Điểm thử"],
            "diem_can_ren_luyen": ["Điều thử"], "ngu_hanh_nang_luong": "Quan hệ thử.",
        },
        "su_nghiep": {
            "phong_cach_lam_viec": "Thử.", "moi_truong_phu_hop": "Thử.",
            "nghe_nghiep_tuong_hop": ["Thử"], "loi_khuyen_phat_trien": "Thử.",
        },
        "tai_chinh": {
            "tu_duy_tien_bac": "Thử.", "co_hoi_tich_luy": "Thử.",
            "rui_ro_can_phong": "Thử.", "loi_khuyen_quan_ly_tai_chinh": "Thử.",
        },
        "tinh_cam": {
            "xu_huong_tinh_cam": "Thử.", "mau_nguoi_tuong_hop": "Thử.",
            "bi_quyet_hoa_hop": "Thử.",
        },
        "van_han_hien_tai": {
            "giai_doan": period, "chu_de_trong_tam": "Thử.",
            "co_hoi_nen_nam_bat": "Thử.", "thach_thuc_can_can_trong": "Thử.",
        },
        "loi_khuyen_hanh_dong": ["Đọc nguồn trước khi kết luận."],
        "luan_diem": points,
    }


def gemini_response(reading: dict) -> Mock:
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "candidates": [{
            "finishReason": "STOP",
            "content": {"parts": [{"text": json.dumps(reading, ensure_ascii=False)}]},
        }]
    }
    return response
