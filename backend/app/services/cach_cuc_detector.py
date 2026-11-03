"""P3 (Plan_Fix_Mai_Anh_v2): nhận diện cách cục bằng code trên dữ kiện lá số.

Bộ nhận diện **không gọi AI** và không đọc văn bản luận giải để suy ra kết quả.
Nó chỉ đọc dữ kiện đã an (sao, cung, quan hệ P2b, trạng thái miếu/vượng/đắc/
bình/hãm, tầng thời gian) rồi đối chiếu với điều kiện của từng quy tắc trong
danh mục P2.

Kết quả (P3 §6.2)
------------------
- ``khop_du``: mọi điều kiện bắt buộc đều đạt.
- ``khop_mot_phan``: cấu trúc (sao/cung/quan hệ) đạt nhưng điều kiện bổ sung
  (trạng thái sao) không đạt.
- ``khong_khop``: có ít nhất một điều kiện cấu trúc không đạt.
- ``chua_the_danh_gia``: thiếu dữ kiện để kết luận (lá số chưa đủ 12 cung,
  chưa an sao, thiếu trạng thái sao, hoặc quy tắc ngoài tầng lá số gốc).

Ràng buộc P3 §6.3
------------------
- Quy tắc ``la_so_goc`` chỉ đọc sao gốc; không lấy sao lưu niên ghép vào.
- Không tự thêm cách cục: kết quả là nguồn duy nhất cho ``rule_ids``; phần
  kiểm tra ``check_rule_ids`` chặn AI dẫn quy tắc ngoài kết quả này.
- Không tự duyệt nội dung: mỗi kết quả giữ nguyên ``trang_thai_noi_dung`` của
  quy tắc (bản đầu là ``chi_tham_khao``), không nâng thành ``duyet_dung``.

``cung_muc_tieu`` chưa được P3 dùng để neo vị trí — chỉ ``cung_neo`` (nếu có)
mới xác định cung neo; quy tắc không có neo thì tìm nhóm cung theo quan hệ.

Điều kiện trạng thái sao
------------------------
Danh mục P2 bổ sung trường máy đọc ``trang_thai_sao`` (tên sao -> một trong
``mieu/vuong/dac/binh/ham``) cho các quy tắc yêu cầu "miếu/vượng" trong văn bản
nguồn. P3 không suy trạng thái từ câu chữ và không sửa bảng trạng thái sao.

Điều kiện thuận/nghịch
----------------------
``can_tuoi`` của danh mục P2 là **điều kiện thuận** (lấy từ mục ``ho_tro`` của
nguồn), không phải điều kiện bắt buộc. Các mô tả ``ho_tro``/``pha_cach`` dạng
văn bản được ghi lại với trạng thái ``chua_kiem_tra`` — không tự diễn giải.
"""
from __future__ import annotations

from typing import Any, Iterator

from backend.app.schemas.horoscope_contract import MISSING
from backend.app.services.cach_cuc_catalog import (
    batch_candidates,
    catalog_signature,
    load_catalog,
)
from backend.app.services.palace_relations import (
    REL_DONG_CUNG,
    REL_GIAP_CUNG,
    REL_TAM_HOP,
    REL_XUNG_CHIEU,
    chi_name_of,
    dac_tinh_in_palace,
    doi_cung,
    giap_cung,
    normalize_chi_name,
    quan_he,
    resolve_anchor,
    tam_hop,
)
from backend.app.services.tu_hoa_tables import normalize_star

OUTCOME_FULL = "khop_du"
OUTCOME_PARTIAL = "khop_mot_phan"
OUTCOME_NONE = "khong_khop"
OUTCOME_UNKNOWN = "chua_the_danh_gia"
OUTCOMES: tuple[str, ...] = (OUTCOME_FULL, OUTCOME_PARTIAL, OUTCOME_NONE, OUTCOME_UNKNOWN)

