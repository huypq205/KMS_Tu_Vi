"""Phân tích dữ kiện sao và tóm tắt cung lá số Tử Vi."""
from __future__ import annotations

import unicodedata
from typing import Any

from backend.app.core.evidence_types import EvidenceType
from backend.app.services.horoscope_annual import tu_hoa_stars_for_can

NATAL_GROUPS = ("chinh_tinh", "risk_stars", "cat_tinh")
CHI_ORDER = ("Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi")
TU_HOA_MARKERS = frozenset({"hóa lộc", "hóa quyền", "hóa khoa", "hóa kỵ"})


def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn"
    ).replace("đ", "d").replace("Đ", "D").lower()


def palace_summary(palace: dict[str, Any] | None) -> str:
    """Tóm tắt đặc trưng cung (tên, chính tinh đắc hãm, sao lưu ý, cát tinh, tuần triệt)."""
    if not palace or not isinstance(palace, dict):
        return "Chưa có dữ liệu cung."

    parts: list[str] = []
    ten = palace.get("ten") or palace.get("chuan_ten") or ""
    if ten:
        parts.append(f"Cung {ten}")

    chinh_tinh = palace.get("chinh_tinh", [])
    if chinh_tinh:
        ct_str = ", ".join(f"{s.get('ten', '')} ({s.get('dac_tinh', '-')})" for s in chinh_tinh)
        parts.append(f"Chính tinh: {ct_str}")
    else:
        parts.append("Vô chính diệu")

    risk_stars = palace.get("risk_stars", [])
    if risk_stars:
        risk_str = ", ".join(s.get("ten", "") for s in risk_stars)
        parts.append(f"Sao cần lưu ý: {risk_str}")

    cat_tinh = palace.get("cat_tinh", [])
    if cat_tinh:
        cat_str = ", ".join(s.get("ten", "") for s in cat_tinh[:4])
        parts.append(f"Cát tinh: {cat_str}")

    modifiers = []
    if palace.get("tuan_trung"):
        modifiers.append("Tuần")
    if palace.get("triet_lo"):
        modifiers.append("Triệt")
    if modifiers:
        parts.append(f"Ngộ {' - '.join(modifiers)}")

    return "; ".join(parts)


def _matching_refs(star_name: str, ref_list: list[dict[str, Any]]) -> list[int]:
    norm_name = strip_accents(star_name)
    matching: list[int] = []
    for ref in ref_list:
        rid = ref.get("ref_id")
        if rid is None:
            continue
        if norm_name and norm_name in strip_accents(ref.get("excerpt", "")):
            if int(rid) not in matching:
                matching.append(int(rid))
    return matching


def _palace_evidence_kind(dia_chi: str, tam_phuong: dict[str, Any] | None) -> str:
    """Loại chứng cứ của một sao theo vị trí cung so với cung Mệnh.

    - Cung Mệnh: tọa thủ.
    - Đối cung Mệnh: xung chiếu.
    - Cung tam hợp với Mệnh: tam hợp.
    - Cung kế cận Mệnh: giáp cung.
    - Các cung còn lại: vẫn là sao tọa thủ tại cung của nó.
    """
    tam_phuong = tam_phuong or {}
    anchor = tam_phuong.get("chinh_cung") or ""
    if not anchor or not dia_chi or dia_chi == anchor:
        return EvidenceType.TOA_THU.value
    if dia_chi == (tam_phuong.get("doi_cung") or ""):
        return EvidenceType.XUNG_CHIEU.value
    if dia_chi in (tam_phuong.get("tam_hop") or []):
        return EvidenceType.TAM_HOP.value
    try:
        index = CHI_ORDER.index(anchor)
        neighbours = {CHI_ORDER[(index - 1) % 12], CHI_ORDER[(index + 1) % 12]}
        if dia_chi in neighbours:
            return EvidenceType.GIAP_CUNG.value
    except ValueError:
        pass
    return EvidenceType.TOA_THU.value


