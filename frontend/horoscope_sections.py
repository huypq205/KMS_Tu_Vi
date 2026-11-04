# -*- coding: utf-8 -*-
"""Horoscope UI Sections (Quy chuẩn giao diện báo cáo cho người xem phổ thông).

Thứ tự 7 khối chuẩn:
1. Thông tin người xem
2. Tổng quan năm (3 đoạn: trọng tâm, cơ hội, cân nhắc & ứng xử)
3. Lá số 12 cung (giữ lưới / đọc từng cung)
4. Chân dung, thế mạnh và điều cần rèn luyện
5. Các chủ đề: Sự nghiệp, Tài chính, Tình cảm, Vận trình
6. Gợi ý hành động
7. Căn cứ và thông tin chuyên môn (mặc định đóng)
"""
from __future__ import annotations

import html
from typing import Any
import streamlit as st

from frontend.horoscope_view import (
    BOOKS, HOURS, TOPICS, content, panel, text, topic_panel,
    annual_panel, star_table, evidence_table, annual_activation_panel,
)
from frontend.laso_renderer import render_laso


def _inject_laso_interactive_script() -> None:
    """Script tương tác động client-side: click cung -> highlight Tam hợp, Xung chiếu, Nhị hợp."""
    import streamlit.components.v1 as components
    js_code = """
    <script>
    (function() {
        function setupInteractions() {
            try {
                const doc = window.parent.document;
                const chart = doc.querySelector('.horoscope-chart');
                if (!chart) return;
                const grid = chart.querySelector('.grid');
                if (!grid) return;
                const cells = chart.querySelectorAll('.cell[data-cung]');
                const thienBan = chart.querySelector('.cell.center.thien-ban');
                if (!cells.length || !thienBan) return;

                const palaceData = {};
                cells.forEach(cell => {
                    const cungSo = parseInt(cell.getAttribute('data-cung'));
                    if (cungSo) {
                        palaceData[cungSo] = {
                            element: cell,
                            cungSo: cungSo,
                        };
                    }
                });

                function getRelations(c) {
                    const tamHop1 = ((c + 4 - 1) % 12) + 1;
                    const tamHop2 = ((c + 8 - 1) % 12) + 1;
                    const xungChieu = ((c + 6 - 1) % 12) + 1;
                    const nhiHopMap = {1:2, 2:1, 3:12, 4:11, 5:10, 6:9, 7:8, 8:7, 9:6, 10:5, 11:4, 12:3};
                    return { tamHop: [tamHop1, tamHop2], xungChieu, nhiHop: nhiHopMap[c] };
                }

                function clearHighlight() {
                    cells.forEach(c => {
                        c.classList.remove('is-selected', 'is-tam-hop', 'is-xung-chieu', 'is-nhi-hop');
                    });
                }

                function selectPalace(cungSo) {
                    clearHighlight();
                    const cur = palaceData[cungSo];
                    if (!cur) return;

                    cur.element.classList.add('is-selected');
                    const rels = getRelations(cungSo);

                    rels.tamHop.forEach(ts => {
                        if (palaceData[ts]) palaceData[ts].element.classList.add('is-tam-hop');
                    });
                    if (palaceData[rels.xungChieu]) {
                        palaceData[rels.xungChieu].element.classList.add('is-xung-chieu');
                    }
                    if (palaceData[rels.nhiHop]) {
                        palaceData[rels.nhiHop].element.classList.add('is-nhi-hop');
                    }
                }

                // Nút "Về Thiên Bàn chung" chỉ bỏ chọn/highlight; phần trung tâm luôn
                // hiển thị thông tin chung của người xem.
                const resetBtn = thienBan.querySelector('#tb-reset-btn');
                if (resetBtn) {
                    resetBtn.onclick = function(e) {
                        e.stopPropagation();
                        clearHighlight();
                    };
                }

                cells.forEach(cell => {
                    cell.onclick = function(e) {
                        const cungSo = parseInt(this.getAttribute('data-cung'));
                        if (this.classList.contains('is-selected')) {
                            clearHighlight();
                        } else {
                            selectPalace(cungSo);
                        }
                    };
                });
            } catch(e) {}
        }
        setTimeout(setupInteractions, 150);
        setTimeout(setupInteractions, 600);
    })();
    </script>
    """
    try:
        components.html(js_code, height=0)
    except Exception:
        pass