CONDITION_DAT = "dat"
CONDITION_KHONG_DAT = "khong_dat"
CONDITION_UNKNOWN = "chua_kiem_tra"
CONDITION_STATUSES: tuple[str, ...] = (
    CONDITION_DAT, CONDITION_KHONG_DAT, CONDITION_UNKNOWN,
)
CONDITION_GROUP_STRUCTURE = "cau_truc"
CONDITION_GROUP_SUPPLEMENT = "bo_sung"

# Bốn nhóm sao của ``describe_palace``; ``risk_stars`` là bản sao của các nhóm
# này nên không lặp để tránh trùng sao.
_STAR_GROUP_KEYS = ("chinh_tinh", "cat_tinh", "sat_tinh", "phu_tinh_khac")
_HOA_STARS = frozenset({
    normalize_star("Hóa Khoa"), normalize_star("Hóa Quyền"),
    normalize_star("Hóa Lộc"), normalize_star("Hóa Kỵ"),
})
RELATION_LABELS = {
    "dong_cung": "đồng cung",
    "tam_hop": "tam hợp",
    "xung_chieu": "xung chiếu",
    "giap_cung": "giáp cung",
    "khong": "không có quan hệ",
}

DETECTION_VERSION = 1
DETECTION_CAVEAT = (
    "Kết quả nhận diện bằng code trên dữ kiện lá số; quy tắc chưa được duyệt "
    "nội dung (trạng thái chi_tham_khao), không dùng như kết luận vận mệnh."
)


def _iter_stars(palace: dict[str, Any]) -> Iterator[dict[str, Any]]:
    saos = palace.get("saos")
    if isinstance(saos, list):
        for star in saos:
            if isinstance(star, dict):
                yield star
        return
    for key in _STAR_GROUP_KEYS:
        group = palace.get(key)
        if isinstance(group, list):
            for star in group:
                if isinstance(star, dict):
                    yield star


def _star_name(star: dict[str, Any]) -> str:
    name = star.get("ten") or star.get("saoTen") or ""
    return name if isinstance(name, str) else ""


def _palace_data_error(palaces: Any) -> str | None:
    """Trả lý do khi dữ kiện cung/sao không đủ để nhận diện; None khi đủ."""
    if not isinstance(palaces, list) or len(palaces) < 12:
        return "Chưa có đủ 12 cung để đối chiếu quy tắc."
    seen: set[int] = set()
    total_stars = 0
    for palace in palaces:
        if not isinstance(palace, dict):
            return "Dữ liệu cung không hợp lệ (không phải mapping)."
        cung_so = palace.get("cung_so")
        if type(cung_so) is not int or not 1 <= cung_so <= 12:
            return "Dữ liệu cung thiếu cung_so hợp lệ 1..12."
        if cung_so in seen:
            return f"Dữ liệu cung trùng cung_so {cung_so}."
        seen.add(cung_so)
        saos = palace.get("saos")
        if isinstance(saos, list):
            total_stars += len(saos)
        else:
            for key in _STAR_GROUP_KEYS:
                group = palace.get(key)
                if isinstance(group, list):
                    total_stars += len(group)
    if seen != set(range(1, 13)):
        return "Dữ liệu cung không phủ đủ 12 địa chi."
    if total_stars == 0:
        return "Chưa có dữ liệu an sao để xác định vị trí các sao."
    return None


def _build_star_index(palaces: list[dict[str, Any]]) -> dict[str, list[tuple[dict[str, Any], dict[str, Any]]]]:
    index: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for palace in palaces:
        for star in _iter_stars(palace):
            key = normalize_star(_star_name(star))
            if not key:
                continue
            index.setdefault(key, []).append((palace, star))
    return index


