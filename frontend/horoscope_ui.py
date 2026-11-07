"""Layman horoscope app. Run: streamlit run frontend/horoscope_ui.py."""
from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import importlib
for _mod in ('frontend.horoscope_view', 'frontend.horoscope_sections', 'frontend.horoscope_transport', 'frontend.laso_renderer'):
    if _mod in sys.modules:
        try:
            importlib.reload(sys.modules[_mod])
        except Exception:
            pass

from frontend.horoscope_view import (BOOKS, HOURS, TOPICS, content,
                                    palace_preview, panel, text, topic_panel, validate_birth_date,
                                    annual_panel, star_table, confidence_badge, evidence_table)
from frontend.laso_renderer import luoi_html, render_laso
from frontend.horoscope_transport import reading_events
from frontend.horoscope_sections import (
    render_header_identity,
    render_annual_overview_section,
    render_chart_section,
    render_overview_section,
    render_topics_section,
    render_action_advice_section,
    render_why_section,
    render_evidence_section,
    render_evidence_and_specialist_section,
    chart_viewer_general,
)

from frontend.ui_themes import apply_theme

st.set_page_config(page_title="Tử Vi · Bản đồ bản thân", layout="wide", initial_sidebar_state="auto")
apply_theme()

def _resolve_api_base() -> str:
    env_url = os.getenv("KMS_API_BASE")
    if env_url:
        return env_url.rstrip("/")
    try:
        r = requests.get("http://127.0.0.1:8000/api/v1/health", timeout=0.3)
        if r.status_code == 200:
            return "http://127.0.0.1:8000"
    except Exception:
        pass
    return "https://tuvi-kms-backend.onrender.com"


API_BASE = _resolve_api_base()
year_now = datetime.now(ZoneInfo("Asia/Bangkok")).year

from frontend.ui_fixture import is_fixture_mode, load_fixture

if is_fixture_mode() and "report" not in st.session_state:
    sample_report = load_fixture("sample_report")
    if isinstance(sample_report, dict):
        st.session_state["report"] = sample_report
        st.session_state["report_input"] = {
            "ho_ten": sample_report.get("ho_ten", "Lê An"),
            "ngay": 15,
            "thang": 8,
            "nam": 1995,
            "chi_gio": 5,
            "gioi_tinh": 1,
            "duong_lich": True,
            "target_year": sample_report.get("meta", {}).get("target_year", year_now),
            "provider": "auto",
            "reading_mode": "chuyen_sau",
            "top_k_per_topic": 4,
        }
        st.session_state["report_priorities"] = list(TOPICS)
        st.session_state["report_time"] = datetime.now(ZoneInfo("Asia/Bangkok")).strftime("%H:%M · %d/%m/%Y")


def _is_in_container() -> bool:
    """Streamlit Cloud / Docker: fallback production là hành vi bình thường, không cảnh báo."""
    return Path("/.dockerenv").exists() or bool(os.getenv("KUBERNETES_SERVICE_HOST"))


# Dev local mà local backend (127.0.0.1:8000) không chạy => app sẽ "im lặng" gọi
# backend production. Cảnh báo để tránh nhầm lẫn khi phát triển.
PROD_FALLBACK = "onrender.com" in API_BASE and not os.getenv("KMS_API_BASE") and not _is_in_container()


def _luu_nien_by_cung_map(luu_nien: dict | None, thap_ni_cung: list[dict]) -> dict[int, list[dict]]:
    if not isinstance(luu_nien, dict):
        return {}
    mapping: dict[int, list[dict]] = {}
    chi_to_cung = {str(c.get("chuan_ten", "")): c.get("cung_so") for c in thap_ni_cung if c.get("cung_so")}

    tt = luu_nien.get("thai_tue")
    if isinstance(tt, dict) and tt.get("dia_chi") in chi_to_cung:
        c_so = chi_to_cung[tt["dia_chi"]]
        mapping.setdefault(c_so, []).append({"sao": "Thái Tuế", "dia_chi": tt["dia_chi"], "loai": "hung"})

    for name, s_info in (luu_nien.get("vong_thai_tue") or {}).items():
        if isinstance(s_info, dict):
            d_chi = s_info.get("dia_chi")
            if d_chi in chi_to_cung:
                c_so = chi_to_cung[d_chi]
                mapping.setdefault(c_so, []).append({"sao": s_info.get("ten", name), "dia_chi": d_chi, "loai": s_info.get("loai")})

    for lth in (luu_nien.get("luu_tu_hoa") or []):
        if isinstance(lth, dict):
            c_ten = lth.get("cung_ten")
            for c in thap_ni_cung:
                if c.get("ten_cung") == c_ten or c.get("chuan_ten") == c_ten:
                    c_so = c.get("cung_so")
                    if c_so:
                        code_label = {"HOA_LOC": "Lộc", "HOA_QUYEN": "Quyền", "HOA_KHOA": "Khoa", "HOA_KY": "Kỵ"}.get(lth.get("code"), "")
                        label = f"Hóa {code_label} ({lth.get('ten_sao')})" if code_label else str(lth.get("ten_sao"))
                        mapping.setdefault(c_so, []).append({"sao": label, "loai": "tu_hoa"})
                    break
    return mapping

