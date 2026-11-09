# -*- coding: utf-8 -*-
"""P5 (Plan_Fix_Mai_Anh_v2 §8): Side-effect-free 12-palace component.

Đặc điểm:
- Danh mục cát/hung tinh dùng chung từ star_classification.
- Chính tinh nổi bật kèm đắc tính (M/V/Đ/B/H).
- Tứ Hóa có nhận diện riêng (không ép vào tốt/xấu).
- Phụ tinh chia 2 cột cát tinh / hung tinh; có khu vực cho sao khác.
- Thể hiện riêng Tuần, Triệt và dấu hiệu sao lưu niên.
- Hỗ trợ cả 2 chế độ: Lưới 12 cung truyền thống 4x4 (desktop) và Danh sách từng cung rõ chữ (mobile).
- Hỗ trợ Thiên Bàn trung tâm và thuộc tính tương tác động cho desktop.
"""
from __future__ import annotations

from html import escape
from typing import Any

from backend.app.services.star_classification import (
    CAT_TINH_IDS,
    DAC_TINH_COLOR,
    DAC_TINH_LABEL,
    GROUP_CAT_TINH,
    GROUP_CHINH_TINH,
    GROUP_HUNG_TINH,
    GROUP_KHAC,
    GROUP_LUU_NIEN,
    GROUP_TU_HOA,
    HUNG_TINH_IDS,
    TU_HOA_IDS,
    partition_palace_stars,
)

# Re-export để tương thích ngược
GOOD_SAOS = set(CAT_TINH_IDS) | {92, 93, 94}
BAD_SAOS = set(HUNG_TINH_IDS) | {95}

# Vendor numbering: 1 = Tý, ..., 12 = Hợi. Zero-based (row, column):
# Tỵ   Ngọ   Mùi   Thân
# Thìn [ Thiên bàn ] Dậu
# Mão  [    2×2    ] Tuất
# Dần  Sửu   Tý    Hợi
CHI_GRID_POS = {
    1: (3, 2), 2: (3, 1), 3: (3, 0), 4: (2, 0), 5: (1, 0),
    6: (0, 0), 7: (0, 1), 8: (0, 2), 9: (0, 3), 10: (1, 3),
    11: (2, 3), 12: (3, 3),
}


def sao_html(c: dict[str, Any], luu_nien_saos: list[dict[str, Any]] | None = None) -> str:
    """Render toàn bộ sao trong ô cung theo cấu trúc phân tầng rõ ràng."""
    raw_saos = c.get("saos", [])
    part = partition_palace_stars(raw_saos, luu_nien_saos=luu_nien_saos)

    sections = []

    # 1. Hàng chính tinh (Major stars) - Nổi bật
    chinh_stars = part[GROUP_CHINH_TINH]
    if chinh_stars:
        chinh_spans = []
        for s in chinh_stars:
            name = escape(str(s.get("saoTen") or s.get("ten") or "—"))
            dignity = s.get("saoDacTinh") or s.get("dac_tinh")
            if dignity and dignity != "—":
                color = DAC_TINH_COLOR.get(str(dignity), "#57606a")
                dig_label = DAC_TINH_LABEL.get(str(dignity), str(dignity))
                badge = f'<span class="qc" style="color:{color}" title="{escape(dig_label)}">{escape(str(dignity))}</span>'
            else:
                badge = ""
            chinh_spans.append(f'<span class="sao chinh">{name}{badge}</span>')
        sections.append(f'<div class="chinh-row">{" ".join(chinh_spans)}</div>')
    else:
        sections.append('<div class="chinh-row vcd"><span class="sao vcd">Vô chính diệu</span></div>')

    # 2. Hàng Tứ Hóa - Nhận diện riêng
    tu_hoa_stars = part[GROUP_TU_HOA]
    if tu_hoa_stars:
        th_spans = []
        for s in tu_hoa_stars:
            name = escape(str(s.get("saoTen") or s.get("ten") or "—"))
            th_spans.append(f'<span class="sao tu-hoa">{name}</span>')
        sections.append(f'<div class="tu-hoa-row">{" ".join(th_spans)}</div>')

    # 3. Phụ tinh chia 2 cột: Cát tinh vs Hung tinh
    cat_stars = part[GROUP_CAT_TINH]
    hung_stars = part[GROUP_HUNG_TINH]
    if cat_stars or hung_stars:
        cat_spans = "".join(f'<div class="sao phu tot">{escape(str(s.get("saoTen") or s.get("ten") or "—"))}</div>' for s in cat_stars)
        hung_spans = "".join(f'<div class="sao phu hung">{escape(str(s.get("saoTen") or s.get("ten") or "—"))}</div>' for s in hung_stars)
        empty_cat = '<div class="sao empty">—</div>'
        empty_hung = '<div class="sao empty">—</div>'
        sections.append(
            '<div class="substars-cols">'
            f'<div class="sub-col cat-col">{cat_spans or empty_cat}</div>'
            f'<div class="sub-col hung-col">{hung_spans or empty_hung}</div>'
            '</div>'
        )

    # 4. Sao khác / chưa phân loại (vòng Tràng Sinh, Bác Sỹ trung tính)
    other_stars = part[GROUP_KHAC]
    if other_stars:
        other_spans = " · ".join(escape(str(s.get("saoTen") or s.get("ten") or "—")) for s in other_stars)
        sections.append(f'<div class="other-row"><span class="muted">{other_spans}</span></div>')

    # 5. Sao lưu niên (nếu có)
    ln_stars = part[GROUP_LUU_NIEN]
    if ln_stars:
        ln_spans = []
        for s in ln_stars:
            ten = s.get("sao") or s.get("ten") or s.get("saoTen") or ""
            badge = f'<span class="sao luu-nien">L.{escape(str(ten))}</span>'
            ln_spans.append(badge)
        sections.append(f'<div class="luu-nien-row">{" ".join(ln_spans)}</div>')

    return "".join(sections) or '<div class="sao phu">Chưa có sao</div>'


