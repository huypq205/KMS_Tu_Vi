"""Phân tích dữ kiện sao và tóm tắt cung lá số Tử Vi."""
from __future__ import annotations

import unicodedata
from typing import Any

from backend.app.services.horoscope_annual import tu_hoa_stars_for_can
from backend.app.services.tu_hoa_tables import normalize_star

NATAL_GROUPS = ("chinh_tinh", "risk_stars", "cat_tinh")


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
        "source_status": status_text,
        "source_refs": matching,
    }


def build_star_facts(features: dict[str, Any], context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Trích xuất danh mục facts cho từng sao và liên kết với mã trích dẫn (source_refs).

    Schema fact thống nhất cho lá số gốc và sao lưu niên:
    fact_id, sao, cung, dia_chi, dac_tinh, nhom, roles, tuan, triet, ngu_hanh,
    source_status, source_refs.
    """
    context = context or {}
    ref_list = context.get("reference_list", [])

    facts: list[dict[str, Any]] = []
    fact_id = 1

    basic = features.get("thong_tin_co_ban", {}) or {}
    birth_can = (basic.get("can_chi_nam") or "").split(" ")[0]
    table_id = (basic.get("tu_hoa_table") or {}).get("id")
    tu_hoa_names = {normalize_star(name) for name in tu_hoa_stars_for_can(birth_can, table_id).values()}

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
                roles = ["Tứ hóa"] if normalize_star(star_name) in tu_hoa_names else []
                facts.append(_make_fact(
                    fact_id, star_name, cung_ten, dia_chi, group_key,
                    s.get("dac_tinh") or "—", roles, tuan, triet, ref_list,
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
        ))
        fact_id += 1

    for entry in annual.get("luu_tu_hoa") or []:
        palace = palace_by_so.get(entry.get("cung_so")) or {}
        display = f"{entry.get('ten_sao', '')} ({entry.get('ten', '')})"
        facts.append(_make_fact(
            fact_id, display, entry.get("cung_ten", ""), entry.get("dia_chi", ""),
            "luu_nien", "—", ["Lưu niên"], bool(palace.get("tuan_trung")),
            bool(palace.get("triet_lo")), ref_list, match_name=entry.get("ten_sao", ""),
        ))
        fact_id += 1

    return facts
