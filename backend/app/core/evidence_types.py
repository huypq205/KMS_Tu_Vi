"""Từ điển loại chứng cứ dùng trong luận giải Tử Vi.

Mỗi fact sao/cung và mỗi luận điểm có thể gắn một loại chứng cứ để người đọc
phân biệt đâu là sao tọa thủ, tam hợp, xung chiếu, tứ hóa, vận hạn... với
phần suy luận nối mạch của người viết.
"""
from __future__ import annotations

from enum import Enum


class EvidenceType(str, Enum):
    TOA_THU = "toa_thu"
    TAM_HOP = "tam_hop"
    XUNG_CHIEU = "xung_chieu"
    GIAP_CUNG = "giap_cung"
    TU_HOA = "tu_hoa"
    MENH_CUC = "menh_cuc"
    VAN_HAN = "van_han"
    NGHIEM_LY = "nghiem_ly"
    TRUONG_PHAI = "truong_phai"
    SUY_LUAN = "suy_luan"


EVIDENCE_LABELS = {
    EvidenceType.TOA_THU: "Tọa thủ",
    EvidenceType.TAM_HOP: "Tam hợp",
    EvidenceType.XUNG_CHIEU: "Xung chiếu",
    EvidenceType.GIAP_CUNG: "Giáp cung",
    EvidenceType.TU_HOA: "Tứ hóa",
    EvidenceType.MENH_CUC: "Mệnh – Cục",
    EvidenceType.VAN_HAN: "Vận hạn",
    EvidenceType.NGHIEM_LY: "Nghiệm lý",
    EvidenceType.TRUONG_PHAI: "Trường phái",
    EvidenceType.SUY_LUAN: "Suy luận",
}

EVIDENCE_TYPE_VALUES = tuple(item.value for item in EvidenceType)

# Câu chuẩn khi nguồn đã lấy không có đoạn trái chiều; UI và prompt dùng chung.
NO_COUNTER_EVIDENCE = "Không ghi nhận phản chứng trong nguồn đã lấy."


def evidence_label(value: object) -> str:
    """Nhãn tiếng Việt của một loại chứng cứ; giá trị lạ trả nhãn trung tính."""
    try:
        return EVIDENCE_LABELS[EvidenceType(str(value or ""))]
    except (ValueError, KeyError):
        return "Chưa rõ loại"
