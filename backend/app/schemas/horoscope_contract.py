"""P1 (Plan_Fix_Mai_Anh_v2): hợp đồng dữ liệu ba mức đọc của báo cáo Horoscope.

Chốt cấu trúc nhận định dùng chung cho ba mức đọc trước khi mở rộng pipeline
(P6) và UI (P7). Nguyên tắc:

- Dữ kiện nằm ở lớp fact; nhận định tham chiếu bằng ID (fact_ids, source_refs,
  rule_ids). Không nhân bản thông tin sao/cung vào từng nhận định.
- ``reading_mode`` là lựa chọn của người dùng; ``provider`` là bộ xử lý thực
  chạy. Hai khái niệm độc lập (P1 §3.4).
- Adapter cho báo cáo cũ: trường chưa tồn tại hiển thị là ``MISSING``
  ("thieu"), không điền bằng suy đoán. Danh rỗng ``[]`` giữ nguyên — nghĩa là
  "đã kiểm tra, không tìm thấy" — khác ``MISSING`` ("chưa có dữ liệu để kiểm tra").

Bản mapping (P1 §3.3) — hai cấu trúc hiện tại tách riêng:

- ``luan_diem``: nhan_dinh, gioi_han, muc_tin_cay, loi_chung_cu, phan_chung,
  fact_ids, source_refs, loai_ket_luan.
- ``ket_luan``: nhan_dinh, giai_thich_thun_viet, gioi_han, muc_tin_cay,
  fact_ids, source_refs, loai_ket_luan. ``giai_thich_thun_viet`` thuộc
  ket_luan, không thuộc luan_diem.
- Mới: ``rule_ids`` (P3 điền; báo cáo cũ luôn ``MISSING``, UI ghi "chưa có
  quy tắc").
"""
from __future__ import annotations

from typing import Any, Literal

ReadingMode = Literal["du_lieu", "giai_thich", "chuyen_sau"]

# "du_lieu": chỉ lá số + dữ kiện, không gọi AI.
# "giai_thich": AI giải thích thuật ngữ, nhận định, liên hệ dữ kiện.
# "chuyen_sau": AI luận giải chuyên sâu (hợp đồng P1; nội dung tổng hợp do P6).
READING_MODES: tuple[str, ...] = ("du_lieu", "giai_thich", "chuyen_sau")
# Mặc định giữ hành vi hiện hành (bài luận có ket_luan) khi client chưa gửi trường.
READING_MODE_DEFAULT: str = "chuyen_sau"

# Bump khi hợp đồng đổi để client và cache biết mình đang đọc phiên bản nào.
CONTRACT_VERSION: int = 1

# Đánh dấu "chưa có dữ liệu để kiểm tra" — khác danh rỗng (đã kiểm tra, không thấy).
MISSING: str = "thieu"

CONTRACT_GROUPS: tuple[str, ...] = (
    "nhan_dinh", "giai_thich", "can_cu", "dieu_kien", "pham_vi", "muc_can_cu",
)

# Mức du_lieu chỉ cần nhóm dữ kiện; hai mức AI cần cả nhóm giai_thich.
GROUPS_REQUIRED_BY_MODE: dict[str, tuple[str, ...]] = {
    "du_lieu": ("nhan_dinh", "can_cu", "dieu_kien", "pham_vi", "muc_can_cu"),
    "giai_thich": CONTRACT_GROUPS,
    "chuyen_sau": CONTRACT_GROUPS,
}

# Khối nguồn theo mức: du_lieu không dùng khối AI (ket_luan).
_ITEM_SOURCES_BY_MODE: dict[str, tuple[str, ...]] = {
    "du_lieu": ("luan_diem",),
    "giai_thich": ("luan_diem", "ket_luan"),
    "chuyen_sau": ("luan_diem", "ket_luan"),
}


def _present(point: dict[str, Any], key: str) -> Any:
    """Giá trị của key; key vắng mặt hoặc None -> MISSING (không bịa dữ liệu)."""
    value = point.get(key, MISSING)
    return MISSING if value is None else value


def adapt_point(point: dict[str, Any], source: str = "ket_luan") -> dict[str, Any]:
    """Map một mục ``luan_diem``/``ket_luan`` (schema cũ hoặc mới) sang hợp đồng 6 nhóm.

    - ``giai_thich``: lấy ``giai_thich_thun_viet`` (chỉ có trong ket_luan);
      mục luan_diem trả ``MISSING`` — phần giải thích của luan_diem là P6.
    - ``dieu_kien.thun``: nhãn loại chứng cứ (loi_chung_cu, chỉ luan_diem).
    - ``dieu_kien.nghich``: phan_chung (chỉ luan_diem; câu "Không ghi nhận
      phản chứng trong nguồn đã lấy" là trạng thái hợp lệ, không phải thiếu).
    - ``dieu_kien.chua_kiem_tra``: trường mới do P3 điền; báo cáo cũ là MISSING.
    - ``can_cu.rule_ids``: trường mới do P3 điền; báo cáo cũ là MISSING.
    - Danh rỗng giữ nguyên (đã kiểm tra, không tìm thấy).
    """
    if not isinstance(point, dict):
        return {"nguyen_nhan": source, **{group: MISSING for group in CONTRACT_GROUPS}}
    return {
        "nguyen_nhan": source,
        "nhan_dinh": _present(point, "nhan_dinh"),
        "giai_thich": _present(point, "giai_thich_thun_viet"),
        "can_cu": {
            "fact_ids": _present(point, "fact_ids"),
            "source_refs": _present(point, "source_refs"),
            "rule_ids": _present(point, "rule_ids"),
        },
        "dieu_kien": {
            "thun": _present(point, "loi_chung_cu"),
            "nghich": _present(point, "phan_chung"),
            "chua_kiem_tra": _present(point, "dieu_kien_chua_kiem_tra"),
        },
        "pham_vi": {
            "loai_ket_luan": _present(point, "loai_ket_luan"),
            "chu_de": _present(point, "chu_de"),
            "gioi_han": _present(point, "gioi_han"),
        },
        "muc_can_cu": _present(point, "muc_tin_cay"),
    }


def adapt_reading(reading: dict[str, Any], mode: str = READING_MODE_DEFAULT) -> dict[str, Any]:
    """Xem một bài đọc (báo cáo cũ hoặc mới) theo hợp đồng 6 nhóm của mức ``mode``.

    - ``du_lieu``: chỉ khối luan_diem (dữ kiện), không bao gồm ket_luan (khối AI).
    - ``giai_thich`` / ``chuyen_sau``: cả luan_diem và ket_luan.

    Không thay đổi ``reading`` gốc; các khóa phụ (``_generation``...) không
    ảnh hưởng kết quả.
    """
    if mode not in READING_MODES:
        raise ValueError(f"reading_mode không hợp lệ: {mode!r}; dùng một trong {', '.join(READING_MODES)}.")
    reading = reading or {}
    items: list[dict[str, Any]] = []
    for source in _ITEM_SOURCES_BY_MODE[mode]:
        for point in reading.get(source) or []:
            items.append(adapt_point(point, source=source))
    return {"mode": mode, "contract_version": CONTRACT_VERSION, "items": items}


def sample_response(mode: str, report: dict[str, Any]) -> dict[str, Any]:
    """Response mẫu hợp đồng cho một mức đọc: report gốc + khối ``contract``.

    Dùng làm định dạng mục tiêu cho P6 (pipeline ba mức) và P7 (UI); P1 chỉ
    chốt cấu trúc, chưa đổi cách sinh bài.
    """
    return {**report, "contract": adapt_reading(report.get("reading") or {}, mode)}