with st.sidebar:
    st.markdown('<div class="brand"><span class="seal-stamp" style="font-size:11px;padding:2px 4px;">KMS</span><strong>Tử Vi Cổ Thư</strong></div>', unsafe_allow_html=True)
    st.markdown("### Thông tin của bạn")
    st.caption("Ngày và giờ sinh là điểm khởi đầu cho bản đồ 12 cung.")
    name = st.text_input("Họ tên (không bắt buộc)", max_chars=80, key="birth_name")
    calendar = st.radio("Lịch ngày sinh", ["Dương lịch", "Âm lịch"], horizontal=True, key="birth_calendar")
    day_col, month_col = st.columns(2)
    day = day_col.number_input("Ngày", min_value=1, max_value=31, value=15, key="birth_day")
    month = month_col.number_input("Tháng", min_value=1, max_value=12, value=8, key="birth_month")
    year = st.number_input("Năm sinh", min_value=1900, max_value=min(year_now, 2100), value=1995, step=1, key="birth_year")
    hour = st.selectbox("Giờ sinh", range(1, 13), index=4, format_func=lambda n: HOURS[n-1], key="birth_hour")
    gender = st.radio("Giới tính theo lá số", [1, 2], format_func=lambda n: "Nam" if n == 1 else "Nữ", horizontal=True, key="birth_gender")
    with st.expander("Tùy chọn bài đọc", expanded=True):
        target_year = st.number_input("Năm chiêm nghiệm (âm lịch)", min_value=1900, max_value=2200, value=year_now, step=1, key="target_year",
                                      help="Chọn năm Can Chi để xem tiểu hạn, vòng Thái Tuế và lưu Tứ Hóa. Đổi năm sẽ hiện nhắc tạo lại báo cáo.")
        priorities = st.pills("Chủ đề muốn đọc trước", list(TOPICS), selection_mode="multi", format_func=TOPICS.get, key="birth_topics",
                              help="Các chủ đề đã chọn được đặt trước trong báo cáo; tổng quan luôn được giữ lại.")
        reading_mode = st.selectbox(
            "Mức độ bài đọc",
            ["du_lieu", "chuyen_sau"],
            index=1,
            format_func={
                "du_lieu": "Lá số & dữ kiện · không gọi AI",
                "chuyen_sau": "AI chuyên sâu · phân tích tổng hợp",
            }.get,
            key="reading_mode",
            help="du_lieu: chỉ hiển thị lá số và dữ kiện; chuyen_sau: AI luận giải chuyên sâu đa chiều.",
        )
    submitted = st.button("Tạo bản luận giải", type="primary", use_container_width=True)
    st.caption("Giờ sinh theo múi giờ Việt Nam (UTC+7). Với lịch âm, thuật toán hiện chưa hỗ trợ lựa chọn tháng nhuận.")

st.markdown('<div class="viewer-bar"><span>KMS Tử Vi · Bản đồ bản thân</span><span>Tri thức từ NPL · Bửu Đình · Đẩu Số</span></div>', unsafe_allow_html=True)
st.title("Bản đồ bản thân & Chiêm nghiệm")
st.markdown("Một góc nhìn từ tri thức truyền thống, để hiểu mình và chiêm nghiệm.")
if PROD_FALLBACK:
    st.warning(
        f"Local backend (http://127.0.0.1:8000) chưa chạy — app đang dùng backend production "
        f"({API_BASE}). Chạy run_server.py, hoặc đặt biến môi trường KMS_API_BASE nếu muốn dùng backend khác."
    )

