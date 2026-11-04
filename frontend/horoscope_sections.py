# -*- coding: utf-8 -*-
"""Horoscope UI Sections (P7 §10 - Luồng 5 khối chuẩn).

Thứ tự 5 khối (§10.2):
Lá số -> Tổng quan -> Chủ đề -> Vì sao -> Xem căn cứ

Cập nhật:
- Phong cách Á Đông thư tịch cổ (giấy dó, mực than, triện son).
- Tương tác động client-side trên bàn lá số 12 cung (highlight Tam hợp, Xung chiếu, Nhị hợp).
- Bỏ phần hỏi đáp nhanh theo yêu cầu để giao diện tinh gọn, tập trung chiêm nghiệm.
"""
from __future__ import annotations

from typing import Any
import streamlit as st

from frontend.horoscope_view import (
    BOOKS, HOURS, TOPICS, content, panel, text, topic_panel,
    annual_panel, star_table, confidence_badge, evidence_table,
)
from frontend.laso_renderer import render_laso


def _inject_laso_interactive_script() -> None:
    """Script tương tác động client-side: click cung -> highlight Tam hợp, Xung chiếu, Nhị hợp & hiển thị tại Thiên Bàn."""
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

                if (!thienBan.dataset.defaultHtml) {
                    thienBan.dataset.defaultHtml = thienBan.innerHTML;
                }

                const palaceData = {};
                cells.forEach(cell => {
                    const cungSo = parseInt(cell.getAttribute('data-cung'));
                    if (cungSo) {
                        palaceData[cungSo] = {
                            element: cell,
                            cungSo: cungSo,
                            chi: cell.getAttribute('data-chi') || '',
                            ten: cell.getAttribute('data-ten') || '',
                            hanh: cell.getAttribute('data-hanh') || '',
                            chinhTinh: cell.querySelector('.chinh-row')?.innerText?.trim() || '',
                            tuHoa: cell.querySelector('.tu-hoa-row')?.innerText?.trim() || '',
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

                    const th1 = palaceData[rels.tamHop[0]] || {};
                    const th2 = palaceData[rels.tamHop[1]] || {};
                    const xc = palaceData[rels.xungChieu] || {};
                    const nh = palaceData[rels.nhiHop] || {};

                    thienBan.innerHTML = `
                        <div class="thien-ban-inspect-card">
                            <div class="tb-inspect-header">
                                <span class="tb-cung-badge">${cur.ten}</span>
                                <span class="tb-chi-badge">${cur.chi} · ${cur.hanh}</span>
                            </div>
                            <div class="tb-inspect-stars">
                                <div class="tb-chinh-text">${cur.chinhTinh || 'Vô chính diệu'}</div>
                                ${cur.tuHoa ? `<div class="tb-tuhoa-tag">${cur.tuHoa}</div>` : ''}
                            </div>
                            <div class="tb-inspect-rels">
                                <div class="tb-rel-item">
                                    <span class="rel-tag yellow">Tam hợp</span>
                                    <span class="rel-desc">${th1.ten || ''} (${th1.chi || ''}) &amp; ${th2.ten || ''} (${th2.chi || ''})</span>
                                </div>
                                <div class="tb-rel-item">
                                    <span class="rel-tag red">Xung chiếu</span>
                                    <span class="rel-desc">${xc.ten || ''} (${xc.chi || ''})</span>
                                </div>
                                <div class="tb-rel-item">
                                    <span class="rel-tag green">Nhị hợp</span>
                                    <span class="rel-desc">${nh.ten || ''} (${nh.chi || ''})</span>
                                </div>
                            </div>
                            <button type="button" class="tb-reset-btn" id="tb-reset-btn">☯ Về Thiên Bàn chung</button>
                        </div>
                    `;

                    const resetBtn = thienBan.querySelector('#tb-reset-btn');
                    if (resetBtn) {
                        resetBtn.onclick = function(e) {
                            e.stopPropagation();
                            clearHighlight();
                            thienBan.innerHTML = thienBan.dataset.defaultHtml;
                        };
                    }
                }

                cells.forEach(cell => {
                    cell.onclick = function(e) {
                        const cungSo = parseInt(this.getAttribute('data-cung'));
                        if (this.classList.contains('is-selected')) {
                            clearHighlight();
                            thienBan.innerHTML = thienBan.dataset.defaultHtml;
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
                           basic: dict[str, Any], input_confidence: str) -> None:
    """Khối Định danh người xem: họ tên, thời gian lập, ngày giờ sinh, bản mệnh và cục số."""
    st.markdown(
        f'<div class="report-heading"><h2>{text(report.get("ho_ten"))}</h2>'
        f'<span>{text(st.session_state.get("report_time", ""))}</span></div>'
        f'<p class="muted">{snapshot["ngay"]:02d}/{snapshot["thang"]:02d}/{snapshot["nam"]} · '
        f'{"Dương lịch" if snapshot["duong_lich"] else "Âm lịch"} · '
        f'{text(HOURS[snapshot["chi_gio"]-1])} · Năm {snapshot["target_year"]} · '
        f'Giờ sinh mức {text(input_confidence)}</p>',
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


def render_chart_section(report: dict[str, Any], luu_nien_by_cung_fn: Any = None) -> None:
    """Khối 1: Lá số 12 cung (đầu trang) kèm panel năm chiêm nghiệm."""
    if report.get('annual'):
        st.markdown(annual_panel(report['annual'], report.get('luu_nien')), unsafe_allow_html=True)

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

            # Thông tin hiển thị mặc định trên Thiên Bàn
            basic = report.get("thong_tin_co_ban", {})
            ho_ten = report.get("ho_ten") or basic.get("ho_ten") or "Chủ Mệnh"
            ban_menh = basic.get("ban_menh") or ""
            ten_cuc = basic.get("ten_cuc") or ""
            cung_menh = basic.get("cung_menh") or ""
            cung_than = basic.get("cung_than") or ""
            thien_ban_info = {
                "ho_ten": ho_ten,
                "menh_cuc": f"{ban_menh} · {ten_cuc}" if ban_menh else "",
                "cung_info": f"Mệnh tại {cung_menh} · Thân tại {cung_than}" if cung_menh else "",
            }

            st.markdown(
                '<div class="horoscope-chart">' + render_laso(palaces, che_do=che_do, luu_nien_by_cung=ln_map, thien_ban=thien_ban_info) + '</div>',
                unsafe_allow_html=True,
            )
            # Kích hoạt tương tác động client-side
            _inject_laso_interactive_script()


def render_overview_section(reading: dict[str, Any]) -> None:
    """Khối 2: Tổng quan - những điểm chính, bản sắc, ngũ hành, thế mạnh và rèn luyện."""
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
    """Khối 3: Theo chủ đề - Sự nghiệp, Tài chính, Tình cảm, Vận trình (tinh gọn, không chat box)."""
    priorities = priorities or []
    order = list(dict.fromkeys(priorities + list(TOPICS)))
    tabs = st.tabs([TOPICS[key] for key in order])
    for key, tab in zip(order, tabs):
        with tab:
            st.markdown(topic_panel(key, reading.get(key, {})), unsafe_allow_html=True)


def render_why_section(reading: dict[str, Any], report: dict[str, Any]) -> None:
    """Khối 4: Vì sao — Giải thích nhận định, dữ kiện tham gia, quy tắc và cách cục liên quan.
    
    Tuân thủ P4 §7.4 & P7 §10.3: Mỗi nhận định có giải thích ngắn tại chỗ; nút/expander 'Vì sao?'
    mở chi tiết gồm 4 yếu tố: Dữ kiện, Quy tắc, Chủ đề, Điều kiện thiếu / Phản chứng.
    """
    st.subheader("Vì sao — Giải thích nhận định & cách cục")
    st.caption("Mỗi nhận định có lời giải thích ngắn tại chỗ; bấm 'Vì sao?' để mở dữ kiện, quy tắc, chủ đề và điều kiện thiếu.")

    fact_map = {f['fact_id']: f for f in report.get('star_analysis', []) if isinstance(f, dict) and 'fact_id' in f}

    # 1. Các kết luận & phân tích chuyên sâu
    ket_luan_list = reading.get('ket_luan') or []
    if ket_luan_list:
        st.markdown("#### Nhận định trọng tâm")
        for index, point in enumerate(ket_luan_list, 1):
            loai_label = {'cau_truc': 'Cấu trúc', 'thoi_diem': 'Thời điểm'}.get(point.get('loai_ket_luan'), 'Chưa phân loại')
            badge = confidence_badge(point.get("muc_tin_cay"))
            st.markdown(
                f'<p class="muted" style="margin:0 0 4px">Nhận định {index} · {badge} · Loại: {text(loai_label)}</p>',
                unsafe_allow_html=True,
            )
            st.markdown(content(point.get('nhan_dinh')), unsafe_allow_html=True)
            if point.get('giai_thich_thun_viet'):
                st.markdown(
                    '<p class="muted"><strong>Giải nghĩa thuần Việt:</strong> ' + text(point.get('giai_thich_thun_viet')) + '</p>',
                    unsafe_allow_html=True,
                )

            # Nút / Expander "Vì sao?" mở 4 yếu tố
            with st.expander(f"Vì sao nhận định {index}? (Dữ kiện & quy tắc)", expanded=False):
                # 1. Dữ kiện
                f_ids = point.get('fact_ids') or []
                f_labels = [
                    f"{fact_map[i]['sao']} tại {fact_map[i]['cung']} ({fact_map[i]['dia_chi']})"
                    for i in f_ids if i in fact_map
                ]
                st.caption(f"**Dữ kiện:** {'; '.join(f_labels) if f_labels else (', '.join(f_ids) or '—')}")

                # 2. Quy tắc (rule_ids từ cách cục hoặc quy tắc lưu niên)
                r_ids = point.get('rule_ids') or []
                rule_desc = ', '.join(r_ids) if r_ids else 'Quy tắc phân tích cấu trúc sao và cung'
                st.caption(f"**Quy tắc:** {rule_desc}")

                # 3. Chủ đề liên quan
                st.caption(f"**Chủ đề:** Mệnh / Thân / Vận trình liên quan")

                # 4. Điều kiện thiếu / Phản chứng & Giới hạn
                limits = point.get('gioi_han', 'Chưa xác minh thủ công.')
                missing = point.get('dieu_kien_chua_kiem_tra') or []
                missing_text = f" · Chưa kiểm tra: {', '.join(missing)}" if missing else ""
                st.caption(f"**Điều kiện / giới hạn:** {limits}{missing_text}")

                # Nguồn tham chiếu
                refs = point.get('source_refs') or []
                if refs:
                    st.caption(f"**Nguồn sách:** {', '.join(f'[{r}]' for r in refs)}")

    # 2. Cách cục đã nhận diện từ P3 (độc lập AI, hoạt động cả ở chế độ du_lieu)
    cach_cuc = reading.get('cach_cuc') or report.get('cach_cuc') or {}
    matched_rules = [
        r for r in (cach_cuc.get('rules') or [])
        if r.get('ket_qua') in ('khop_du', 'khop_mot_phan')
    ]
    st.markdown("#### Cách cục đã nhận diện từ lá số")
    if matched_rules:
        st.caption("Các cấu trúc sao và quan hệ cung được xác định tự động bằng quy tắc tất định (P3).")
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

    # 3. Gợi ý để chiêm nghiệm
    loi_khuyen = reading.get("loi_khuyen_hanh_dong")
    if loi_khuyen:
        st.markdown(panel("Gợi ý để chiêm nghiệm", content(loi_khuyen)), unsafe_allow_html=True)


def render_evidence_section(report: dict[str, Any], meta: dict[str, Any]) -> None:
    """Khối 5: Xem căn cứ — Bảng lập luận, Bảng sao đối chiếu, Trích dẫn sách gốc và Thông số kỹ thuật."""
    st.subheader("Xem căn cứ")
    st.caption("Chi tiết dữ kiện sao, bảng đối chiếu chứng cứ, trích đoạn sách gốc và thông số kỹ thuật.")

    reading = report.get("reading") or {}
    fact_map = {f['fact_id']: f for f in report.get('star_analysis', []) if isinstance(f, dict) and 'fact_id' in f}

    # 1. Bảng lập luận từ sao và nguồn sách (loi_chung_cu & phan_chung)
    if reading.get('luan_diem'):
        st.markdown("#### Lập luận từ sao và nguồn sách")
        st.caption("Dấu hiệu thuận là loại chứng cứ gắn với fact_id; dấu hiệu nghịch là phản chứng trong nguồn hoặc câu 'Không ghi nhận phản chứng trong nguồn đã lấy'.")
        st.markdown(evidence_table(reading['luan_diem'], fact_map), unsafe_allow_html=True)

    # 2. Bảng sao & dữ kiện cần đối chiếu
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

    # 3. Trích dẫn sách gốc
    st.markdown("#### Đối chiếu & tìm hiểu thêm")
    show_sources = st.toggle("Xem trích dẫn sách gốc", key="show_sources")
    if show_sources:
        citations = report.get("citations", [])
        st.caption("Đây là các đoạn được truy xuất để đối chiếu. Việc một đoạn xuất hiện ở đây chưa xác nhận mọi nhận định trong bài được nguồn đó hỗ trợ.")
        if not citations:
            st.info("Chưa có đoạn sách được truy xuất cho báo cáo này.")
        for source in citations:
            title = f'[{source.get("ref_id", "—")}] {BOOKS.get(source.get("book_code"), source.get("book_code", "Nguồn"))}'
            with st.expander(title):
                st.caption(f'{source.get("page_label", "Trang không xác định")} · {source.get("chapter") or "Chưa có tên chương"} · Chưa kiểm duyệt thủ công')
                st.text(source.get("excerpt") or "Chưa có đoạn trích.")

    # 4. Thời gian xử lý và chế độ thực chạy
    with st.expander('Thời gian xử lý và chế độ thực chạy'):
        timings = meta.get('timings_ms', {})
        provider_label = {
            'gemini': 'Luận giải thông minh (online)',
            'mock': 'Chỉ dữ kiện lá số (không dùng AI)',
        }.get(meta.get('actual_provider'), meta.get('actual_provider', '—'))
        actual_m = meta.get('actual_reading_mode', meta.get('reading_mode', 'chuyen_sau'))
        st.caption(f"Chế độ: {provider_label} (Mức: {actual_m}) · Số lần xử lý: {meta.get('attempts', 0)} · Cache: {'trúng' if meta.get('cached') else 'chưa có'}")
        if meta.get('star_meanings_provided_to_ai'):
            st.caption('Đã cấp thêm ý nghĩa sao từ skill tham khảo cho AI; chưa đối chiếu sách KMS, không thay nguồn sách gốc.')
        st.caption(' · '.join(
            f"{label}: {timings.get(key, 0) / 1000:.2f}s"
            for key, label in [('chart', 'Lập lá số'), ('retrieval', 'Lấy nguồn'), ('generation', 'Tạo bài'), ('total', 'Tổng')]
        ))
