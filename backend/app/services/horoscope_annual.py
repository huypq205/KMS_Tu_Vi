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


def compute_luu_nien(
    thap_ni_cung: list[dict[str, Any]],
    year: int,
    cung_menh_so: int | None = None,
    cung_than_so: int | None = None,
    dai_han_cung_so: int | None = None,
    tieu_han_cung_so: int | None = None,
    tu_hoa_table_id: str | None = None,
) -> dict[str, Any]:
    """An lưu niên cho một năm: Can Chi, vòng Thái Tuế, lưu Tứ Hóa và cờ cần lưu ý."""
    can, chi = can_chi_of_year(year)
    table = get_tu_hoa_table(tu_hoa_table_id)
    method = f"{METHOD} Bảng Tứ Hóa: {table['school']}."
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

    hits: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def add_hit(star: str, cung_so: int | None, role: str, cung_ten: str) -> None:
        key = (star, role)
        if cung_so is None or key in seen:
            return
        seen.add(key)
        hits.append({"sao": star, "cung_ten": cung_ten, "don_vai": role})

    for star_name in CAUTION_STARS:
        entry = vong.get(star_name)
        if not entry:
            continue
        for role, cung_so in roles:
            if entry.get("cung_so") == cung_so:
                add_hit(star_name, cung_so, role, entry.get("cung_ten", ""))

    for entry in luu_tu_hoa:
        if entry["code"] != "HOA_KY":
            continue
        for role, cung_so in roles:
            if entry.get("cung_so") == cung_so:
                add_hit(f"{entry['ten_sao']} lưu Kỵ", cung_so, role, entry.get("cung_ten", ""))

    if not hits:
        level = "nhan"
    elif len(hits) >= 2 or any(hit["don_vai"] in ("menh", "than") for hit in hits):
        level = "nang"
    else:
        level = "vua"

    return {
        "year": year,
        "can": can,
        "chi": chi,
        "can_chi": f"{can} {chi}",
        "thai_tue": _palace_brief(thai_tue_cung, "Thái Tuế"),
        "vong_thai_tue": vong,
        "luu_tu_hoa": luu_tu_hoa,
        "can_luu_y": {
            "count": len(hits),
            "level": level,
            "hits": hits,
            "method": method,
            "limitations": LIMITATIONS,
        },
        "tu_hoa_table": table_metadata(table),
        "method": method,
        "limitations": LIMITATIONS,
    }