def _render_cell_content(
    cung: dict[str, Any],
    luu_nien_saos: list[dict[str, Any]] | None = None,
) -> str:
    """Tạo nội dung HTML cho một ô cung."""
    chuan_ten = escape(str(cung.get("chuan_ten", "")))
    hanh_cung = escape(str(cung.get("hanh_cung", "")))
    ten_cung = escape(str(cung.get("ten_cung", "")))
    is_than = bool(cung.get("co_thanh"))
    title = f"{ten_cung} (Thân)" if is_than else ten_cung

    # Badges Tuần / Triệt
    badges = []
    if cung.get("tuan_trung"):
        badges.append('<span class="badge-tag tuan" title="Tuần Trung Không Vong">Tuần</span>')
    if cung.get("triet_lo"):
        badges.append('<span class="badge-tag triet" title="Triệt Lộ Không Vong">Triệt</span>')
    badge_html = f'<div class="badges-row">{"".join(badges)}</div>' if badges else ""

    # Meta đại hạn / tiểu hạn
    meta_parts = []
    age = cung.get("tu_dai_han")
    if age is not None:
        meta_parts.append(f"Đại hạn {age}–{age + 9}")
    if cung.get("tieu_han_chi"):
        meta_parts.append(f"Tiểu hạn: {escape(str(cung['tieu_han_chi']))}")

    meta_html = f'<div class="meta">{escape(" · ".join(meta_parts))}</div>' if meta_parts else ""

    return (
        '<div class="cell-header">'
        f'<div class="chi">{chuan_ten} · {hanh_cung}</div>'
        f'{badge_html}'
        '</div>'
        f'<div class="ten">{title}</div>'
        f'<div class="saos">{sao_html(cung, luu_nien_saos=luu_nien_saos)}</div>'
        f'{meta_html}'
    )


