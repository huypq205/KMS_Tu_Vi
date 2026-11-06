"""T14 — Giao diện Streamlit cho KMS Tử Vi.

Ba tab:
  1. Tra cứu  — tìm kiếm từ khóa (FTS5 bỏ dấu), kết quả tách theo sách,
                 badge Trust Tier và số trang PDF.
  2. Hỏi đáp  — gọi /api/v1/chat/ask, trả lời có dẫn nguồn [1], [2].
  3. Thống kê — tổng số bản ghi và phân bố Trust Tier.

Chạy:
    uvicorn backend.app.main:app --reload --port 8000   # terminal 1
    streamlit run frontend/app.py                        # terminal 2
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import altair as alt
import pandas as pd
import requests
import streamlit as st

from frontend.ui_fixture import is_fixture_mode, load_fixture, mock_search, mock_stats
from frontend.ui_themes import apply_theme


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
TIMEOUT = 120

BOOK_TITLES = {
    "NPL": "Nguyễn Phát Lộc",
    "DAU": "Tử Vi Đẩu Số Toàn Thư",
    "BD": "Tử Vi Ứng Dụng — Bửu Đình",
}

st.set_page_config(
    page_title="KMS Tử Vi",
    layout="wide",
)
apply_theme()


# --------------------------------------------------------------------------
# gọi API
# --------------------------------------------------------------------------
def api_get(path: str) -> dict[str, Any] | None:
    if is_fixture_mode():
        if path == "/api/v1/health":
            return {"status": "ok", "knowledge_items": 10456, "chunks": 4350}
        if path == "/api/v1/stats":
            return mock_stats()
    try:
        resp = requests.get(f"{API_BASE}{path}", timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        st.error(f"Không gọi được API tại {API_BASE}{path}: {exc}")
        return None


def api_post(path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    if is_fixture_mode():
        if path == "/api/v1/search":
            return mock_search(payload.get("query"))
        if path == "/api/v1/chat/ask":
            raw_ask = load_fixture("sample_ask")
            citations = [
                {
                    "ref": str(c.get("ref_id", i + 1)),
                    "book_code": c.get("book_code", "NPL"),
                    "book_title": c.get("book_title"),
                    "part_number": c.get("part_number"),
                    "pdf_page_start": c.get("pdf_page_start"),
                    "pdf_page_end": c.get("pdf_page_end"),
                    "trust_tier": c.get("trust_tier", 1),
                    "verification_status": c.get("verification_status", "unverified"),
                    "ui_badge": c.get("ui_badge", "Bản mẫu fixture"),
                    "excerpt": c.get("excerpt", ""),
                    "knowledge_ids": [c.get("chunk_id", "")],
                }
                for i, c in enumerate(raw_ask.get("citations", []))
            ]
            return {
                "status": "answered",
                "answer": raw_ask.get("tra_loi", ""),
                "citations": citations,
                "retrieval": {
                    "num_candidates": len(citations),
                    "num_contexts": len(citations),
                    "books_covered": ["NPL", "DAU", "BD"],
                },
                "message": "Dữ liệu mẫu fixture (KMS_UI_FIXTURE=1)",
            }
    try:
        resp = requests.post(f"{API_BASE}{path}", json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        st.error(f"Không gọi được API tại {API_BASE}{path}: {exc}")
        return None


def tier_badge(tier: int, badge: str | None) -> str:
    tier_class = f"tier-t{tier}"
    label = badge or f"Tier {tier}"
    return f'<span class="tier-badge {tier_class}">Tier {tier} · {label}</span>'


def book_chip(book_code: str) -> str:
    return f"**{book_code}** — {BOOK_TITLES.get(book_code, book_code)}"


def page_label(c: dict) -> str:
    """Dựng nhãn trang theo quy ước: 'Phần N, PDF tr. X' cho BD, 'PDF tr. X' cho NPL/DAU."""
    page = c.get("pdf_page_start")
    if page is None:
        return "trang không xác định"
    part = c.get("part_number")
    if c.get("book_code") == "BD" and part:
        return f"Phần {part}, PDF tr. {page}"
    return f"PDF tr. {page}"


# --------------------------------------------------------------------------
# sidebar
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### KMS Tử Vi")
    st.caption("Tra cứu tri thức Tử Vi từ 3 sách nguồn, có dẫn nguồn.")
    st.caption(f"API: `{API_BASE}`")

    health = api_get("/api/v1/health")
    if health and health.get("status") == "ok":
        st.success(
            f"DB: {health['knowledge_items']:,} bản ghi · {health['chunks']:,} chunk"
        )
    else:
        st.error(
            f"Không kết nối được backend. Hãy chạy:\n\n"
            f"`uvicorn backend.app.main:app --port 8000`"
        )


# --------------------------------------------------------------------------
# tiêu đề + tab
# --------------------------------------------------------------------------
st.title("KMS Tử Vi")
tab_search, tab_chat, tab_stats = st.tabs(["Tra cứu", "Hỏi đáp RAG", "Thống kê"])


# --------------------------------------------------------------------------
# TAB 1 — Tra cứu
# --------------------------------------------------------------------------
with tab_search:
    st.markdown(
        "Tìm kiếm từ khóa trong nội dung ba sách. Tìm kiếm **không phân biệt dấu**, "
        'nên "tu vi" khớp "Tử Vi".'
    )

    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        default_query = "Tử Vi" if is_fixture_mode() else ""
        query = st.text_input(
            "Từ khóa",
            value=default_query,
            placeholder="VD: sao Thiên Phủ, khoa bảng, địa chi",
            label_visibility="collapsed",
        )
    with c2:
        top_k = st.number_input("Số kết quả", min_value=1, max_value=30, value=10, step=1)
    with c3:
        st.write("")
        st.write("")
        do_search = st.button("Tìm kiếm", type="primary", use_container_width=True)

    search_data = None
    if do_search or (is_fixture_mode() and "sample_search_loaded" not in st.session_state):
        if is_fixture_mode():
            st.session_state["sample_search_loaded"] = True
        if not query.strip():
            st.warning("Nhập từ khóa cần tìm.")
        else:
            with st.spinner("Đang tìm..."):
                search_data = api_post(
                    "/api/v1/search",
                    {
                        "query": query,
                        "top_k": int(top_k),
                        "use_dense": False,
                        "use_fts": True,
                    },
                )
            if search_data:
                st.session_state["current_search_data"] = search_data

    active_search = search_data or st.session_state.get("current_search_data")
    if active_search:
        if active_search.get("status") != "ok" or not active_search.get("results"):
            st.info("Không tìm thấy kết quả nào.")
        else:
            meta = active_search.get("meta", {})
            st.caption(
                f"{meta.get('count', 0)} kết quả · sách: "
                f"{', '.join(meta.get('books', []))} · "
                f"tier được bật: {meta.get('enabled_tiers', [])}"
            )

            # gom kết quả theo sách để "tách NPL / DAU / BD"
            by_book: dict[str, list[dict]] = {}
            for r in active_search["results"]:
                by_book.setdefault(r["book_code"], []).append(r)

            for book_code in ["NPL", "DAU", "BD"]:
                if book_code not in by_book:
                    continue
                with st.expander(
                    f"{BOOK_TITLES.get(book_code, book_code)} ({book_code})"
                    f" — {len(by_book[book_code])} kết quả",
                    expanded=True,
                ):
                    for r in by_book[book_code]:
                        st.markdown(
                            f"**[{r.get('index', '?')}] {r.get('chapter') or '—'}**"
                        )
                        st.markdown(
                            f"{tier_badge(r['trust_tier'], r.get('ui_badge'))}"
                            f" &nbsp;|&nbsp; `{r.get('page_label', '')}`"
                            f" &nbsp;|&nbsp; mức tin cậy tier {r['trust_tier']}",
                            unsafe_allow_html=True,
                        )
                        st.write(r.get("text", ""))
                        st.caption(
                            f"chunk `{r.get('chunk_id')}` · "
                            f"bản ghi: {', '.join(r.get('knowledge_ids', []))}"
                        )
                        st.divider()


# --------------------------------------------------------------------------
# TAB 2 — Hỏi đáp RAG
# --------------------------------------------------------------------------
with tab_chat:
    st.markdown(
        "Hỏi đáp dựa trên nội dung đã truy xuất từ ba sách. Câu trả lời **tách theo từng sách** "
        "và có dẫn nguồn `[1]`, `[2]`."
    )

    with st.expander("Gợi ý câu hỏi", expanded=False):
        st.markdown(
            "- Sao Thiên Phủ được giải nghĩa thế nào?\n"
            "- Cách khoa bảng được nói đến ở đâu?\n"
            "- So sánh cách giải thích của các sách về sao Tử Vi"
        )

    c1, c2 = st.columns([4, 1])
    with c1:
        question = st.text_area(
            "Câu hỏi",
            placeholder="VD: Sao Thiên Phủ được giải nghĩa thế nào?",
            height=90,
            label_visibility="collapsed",
        )
    with c2:
        st.write("")
        rag_top_k = st.number_input("Số nguồn", min_value=1, max_value=12, value=5, step=1)
        st.write("")
        do_ask = st.button("Hỏi", type="primary", use_container_width=True)

    if do_ask:
        if not question.strip():
            st.warning("Nhập câu hỏi.")
        else:
            with st.spinner("Đang truy xuất và tổng hợp..."):
                data = api_post(
                    "/api/v1/chat/ask",
                    {"question": question, "top_k": int(rag_top_k)},
                )

            if data:
                status = data.get("status", "error")
                answer = data.get("answer", "")

                if status == "answered":
                    st.markdown(answer)
                elif status == "out_of_scope":
                    st.warning(answer)
                elif status == "insufficient_evidence":
                    st.info(answer)
                else:
                    st.error(answer or "Không tạo được câu trả lời.")

                if data.get("message"):
                    st.caption(f"Thông báo hệ thống: {data['message']}")

                retr = data.get("retrieval", {})
                if retr:
                    st.caption(
                        f"Ứng viên: {retr.get('num_candidates', 0)} · "
                        f"ngữ cảnh dùng: {retr.get('num_contexts', 0)} · "
                        f"sách phủ: {', '.join(retr.get('books_covered', [])) or '—'}"
                    )

                # thẻ nguồn
                citations = data.get("citations", [])
                if citations:
                    st.subheader("Nguồn trích dẫn")
                    for c in citations:
                        with st.container(border=True):
                            st.markdown(
                                f"**[{c['ref']}] {c.get('book_title') or c['book_code']}** "
                                f"({c['book_code']})"
                            )
                            st.markdown(page_label(c))
                            st.markdown(
                                f"{tier_badge(c['trust_tier'], c.get('ui_badge'))}",
                                unsafe_allow_html=True,
                            )
                            st.caption(
                                f"bản ghi: {', '.join(c.get('knowledge_ids', []))} · "
                                f"xác minh: {c.get('verification_status', 'unverified')}"
                            )
                            st.write(c.get("excerpt", ""))


# --------------------------------------------------------------------------
# TAB 3 — Thống kê
# --------------------------------------------------------------------------
with tab_stats:
    st.markdown("Tổng số bản ghi và phân bố Trust Tier.")

    data = api_get("/api/v1/stats")
    if not data or data.get("status") != "ok":
        st.error("Không lấy được dữ liệu thống kê.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng bản ghi", f"{data.get('total_records', 0):,}")
        c2.metric("Chunk đã index", f"{data.get('chunks', 0):,}")
        c3.metric("Dòng chỉ mục FTS5", f"{data.get('fts_rows', 0):,}")

        st.subheader("Phân bố Trust Tier")
        tiers = data.get("by_tier", [])
        if tiers:
            rows = []
            for t in tiers:
                rows.append(
                    {
                        "Trust Tier": t["trust_tier"],
                        "Số bản ghi": t["count"],
                        "Nhãn": t["label"],
                        "Badge UI": t["ui_badge"],
                        "Được index": "Có" if t["enabled"] else "Không",
                    }
                )
            st.dataframe(rows, use_container_width=True, hide_index=True)

            # thanh phân bố Altair đồng bộ theme palette
            try:
                df = pd.DataFrame(rows)
                df["Tier_Label"] = df["Trust Tier"].apply(lambda t: f"Tier {t}")
                chart = (
                    alt.Chart(df)
                    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                    .encode(
                        x=alt.X(
                            "Tier_Label:N",
                            sort=None,
                            title="Mức tin cậy (Trust Tier)",
                            axis=alt.Axis(
                                labelAngle=0,
                                labelFont="IBM Plex Sans",
                                titleFont="IBM Plex Sans",
                                labelColor="#5d5f60",
                                titleColor="#131416",
                                domainColor="#e8eaec",
                                tickColor="#e8eaec",
                            ),
                        ),
                        y=alt.Y(
                            "Số bản ghi:Q",
                            title="Số bản ghi",
                            axis=alt.Axis(
                                labelFont="IBM Plex Sans",
                                titleFont="IBM Plex Sans",
                                labelColor="#5d5f60",
                                titleColor="#131416",
                                gridColor="#f0f1f2",
                                domainColor="#e8eaec",
                            ),
                        ),
                        color=alt.Color(
                            "Tier_Label:N",
                            scale=alt.Scale(
                                domain=["Tier 1", "Tier 2", "Tier 3", "Tier 9"],
                                range=["#1b6c80", "#2f70bb", "#a86f0c", "#5d5f60"],
                            ),
                            legend=None,
                        ),
                        tooltip=[
                            alt.Tooltip("Tier_Label:N", title="Phân tầng"),
                            alt.Tooltip("Nhãn:N", title="Mô tả"),
                            alt.Tooltip("Số bản ghi:Q", title="Số lượng", format=","),
                            alt.Tooltip("Được index:N", title="Index vào search"),
                        ],
                    )
                    .properties(height=260)
                    .configure_view(strokeWidth=0)
                )
                st.altair_chart(chart, use_container_width=True)
            except Exception:
                pass

            st.caption(
                "Tier 9 = loại khỏi index cho đến khi review. "
                "Mọi bản ghi đều ở trạng thái `unverified` — chưa có dấu vết duyệt thủ công."
            )

        st.subheader("Phân bố theo sách")
        books = data.get("by_book", [])
        if books:
            st.dataframe(
                [{"Mã sách": b["book_code"], "Tên sách": BOOK_TITLES.get(b["book_code"], ""), "Số bản ghi": b["count"]} for b in books],
                use_container_width=True,
                hide_index=True,
            )
