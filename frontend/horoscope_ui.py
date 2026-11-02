"""Layman horoscope app. Run: streamlit run frontend/horoscope_ui.py."""
from __future__ import annotations

from datetime import datetime
import base64
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
for _mod in ('frontend.horoscope_view', 'frontend.horoscope_transport', 'frontend.horoscope_ask', 'frontend.laso_renderer'):
    if _mod in sys.modules:
        try:
            importlib.reload(sys.modules[_mod])
        except Exception:
            pass

from frontend.horoscope_view import (BOOKS, HOURS, TOPICS, content,
                                    palace_preview, panel, text, topic_panel, validate_birth_date,
                                    annual_panel, star_table)
from frontend.laso_renderer import luoi_html
from frontend.horoscope_transport import reading_events
from frontend.horoscope_ask import ask_box

st.set_page_config(page_title="Tử Vi · Bản đồ bản thân", layout="wide", initial_sidebar_state="auto")
style = (ROOT / "frontend/assets/horoscope.css").read_text(encoding="utf-8")
font_faces = ""
for weight in (400, 500, 600):
    encoded = base64.b64encode((ROOT / f"frontend/assets/fonts/IBMPlexSans-{weight}.ttf").read_bytes()).decode("ascii")
    font_faces += f"@font-face{{font-family:'IBM Plex Sans';font-weight:{weight};font-style:normal;font-display:swap;src:url(data:font/ttf;base64,{encoded}) format('truetype');}}"
st.markdown(f"<style>{font_faces}{style}</style>", unsafe_allow_html=True)

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

CONFIDENCE_OPTIONS = {
    "A": "A · Giờ sinh rõ, không sát ranh giới giờ",
    "B": "B · Sai số nhỏ, không sát ranh giới giờ",
    "C": "C · Sát ranh giới giờ hoặc chỉ nhớ gần đúng",
    "D": "D · Thiếu dữ liệu giờ sinh cốt lõi",
}
CONFIDENCE_SOURCES = {
    "document": "Giấy tờ/hồ sơ ghi rõ",
    "memory": "Nhớ lại từ gia đình",
    "estimate": "Ước lượng",
    "unknown": "Không rõ",
}


def _is_in_container() -> bool:
    """Streamlit Cloud / Docker: fallback production là hành vi bình thường, không cảnh báo."""
    return Path("/.dockerenv").exists() or bool(os.getenv("KUBERNETES_SERVICE_HOST"))


# Dev local mà local backend (127.0.0.1:8000) không chạy => app sẽ "im lặng" gọi
# backend production. Cảnh báo để tránh nhầm lẫn khi phát triển.
PROD_FALLBACK = "onrender.com" in API_BASE and not os.getenv("KMS_API_BASE") and not _is_in_container()


with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark" aria-hidden="true">田</span><strong>KMS Tử Vi</strong></div>', unsafe_allow_html=True)
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
    with st.expander("Độ tin cậy dữ liệu giờ sinh", expanded=False):
        confidence = st.selectbox(
            "Độ tin cậy giờ sinh", list(CONFIDENCE_OPTIONS), index=0,
            format_func=CONFIDENCE_OPTIONS.get, key="input_confidence",
            help="C/D nghĩa là giờ sinh sát ranh giới hoặc thiếu dữ liệu; báo cáo chỉ nêu kết luận cấu trúc, không kết luận thời điểm/sự kiện.",
        )
        gio_sinh_source = st.selectbox(
            "Nguồn giờ sinh", list(CONFIDENCE_SOURCES), index=1,
            format_func=CONFIDENCE_SOURCES.get, key="gio_sinh_source",
        )
        gio_sinh_error = st.number_input(
            "Sai số ước tính (phút, 0 = không rõ)", min_value=0, max_value=720, value=0, step=5,
            key="gio_sinh_error",
        )
        if confidence in ("C", "D"):
            st.warning("Mức C/D: báo cáo chỉ nêu kết luận cấu trúc và ghi rõ giới hạn; không kết luận thời điểm/sự kiện cụ thể.")
    with st.expander("Tùy chọn bài đọc", expanded=True):
        target_year = st.number_input("Năm chiêm nghiệm (âm lịch)", min_value=1900, max_value=2200, value=year_now, step=1, key="target_year",
                                      help="Chọn năm Can Chi để xem tiểu hạn, vòng Thái Tuế và lưu Tứ Hóa. Đổi năm sẽ hiện nhắc tạo lại báo cáo.")
        priorities = st.pills("Chủ đề muốn đọc trước", list(TOPICS), selection_mode="multi", format_func=TOPICS.get, key="birth_topics",
                              help="Các chủ đề đã chọn được đặt trước trong báo cáo; tổng quan luôn được giữ lại.")
        mode = st.selectbox("Bản luận giải", ["auto", "mock"], format_func=lambda v: "Luận giải thông minh · tự động" if v == "auto" else "Chỉ dữ kiện lá số · không dùng AI", key="birth_provider")
    submitted = st.button("Tạo bản luận giải", type="primary", use_container_width=True)
    st.caption("Giờ sinh theo múi giờ Việt Nam (UTC+7). Với lịch âm, thuật toán hiện chưa hỗ trợ lựa chọn tháng nhuận.")