def luoi_html(
    cacs_cung: list[dict[str, Any]],
    luu_nien_by_cung: dict[int, list[dict[str, Any]]] | None = None,
    thien_ban: dict[str, Any] | None = None,
) -> str:
    """Bố cục lưới truyền thống 4x4; hỗ trợ Thiên Bàn trung tâm và thuộc tính tương tác động."""
    cells = {}
    ln_map = luu_nien_by_cung or {}

    for cung in cacs_cung:
        cung_so = cung.get("cung_so")
        position = CHI_GRID_POS.get(cung_so)
        if position is None:
            continue
        cung_ln = ln_map.get(cung_so)
        chuan_ten = escape(str(cung.get("chuan_ten", "")))
        ten_cung = escape(str(cung.get("ten_cung", "")))
        hanh_cung = escape(str(cung.get("hanh_cung", "")))
        cells[position] = (
            f'<div class="cell" data-cung="{cung_so}" data-chi="{chuan_ten}" '
            f'data-ten="{ten_cung}" data-hanh="{hanh_cung}">'
            f'{_render_cell_content(cung, luu_nien_saos=cung_ln)}'
            '</div>'
        )

    # Dựng Thiên Bàn trung tâm (2x2: chiếm ô 1-2 trên hàng và cột)
    tb = thien_ban or {}
    ho_ten = escape(str(tb.get("ho_ten") or "Bản Đồ Tử Vi"))
    general = tb.get("general") or {}
    if general:
        def _text(value: Any) -> str:
            return escape(str(value)) if value not in (None, "") else "—"

        def _date_row(label: str, value: Any, lunar: Any, extra: Any, note: str = "") -> str:
            lunar_html = (
                f'<span class="tb-gen-lunar" title="Âm lịch">{escape(str(lunar))}</span>'
                if lunar not in (None, "") else ""
            )
            note_html = f'<span class="tb-gen-note">{escape(note)}</span>' if note else ""
            return (
                '<div class="tb-gen-row">'
                f'<span class="tb-gen-label">{escape(label)}</span>'
                f'<span class="tb-gen-value">{_text(value)}{lunar_html}{note_html}</span>'
                f'<span class="tb-gen-extra">{_text(extra)}</span>'
                '</div>'
            )

        def _group_row(label: str, primary: Any, notes: list[Any] | tuple[Any, ...] = ()) -> str:
            notes_html = "".join(
                f'<span class="tb-gen-sub">{escape(str(note))}</span>'
                for note in notes if note not in (None, "")
            )
            return (
                '<div class="tb-gen-row tb-gen-group">'
                f'<span class="tb-gen-label">{escape(label)}</span>'
                f'<span class="tb-gen-value tb-gen-span">{_text(primary)}{notes_html}</span>'
                '</div>'
            )

        show_lunar = bool(general.get("show_lunar"))
        general_rows = "".join([
            '<div class="tb-gen-row tb-gen-name-row">'
            '<span class="tb-gen-label">Họ tên</span>'
            f'<span class="tb-gen-value tb-gen-name">{_text(general.get("ho_ten"))}</span>'
            '</div>',
            _date_row("Năm", general.get("nam_sinh"), None, general.get("can_chi_nam")),
            _date_row("Tháng", general.get("thang_sinh"),
                      general.get("thang_am") if show_lunar else None,
                      general.get("can_chi_thang")),
            _date_row("Ngày", general.get("ngay_sinh"),
                      general.get("ngay_am") if show_lunar else None,
                      general.get("can_chi_ngay")),
            _date_row("Giờ", general.get("gio_chi"), None, general.get("can_chi_gio"),
                      note=str(general.get("gio_range") or "")),
            _date_row("Năm xem", general.get("nam_xem"), None, general.get("can_chi_nam_xem")),
        ])

        tuoi_am = general.get("tuoi_am")
        if tuoi_am:
            general_rows += (
                '<div class="tb-gen-row tb-gen-age">'
                '<span></span><span></span>'
                f'<span class="tb-gen-extra">{escape(str(tuoi_am))} tuổi</span>'
                '</div>'
            )

        cach_items = general.get("cach") or []
        cach_html = "".join(
            f'<span class="tb-gen-sub tb-gen-cach">{escape(str(item))}</span>'
            for item in cach_items
        ) or '<span class="tb-gen-sub tb-gen-empty">Chưa nhận diện cách cục nổi bật</span>'

        tb_html_parts = [
            '<div class="cell center thien-ban" id="thien-ban-panel">',
            '<div class="thien-ban-default tb-general">',
            f'<div class="tb-gen-calendar">{escape(str(general.get("calendar") or ""))}</div>',
            '<div class="tb-gen-table">' + general_rows + '</div>',
            _group_row("Âm Dương", general.get("am_duong"), [general.get("am_duong_ly")]),
            _group_row("Mệnh", general.get("menh")),
            _group_row("Cục", general.get("cuc"), general.get("cuc_notes") or []),
            '<div class="tb-gen-row tb-gen-group">'
            '<span class="tb-gen-label">Cách</span>'
            f'<span class="tb-gen-value tb-gen-span">{cach_html}</span>'
            '</div>',
        ]
        hint = escape(str(tb.get("hint") or "Bấm vào ô cung để xem Tam hợp · Xung chiếu · Nhị hợp"))
        tb_html_parts.append(
            f'<div class="tb-hint">{hint}</div>'
            '<button type="button" class="tb-reset-btn" id="tb-reset-btn">Về Thiên Bàn chung</button>'
            '</div>'
            '</div>'
        )
        thien_ban_cell = "".join(tb_html_parts)
    else:
        birth_time = escape(str(tb.get("birth_time") or ""))
        menh_cuc = escape(str(tb.get("menh_cuc") or ""))
        cung_info = escape(str(tb.get("cung_info") or ""))

        tb_html_parts = [
            '<div class="cell center thien-ban" id="thien-ban-panel">',
            '<div class="thien-ban-default">',
            '<div class="tb-seal"><span class="seal-stamp">KMS<br>TỬ VI</span></div>',
            f'<div class="tb-name">{ho_ten}</div>',
        ]
        if birth_time:
            tb_html_parts.append(f'<div class="tb-meta">{birth_time}</div>')
        if menh_cuc:
            tb_html_parts.append(f'<div class="tb-stat"><strong>Mệnh Cục:</strong> {menh_cuc}</div>')
        if cung_info:
            tb_html_parts.append(f'<div class="tb-stat"><strong>Mệnh/Thân:</strong> {cung_info}</div>')
        tb_html_parts.append(
            '<div class="tb-hint">Bấm vào ô cung để xem Tam hợp · Xung chiếu · Nhị hợp</div>'
            '</div>'
            '</div>'
        )
        thien_ban_cell = "".join(tb_html_parts)

    result = []
    for row in range(4):
        for col in range(4):
            if (row, col) == (1, 1):
                result.append(thien_ban_cell)
            elif (row, col) in ((1, 2), (2, 1), (2, 2)):
                result.append('<div class="cell center spacer" style="display:none;" aria-hidden="true"></div>')
            else:
                result.append(cells.get((row, col), '<div class="cell center" aria-hidden="true"></div>'))

    return '<div class="grid">' + "".join(result) + '</div>'