def _build_fact_index(facts: Any) -> dict[tuple[str, str], list[str]]:
    index: dict[tuple[str, str], list[str]] = {}
    for fact in facts or []:
        if not isinstance(fact, dict) or fact.get("nhom") == "luu_nien":
            continue
        star_key = normalize_star(str(fact.get("sao") or ""))
        chi_key = normalize_chi_name(fact.get("dia_chi"))
        if not star_key or chi_key is None:
            continue
        fact_id = fact.get("fact_id")
        if fact_id is None:
            continue
        index.setdefault((star_key, chi_key), []).append(str(fact_id))
    return index


def _facts_for(index: dict[tuple[str, str], list[str]], star_name: str,
               palace: dict[str, Any]) -> list[str]:
    chi_key = normalize_chi_name(palace.get("chuan_ten"))
    if chi_key is None:
        return []
    return index.get((normalize_star(star_name), chi_key), [])


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _condition(code: str, group: str, description: str, status: str,
               **extra: Any) -> dict[str, Any]:
    if status not in CONDITION_STATUSES:
        raise ValueError(f"Trạng thái điều kiện không hợp lệ: {status!r}")
    return {"ma": code, "nhom": group, "mo_ta": description,
            "trang_thai": status, **extra}


def _allowed_positions(anchor: int, relations: list[str]) -> set[int]:
    """Các cung được phép của một sao so với cung neo (đồng cung luôn gồm neo)."""
    allowed = {anchor}
    if REL_TAM_HOP in relations:
        allowed.update(tam_hop(anchor))
    if REL_XUNG_CHIEU in relations:
        allowed.add(doi_cung(anchor))
    if REL_GIAP_CUNG in relations:
        allowed.update(giap_cung(anchor))
    return allowed


def _first_hit(placements: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]],
               name: str, allowed: set[int] | None = None):
    for palace, star in placements.get(name, []):
        if allowed is None or palace.get("cung_so") in allowed:
            return palace, star
    return None


def _match_against_anchor(required: list[str], placements: dict, anchor: int,
                          relations: list[str]) -> dict[str, tuple] | None:
    allowed = _allowed_positions(anchor, relations)
    chosen: dict[str, tuple] = {}
    for name in required:
        hit = _first_hit(placements, name, allowed)
        if hit is None:
            return None
        chosen[name] = hit
    return chosen


def _match_group(required: list[str], placements: dict,
                 relations: list[str]) -> tuple[dict[str, tuple] | None, int | None]:
    """Tìm một cung neo sao cho mọi sao bắt buộc đều nằm trong nhóm quan hệ."""
    for anchor_palace, _ in placements.get(required[0], []):
        anchor = anchor_palace.get("cung_so")
        if type(anchor) is not int:
            continue
        chosen = _match_against_anchor(required, placements, anchor, relations)
        if chosen is not None:
            return chosen, anchor
    return None, None


def _actual_relation(placements: dict, required: list[str], anchor: int | None) -> str | None:
    if not required:
        return None
    first = _first_hit(placements, required[0])
    if first is None:
        return None
    if anchor is not None:
        return quan_he(anchor, first[0]["cung_so"])
    if len(required) < 2:
        return None
    second = _first_hit(placements, required[1])
    if second is None:
        return None
    return quan_he(first[0]["cung_so"], second[0]["cung_so"])


def _birth_stem(features: dict[str, Any]) -> str | None:
    basic = features.get("thong_tin_co_ban") or {}
    can_chi = basic.get("can_chi_nam")
    if not isinstance(can_chi, str):
        return None
    parts = can_chi.split()
    return parts[0] if parts else None