def _make_fact(
    fact_id: int,
    star_name: str,
    cung_ten: str,
    dia_chi: str,
    nhom: str,
    dac_tinh: str,
    roles: list[str],
    tuan: bool,
    triet: bool,
    ref_list: list[dict[str, Any]],
    match_name: str | None = None,
    kind: str = EvidenceType.TOA_THU.value,
) -> dict[str, Any]:
    matching = _matching_refs(match_name or star_name, ref_list)
    status_text = (
        f"Có {len(matching)} trích dẫn đối chiếu từ sách gốc"
        if matching
        else "Chưa có trích dẫn đối chiếu từ nguồn đã lấy"
    )
    return {
        "fact_id": str(fact_id),
        "sao": star_name,
        "cung": cung_ten,
        "dia_chi": dia_chi,
        "trang_thai": dac_tinh,
        "dac_tinh": dac_tinh,
        "nhom": nhom,
        "roles": roles,
        "tuan": tuan,
        "triet": triet,
        "ngu_hanh": "—",
        "kind": kind,
        "source_status": status_text,
        "source_refs": matching,
    }


def build_star_facts(features: dict[str, Any], context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Trích xuất danh mục facts cho từng sao và liên kết với mã trích dẫn (source_refs).

    Schema fact thống nhất cho lá số gốc và sao lưu niên:
    fact_id, sao, cung, dia_chi, dac_tinh, nhom, roles, tuan, triet, ngu_hanh,
    kind, source_status, source_refs.
    """
    context = context or {}
    ref_list = context.get("reference_list", [])

    facts: list[dict[str, Any]] = []
    fact_id = 1

    basic = features.get("thong_tin_co_ban", {}) or {}
    birth_can = (basic.get("can_chi_nam") or "").split(" ")[0]
    tu_hoa_names = {name.casefold() for name in tu_hoa_stars_for_can(birth_can).values()}
    tam_phuong = features.get("tam_phuong_tu_chinh_menh") or {}

    palaces = features.get("palaces", [])
    for p in palaces:
        cung_ten = p.get("ten", "")
        dia_chi = p.get("chuan_ten", "")
        tuan = bool(p.get("tuan_trung"))
        triet = bool(p.get("triet_lo"))

        for group_key in NATAL_GROUPS:
            for s in p.get(group_key, []):
                star_name = s.get("ten", "")
                if not star_name:
                    continue
                roles = ["Tứ hóa"] if star_name.casefold() in tu_hoa_names else []
                is_tu_hoa = star_name.casefold() in tu_hoa_names or star_name.casefold() in TU_HOA_MARKERS
                kind = (EvidenceType.TU_HOA.value if is_tu_hoa
                        else _palace_evidence_kind(dia_chi, tam_phuong))
                facts.append(_make_fact(
                    fact_id, star_name, cung_ten, dia_chi, group_key,
                    s.get("dac_tinh") or "—", roles, tuan, triet, ref_list,
                    kind=kind,
                ))
                fact_id += 1

    annual = features.get("luu_nien") or {}
    palace_by_so = {p.get("cung_so"): p for p in palaces}

    for entry in (annual.get("vong_thai_tue") or {}).values():
        palace = palace_by_so.get(entry.get("cung_so")) or {}
        facts.append(_make_fact(
            fact_id, entry.get("ten", ""), entry.get("cung_ten", ""), entry.get("dia_chi", ""),
            "luu_nien", "—", ["Lưu niên"], bool(palace.get("tuan_trung")),
            bool(palace.get("triet_lo")), ref_list,
            kind=EvidenceType.VAN_HAN.value,
        ))
        fact_id += 1

    for entry in annual.get("luu_tu_hoa") or []:
        palace = palace_by_so.get(entry.get("cung_so")) or {}
        display = f"{entry.get('ten_sao', '')} ({entry.get('ten', '')})"
        facts.append(_make_fact(
            fact_id, display, entry.get("cung_ten", ""), entry.get("dia_chi", ""),
            "luu_nien", "—", ["Lưu niên"], bool(palace.get("tuan_trung")),
            bool(palace.get("triet_lo")), ref_list, match_name=entry.get("ten_sao", ""),
            kind=EvidenceType.TU_HOA.value,
        ))
        fact_id += 1

    return facts