def render_header_identity(report: dict[str, Any], snapshot: dict[str, Any],
                           basic: dict[str, Any]) -> None:
    """Khối 1: Định danh người xem (ngôn ngữ phổ thông)."""
    st.markdown(
        f'<div class="report-heading"><h2>{text(report.get("ho_ten"))}</h2>'
        f'<span>{text(st.session_state.get("report_time", ""))}</span></div>'
        f'<p class="muted">{snapshot["ngay"]:02d}/{snapshot["thang"]:02d}/{snapshot["nam"]} · '
        f'{"Dương lịch" if snapshot["duong_lich"] else "Âm lịch"} · '
        f'{text(HOURS[snapshot["chi_gio"]-1])} · Năm chiêm nghiệm {snapshot["target_year"]}</p>',
        unsafe_allow_html=True,
    )

    element = str(basic.get("ban_menh", "")).upper()
    element_class = next(
        (v for k, v in {"HỎA": "hoa", "THỦY": "thuy", "MỘC": "moc", "KIM": "kim", "THỔ": "tho"}.items() if k in element),
        "neutral",
    )
    stats = [
        ("Bản mệnh", basic.get("ban_menh")),
        ("Cục số", basic.get("ten_cuc")),
        ("Mệnh tại", basic.get("cung_menh")),
        ("Thân tại", basic.get("cung_than")),
    ]
    identity_items = []
    for index, (label, value) in enumerate(stats):
        marker = f'<i class="element-dot {element_class}" aria-hidden="true"></i>' if index == 0 else ""
        identity_items.append(f'<div><span class="muted">{label}</span><strong>{marker}{text(value)}</strong></div>')
    st.markdown('<div class="identity-strip">' + ''.join(identity_items) + '</div>', unsafe_allow_html=True)