def _favourable_conditions(rule: dict[str, Any], features: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    stems = rule.get("can_tuoi") or []
    if stems:
        stem = _birth_stem(features)
        if stem is None:
            status, actual = CONDITION_UNKNOWN, MISSING
        elif stem in stems:
            status, actual = CONDITION_DAT, stem
        else:
            status, actual = CONDITION_KHONG_DAT, stem
        result.append(_condition(
            "can_tuoi", CONDITION_GROUP_STRUCTURE,
            f"Can tuổi thuận: {', '.join(stems)}", status, gia_tri_thuc_te=actual,
        ))
    for text in rule.get("dieu_kien", {}).get("ho_tro") or []:
        result.append(_condition(
            "ho_tro_nguon", CONDITION_GROUP_STRUCTURE, str(text), CONDITION_UNKNOWN,
            ly_do="Mô tả nguồn chưa có điều kiện máy đọc; không tự diễn giải.",
        ))
    return result


def _adverse_conditions(rule: dict[str, Any]) -> list[dict[str, Any]]:
    return [_condition(
        "pha_cach_nguon", CONDITION_GROUP_STRUCTURE, str(text), CONDITION_UNKNOWN,
        ly_do="Mô tả nguồn chưa có điều kiện máy đọc; không tự kết luận phá cách.",
    ) for text in rule.get("dieu_kien", {}).get("pha_cach") or []]


def _unknown_result(rule: dict[str, Any], reason: str,
                    conditions: list[dict[str, Any]],
                    favourable: list[dict[str, Any]] | None = None,
                    adverse: list[dict[str, Any]] | None = None,
                    fact_ids: list[str] | None = None) -> dict[str, Any]:
    conditions = conditions or [_condition(
        "du_lieu_la_so", CONDITION_GROUP_STRUCTURE, reason, CONDITION_UNKNOWN,
    )]
    return _result(rule, OUTCOME_UNKNOWN, conditions, favourable or [], adverse or [],
                   fact_ids or [], ly_do=f"Chưa thể đánh giá: {reason}")


def _result(rule: dict[str, Any], outcome: str, conditions: list[dict[str, Any]],
            favourable: list[dict[str, Any]], adverse: list[dict[str, Any]],
            fact_ids: list[str], ly_do: str) -> dict[str, Any]:
    unknown = [c["mo_ta"] for c in conditions if c["trang_thai"] == CONDITION_UNKNOWN]
    return {
        "rule_id": rule["id"],
        "ten": rule.get("ten", ""),
        "nhom": rule.get("nhom", ""),
        "trang_thai_noi_dung": rule.get("trang_thai", ""),
        "san_sang_thuc_thi": bool(rule.get("san_sang_thuc_thi")),
        "ung_vien_ban_dau": bool(rule.get("ung_vien_ban_dau")),
        "ket_qua": outcome,
        "dieu_kien": conditions,
        "dieu_kien_thuan": favourable,
        "dieu_kien_nghich": adverse,
        "dieu_kien_chua_kiem_tra": unknown,
        "co_dieu_kien_nghich_chua_kiem_tra": any(
            c["trang_thai"] == CONDITION_UNKNOWN for c in adverse),
        "fact_ids": _unique(fact_ids),
        "ly_do": ly_do,
    }


def _outcome(conditions: list[dict[str, Any]]) -> str:
    structural = [c for c in conditions if c["nhom"] == CONDITION_GROUP_STRUCTURE]
    if any(c["trang_thai"] == CONDITION_KHONG_DAT for c in structural):
        return OUTCOME_NONE
    if any(c["trang_thai"] == CONDITION_UNKNOWN for c in structural):
        return OUTCOME_UNKNOWN
    supplementary = [c for c in conditions if c["nhom"] == CONDITION_GROUP_SUPPLEMENT]
    if any(c["trang_thai"] == CONDITION_KHONG_DAT for c in supplementary):
        return OUTCOME_PARTIAL
    if any(c["trang_thai"] == CONDITION_UNKNOWN for c in supplementary):
        return OUTCOME_UNKNOWN
    return OUTCOME_FULL


def _reason_text(outcome: str, conditions: list[dict[str, Any]],
                 favourable: list[dict[str, Any]]) -> str:
    if outcome == OUTCOME_FULL:
        text = "Khớp đủ điều kiện bắt buộc; chỉ là nhận diện cấu trúc, chưa kết luận vận mệnh."
        unmet_favourable = [c for c in favourable if c["trang_thai"] == CONDITION_KHONG_DAT]
        if unmet_favourable:
            text += " Chưa đạt điều kiện thuận: " + "; ".join(c["mo_ta"] for c in unmet_favourable) + "."
        return text
    if outcome == OUTCOME_PARTIAL:
        failed = [c for c in conditions if c["trang_thai"] == CONDITION_KHONG_DAT]
        return "Khớp cấu trúc nhưng thiếu điều kiện bổ sung: " + "; ".join(c["mo_ta"] for c in failed) + "."
    if outcome == OUTCOME_NONE:
        failed = [c for c in conditions
                  if c["nhom"] == CONDITION_GROUP_STRUCTURE
                  and c["trang_thai"] == CONDITION_KHONG_DAT]
        return "Không khớp: " + "; ".join(c["mo_ta"] for c in failed) + "."
    unknown = [c for c in conditions if c["trang_thai"] == CONDITION_UNKNOWN]
    return "Chưa thể đánh giá: " + "; ".join(c["mo_ta"] for c in unknown) + "."


def _evaluate_rule(rule: dict[str, Any], features: dict[str, Any],
                   palaces: Any, star_index: dict, fact_index: dict) -> dict[str, Any]:
    favourable = _favourable_conditions(rule, features)
    adverse = _adverse_conditions(rule)

    time_layer = rule.get("tang_thoi_gian")
    if time_layer != "la_so_goc":
        return _unknown_result(
            rule, f"Quy tắc thuộc tầng thời gian {time_layer!r}; P3 bản đầu chỉ nhận diện lá số gốc.",
            [_condition("tang_thoi_gian", CONDITION_GROUP_STRUCTURE,
                        f"Tầng thời gian {time_layer}", CONDITION_UNKNOWN)],
            favourable=favourable, adverse=adverse,
        )

    data_error = _palace_data_error(palaces)
    if data_error:
        return _unknown_result(
            rule, data_error,
            [_condition("du_lieu_la_so", CONDITION_GROUP_STRUCTURE,
                        data_error, CONDITION_UNKNOWN)],
            favourable=favourable, adverse=adverse,
        )

    required = [name for name in (rule.get("sao") or []) if isinstance(name, str) and name.strip()]
    if not required:
        return _unknown_result(rule, "Quy tắc không có sao bắt buộc để đối chiếu.",
                               favourable=favourable, adverse=adverse)

    conditions: list[dict[str, Any]] = []
    placements: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    fact_ids: list[str] = []
    any_hoa = any(key in _HOA_STARS for key in star_index)

    for name in required:
        hits = star_index.get(normalize_star(name), [])
        if hits:
            placements[name] = hits
            conditions.append(_condition(
                f"sao:{name}", CONDITION_GROUP_STRUCTURE,
                f"Sao {name} có trong lá số gốc", CONDITION_DAT,
                cung=[p.get("chuan_ten") for p, _ in hits],
            ))
            for palace, _ in hits:
                fact_ids.extend(_facts_for(fact_index, name, palace))
            continue
        if normalize_star(name) in _HOA_STARS and not any_hoa:
            conditions.append(_condition(
                f"sao:{name}", CONDITION_GROUP_STRUCTURE,
                f"Chưa có dữ liệu Tứ Hóa để xác định {name}", CONDITION_UNKNOWN,
            ))
        else:
            conditions.append(_condition(
                f"sao:{name}", CONDITION_GROUP_STRUCTURE,
                f"Sao {name} không có trong lá số gốc", CONDITION_KHONG_DAT,
            ))

    anchor: int | None = None
    anchor_rule = rule.get("cung_neo")
    if anchor_rule:
        try:
            anchor = resolve_anchor(palaces, anchor_rule)
            conditions.append(_condition(
                "cung_neo", CONDITION_GROUP_STRUCTURE,
                f"Cung neo {anchor_rule} xác định được", CONDITION_DAT,
                cung=chi_name_of(anchor),
            ))
        except ValueError as exc:
            conditions.append(_condition(
                "cung_neo", CONDITION_GROUP_STRUCTURE,
                f"Không xác định được cung neo {anchor_rule!r}", CONDITION_UNKNOWN,
                ly_do=str(exc),
            ))

    relations = list(rule.get("quan_he") or [])
    chosen: dict[str, tuple] | None = None
    relation_status: str | None = None
    if anchor is not None:
        if not required:
            relation_status = CONDITION_UNKNOWN
        else:
            chosen = _match_against_anchor(required, placements, anchor, relations)
            relation_status = CONDITION_DAT if chosen else CONDITION_KHONG_DAT
    elif len(required) >= 2:
        if not relations:
            relation_status = CONDITION_UNKNOWN
        else:
            chosen, _ = _match_group(required, placements, relations)
            relation_status = CONDITION_DAT if chosen else CONDITION_KHONG_DAT
    else:
        chosen = {name: _first_hit(placements, name) for name in required}
        chosen = {name: hit for name, hit in chosen.items() if hit is not None}

    if relation_status is not None:
        actual = _actual_relation(placements, required, anchor)
        description = (f"Quan hệ {', '.join(RELATION_LABELS.get(r, r) for r in relations) or 'đồng cung'} "
                       f"giữa {', '.join(required)}")
        if anchor is not None:
            description += f" và cung neo {chi_name_of(anchor)}"
        conditions.append(_condition(
            "quan_he", CONDITION_GROUP_STRUCTURE, description,
            relation_status if chosen or relation_status == CONDITION_KHONG_DAT else CONDITION_UNKNOWN,
            quan_he_thuc_te=actual,
        ))

    # Cung/chi của vị trí neo (cung neo nếu có, ngược lại cung của sao đầu tiên).
    branch_anchor = anchor
    if branch_anchor is None and required:
        first = _first_hit(placements, required[0])
        branch_anchor = first[0].get("cung_so") if first else None
    allowed_chi = [normalize_chi_name(c) for c in (rule.get("chi") or [])]
    allowed_chi = [c for c in allowed_chi if c is not None]
    if allowed_chi:
        if branch_anchor is None:
            conditions.append(_condition(
                "chi", CONDITION_GROUP_STRUCTURE,
                f"Vị trí phải thuộc {', '.join(allowed_chi)}", CONDITION_UNKNOWN,
            ))
        else:
            actual_chi = chi_name_of(branch_anchor)
            status = CONDITION_DAT if actual_chi in allowed_chi else CONDITION_KHONG_DAT
            conditions.append(_condition(
                "chi", CONDITION_GROUP_STRUCTURE,
                f"Vị trí phải thuộc {', '.join(allowed_chi)}", status,
                gia_tri_thuc_te=actual_chi,
            ))

    for name, state in (rule.get("trang_thai_sao") or {}).items():
        hit = (chosen or {}).get(name) or _first_hit(placements, name)
        if hit is None:
            conditions.append(_condition(
                f"trang_thai_sao:{name}", CONDITION_GROUP_SUPPLEMENT,
                f"Trạng thái {name} phải là {state}", CONDITION_UNKNOWN,
                gia_tri_thuc_te=MISSING,
            ))
            continue
        actual = dac_tinh_in_palace(hit[0], name)
        if actual == MISSING:
            status = CONDITION_UNKNOWN
        elif actual == state:
            status = CONDITION_DAT
        else:
            status = CONDITION_KHONG_DAT
        conditions.append(_condition(
            f"trang_thai_sao:{name}", CONDITION_GROUP_SUPPLEMENT,
            f"Trạng thái {name} phải là {state}", status,
            gia_tri_thuc_te=actual,
        ))

    if chosen:
        for name, (palace, _) in chosen.items():
            fact_ids.extend(_facts_for(fact_index, name, palace))

    outcome = _outcome(conditions)
    return _result(rule, outcome, conditions, favourable, adverse, fact_ids,
                   _reason_text(outcome, conditions, favourable))


def _fact_sort_key(fact_id: str):
    return (0, int(fact_id)) if fact_id.isdigit() else (1, fact_id)


def detect_cach_cuc(features: dict[str, Any], catalog: dict | None = None,
                    rules: list[dict[str, Any]] | None = None,
                    facts: list[dict[str, Any]] | None = None,
                    context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Nhận diện cách cục trên dữ kiện lá số; mặc định chạy 8 quy tắc bản đầu.

    ``rules`` cho phép chạy một tập quy tắc cụ thể (dùng trong kiểm thử hoặc khi
    P2 duyệt thêm). Không truyền ``rules`` thì dùng ``batch_candidates``.
    """
    catalog = catalog or load_catalog()
    selected = list(rules) if rules is not None else batch_candidates(catalog)
    features = features or {}
    if facts is None:
        from backend.app.services.horoscope_analysis import build_star_facts
        facts = build_star_facts(features, context or {})

    palaces = features.get("palaces")
    star_index = _build_star_index(palaces) if isinstance(palaces, list) else {}
    fact_index = _build_fact_index(facts)

    results = [_evaluate_rule(rule, features, palaces, star_index, fact_index)
               for rule in selected]

    usage: dict[str, list[str]] = {}
    for result in results:
        for fact_id in result["fact_ids"]:
            usage.setdefault(fact_id, []).append(result["rule_id"])
    fact_reuse = [
        {"fact_id": fact_id, "rule_ids": rule_ids}
        for fact_id, rule_ids in sorted(usage.items(), key=lambda item: _fact_sort_key(item[0]))
        if len(rule_ids) >= 2
    ]

    summary = {outcome: 0 for outcome in OUTCOMES}
    for result in results:
        summary[result["ket_qua"]] += 1

    return {
        "phien_ban": DETECTION_VERSION,
        "catalog_signature": catalog_signature(catalog),
        "tong_so_quy_tac": len(results),
        "tom_tat": summary,
        "rules": results,
        "fact_reuse": fact_reuse,
        "canh_bao": DETECTION_CAVEAT,
    }


def check_rule_ids(reading: dict[str, Any], detection: dict[str, Any]) -> str | None:
    """Chặn AI tự thêm cách cục ngoài kết quả nhận diện.

    - ``rule_ids`` vắng mặt/None/``MISSING``: báo cáo cũ, bỏ qua.
    - Danh sách phải gồm rule_id có trong ``detection`` và quy tắc đó phải
      ``khop_du`` hoặc ``khop_mot_phan``; không được dẫn quy tắc ``khong_khop``
      hay ``chua_the_danh_gia``.
    """
    detected = {r.get("rule_id"): r for r in detection.get("rules") or [] if isinstance(r, dict)}
    for section in ("luan_diem", "ket_luan"):
        for point in reading.get(section) or []:
            if not isinstance(point, dict):
                continue
            rule_ids = point.get("rule_ids")
            if rule_ids is None or rule_ids == MISSING:
                continue
            if not isinstance(rule_ids, list) or not all(isinstance(r, str) for r in rule_ids):
                return f'"{section}" có rule_ids không phải danh sách chuỗi.'
            for rule_id in rule_ids:
                result = detected.get(rule_id)
                if result is None:
                    return (f'rule_id "{rule_id}" không có trong kết quả nhận diện; '
                            'không được tự thêm cách cục ngoài kết quả code.')
                if result.get("ket_qua") not in (OUTCOME_FULL, OUTCOME_PARTIAL):
                    return (f'rule_id "{rule_id}" có kết quả "{result.get("ket_qua")}"; '
                            'chỉ được dẫn quy tắc khớp đủ hoặc khớp một phần.')
    return None