st.markdown('<div class="viewer-bar"><span>KMS Tử Vi · Bản đồ bản thân</span><span>Tri thức từ NPL · Bửu Đình · Đẩu Số</span></div>', unsafe_allow_html=True)
st.title("Bản luận giải Tử Vi")
st.markdown("Một góc nhìn từ tri thức truyền thống, để hiểu mình và chiêm nghiệm.")
if PROD_FALLBACK:
    st.warning(
        f"Local backend (http://127.0.0.1:8000) chưa chạy — app đang dùng backend production "
        f"({API_BASE}). Chạy run_server.py, hoặc đặt biến môi trường KMS_API_BASE nếu muốn dùng backend khác."
    )

if submitted:
    validation = validate_birth_date(day, month, year, calendar == "Dương lịch")
    if target_year < year:
        validation = "Năm chiêm nghiệm cần từ năm sinh trở đi."
    if validation:
        st.error(validation)
    else:
        payload = {"ho_ten": name.strip(), "ngay": day, "thang": month, "nam": year,
                   "chi_gio": hour, "gioi_tinh": gender, "duong_lich": calendar == "Dương lịch",
                   "input_confidence": confidence, "gio_sinh_source": gio_sinh_source,
                   "gio_sinh_error_phut": int(gio_sinh_error) if gio_sinh_error else None,
                   "target_year": target_year, "provider": mode, "top_k_per_topic": 4}
        try:
            preview = st.empty()
            with st.status("Đang lập lá số và đối chiếu sách…", expanded=True) as progress:
                result = None
                for event in reading_events(API_BASE, payload):
                    if event.get('event') == 'progress':
                        seconds = event.get('elapsed_ms', 0) / 1000
                        progress.update(label=f"{event.get('message', 'Đang xử lý…')} · {seconds:.0f} giây")
                    elif event.get('event') == 'prepared':
                        prepared = event['report']
                        with preview.container():
                            st.caption(f"Đã lập xong 12 cung và lấy {len(prepared.get('citations', []))} nguồn. Đây là dữ kiện trước khi luận giải thông minh diễn giải.")
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
    input_confidence = str(basic.get("input_confidence") or "A").upper()
    if input_confidence in ("C", "D"):
        st.warning(f"Dữ liệu giờ sinh chưa chắc chắn (mức {input_confidence}): báo cáo chỉ nêu kết luận cấu trúc, "
                   "không kết luận thời điểm/sự kiện cụ thể. Hãy đối chiếu lại giờ sinh nếu có thể.")
    if is_mock:
        reason = "Bạn đã chọn chế độ chỉ dữ kiện lá số." if meta.get('reason') == 'requested' else meta.get('message', 'Luận giải thông minh chưa trả được bài hợp lệ.')
        st.markdown('<p class="notice">Phân tích dữ kiện lá số · ' + text(reason) + ' Phần dưới mô tả sao/cung tính được; chưa phải bài luận giải thông minh.</p>', unsafe_allow_html=True)
    elif is_mock is None:
        st.markdown('<p class="notice">Dịch vụ chưa cung cấp thông tin xác nhận chế độ tạo bài.</p>', unsafe_allow_html=True)
    else:
        st.caption("Bài luận giải thông minh · Nội dung và nguồn trích dẫn chưa được kiểm duyệt thủ công.")
    if meta.get('specificity_low'):
        st.caption('Bài tổng hợp dựa trên ít dữ kiện riêng của lá số; xem mục Phân tích sao để đối chiếu.')
    st.markdown(f'<div class="report-heading"><h2>{text(report.get("ho_ten"))}</h2><span>{text(st.session_state["report_time"])}</span></div>'
                f'<p class="muted">{snapshot["ngay"]:02d}/{snapshot["thang"]:02d}/{snapshot["nam"]} · {"Dương lịch" if snapshot["duong_lich"] else "Âm lịch"} · {text(HOURS[snapshot["chi_gio"]-1])} · Năm {snapshot["target_year"]} · Giờ sinh mức {text(input_confidence)}</p>', unsafe_allow_html=True)
    report_year = meta.get('target_year') or (report.get('annual') or {}).get('year')
    if report_year and target_year != report_year:
        st.warning(f"Báo cáo bên dưới là của năm {report_year}. Ô Năm chiêm nghiệm đang là {target_year}; "
                   "bấm Tạo bản luận giải để tạo lại báo cáo cho năm mới.")
    element = str(basic.get("ban_menh", "")).upper()
    element_class = next((v for k, v in {"HỎA": "hoa", "THỦY": "thuy", "MỘC": "moc", "KIM": "kim", "THỔ": "tho"}.items() if k in element), "neutral")
    stats = [("Bản mệnh", basic.get("ban_menh")), ("Cục số", basic.get("ten_cuc")),
             ("Mệnh tại", basic.get("cung_menh")), ("Thân tại", basic.get("cung_than"))]
    identity_items = []
    for index, (label, value) in enumerate(stats):
        marker = f'<i class="element-dot {element_class}" aria-hidden="true"></i>' if index == 0 else ""
        identity_items.append(f'<div><span class="muted">{label}</span><strong>{marker}{text(value)}</strong></div>')
    st.markdown('<div class="identity-strip">' + ''.join(identity_items) + '</div>', unsafe_allow_html=True)
    if report.get('annual'):
        st.markdown(annual_panel(report['annual'], report.get('luu_nien')), unsafe_allow_html=True)
    overview = reading.get("tong_quan", {})
    if not isinstance(overview, dict):
        overview = {}
    left = panel("Chân dung của bạn", content(overview.get("ban_sac")) + '<h3>Mệnh và môi trường sống</h3>' + content(overview.get("ngu_hanh_nang_luong")))
    right = panel("Thế mạnh & điều cần rèn luyện", '<h3>Thế mạnh</h3>' + content(overview.get("diem_manh")) + '<h3>Điều cần rèn luyện</h3>' + content(overview.get("diem_can_ren_luyen")))
    st.markdown('<div class="overview-grid">' + left + right + '</div>', unsafe_allow_html=True)
    order = list(dict.fromkeys(st.session_state.get("report_priorities", []) + list(TOPICS)))
    tabs = st.tabs([TOPICS[key] for key in order])
    for key, tab in zip(order, tabs):
        with tab:
            st.markdown(topic_panel(key, reading.get(key, {})), unsafe_allow_html=True)
            ask_box(key, snapshot, snapshot.get('provider', 'auto'), API_BASE)
    if reading.get('ket_luan'):
        st.subheader('Kết luận & phân tích sâu')
        st.caption('Mỗi mục gồm nhận định chuyên môn và phần chuyển thuật ngữ sang nghĩa đời thường, kèm dữ kiện/nguồn đối chiếu.')
        fact_map = {f['fact_id']: f for f in report.get('star_analysis', [])}
        for index, point in enumerate(reading['ket_luan'], 1):
            st.markdown(f'<p class="muted">Kết luận {index}</p>', unsafe_allow_html=True)
            st.markdown(content(point.get('nhan_dinh')), unsafe_allow_html=True)
            if point.get('giai_thich_thun_viet'):
                st.markdown('<p class="muted"><strong>Giải nghĩa thuần Việt:</strong> ' + text(point.get('giai_thich_thun_viet')) + '</p>', unsafe_allow_html=True)
            labels = [f"{fact_map[i]['sao']} tại {fact_map[i]['cung']} ({fact_map[i]['dia_chi']})" for i in point.get('fact_ids', []) if i in fact_map]
            st.caption('Dữ kiện: ' + ('; '.join(labels) or '—') + ' · Nguồn: ' + (', '.join(f'[{r}]' for r in point.get('source_refs', [])) or '—'))
            st.caption('Điều kiện / giới hạn: ' + point.get('gioi_han', 'Chưa xác minh thủ công.'))
    st.markdown(panel("Gợi ý để chiêm nghiệm", content(reading.get("loi_khuyen_hanh_dong"))), unsafe_allow_html=True)
    if reading.get('luan_diem'):
        st.subheader('Lập luận từ sao và nguồn sách')
        fact_map = {f['fact_id']: f for f in report.get('star_analysis', [])}
        for point in reading['luan_diem']:
            st.markdown(content(point.get('nhan_dinh')), unsafe_allow_html=True)
            labels = [f"{fact_map[i]['sao']} tại {fact_map[i]['cung']} ({fact_map[i]['dia_chi']})" for i in point.get('fact_ids', []) if i in fact_map]
            st.caption('Dữ kiện: ' + '; '.join(labels) + ' · Nguồn: ' + ', '.join(f'[{r}]' for r in point.get('source_refs', [])))
            st.caption('Điều kiện / giới hạn: ' + point.get('gioi_han', 'Chưa xác minh thủ công.'))
    if report.get('star_analysis'):
        st.subheader('Sao & yếu tố cần đối chiếu')
        st.caption('Nhóm cần lưu ý lấy từ danh mục sao truyền thống; không phải điểm rủi ro hay dự báo một biến cố. M/V/Đ/B/H là trạng thái sao gốc.')
        group = st.selectbox('Phạm vi sao', ['Cần lưu ý', 'Chính tinh', 'Hỗ trợ', 'Tất cả'] + (
            [f"Lưu niên năm {meta.get('target_year') or (report.get('annual') or {}).get('year')}"]
            if any(f.get('nhom') == 'luu_nien' for f in report['star_analysis']) else []
        ), key='star_filter')
        groups = {'Cần lưu ý': 'risk_stars', 'Chính tinh': 'chinh_tinh', 'Hỗ trợ': 'cat_tinh'}
        if group.startswith('Lưu niên'):
            selected = [f for f in report['star_analysis'] if f.get('nhom') == 'luu_nien']
        else:
            selected = [f for f in report['star_analysis'] if group == 'Tất cả' or f.get('nhom') == groups.get(group)]
        if selected:
            st.markdown(star_table(selected), unsafe_allow_html=True)
            with st.expander('Đối chiếu nguồn của một sao'):
                fact = st.selectbox('Chọn sao và cung', selected, format_func=lambda f: f"{f['sao']} · {f['cung']} tại {f['dia_chi']}", key='selected_star')
                st.caption(fact['source_status'])
                for source in report.get('citations', []):
                    if source['ref_id'] in fact['source_refs']:
                        st.caption(f"[{source['ref_id']}] {BOOKS.get(source['book_code'], source['book_code'])} · {source.get('page_label', '')}")
                        st.text(source['excerpt'])
        else:
            st.info('Chưa có sao thuộc nhóm này trong các cung đang phân tích.')
    st.subheader("Đối chiếu & tìm hiểu thêm")
    show_chart = st.toggle("Xem lá số chi tiết 12 cung", key="show_chart")
    if show_chart:
        palaces = report.get("la_so", {}).get("thap_ni_cung", [])
        if palaces:
            st.caption("M: Miếu · V: Vượng · Đ: Đắc · B: Bình · H: Hãm. Đây là ký hiệu vị trí sao trong lý thuyết truyền thống.")
            st.markdown('<div class="horoscope-chart">' + luoi_html(palaces) + '</div>', unsafe_allow_html=True)
        else:
            st.info("Dịch vụ chưa trả dữ liệu 12 cung cho báo cáo này.")
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
    with st.expander('Thời gian xử lý và chế độ thực chạy'):
        timings = meta.get('timings_ms', {})
        provider_label = {'gemini': 'Luận giải thông minh (online)', 'mock': 'Chỉ dữ kiện lá số (không dùng AI)'}.get(meta.get('actual_provider'), meta.get('actual_provider', '—'))
        st.caption(f"Chế độ: {provider_label} · Số lần xử lý: {meta.get('attempts', 0)} · Cache: {'trúng' if meta.get('cached') else 'chưa có'}")
        st.caption(' · '.join(f"{label}: {timings.get(key, 0) / 1000:.2f}s" for key, label in [('chart', 'Lập lá số'), ('retrieval', 'Lấy nguồn'), ('generation', 'Tạo bài'), ('total', 'Tổng')]))

st.markdown('<footer>Tử Vi là một hệ thống văn hóa truyền thống để tham khảo và chiêm nghiệm. Luận giải không quyết định số phận và không thay thế tư vấn y khoa, pháp lý hay tài chính chuyên nghiệp.</footer>', unsafe_allow_html=True)