def danh_sach_html(
    cacs_cung: list[dict[str, Any]],
    luu_nien_by_cung: dict[int, list[dict[str, Any]]] | None = None,
) -> str:
    """Bố cục danh sách từng cung rõ chữ, tối ưu cho màn hình điện thoại (mobile)."""
    ln_map = luu_nien_by_cung or {}
    items = []

    sorted_cungs = sorted(cacs_cung, key=lambda c: c.get("cung_so", 0))
    for cung in sorted_cungs:
        cung_so = cung.get("cung_so")
        cung_ln = ln_map.get(cung_so)
        chuan_ten = escape(str(cung.get("chuan_ten", "")))
        ten_cung = escape(str(cung.get("ten_cung", "")))
        hanh_cung = escape(str(cung.get("hanh_cung", "")))
        items.append(
            f'<div class="danh-sach-card" data-cung="{cung_so}" data-chi="{chuan_ten}" '
            f'data-ten="{ten_cung}" data-hanh="{hanh_cung}">'
            f'{_render_cell_content(cung, luu_nien_saos=cung_ln)}'
            '</div>'
        )

    return '<div class="danh-sach">' + "".join(items) + '</div>'


def render_laso(
    cacs_cung: list[dict[str, Any]],
    che_do: str = "luoi",
    luu_nien_by_cung: dict[int, list[dict[str, Any]]] | None = None,
    thien_ban: dict[str, Any] | None = None,
) -> str:
    """Renderer hợp nhất cho lá số 12 cung:

    - che_do="luoi": Lưới truyền thống 4x4
    - che_do="danh_sach": Danh sách thẻ từng cung rõ chữ
    """
    if che_do == "danh_sach":
        return danh_sach_html(cacs_cung, luu_nien_by_cung=luu_nien_by_cung)
    return luoi_html(cacs_cung, luu_nien_by_cung=luu_nien_by_cung, thien_ban=thien_ban)