retry_payload = st.session_state.pop("retry_ai_payload", None)
if submitted or retry_payload is not None:
    if retry_payload is None:
        validation = validate_birth_date(day, month, year, calendar == "Dương lịch")
        if target_year < year:
            validation = "Năm chiêm nghiệm cần từ năm sinh trở đi."
    else:
        validation = None
    if validation:
        st.error(validation)
    else:
        payload = retry_payload or {"ho_ten": name.strip(), "ngay": day, "thang": month, "nam": year,
                   "chi_gio": hour, "gioi_tinh": gender, "duong_lich": calendar == "Dương lịch",
                   "target_year": target_year, "provider": "auto", "reading_mode": reading_mode, "top_k_per_topic": 4}
        try:
            preview = st.empty()
            with st.status("Đang lập lá số và đối chiếu sách…", expanded=True) as progress:
                result = None
                for event in reading_events(API_BASE, payload):
                    if event.get('event') == 'progress':
                        seconds = event.get('elapsed_ms', 0) / 1000
                        progress.update(label=f"{event.get('message', 'Đang xử lý…')} · {seconds:.0f} giây")
                    elif event.get('event') == 'chart_ready':
                        chart_data = event['report']
                        st.session_state["chart_backup"] = chart_data
                        with preview.container():
                            st.caption("Đã tính xong lá số 12 cung. Bạn có thể xem ngay bên dưới trong khi hệ thống tìm nguồn sách và luận giải.")
                            palaces = chart_data.get("la_so", {}).get("thap_ni_cung", [])
                            if palaces:
                                ln_map = _luu_nien_by_cung_map(chart_data.get("luu_nien"), palaces)
                                ho_ten = chart_data.get("ho_ten") or "Chủ Mệnh"
                                thien_ban = {"ho_ten": ho_ten, "general": chart_viewer_general(chart_data, ho_ten)}
                                st.markdown('<div class="horoscope-chart">' + render_laso(palaces, che_do="luoi", luu_nien_by_cung=ln_map, thien_ban=thien_ban) + '</div>', unsafe_allow_html=True)
                            if chart_data.get("annual"):
                                st.markdown(annual_panel(chart_data["annual"], chart_data.get("luu_nien")), unsafe_allow_html=True)
                    elif event.get('event') == 'prepared':
                        prepared = event['report']
                        with preview.container():
                            st.caption(f"Đã lập xong 12 cung và lấy {len(prepared.get('citations', []))} nguồn. Đây là dữ kiện trước khi luận giải thông minh diễn giải.")
                            palaces = prepared.get("la_so", {}).get("thap_ni_cung", [])
                            if palaces:
                                ln_map = _luu_nien_by_cung_map(prepared.get("luu_nien"), palaces)
                                ho_ten = prepared.get("ho_ten") or "Chủ Mệnh"
                                thien_ban = {"ho_ten": ho_ten, "general": chart_viewer_general(prepared, ho_ten)}
                                st.markdown('<div class="horoscope-chart">' + render_laso(palaces, che_do="luoi", luu_nien_by_cung=ln_map, thien_ban=thien_ban) + '</div>', unsafe_allow_html=True)
                            st.markdown(annual_panel(prepared.get('annual', {}), prepared.get('luu_nien')), unsafe_allow_html=True)
                    elif event.get('event') == 'result':
                        result = event['report']
                if result is None:
                    raise ValueError('Dịch vụ chưa gửi báo cáo hoàn tất.')
                st.session_state["report"] = result
                st.session_state["report_input"] = payload
                st.session_state["report_priorities"] = priorities
                st.session_state["report_time"] = datetime.now(ZoneInfo("Asia/Bangkok")).strftime("%H:%M · %d/%m/%Y")
                # Report mới => giá trị bộ lọc sao cũ (theo năm/theo báo cáo trước) có thể
                # không còn trong danh sách option; trả hai widget về mặc định.
                for stale_key in ("star_filter", "selected_star"):
                    st.session_state.pop(stale_key, None)
                progress.update(label="Bản luận giải đã sẵn sàng", state="complete", expanded=False)
            preview.empty()
        except requests.Timeout:
            progress.update(label='Kết nối quá thời gian chờ', state='error')
            st.error("Kết nối đến backend vượt thời gian chờ. Hãy thử lại hoặc chọn Dữ kiện lá số; báo cáo trước vẫn được giữ.")
        except requests.RequestException:
            progress.update(label='Không kết nối được dịch vụ', state='error')
            st.error("Không kết nối được dịch vụ luận giải. Hãy thử lại bằng nút Tạo bản luận giải; báo cáo đã có vẫn được giữ lại.")
        except (ValueError, TypeError) as exc:
            progress.update(label='Bài đọc chưa hoàn tất', state='error')
            st.error(str(exc) if isinstance(exc, ValueError) else "Dịch vụ trả dữ liệu không hợp lệ; báo cáo trước vẫn được giữ.")

