# -*- coding: utf-8 -*-
"""P5 (Plan_Fix_Mai_Anh_v2 §8): Danh mục sao dùng chung backend & frontend.

Đảm bảo nguyên tắc:
1. Chính tinh (14 sao) giữ nhận diện riêng nổi bật (M/V/Đ/B/H).
2. Tứ Hóa (4 sao) giữ nhận diện riêng (badge Khoa/Quyền/Lộc/Kỵ); KHÔNG ép vào cát tinh hay hung tinh.
3. Phụ tinh phân tách rõ ràng thành: Cát tinh, Hung tinh, Sao khác / chưa phân loại.
4. Bảo toàn tính toàn vẹn: mọi sao thuộc đúng 1 nhóm duy nhất, không sót sao, không nhân đôi sao.
"""
from __future__ import annotations

import unicodedata
from typing import Any

GROUP_CHINH_TINH = "chinh_tinh"
GROUP_TU_HOA = "tu_hoa"
GROUP_CAT_TINH = "cat_tinh"
GROUP_HUNG_TINH = "hung_tinh"
GROUP_KHAC = "khac"
GROUP_LUU_NIEN = "luu_nien"

GROUPS = (
    GROUP_CHINH_TINH,
    GROUP_TU_HOA,
    GROUP_CAT_TINH,
    GROUP_HUNG_TINH,
    GROUP_KHAC,
)

# 14 Chính tinh (saoLoai == 1 trong vendor lasotuvi)
CHINH_TINH_IDS = frozenset(range(1, 15))

# 4 Tứ Hóa (sao gốc mang Hóa Khoa, Hóa Quyền, Hóa Lộc, Hóa Kỵ)
TU_HOA_IDS = frozenset({92, 93, 94, 95})

# Cát tinh truyền thống
CAT_TINH_IDS = frozenset({
    # Xương Khúc, Khôi Việt, Tả Hữu, Lộc Tồn, Thiên Mã
    57, 58, 59, 60, 61, 62, 27, 98,
    # Long Phượng, Thai Tọa, Quang Quý
    63, 64, 65, 66, 67, 68,
    # Tam Đức (Thiên Đức, Nguyệt Đức, Phúc Đức, Long Đức)
    71, 72, 24, 22,
    # Hỷ tinh (Thiên Hỷ, Hỷ Thần, Đào Hoa, Hồng Loan)
    80, 34, 78, 79,
    # Giải tinh (Thiên Giải, Địa Giải, Giải Thần)
    81, 82, 83,
    # Quý tinh & Cát tinh khác
    75, 76, 77, 84, 85, 86, 87, 100, 101, 103, 105, 106,
    # Cát tinh vòng Thái Tuế / Bác Sỹ
    16, 18, 29, 31, 32, 109,
})

# Hung tinh / Sát tinh / Bại tinh truyền thống
HUNG_TINH_IDS = frozenset({
    # Lục sát tinh
    51, 52, 53, 54, 55, 56,
    # Bại tinh vòng Thái Tuế
    17, 21, 23, 25,
    # Hao tinh (Tiểu Hao, Đại Hao)
    30, 36,
    # Khốc Hư, Hình Diêu
    69, 70, 73, 74,
    # Ám / Sát tinh khác
    96, 97, 99, 104, 108,
    # Hung tinh khác
    33, 35, 37, 88, 89, 90, 91, 102,
})

# Bảng màu đắc tính
DAC_TINH_COLOR = {
    "M": "#1a7f37",  # Miếu - xanh lá đậm
    "V": "#2da44e",  # Vượng - xanh lá tươi
    "Đ": "#0969da",  # Đắc - xanh dương
    "B": "#57606a",  # Bình - xám trung tính
    "H": "#cf222e",  # Hãm - đỏ
}

DAC_TINH_LABEL = {
    "M": "Miếu",
    "V": "Vượng",
    "Đ": "Đắc",
    "B": "Bình",
    "H": "Hãm",
}


def _normalize_name(name: str) -> str:
    nfkd = unicodedata.normalize("NFKD", name or "").strip().lower()
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# Mapping tên sao phòng trường hợp saoID bị thiếu
_NAME_TO_GROUP: dict[str, str] = {
    "hoa khoa": GROUP_TU_HOA,
    "hoa quyen": GROUP_TU_HOA,
    "hoa loc": GROUP_TU_HOA,
    "hoa ky": GROUP_TU_HOA,
}


def classify_star(star: dict[str, Any]) -> str:
    """Phân loại một sao vào đúng 1 nhóm:

    - 'chinh_tinh'
    - 'tu_hoa'
    - 'cat_tinh'
    - 'hung_tinh'
    - 'khac'
    """
    sid = star.get("saoID")
    loai = star.get("saoLoai")
    ten = star.get("saoTen") or star.get("ten") or ""

    # 1. Chính tinh (luôn ưu tiên saoLoai == 1 hoặc sid thuộc CHINH_TINH_IDS)
    if loai == 1 or (isinstance(sid, int) and sid in CHINH_TINH_IDS):
        return GROUP_CHINH_TINH

    # 2. Tứ Hóa (không ép vào cát/hung)
    if isinstance(sid, int) and sid in TU_HOA_IDS:
        return GROUP_TU_HOA
    norm = _normalize_name(ten)
    if norm in _NAME_TO_GROUP:
        return _NAME_TO_GROUP[norm]

    # 3. Cát tinh
    if isinstance(sid, int) and sid in CAT_TINH_IDS:
        return GROUP_CAT_TINH

    # 4. Hung tinh
    if isinstance(sid, int) and sid in HUNG_TINH_IDS:
        return GROUP_HUNG_TINH

    # 5. Khác (Vòng Tràng Sinh, Bác Sỹ trung tính, v.v.)
    return GROUP_KHAC


def partition_palace_stars(
    saos: list[dict[str, Any]],
    luu_nien_saos: list[dict[str, Any]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Phân chia tập sao trong cung thành các nhóm độc lập.

    Đảm bảo 100% sao đầu vào được phân bổ đúng, không sót, không nhân đôi.
    """
    result: dict[str, list[dict[str, Any]]] = {
        GROUP_CHINH_TINH: [],
        GROUP_TU_HOA: [],
        GROUP_CAT_TINH: [],
        GROUP_HUNG_TINH: [],
        GROUP_KHAC: [],
        GROUP_LUU_NIEN: list(luu_nien_saos or []),
    }

    for s in saos:
        grp = classify_star(s)
        result[grp].append(s)

    return result