def render_annual_overview_section(reading: dict[str, Any], report: dict[str, Any], target_year: int) -> None:
    """Khối 2: Tổng quan năm (150-220 từ, 3 đoạn rõ ràng: trọng tâm, cơ hội, cân nhắc & ứng xử)."""
    annual = report.get('annual') or {}
    can_chi = annual.get('can_chi', '')
    title_suffix = f" · {can_chi}" if can_chi else ""
    st.subheader(f"Tổng quan năm {target_year}{title_suffix}")

    tom_tat_nam = reading.get("tom_tat_nam")
    if isinstance(tom_tat_nam, list) and len(tom_tat_nam) >= 3:
        p1 = html.escape(tom_tat_nam[0])
        p2 = html.escape(tom_tat_nam[1])
        p3 = html.escape(tom_tat_nam[2])
        st.markdown(
            f'<div class="annual-overview-card" style="background:#fcfbf8; border:1px solid #e8e3d9; '
            f'border-radius:8px; padding:18px 22px; margin-bottom:18px; line-height:1.7;">'
            f'<p style="margin-bottom:12px;"><strong>Trọng tâm của năm:</strong> {p1}</p>'
            f'<p style="margin-bottom:12px;"><strong>Cơ hội đáng chú ý:</strong> {p2}</p>'
            f'<p style="margin-bottom:0;"><strong>Điều nên cân nhắc và hướng ứng xử:</strong> {p3}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("Báo cáo được tạo theo phiên bản cũ chưa có phần tổng quan năm. Vui lòng bấm 'Tạo bản luận giải' để cập nhật bản mới.")


def chart_viewer_general(report: dict[str, Any], ho_ten: str) -> dict[str, Any]:
    """Thông tin chung của người xem hiển thị tại Thiên Bàn trung tâm."""
    basic = report.get("thong_tin_co_ban") or {}
    menh_cuc = report.get("menh_cuc") or {}
    reading = report.get("reading") or {}
    cach_cuc = reading.get("cach_cuc") or report.get("cach_cuc") or {}

    can_nam = str(basic.get("can_chi_nam") or "").split(" ")[0]
    is_duong = can_nam in {"Giáp", "Bính", "Mậu", "Canh", "Nhâm"}
    gender = str(basic.get("gioi_tinh") or "")
    am_duong = f"{'Dương' if is_duong else 'Âm'} {gender}".strip()
    thuan_ly = (is_duong and gender == "Nam") or (not is_duong and gender == "Nữ")

    rel_labels = {
        "MENH_CUC_TI_HOA": "Mệnh Cục bình hoà",
        "CUC_SINH_MENH": "Cục sinh Mệnh",
        "MENH_SINH_CUC": "Mệnh sinh Cục",
        "MENH_KHAC_CUC": "Mệnh khắc Cục",
        "CUC_KHAC_MENH": "Cục khắc Mệnh",
    }
    cuc_notes = []
    relation_label = rel_labels.get(str(menh_cuc.get("relation_type") or ""))
    if relation_label:
        cuc_notes.append(relation_label)
    if basic.get("cung_menh") and basic.get("cung_menh") == basic.get("cung_than"):
        cuc_notes.append("Thân Mệnh đồng cung")

    matched_cach = []
    matched_pha = []
    rules = cach_cuc.get("rules") or []
    for rule in rules:
        outcome = rule.get("ket_qua")
        if outcome not in ("khop_du", "khop_mot_phan"):
            continue
        name = rule.get("ten") or rule.get("rule_id")
        if not name:
            continue
        entry = str(name) if outcome == "khop_du" else f"{name} (một phần)"
        if rule.get("nhom") == "pha_cach":
            matched_pha.append(entry)
        else:
            matched_cach.append(entry)

    # Bản đầu chưa chạy quy tắc phá cách; chỉ kết luận "Không phá cách" khi đã
    # có kết quả nhận diện. Khi P3 bật thêm quy tắc, tên phá cách sẽ tự thay thế.
    if matched_pha:
        matched_cach.extend(matched_pha)
    elif rules:
        matched_cach.append("Không phá cách")

    chi_gio = basic.get("chi_gio")
    gio_chi = ""
    gio_range = ""
    try:
        gio_label = HOURS[int(chi_gio) - 1]
        gio_chi, _, gio_range = gio_label.partition(" · ")
    except (TypeError, ValueError, IndexError):
        pass

    nam_xem = (report.get("annual") or {}).get("year")
    can_chi_nam_xem = str(basic.get("can_chi_nam_xem") or "")
    tuoi_am = basic.get("tuoi_am")

    return {
        "ho_ten": ho_ten,
        "calendar": "Dương lịch · Âm lịch" if basic.get("duong_lich", True) else "Âm lịch",
        "show_lunar": bool(basic.get("duong_lich", True)),
        "nam_sinh": basic.get("nam_sinh") or "—",
        "thang_sinh": basic.get("thang_sinh") or "—",
        "ngay_sinh": basic.get("ngay_sinh") or "—",
        "thang_am": basic.get("thang_am"),
        "ngay_am": basic.get("ngay_am"),
        "gio_chi": gio_chi or "—",
        "gio_range": gio_range,
        "nam_xem": nam_xem or "—",
        "can_chi_nam": basic.get("can_chi_nam") or "",
        "can_chi_thang": basic.get("can_chi_thang") or "",
        "can_chi_ngay": basic.get("can_chi_ngay") or "",
        "can_chi_gio": basic.get("can_chi_gio") or "",
        "can_chi_nam_xem": can_chi_nam_xem,
        "tuoi_am": tuoi_am,
        "am_duong": am_duong,
        "am_duong_ly": "Âm Dương thuận lý" if thuan_ly else "Âm Dương nghịch lý",
        "menh": str(basic.get("ban_menh") or "").title(),
        "cuc": str(basic.get("ten_cuc") or "").title(),
        "cuc_notes": cuc_notes,
        "cach": matched_cach,
    }


def render_chart_section(report: dict[str, Any], luu_nien_by_cung_fn: Any = None) -> None:
    """Khối 3: Lá số 12 cung (chuyển khối năm chuyên môn xuống mục căn cứ)."""
    palaces = report.get("la_so", {}).get("thap_ni_cung", [])
    if palaces:
        st.subheader("Lá số 12 cung")
        show_chart = st.toggle("Xem lá số chi tiết 12 cung", value=True, key="show_chart")
        if show_chart:
            view_col1, view_col2 = st.columns([2, 1])
            with view_col2:
                chart_view = st.radio(
                    "Bố cục hiển thị",
                    ["Lưới 12 cung", "Đọc từng cung"],
                    horizontal=True,
                    label_visibility="collapsed",
                    key="chart_view_mode",
                )
            che_do = "danh_sach" if chart_view == "Đọc từng cung" else "luoi"
            ln_map = luu_nien_by_cung_fn(report.get("luu_nien"), palaces) if luu_nien_by_cung_fn else {}
            st.caption("M: Miếu · V: Vượng · Đ: Đắc · B: Bình · H: Hãm · L.: Sao lưu niên · [Tuần/Triệt]: Không Vong.")

            basic = report.get("thong_tin_co_ban", {})
            ho_ten = report.get("ho_ten") or basic.get("ho_ten") or "Chủ Mệnh"
            thien_ban_info = {
                "ho_ten": ho_ten,
                "general": chart_viewer_general(report, ho_ten),
            }

            st.markdown(
                '<div class="horoscope-chart">' + render_laso(palaces, che_do=che_do, luu_nien_by_cung=ln_map, thien_ban=thien_ban_info) + '</div>',
                unsafe_allow_html=True,
            )
            _inject_laso_interactive_script()


def render_overview_section(reading: dict[str, Any]) -> None:
    """Khối 4: Tổng quan - chân dung, thế mạnh và điều cần rèn luyện."""
    overview = reading.get("tong_quan", {})
    if not isinstance(overview, dict):
        overview = {}
    left = panel(
        "Chân dung của bạn",
        content(overview.get("ban_sac")) + '<h3>Mệnh và môi trường sống</h3>' + content(overview.get("ngu_hanh_nang_luong")),
    )
    right = panel(
        "Thế mạnh & điều cần rèn luyện",
        '<h3>Thế mạnh</h3>' + content(overview.get("diem_manh")) + '<h3>Điều cần rèn luyện</h3>' + content(overview.get("diem_can_ren_luyen")),
    )
    st.markdown('<div class="overview-grid">' + left + right + '</div>', unsafe_allow_html=True)


def render_topics_section(reading: dict[str, Any], snapshot: dict[str, Any],
                          api_base: str, priorities: list[str] | None = None) -> None:
    """Khối 5: Theo chủ đề - Sự nghiệp, Tài chính, Tình cảm, Vận trình."""
    priorities = priorities or []
    order = list(dict.fromkeys(priorities + list(TOPICS)))
    tabs = st.tabs([TOPICS[key] for key in order])
    for key, tab in zip(order, tabs):
        with tab:
            st.markdown(topic_panel(key, reading.get(key, {})), unsafe_allow_html=True)


def render_action_advice_section(reading: dict[str, Any]) -> None:
    """Khối 6: Gợi ý hành động dành cho người xem web (đời thường, dễ áp dụng)."""
    loi_khuyen = reading.get("loi_khuyen_hanh_dong")
    if loi_khuyen:
        st.markdown(
            panel(
                "Gợi ý hành động cho bạn",
                '<p class="muted">Những việc cụ thể bạn có thể áp dụng trong công việc, tài chính, '
                'quan hệ và chăm sóc bản thân.</p>' + content(loi_khuyen),
            ),
            unsafe_allow_html=True,
        )


def _render_why_content(reading: dict[str, Any], report: dict[str, Any]) -> None:
    """Nội dung Vì sao & Cách cục nằm bên trong mục Căn cứ."""
    st.subheader("Vì sao — Giải thích nhận định & cách cục")
    fact_map = {f['fact_id']: f for f in report.get('star_analysis', []) if isinstance(f, dict) and 'fact_id' in f}

    ket_luan_list = reading.get('ket_luan') or []
    if ket_luan_list:
        for index, point in enumerate(ket_luan_list, 1):
            loai_label = {'cau_truc': 'Cấu trúc', 'thoi_diem': 'Thời điểm'}.get(point.get('loai_ket_luan'), 'Chưa phân loại')
            st.markdown(f'<p class="muted" style="margin:8px 0 2px"><strong>Nhận định {index}</strong> · Loại: {text(loai_label)}</p>', unsafe_allow_html=True)
            st.markdown(content(point.get('nhan_dinh')), unsafe_allow_html=True)
            if point.get('giai_thich_thun_viet'):
                st.markdown(
                    '<p class="muted"><strong>Giải nghĩa thuần Việt:</strong> ' + text(point.get('giai_thich_thun_viet')) + '</p>',
                    unsafe_allow_html=True,
                )
            with st.expander(f"Dữ kiện & quy tắc nhận định {index}", expanded=False):
                f_ids = point.get('fact_ids') or []
                f_labels = [
                    f"{fact_map[i]['sao']} tại {fact_map[i]['cung']} ({fact_map[i]['dia_chi']})"
                    for i in f_ids if i in fact_map
                ]
                st.caption(f"**Dữ kiện:** {'; '.join(f_labels) if f_labels else (', '.join(f_ids) or '—')}")
                r_ids = point.get('rule_ids') or []
                st.caption(f"**Quy tắc:** {', '.join(r_ids) if r_ids else 'Quy tắc phân tích cấu trúc sao và cung'}")
                limits = point.get('gioi_han', 'Chưa xác minh thủ công.')
                missing = point.get('dieu_kien_chua_kiem_tra') or []
                missing_text = f" · Chưa kiểm tra: {', '.join(missing)}" if missing else ""
                st.caption(f"**Điều kiện / giới hạn:** {limits}{missing_text}")
                refs = point.get('source_refs') or []
                skill_refs = point.get('reference_ids') or []
                if refs:
                    st.caption(f"**Nguồn sách:** {', '.join(f'[{r}]' for r in refs)}")
                if skill_refs:
                    st.caption(f"**Nguồn tham khảo skill:** {', '.join(skill_refs)}")

    cach_cuc = reading.get('cach_cuc') or report.get('cach_cuc') or {}
    matched_rules = [
        r for r in (cach_cuc.get('rules') or [])
        if r.get('ket_qua') in ('khop_du', 'khop_mot_phan')
    ]
    if matched_rules:
        st.markdown("##### Cách cục đã nhận diện từ lá số")
        for r in matched_rules:
            status_badge = "Khớp đủ" if r.get('ket_qua') == 'khop_du' else "Khớp một phần"
            nhom = "Cát cục" if r.get('nhom') == 'cat' else "Cần lưu ý"
            with st.expander(f"{r.get('ten', r.get('rule_id'))} · {status_badge} ({nhom})", expanded=False):
                st.markdown(f"<p>{text(r.get('mo_ta') or r.get('dien_giai') or 'Cấu trúc sao theo quy tắc truyền thống.')}</p>", unsafe_allow_html=True)
                saos = r.get('saos_found') or r.get('fact_ids') or []
                st.caption(f"**Dữ kiện khớp:** {', '.join(map(str, saos)) if saos else 'Đã xác định vị trí'}")
                untested = r.get('dieu_kien_chua_kiem_tra') or []
                if untested:
                    st.caption(f"**Điều kiện chưa kiểm tra:** {'; '.join(untested)}")
    else:
        st.caption("Đã đối chiếu 30 cách cục truyền thống: lá số chưa ghi nhận cách cục đặc thù trong danh mục hiện tại.")


def render_why_section(reading: dict[str, Any], report: dict[str, Any]) -> None:
    """Tương thích ngược: render khối Vì sao nếu client cũ gọi riêng."""
    _render_why_content(reading, report)


def render_evidence_and_specialist_section(report: dict[str, Any], meta: dict[str, Any]) -> None:
    """Khối 7: Căn cứ và thông tin chuyên môn (mặc định đóng)."""
    with st.expander("Căn cứ và thông tin chuyên môn", expanded=False):
        reading = report.get("reading") or {}
        fact_map = {f['fact_id']: f for f in report.get('star_analysis', []) if isinstance(f, dict) and 'fact_id' in f}

        # 1. Khối năm chuyên môn
        if report.get('annual'):
            st.markdown(annual_panel(report['annual'], report.get('luu_nien')), unsafe_allow_html=True)

        # 2. Bảng kích hoạt bốn tầng & so sánh năm
        van_han = reading.get('van_han_hien_tai') or {}
        if van_han.get('bang_kich_hoat') or van_han.get('so_sanh_nam'):
            st.markdown(annual_activation_panel(van_han), unsafe_allow_html=True)

        # 3. Vì sao & Cách cục
        _render_why_content(reading, report)

        # 4. Bảng lập luận từ sao và nguồn sách
        st.subheader("Xem căn cứ")
        if reading.get('luan_diem'):
            st.markdown("#### Lập luận từ sao và nguồn sách")
            st.caption("Dấu hiệu thuận là loại chứng cứ gắn với fact_id; dấu hiệu nghịch là phản chứng trong nguồn hoặc câu 'Không ghi nhận phản chứng trong nguồn đã lấy'.")
            st.markdown(evidence_table(reading['luan_diem'], fact_map), unsafe_allow_html=True)

        # 5. Bảng sao & dữ kiện cần đối chiếu
        if report.get('star_analysis'):
            st.markdown("#### Sao & yếu tố cần đối chiếu")
            st.caption("Nhóm cần lưu ý lấy từ danh mục sao truyền thống; không phải điểm rủi ro hay dự báo một biến cố. M/V/Đ/B/H là trạng thái sao gốc.")
            group = st.selectbox(
                'Phạm vi sao',
                ['Cần lưu ý', 'Chính tinh', 'Hỗ trợ', 'Tất cả'] + (
                    [f"Lưu niên năm {meta.get('target_year') or (report.get('annual') or {}).get('year')}"]
                    if any(f.get('nhom') == 'luu_nien' for f in report['star_analysis']) else []
                ),
                key='star_filter',
            )
            groups = {'Cần lưu ý': 'risk_stars', 'Chính tinh': 'chinh_tinh', 'Hỗ trợ': 'cat_tinh'}
            if group.startswith('Lưu niên'):
                selected = [f for f in report['star_analysis'] if f.get('nhom') == 'luu_nien']
            else:
                selected = [f for f in report['star_analysis'] if group == 'Tất cả' or f.get('nhom') == groups.get(group)]

            if selected:
                st.markdown(star_table(selected), unsafe_allow_html=True)
                with st.expander('Đối chiếu nguồn của một sao'):
                    fact = st.selectbox(
                        'Chọn sao và cung',
                        selected,
                        format_func=lambda f: f"{f['sao']} · {f['cung']} tại {f['dia_chi']}",
                        key='selected_star',
                    )
                    st.caption(fact['source_status'])
                    for source in report.get('citations', []):
                        if source['ref_id'] in fact['source_refs']:
                            st.caption(f"[{source['ref_id']}] {BOOKS.get(source['book_code'], source['book_code'])} · {source.get('page_label', '')}")
                            st.text(source['excerpt'])
            else:
                st.info('Chưa có sao thuộc nhóm này trong các cung đang phân tích.')

        # 6. Trích dẫn sách gốc & tài liệu tham khảo skill
        st.markdown("#### Đối chiếu & tìm hiểu thêm")
        show_sources = st.toggle("Xem trích dẫn sách gốc", key="show_sources")
        if show_sources:
            citations = report.get("citations", [])
            st.caption("Đây là các đoạn được truy xuất để đối chiếu từ ba cuốn sách KMS.")
            if not citations:
                st.info("Chưa có đoạn sách được truy xuất cho báo cáo này.")
            for source in citations:
                title = f'[{source.get("ref_id", "—")}] {BOOKS.get(source.get("book_code"), source.get("book_code", "Nguồn"))}'
                with st.expander(title):
                    st.caption(f'{source.get("page_label", "Trang không xác định")} · {source.get("chapter") or "Chưa có tên chương"} · Chưa kiểm duyệt thủ công')
                    st.text(source.get("excerpt") or "Chưa có đoạn trích.")

        # Nguồn skill tham khảo
        knowledge_refs = report.get("knowledge_references", [])
        if knowledge_refs:
            with st.expander("Tài liệu tham khảo từ bộ skill (Tử Vi Đẩu Số Toàn Tập)", expanded=False):
                st.caption("Tài liệu tham khảo từ bộ skill; chưa đối chiếu bản sách KMS. Không gán số trang hay thông tin xuất bản.")
                for kref in knowledge_refs[:15]:
                    st.markdown(f"**{kref.get('reference_id')} · {kref.get('name')}** ({kref.get('group_heading', '')})")
                    st.text(kref.get("text", "")[:400])

        # 7. Thời gian xử lý và chế độ thực chạy
        with st.expander('Thời gian xử lý và chế độ thực chạy'):
            timings = meta.get('timings_ms', {})
            provider_label = {
                'gemini': 'Luận giải thông minh (online)',
                'mock': 'Chỉ dữ kiện lá số (không dùng AI)',
            }.get(meta.get('actual_provider'), meta.get('actual_provider', '—'))
            actual_m = meta.get('actual_reading_mode', meta.get('reading_mode', 'chuyen_sau'))
            st.caption(f"Chế độ: {provider_label} (Mức: {actual_m}) · Số lần xử lý: {meta.get('attempts', 0)} · Cache: {'trúng' if meta.get('cached') else 'chưa có'}")
            st.caption(' · '.join(
                f"{label}: {timings.get(key, 0) / 1000:.2f}s"
                for key, label in [('chart', 'Lập lá số'), ('retrieval', 'Lấy nguồn'), ('generation', 'Tạo bài'), ('total', 'Tổng')]
            ))


def render_evidence_section(report: dict[str, Any], meta: dict[str, Any]) -> None:
    """Tương thích ngược với tên gọi hàm cũ."""
    render_evidence_and_specialist_section(report, meta)