report = st.session_state.get("report")
if not report:
    st.markdown('<div class="intro-grid">' + panel("Bắt đầu từ ngày sinh của bạn",
                '<p>Điền thông tin và chọn <strong>Tạo bản luận giải</strong>. Bạn sẽ nhận được một báo cáo bằng ngôn ngữ đời thường, cùng lá số để đối chiếu.</p>'
                '<div class="intro-topics"><span>Tính cách &amp; thế mạnh</span><span>Sự nghiệp &amp; tài chính</span><span>Tình cảm &amp; vận trình</span></div>'
                '<p class="muted">Chưa có dữ liệu cá nhân. Sơ đồ bên cạnh chỉ minh họa 12 địa chi.</p>') + palace_preview() + '</div>', unsafe_allow_html=True)
    st.markdown(panel("Đọc hiểu cùng ba nguồn sách", '<div class="book-row">'
                '<div><strong>Nguyễn Phát Lộc</strong><p>Đối chiếu kiến thức theo chủ đề.</p></div>'
                '<div><strong>Bửu Đình</strong><p>Các trích đoạn từ Tử Vi Ứng Dụng.</p></div>'
                '<div><strong>Đẩu Số Toàn Thư</strong><p>Tham khảo cách diễn giải cổ điển.</p></div></div>'), unsafe_allow_html=True)
else:
    basic = report.get("thong_tin_co_ban", {})
    reading = report["reading"]
    meta = report.get("meta", {})
    snapshot = st.session_state["report_input"]
    is_mock = meta.get("is_mock")
    actual_mode = meta.get("actual_reading_mode", meta.get("reading_mode", "chuyen_sau"))
    req_mode = meta.get("reading_mode", actual_mode)
    fallback_reason = meta.get("fallback_reason")

    if is_mock:
        reason = "Bạn đã chọn chế độ chỉ dữ kiện lá số." if meta.get('reason') == 'requested' else meta.get('message', 'Luận giải thông minh chưa trả được bài hợp lệ.')
        st.markdown('<p class="notice">Phân tích dữ kiện lá số · ' + text(reason) + ' Phần dưới mô tả sao/cung tính được; chưa phải bài luận giải thông minh.</p>', unsafe_allow_html=True)
        attempts_detail = meta.get("attempts_detail")
        if attempts_detail and isinstance(attempts_detail, list):
            with st.expander("Chi tiết lỗi các provider AI (Chẩn đoán kết nối)", expanded=False):
                rows = []
                for att in attempts_detail:
                    p_name = str(att.get("provider", "—")).capitalize()
                    m_name = str(att.get("model", "—"))
                    code = str(att.get("code", "—"))
                    msg = str(att.get("message", "—")).replace("|", "-").replace("\n", " ")
                    rows.append(f"| **{p_name}** | `{m_name}` | `{code}` | {msg} |")
                table_md = (
                    "| Provider | Model | Mã lỗi | Chi tiết thông báo |\n"
                    "| :--- | :--- | :--- | :--- |\n"
                    + "\n".join(rows)
                )
                st.markdown(table_md)
    elif is_mock is None:
        st.markdown('<p class="notice">Dịch vụ chưa cung cấp thông tin xác nhận chế độ tạo bài.</p>', unsafe_allow_html=True)
    else:
        mode_label = "AI Chuyên sâu" if actual_mode == "chuyen_sau" else "AI Giải thích"
        st.caption(f"Bài luận giải thông minh ({mode_label}) · Nội dung và nguồn trích dẫn chưa được kiểm duyệt thủ công.")
    if fallback_reason:
        st.warning(f"Lưu ý: Yêu cầu mức '{req_mode}', nhưng hệ thống hạ về '{actual_mode}' do: {fallback_reason}. Lá số và dữ kiện vẫn được bảo toàn.")
    if meta.get('specificity_low'):
        st.caption('Bài tổng hợp dựa trên ít dữ kiện riêng của lá số; xem mục Phân tích sao để đối chiếu.')
    # Định danh người xem
    render_header_identity(report, snapshot, basic)
    report_year = meta.get('target_year') or (report.get('annual') or {}).get('year')
    if report_year and target_year != report_year:
        st.warning(f"Báo cáo bên dưới là của năm {report_year}. Ô Năm chiêm nghiệm đang là {target_year}; "
                   "bấm Tạo bản luận giải để tạo lại báo cáo cho năm mới.")

    # Luồng hiển thị mới:
    # 2. Tổng quan năm
    render_annual_overview_section(reading, report, report_year)

    # 3. Lá số 12 cung
    render_chart_section(report, luu_nien_by_cung_fn=_luu_nien_by_cung_map)

    # 4. Chân dung, thế mạnh và điều cần rèn luyện
    render_overview_section(reading)

    # 5. Theo chủ đề
    render_topics_section(reading, snapshot, API_BASE, st.session_state.get("report_priorities", []))

    # 6. Gợi ý hành động
    render_action_advice_section(reading)

    # 7. Căn cứ và thông tin chuyên môn (mặc định đóng)
    render_evidence_and_specialist_section(report, meta)

st.markdown('<footer>Tử Vi là một hệ thống văn hóa truyền thống để tham khảo và chiêm nghiệm. Luận giải không quyết định số phận và không thay thế tư vấn y khoa, pháp lý hay tài chính chuyên nghiệp.</footer>', unsafe_allow_html=True)
