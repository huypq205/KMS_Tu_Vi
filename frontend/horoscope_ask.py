"""Ô "Hỏi nhanh có đáp · kèm nguồn sách" trong tab chủ đề.

Tách từ horoscope_ui.py để giữ trang chủ ngắn gọn; widget vẫn đăng ký
bình thường khi được gọi từ script Streamlit chính.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import streamlit as st

from frontend.horoscope_view import ASK_LABELS, ASK_SUGGESTIONS, text
from frontend.horoscope_transport import ask_horoscope


def render_ask_answer(saved: dict) -> None:
    result = saved["result"]
    level = ASK_LABELS.get(result.get("muc_do_can_cu"), "—")
    if result.get("muc_do_can_cu") == "dau_hieu_ro":
        st.success(level)
    elif result.get("muc_do_can_cu") == "dau_hieu_yeu":
        st.warning(level)
    else:
        st.info(level)
    body = f'<p>{text(result.get("tra_loi"))}</p>'
    if result.get("giai_thich_thun_viet"):
        body += f'<p class="muted">{text(result.get("giai_thich_thun_viet"))}</p>'
    if result.get("gioi_han"):
        body += f'<p class="muted">Giới hạn: {text(result.get("gioi_han"))}</p>'
    st.markdown(body, unsafe_allow_html=True)
    meta = result.get("meta", {})
    mode_note = " · Chế độ chỉ dữ kiện lá số (không dùng AI)" if meta.get("is_mock") else ""
    st.caption(f"Câu hỏi: “{text(saved.get('question'))}” · {text(saved.get('time', ''))}{mode_note} · Trích dẫn chưa kiểm duyệt thủ công.")
    if result.get("citations"):
        with st.expander(f"Nguồn sách đã đối chiếu ({len(result['citations'])})"):
            for c in result["citations"]:
                st.caption(f'[{c.get("ref_id")}] {c.get("book_title") or c.get("book_code", "Nguồn")} · {c.get("page_label") or "Trang không xác định"}')
                st.text(c.get("excerpt") or "Chưa có đoạn trích.")


def ask_box(key: str, snapshot: dict, api_base: str) -> None:
    """Ô hỏi nhanh theo chủ đề; câu trả lời lưu theo key chủ đề trong session_state."""
    st.markdown('<p class="muted"><strong>Hỏi nhanh có đáp · kèm nguồn sách</strong> — trả lời theo dữ kiện lá số và trích dẫn 3 sách nguồn; chưa kiểm duyệt thủ công.</p>', unsafe_allow_html=True)
    for sug_index, suggestion in enumerate(ASK_SUGGESTIONS.get(key, [])):
        if st.button(suggestion, key=f'ask_sug_{key}_{sug_index}'):
            st.session_state[f'ask_q_{key}'] = suggestion
    ask_input = st.text_input("Câu hỏi của bạn (tối đa 300 ký tự)", key=f'ask_q_{key}', max_chars=300,
                              placeholder="VD: Năm nay có người tìm hiểu không?")
    if st.button("Hỏi luận giải thông minh", key=f'ask_btn_{key}'):
        question = str(ask_input).strip()
        if question:
            payload = {'ho_ten': snapshot.get('ho_ten', ''), 'ngay': snapshot['ngay'], 'thang': snapshot['thang'],
                       'nam': snapshot['nam'], 'chi_gio': snapshot['chi_gio'], 'gioi_tinh': snapshot['gioi_tinh'],
                       'duong_lich': snapshot['duong_lich'],
                       'target_year': snapshot.get('target_year'),
                       'topic': key, 'question': question, 'provider': 'auto'}
            with st.spinner("Đang hỏi luận giải thông minh…"):
                try:
                    result = ask_horoscope(api_base, payload)
                    st.session_state[f'ask_answer_{key}'] = {'question': question, 'result': result,
                                                             'time': datetime.now(ZoneInfo("Asia/Bangkok")).strftime('%H:%M')}
                except requests.Timeout:
                    st.error("Kết nối đến dịch vụ hỏi đáp quá thời gian chờ. Thử lại sau.")
                except requests.RequestException:
                    st.error("Không kết nối được dịch vụ hỏi đáp. Báo cáo hiện có vẫn được giữ.")
                except ValueError as exc:
                    st.error(str(exc))
    saved = st.session_state.get(f'ask_answer_{key}')
    if saved:
        render_ask_answer(saved)
