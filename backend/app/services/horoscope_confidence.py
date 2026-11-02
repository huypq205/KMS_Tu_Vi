"""Quy tắc độ tin cậy dữ liệu giờ sinh (input_confidence A–D).

Mức A/B đủ chắc để luận cả cấu trúc lẫn vận hạn; mức C/D chỉ cho phép kết luận
cấu trúc, không kết luận thời điểm/sự kiện cụ thể. Không dùng phần trăm tin cậy
vì KMS chưa có thống kê nghiệm lý đủ mẫu.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

INPUT_CONFIDENCE_LEVELS = ("A", "B", "C", "D")
LOW_INPUT_CONFIDENCE_LEVELS = frozenset({"C", "D"})
DEFAULT_INPUT_CONFIDENCE = "A"
DEFAULT_GIO_SINH_SOURCE = "memory"

INPUT_CONFIDENCE_LABELS = {
    "A": "giờ sinh rõ ràng, không sát ranh giới giờ",
    "B": "giờ sinh có sai số nhỏ, không sát ranh giới giờ",
    "C": "giờ sinh sát ranh giới giờ hoặc chỉ nhớ gần đúng",
    "D": "thiếu dữ liệu giờ sinh cốt lõi",
}
GIO_SINH_SOURCE_LABELS = {
    "document": "giấy tờ/hồ sơ ghi rõ",
    "memory": "nhớ lại từ gia đình",
    "estimate": "ước lượng",
    "unknown": "không rõ",
}

LOW_CONFIDENCE_CAVEAT = "Dữ liệu giờ sinh chưa chắc chắn (mức C/D)"
LOW_CONFIDENCE_POLICY = (
    "Chỉ kết luận cấu trúc (tính cách, xu hướng, điều kiện); không kết luận thời điểm "
    "hoặc sự kiện cụ thể (năm/tháng/ngày sẽ xảy ra chuyện gì)."
)

# Chỉ bắt các mẫu nêu sự kiện/thời điểm rõ ràng; không bắt mọi câu có chữ "sẽ".
_TIMING_CLAIM_PATTERNS = (
    re.compile(
        r"\bsẽ\s+(?:kết hôn|ly hôn|sinh con|mất việc|qua đời|phá sản|thăng chức|"
        r"chuyển việc|đổi việc|trúng tuyển|xuất ngoại|tai nạn|bệnh nặng)\b"
    ),
    re.compile(
        r"\b(?:kết hôn|ly hôn|sinh con|mất việc|qua đời|phá sản|thăng chức|"
        r"chuyển việc|đổi việc)\s+(?:trong|vào)\s+(?:năm|tháng)\s+\d{2,4}\b"
    ),
    re.compile(r"\b(?:năm|tháng)\s+\d{2,4}\b[^.\n]{0,40}\bsẽ\b"),
    re.compile(r"\btrong\s+(?:năm|tháng)\s+\d{2,4}\b[^.\n]{0,60}\bsẽ\b"),
    re.compile(r"\bgiai\s+đoạn\b[^.\n]{0,60}\bsẽ\b"),
)


def normalize_level(value: Any) -> str:
    """Chuẩn hóa mức tin cậy; giá trị lạ quay về A để không chặn luồng cũ."""
    level = str(value or DEFAULT_INPUT_CONFIDENCE).strip().upper()
    return level if level in INPUT_CONFIDENCE_LEVELS else DEFAULT_INPUT_CONFIDENCE


def _basic(features: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(features, dict):
        return {}
    basic = features.get("thong_tin_co_ban")
    return basic if isinstance(basic, dict) else {}


def level_of(features: dict[str, Any] | None) -> str:
    return normalize_level(_basic(features).get("input_confidence"))


def is_low_confidence(features: dict[str, Any] | None) -> bool:
    return level_of(features) in LOW_INPUT_CONFIDENCE_LEVELS


def confidence_prompt_line(basic: dict[str, Any] | None) -> str:
    """Dòng dữ kiện mô tả mức tin cậy/nguồn/sai số giờ sinh cho prompt."""
    basic = basic if isinstance(basic, dict) else {}
    level = normalize_level(basic.get("input_confidence"))
    source = str(basic.get("gio_sinh_source") or DEFAULT_GIO_SINH_SOURCE)
    line = (
        f"- Độ tin cậy giờ sinh: {level} — {INPUT_CONFIDENCE_LABELS[level]} "
        f"| Nguồn giờ sinh: {source} ({GIO_SINH_SOURCE_LABELS.get(source, 'chưa rõ')})"
    )
    error = basic.get("gio_sinh_error_phut")
    if isinstance(error, int) and error >= 0:
        line += f" | Sai số ước tính: ±{error} phút"
    return line + "\n"


def low_confidence_prompt_line(basic: dict[str, Any] | None) -> str:
    """Ràng buộc bổ sung khi giờ sinh ở mức C/D; rỗng với mức A/B."""
    basic = basic if isinstance(basic, dict) else {}
    if normalize_level(basic.get("input_confidence")) not in LOW_INPUT_CONFIDENCE_LEVELS:
        return ""
    return (
        "- RÀNG BUỘC DỮ LIỆU: giờ sinh mức C/D — chỉ kết luận cấu trúc; cấm kết luận "
        "thời điểm hoặc sự kiện cụ thể (năm/tháng/ngày sẽ xảy ra chuyện gì). "
        f'Mỗi mục gioi_han phải nêu nguyên văn "{LOW_CONFIDENCE_CAVEAT}".\n'
    )


def _iter_text(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_text(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _iter_text(item)


def contains_timing_claim(text: Any) -> bool:
    """True nếu chuỗi chứa kết luận thời điểm/sự kiện cụ thể đã biết."""
    if not isinstance(text, str) or not text.strip():
        return False
    normalized = unicodedata.normalize("NFC", text).casefold()
    return any(pattern.search(normalized) for pattern in _TIMING_CLAIM_PATTERNS)


def has_low_confidence_caveat(text: Any) -> bool:
    if not isinstance(text, str) or not text.strip():
        return False
    return LOW_CONFIDENCE_CAVEAT.casefold() in unicodedata.normalize("NFC", text).casefold()


def check_input_confidence(reading: dict[str, Any], features: dict[str, Any]) -> str | None:
    """Kiểm tra bài đọc có tuân thủ ràng buộc C/D không; None nếu đạt."""
    if not isinstance(reading, dict) or not is_low_confidence(features):
        return None
    if any(contains_timing_claim(text) for text in _iter_text(reading)):
        return (
            "Giờ sinh mức C/D nhưng bài đọc có kết luận thời điểm/sự kiện cụ thể. "
            + LOW_CONFIDENCE_POLICY
        )
    if not any(has_low_confidence_caveat(text) for text in _iter_text(reading)):
        return (
            "Giờ sinh mức C/D: bài đọc phải nêu rõ "
            f'"{LOW_CONFIDENCE_CAVEAT}" trong phần giới hạn.'
        )
    for key in ("luan_diem", "ket_luan"):
        for point in reading.get(key) or []:
            if isinstance(point, dict) and not has_low_confidence_caveat(point.get("gioi_han")):
                return (
                    "Giờ sinh mức C/D: mỗi mục gioi_han phải nêu nguyên văn "
                    f'"{LOW_CONFIDENCE_CAVEAT}".'
                )
    return None


def check_ask_input_confidence(answer: dict[str, Any], features: dict[str, Any]) -> str | None:
    """Kiểm tra câu trả lời hỏi nhanh có tuân thủ ràng buộc C/D không."""
    if not isinstance(answer, dict) or not is_low_confidence(features):
        return None
    for key in ("tra_loi", "giai_thich_thun_viet"):
        if contains_timing_claim(answer.get(key)):
            return (
                "Giờ sinh mức C/D nhưng câu trả lời có kết luận thời điểm/sự kiện cụ thể. "
                + LOW_CONFIDENCE_POLICY
            )
    if not has_low_confidence_caveat(answer.get("gioi_han")):
        return (
            "Giờ sinh mức C/D: mục gioi_han phải nêu nguyên văn "
            f'"{LOW_CONFIDENCE_CAVEAT}".'
        )
    return None
