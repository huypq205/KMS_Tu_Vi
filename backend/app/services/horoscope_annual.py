# -*- coding: utf-8 -*-
"""An lưu niên theo năm Can Chi: vòng Thái Tuế và lưu Tứ Hóa.

Quy tắc tham chiếu vendor/lasotuvi/App.py:
- Vòng Thái Tuế: 12 sao, offset tính từ cung Thái Tuế (App.py dòng 150-185).
- Bảng Tứ Hóa theo 10 thiên can (App.py dòng 402-451).

Đây là lớp dữ kiện tất định (không gọi AI): dùng để hiển thị ngay cho người xem
và làm đầu vào cho phần luận giải. Các sao lưu niên chỉ để tham khảo, chiêm nghiệm;
không phải dự báo sự kiện.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
import json
import unicodedata
from backend.app.schemas.annual_report import AnnualReport

ROOT = Path(__file__).resolve().parents[3]
VENDOR_PATH = ROOT / "vendor"
if str(VENDOR_PATH) not in sys.path:
    sys.path.insert(0, str(VENDOR_PATH))

from lasotuvi.AmDuong import diaChi, dichCung, thienCan  # noqa: E402
from backend.app.services.tu_hoa_tables import (  # noqa: E402
    TU_HOA_CODES, find_parent_palace, get_tu_hoa_table, table_metadata,
)

TU_HOA_NAMES = {
    "HOA_LOC": "Hóa lộc",
    "HOA_QUYEN": "Hóa quyền",
    "HOA_KHOA": "Hóa khoa",
    "HOA_KY": "Hóa kỵ",
}

# Compatibility export: always the default vendor table. Runtime selection below
# uses table ids so an environment change cannot relabel an older chart.
TU_HOA_BY_CAN: dict[str, dict[str, str]] = get_tu_hoa_table('lasotuvi')['by_can']

# (tên sao, offset từ Thái Tuế, phân loại). Nguồn: vendor/lasotuvi/App.py dòng 150-185.
VONG_THAI_TUE: tuple[tuple[str, int, str], ...] = (
    ("Thái Tuế", 0, "trung"),
    ("Thiếu Dương", 1, "trung"),
    ("Tang Môn", 2, "hung"),
    ("Thiếu Âm", 3, "trung"),
    ("Quan Phù", 4, "cat"),
    ("Tử Phủ", 5, "cat"),
    ("Tuế Phá", 6, "hung"),
    ("Long Đức", 7, "cat"),
    ("Bạch Hổ", 8, "hung"),
    ("Phúc Đức", 9, "cat"),
    ("Điếu Khách", 10, "cat"),
    ("Trực Phù", 11, "cat"),
)

CAUTION_STARS = ("Thái Tuế", "Tuế Phá", "Bạch Hổ", "Tang Môn")

METHOD = (
    "An lưu niên theo vòng Thái Tuế (12 sao) và lưu Tứ Hóa theo can năm."
)
LIMITATIONS = (
    "Chỉ an vòng Thái Tuế và lưu Tứ Hóa; chưa an các lưu tinh khác. "
    "Dùng để tham khảo và chiêm nghiệm, không phải dự báo sự kiện."
)

# P4: phân mức tín hiệu là một quy tắc riêng, có phiên bản và điều kiện code
# truy được. Đổi ngưỡng phải tăng phiên bản và cập nhật test tương ứng.
ACTIVATION_RULE_VERSION = 2
ACTIVATION_LEVELS = ("nhan", "vua", "nang", "chua_du_du_lieu")
ACTIVATION_LEVEL_LABELS = {
    "nhan": "Thấp",
    "vua": "Vừa",
    "nang": "Cao",
    "chua_du_du_lieu": "Chưa đủ dữ liệu",
}
ACTIVATION_THRESHOLD = (
    "Có vai trò Mệnh/Thân hoặc từ 2 tín hiệu khác nhau trở lên → Cao; "
    "1 tín hiệu chỉ ở đại hạn/tiểu hạn → Vừa; 0 tín hiệu → Thấp."
)
ACTIVATION_CAVEAT = (
    "Đây là mức tập trung tín hiệu cần xem xét, không phải mức độ xấu hay "
    "độ chắc chắn của dự báo."
)

ROLE_LABELS = {
    "menh": "Mệnh",
    "than": "Thân",
    "dai_han": "Đại hạn",
    "tieu_han": "Tiểu hạn",
}
ROLE_TOPICS = {
    "menh": "Bản thân",
    "than": "Thân và hành động",
    "dai_han": "Vận đại hạn",
    "tieu_han": "Vận tiểu hạn",
}

SIGNAL_RULES = {
    "vong_thai_tue": {
        "id": "luu_nien.vong_thai_tue_trung_cung",
        "mo_ta": "Sao thuộc vòng Thái Tuế trùng cung trọng tâm của năm đang xem.",
    },
    "luu_ky": {
        "id": "luu_nien.luu_ky_trung_cung",
        "mo_ta": "Sao gốc nhận Hóa Kỵ theo can năm, tọa tại cung trọng tâm của năm đang xem.",
    },
}
SIGNAL_MISSING = (
    "Chưa an lưu nguyệt/ngày; không kết luận thời điểm.",
    "Chưa có nguồn luận giải đã duyệt cho tín hiệu lưu niên.",
)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def classify_activation(
    signals: list[dict[str, Any]] | None,
    missing_reasons: list[str] | None = None,
) -> dict[str, Any]:
    """Xếp mức tập trung tín hiệu theo **số tín hiệu**, không theo số vai trò.

    Tín hiệu là đơn vị vật lý đã định danh (sao + cung + tầng thời gian + năm);
    một tín hiệu có thể mang nhiều vai trò. Trùng vai trò không tạo thêm tín
    hiệu, nên không đẩy mức tập trung lên như nhiều chứng cứ độc lập.

    Hiệu chỉnh #1 của plan: một tín hiệu đơn tại Mệnh/Thân **vẫn** giữ mức Cao;
    việc gộp trùng không tự động hạ nhãn. Trùng đại hạn/tiểu hạn trên cùng một
    tín hiệu thì không còn tự đẩy từ Vừa lên Cao.
    """
    signals = list(signals or [])
    missing = [reason for reason in (missing_reasons or []) if reason]
    count = len(signals)
    role_count = sum(len(signal.get("vai_tro") or []) for signal in signals)
    co_menh_than = any(
        {"menh", "than"} & set(signal.get("vai_tro") or []) for signal in signals
    )
    basis = {
        "so_tin_hieu": count,
        "so_vai_tro": role_count,
        "co_menh_than": co_menh_than,
        "nguong": ACTIVATION_THRESHOLD,
    }

    if missing:
        level = "chua_du_du_lieu"
        reason = ("Chưa thể phân mức vì thiếu dữ kiện: " + " ".join(missing)
                  + " " + ACTIVATION_CAVEAT)
    elif not signals:
        level = "nhan"
        reason = (f"Không có tín hiệu lưu niên nào trùng cung trọng tâm, theo quy tắc "
                  f"v{ACTIVATION_RULE_VERSION}. " + ACTIVATION_CAVEAT)
    elif co_menh_than:
        level = "nang"
        reason = (f"Có tín hiệu lưu niên trùng cung Mệnh/Thân, theo quy tắc "
                  f"v{ACTIVATION_RULE_VERSION}. " + ACTIVATION_CAVEAT)
    elif count >= 2:
        level = "nang"
        reason = (f"Có {count} tín hiệu lưu niên khác nhau cùng trùng cung trọng tâm, "
                  f"theo quy tắc v{ACTIVATION_RULE_VERSION}. " + ACTIVATION_CAVEAT)
    else:
        level = "vua"
        reason = (f"Chỉ có 1 tín hiệu lưu niên và không trùng cung Mệnh/Thân, "
                  f"theo quy tắc v{ACTIVATION_RULE_VERSION}. " + ACTIVATION_CAVEAT)

    return {
        "level": level,
        "level_label": ACTIVATION_LEVEL_LABELS[level],
        "level_reason": reason,
        "level_rule_version": ACTIVATION_RULE_VERSION,
        "level_basis": basis,
    }


def build_year_comparison(raw: dict, year: int) -> list[dict]:
    """Compute each valid neighbor independently, preserving the selected table."""
    from backend.app.services.horoscope_features import analyze_year, find_current_dai_han
    cungs=raw['thap_ni_cung']
    table_id=(raw.get('tu_hoa_table') or {}).get('id','lasotuvi')
    birth_year=raw.get('nam_sinh_am',raw['nam_sinh'])
    rows=[]
    for target in (year-1,year,year+1):
        row={'year':target,'status':'out_of_range','can_chi':None,'dai_han':'Chưa tính',
             'tieu_han':'Chưa tính','luu_tu_hoa':[],'tu_hoa_table':None,
             'gioi_han':'Ngoài phạm vi năm 1900–2100; không thực hiện an sao.'}
        if 1900<=target<=2100:
            annual=analyze_year(cungs,target,birth_year)
            decade=find_current_dai_han(cungs,target-birth_year+1) or {}
            minor=annual.get('tieu_han') or {}
            moving=compute_luu_nien(cungs,target,tu_hoa_table_id=table_id)
            row.update(status='available',can_chi=annual['can_chi'],
                dai_han=(f"{decade.get('tu_tuoi')}–{decade.get('den_tuoi')} tuổi · {decade.get('cung_ten')}"
                         if decade else 'Chưa xác định đại hạn ở tuổi này'),
                tieu_han=minor.get('ten','Chưa xác định'),
                luu_tu_hoa=[f"{e['ten_sao']} {e['ten']} · {e['cung_ten']}" for e in moving['luu_tu_hoa']],
                tu_hoa_table=table_id,gioi_han='So sánh dữ kiện theo năm âm lịch; không suy ra sự kiện hoặc thời điểm tháng/ngày.')
        rows.append(row)
    return rows


def _norm(value):
    return ''.join(c for c in unicodedata.normalize('NFD',value.lower()) if unicodedata.category(c)!='Mn')


def build_annual_report(features: dict, facts: list[dict]) -> dict:
    """Assemble locked factual layers server-side; the LLM cannot fill gaps."""
    year=(features.get('nam_xem') or {}).get('year')
    decade=features.get('dai_han_hien_tai') or {}
    decade_branch=decade.get('cung_ten','')
    def layer(items,prefix):
        return {'status':'available' if items else 'missing','noi_dung':prefix+(
            '; '.join(f"{f['sao']} tại {f['cung']} ({f['dia_chi']})" for f in items)
            if items else 'Chưa có dữ kiện phù hợp.'), 'fact_ids':[str(f['fact_id']) for f in items]}
    rows=[]
    for topic,names in [('Sự nghiệp',('Quan lộc','Thiên di','Mệnh')),
                        ('Tài chính',('Tài bạch','Điền trạch','Quan lộc')),
                        ('Tình cảm',('Phu thê','Phúc đức','Mệnh'))]:
        matching=[f for f in facts if _norm(f.get('cung','')) in {_norm(n) for n in names}]
        natal=[f for f in matching if f.get('nhom')!='luu_nien'][:4]
        moving=[f for f in matching if f.get('nhom')=='luu_nien'][:4]
        decadal=[f for f in facts if decade_branch and _norm(f.get('dia_chi',''))==_norm(decade_branch)
                 and f.get('nhom')!='luu_nien'][:3]
        rows.append({'chu_de':topic,'la_so_goc':layer(natal,'Sao gốc: '),
            'dai_han':layer(decadal,f"Đại hạn {decade.get('tu_tuoi','—')}–{decade.get('den_tuoi','—')} tuổi tại {decade.get('ten_linh_vuc','—')} ({decade_branch or '—'}); sao gốc tại cung hạn: "),
            'luu_nien':layer(moving,f'Lưu niên {year}: '),
            'luu_nguyet':{'status':'missing','noi_dung':'Chưa an lưu nguyệt; không kết luận theo tháng.','fact_ids':[]},
            'phan_chung':'Chưa đối chiếu đầy đủ điều kiện thuận/nghịch trong từng sách; sao cùng cung chưa chứng minh một sự kiện.',
            'muc_tin_cay':'yeu','loai_ket_luan':'cau_truc'})
    comparison=features.get('annual_comparison') or [
        {'year':y,'status':'missing','can_chi':None,'dai_han':'Chưa có dữ liệu',
         'tieu_han':'Chưa có dữ liệu','luu_tu_hoa':[],'tu_hoa_table':None,
         'gioi_han':'Chưa có dữ kiện gốc để tính so sánh.'} for y in
        ((year-1,year,year+1) if isinstance(year,int) else (None,None,None))]
    missing=['Chưa an lưu nguyệt hoặc khung ngày/tháng.',
             'Chưa đủ căn cứ để khẳng định sự kiện, thu nhập, hôn nhân hoặc sức khỏe.',
             'Chưa có phản chứng đã đối chiếu đầy đủ theo từng sách hoặc mẫu nghiệm lý đủ đại diện.']
    if (features.get('thong_tin_co_ban') or {}).get('input_confidence') in ('C','D'):
        missing.append('Dữ liệu giờ sinh chưa chắc chắn (mức C/D); chỉ kết luận cấu trúc, không kết luận thời điểm/sự kiện.')
    return AnnualReport.model_validate({'bang_kich_hoat':rows,'so_sanh_nam':comparison,
                                       'viec_chua_du_can_cu':missing}).model_dump()


def validate_annual_report(report: dict, facts: list[dict]):
    checked=AnnualReport.model_validate(report)
    fact_map={str(f['fact_id']):f for f in facts}
    for row in checked.bang_kich_hoat:
        if row.luu_nguyet.status!='missing' or row.luu_nguyet.fact_ids:
            raise ValueError('Chưa hỗ trợ lưu nguyệt.')
        for key in ('la_so_goc','dai_han','luu_nien','luu_nguyet'):
            layer=getattr(row,key)
            if any(i not in fact_map for i in layer.fact_ids): raise ValueError('fact_id không hợp lệ.')
            if layer.status=='missing' and layer.fact_ids: raise ValueError('Mục thiếu không có fact.')
            for fid in layer.fact_ids:
                if (fact_map[fid].get('nhom')=='luu_nien') != (key=='luu_nien'):
                    raise ValueError('Sai tầng dữ kiện.')
        if row.muc_tin_cay!='yeu': raise ValueError('Bảng dữ kiện chưa đủ điều kiện tăng mức tin cậy.')
    if '%' in json.dumps(report,ensure_ascii=False): raise ValueError('Không dùng phần trăm.')
    return checked


def can_chi_of_year(year: int) -> tuple[str, str]:
    """Trả về (can, chi) của năm âm lịch. 2026 -> ("Bính", "Ngọ")."""
    can = thienCan[(year - 4) % 10 + 1]["tenCan"]
    chi = diaChi[(year - 4) % 12 + 1]["tenChi"]
    return can, chi


def tu_hoa_stars_for_can(can: str, table_id: str | None = None) -> dict[str, str]:
    """Bốn sao nhận Tứ Hóa theo can (map code -> tên sao gốc)."""
    return get_tu_hoa_table(table_id)['by_can'].get(can, {})


def _find_star_palace(cungs: list[dict[str, Any]], star_name: str) -> dict[str, Any] | None:
    """Tìm sao gốc, kể cả cách viết Tả phù/Tả Phụ của hai nguồn."""
    return find_parent_palace(cungs, star_name)


def _palace_brief(cung: dict[str, Any] | None, star_name: str) -> dict[str, Any]:
    if not cung:
        return {
            "ten": star_name,
            "cung_so": None,
            "cung_ten": "",
            "chuan_ten": "",
            "dia_chi": "",
        }
    return {
        "ten": star_name,
        "cung_so": cung.get("cung_so"),
        "cung_ten": cung.get("ten_cung") or cung.get("chuan_ten", ""),
        "chuan_ten": cung.get("chuan_ten", ""),
        "dia_chi": cung.get("chuan_ten", ""),
    }


def _signal_id(year: int, source: str, star: str, cung_so: int) -> str:
    slug = _norm(star).replace(" ", "-")
    return f"ln-{year}-{source.replace('_', '-')}-{slug}-{cung_so}"


def _make_signal(
    display_name: str,
    root_name: str,
    entry: dict[str, Any],
    vai_tro: list[str],
    source: str,
    year: int,
    can: str,
    can_chi: str,
) -> dict[str, Any]:
    return {
        "tin_hieu_id": _signal_id(year, source, display_name, entry["cung_so"]),
        "sao": display_name,
        "sao_goc": root_name,
        "loai_tin_hieu": source,
        "loai": entry.get("loai", "hung"),
        "cung_so": entry.get("cung_so"),
        "cung_ten": entry.get("cung_ten", ""),
        "dia_chi": entry.get("dia_chi", ""),
        "tang_thoi_gian": "luu_nien",
        "nam": year,
        "can": can,
        "can_chi": can_chi,
        "vai_tro": list(vai_tro),
        "so_vai_tro": len(vai_tro),
    }


def _enrich_signal(signal: dict[str, Any], others: list[dict[str, Any]]) -> None:
    """Gắn phần "vì sao" tất định: dữ kiện · quy tắc · chủ đề · điều kiện thiếu."""
    rule = SIGNAL_RULES[signal["loai_tin_hieu"]]
    role_labels = [ROLE_LABELS[role] for role in signal["vai_tro"]]
    topics = _unique(
        [ROLE_TOPICS[role] for role in signal["vai_tro"]] + [signal["cung_ten"]]
    )
    if signal["loai_tin_hieu"] == "luu_ky":
        start = (
            f"{signal['sao_goc']} nhận Hóa Kỵ theo can {signal['can']} của năm "
            f"{signal['can_chi']}; đây là tín hiệu lưu niên gắn với sao gốc, tọa tại "
            f"cung {signal['cung_ten']} ({signal['dia_chi']})."
        )
    else:
        start = (
            f"{signal['sao']} là sao thuộc vòng lưu niên của năm {signal['can_chi']}, "
            f"tọa tại cung {signal['cung_ten']} ({signal['dia_chi']})."
        )
    explanation = (
        start
        + f" Hệ thống xếp vào nhóm cần xem xét vì vị trí trùng cung "
          f"{', '.join(role_labels)} theo quy tắc {rule['id']}."
    )
    if others:
        explanation += (
            " Cùng cung còn " + ", ".join(other["sao"] for other in others)
            + "; đây là tín hiệu khác, cùng thuộc tầng lưu niên — "
              "không phải hai tầng xác nhận."
        )
    explanation += " Riêng tín hiệu này chưa đủ để kết luận một sự kiện cụ thể."
    signal["vi_sao"] = {
        "du_kien": {
            "sao": signal["sao"],
            "sao_goc": signal["sao_goc"],
            "cung_so": signal["cung_so"],
            "cung_ten": signal["cung_ten"],
            "dia_chi": signal["dia_chi"],
            "tang_thoi_gian": signal["tang_thoi_gian"],
            "nam": signal["nam"],
            "can_chi": signal["can_chi"],
        },
        "quy_tac": dict(rule),
        "chu_de": topics,
        "dieu_kien_thieu": list(SIGNAL_MISSING),
        "tin_hieu_cung_cung": [other["tin_hieu_id"] for other in others],
        "giai_thich": explanation,
    }


def compute_luu_nien(
    thap_ni_cung: list[dict[str, Any]],
    year: int,
    cung_menh_so: int | None = None,
    cung_than_so: int | None = None,
    dai_han_cung_so: int | None = None,
    tieu_han_cung_so: int | None = None,
    tu_hoa_table_id: str | None = None,
) -> dict[str, Any]:
    """An lưu niên cho một năm: Can Chi, vòng Thái Tuế, lưu Tứ Hóa và tín hiệu."""
    can, chi = can_chi_of_year(year)
    table = get_tu_hoa_table(tu_hoa_table_id)
    method = (
        f"{METHOD} Bảng Tứ Hóa: {table['school']}. Phân mức tín hiệu theo quy tắc "
        f"v{ACTIVATION_RULE_VERSION}, dựa trên số tín hiệu đã định danh (không phải "
        "số vai trò trùng khớp)."
    )
    by_cung_so = {c.get("cung_so"): c for c in thap_ni_cung}
    thai_tue_cung = next((c for c in thap_ni_cung if c.get("chuan_ten") == chi), None)

    vong: dict[str, dict[str, Any]] = {}
    if thai_tue_cung:
        for star_name, offset, loai in VONG_THAI_TUE:
            cung_so = dichCung(thai_tue_cung["cung_so"], offset)
            entry = _palace_brief(by_cung_so.get(cung_so), star_name)
            entry["loai"] = loai
            vong[star_name] = entry

    luu_tu_hoa: list[dict[str, Any]] = []
    for code in TU_HOA_CODES:
        star_name = table['by_can'][can][code]
        cung = _find_star_palace(thap_ni_cung, star_name)
        entry = _palace_brief(cung, star_name)
        entry.update({"ten_sao": star_name, "code": code, "ten": TU_HOA_NAMES[code]})
        luu_tu_hoa.append(entry)

    roles: list[tuple[str, int]] = []
    if cung_menh_so:
        roles.append(("menh", cung_menh_so))
    if cung_than_so:
        roles.append(("than", cung_than_so))
    if dai_han_cung_so:
        roles.append(("dai_han", dai_han_cung_so))
    if tieu_han_cung_so:
        roles.append(("tieu_han", tieu_han_cung_so))

    signals: list[dict[str, Any]] = []

    def add_signal(display_name: str, root_name: str, entry: dict[str, Any],
                   source: str) -> None:
        cung_so = entry.get("cung_so")
        if cung_so is None:
            return
        vai_tro = [role for role, role_cung_so in roles if role_cung_so == cung_so]
        if not vai_tro:
            return
        signals.append(_make_signal(
            display_name, root_name, entry, vai_tro, source, year, can, f"{can} {chi}",
        ))

    for star_name in CAUTION_STARS:
        entry = vong.get(star_name)
        if entry:
            add_signal(star_name, star_name, entry, "vong_thai_tue")

    for entry in luu_tu_hoa:
        if entry["code"] != "HOA_KY":
            continue
        add_signal(f"{entry['ten_sao']} lưu Kỵ", entry["ten_sao"], entry, "luu_ky")

    by_palace: dict[int, list[dict[str, Any]]] = {}
    for signal in signals:
        by_palace.setdefault(signal["cung_so"], []).append(signal)
    for signal in signals:
        others = [other for other in by_palace[signal["cung_so"]] if other is not signal]
        _enrich_signal(signal, others)

    missing: list[str] = []
    valid_palaces = {
        c.get("cung_so") for c in thap_ni_cung
        if isinstance(c, dict) and type(c.get("cung_so")) is int
    }
    if len(valid_palaces) < 12:
        missing.append("Dữ liệu lá số chưa đủ 12 cung; kết quả an lưu niên có thể thiếu.")
    if not thai_tue_cung:
        missing.append(
            f"Chưa xác định được cung Thái Tuế theo chi {chi} của năm {year}; "
            "không đủ dữ liệu an vòng lưu niên."
        )
    if not roles:
        missing.append(
            "Chưa có cung trọng tâm (Mệnh/Thân/đại hạn/tiểu hạn) để đối chiếu tín hiệu."
        )

    activation = classify_activation(signals, missing)
    role_count = sum(signal["so_vai_tro"] for signal in signals)

    return {
        "year": year,
        "can": can,
        "chi": chi,
        "can_chi": f"{can} {chi}",
        "thai_tue": _palace_brief(thai_tue_cung, "Thái Tuế"),
        "vong_thai_tue": vong,
        "luu_tu_hoa": luu_tu_hoa,
        "can_luu_y": {
            "count": len(signals),
            "role_count": role_count,
            "signals": signals,
            "level": activation["level"],
            "level_label": activation["level_label"],
            "level_reason": activation["level_reason"],
            "level_rule_version": activation["level_rule_version"],
            "level_basis": activation["level_basis"],
            "pham_vi_doi_chieu": [role for role, _ in roles],
            "dieu_kien_thieu": missing,
            "method": method,
            "limitations": LIMITATIONS,
        },
        "tu_hoa_table": table_metadata(table),
        "method": method,
        "limitations": LIMITATIONS,
    }
