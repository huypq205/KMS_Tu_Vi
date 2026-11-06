"""T6: source-separated star dossier, explicit unknown and unverified states."""
from __future__ import annotations

import os
from pathlib import Path
import sys
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from backend.app.services.star_dossier import SEED_STARS
from frontend.research_ui import setup
from frontend import research_transport
from frontend.ui_fixture import is_fixture_mode, mock_dossier

BOOK_NAMES = {
    "NPL": "Nguyễn Phát Lộc",
    "BD": "Bửu Đình",
    "DAU": "Đẩu Số Toàn Thư",
}


def book_badge_html(book_code: str, show_full_name: bool = False) -> str:
    code = (book_code or "").strip().upper()
    css_code = code.lower()
    label = f"{code} · {BOOK_NAMES.get(code, code)}" if show_full_name else code
    return f'<span class="book-badge book-{css_code} badge-book-{css_code}">{label}</span>'


setup("Hồ sơ sao")
st.write("Đối chiếu ý nghĩa và điều kiện của một sao, giữ riêng tiếng nói từng sách.")

requested = st.query_params.get("star")
default_index = SEED_STARS.index(requested) if requested in SEED_STARS else 0
star = st.selectbox(
    "Sao cần tra cứu",
    SEED_STARS,
    index=default_index,
    key="dossier_star",
)
seeds = st.checkbox("Bổ sung tham khảo chưa đối chiếu sách KMS", value=False, key="dossier_seeds")
load = st.button("Tra cứu hồ sơ", type="primary", key="load_dossier")

# Offline fixture fallback
if is_fixture_mode() and "dossier_result" not in st.session_state:
    st.session_state["dossier_result"] = mock_dossier(star or requested or "Tử Vi")

if load or (requested in SEED_STARS and st.session_state.get("dossier_result", {}).get("name") != requested):
    if is_fixture_mode():
        st.session_state["dossier_result"] = mock_dossier(star)
    else:
        try:
            with st.spinner("Đang tìm bản ghi và trang dẫn…"):
                payload = research_transport.api_get(
                    "/api/v1/stars/" + quote(star, safe="") + "/dossier",
                    include_seeds=seeds,
                )
                if not isinstance(payload, dict) or not isinstance(payload.get("slots"), dict) or len(payload["slots"]) != 14:
                    raise ValueError("Invalid dossier response")
                st.session_state["dossier_result"] = payload
        except Exception:
            st.error("Chưa tải được hồ sơ sao. Kiểm tra kết nối dịch vụ và thử tra cứu lại.")

result = st.session_state.get("dossier_result")
if result:
    st.subheader(result["name"])

    # Metadata strip with Book Badges
    badges_html = " ".join(book_badge_html(b) for b in result.get("books", []))
    st.markdown(
        f'<div style="margin-bottom: 8px;">'
        f'<span style="font-size: 13px; color: var(--muted); margin-right: 8px;">Nguồn KMS: '
        f'<strong>{result["canonical_records"]}</strong> bản ghi</span>'
        f"{badges_html}"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        f"Nguồn KMS: {result['canonical_records']} bản ghi trong kết quả · "
        + (", ".join(result["books"]) or "Chưa có bản ghi có trang dẫn")
    )
    st.caption("Các đoạn dưới là lời ghi của từng nguồn truyền thống, chưa phải kết luận cho cá nhân.")

    # =========================================================================
    # SECTION 1: Tiếng nói từng sách và trang dẫn
    # =========================================================================
    st.markdown("### Tiếng nói từng sách và trang dẫn")

    school_slot = result["slots"].get("school_differences", {})
    if school_slot.get("entries") and result.get("books"):
        columns = st.columns(len(result["books"]))
        for col, book in zip(columns, result["books"]):
            with col:
                st.markdown(book_badge_html(book, show_full_name=True), unsafe_allow_html=True)
                entries = [e for e in school_slot["entries"] if e.get("book_code") == book]
                st.caption(f"{len(entries)} bản ghi trong kết quả")
                for entry in entries[:3]:
                    st.write(f"Nguồn {book} ghi:")
                    st.markdown("> " + entry["text"].replace("\n", "\n> "))
                    citations = entry.get("citations", [])
                    cite_str = "; ".join(
                        (f"Phần {c['part_number']}, " if c.get("part_number") else "") + f"PDF tr. {c['pdf_page']}"
                        for c in citations
                    )
                    st.caption(f"{entry['knowledge_id']} · {cite_str}")
                    if entry.get("author_stance") or entry.get("conflict_status"):
                        st.caption(
                            "Lập trường tác giả: "
                            + str(entry.get("author_stance") or "Chưa có metadata")
                            + " · Xung đột: "
                            + str(entry.get("conflict_status") or "Chưa đánh giá")
                        )
                if len(entries) > 3:
                    with st.expander(f"Xem các bản ghi còn lại của {book}"):
                        for entry in entries[3:]:
                            st.write(entry["text"])
                            st.caption(f"{entry['knowledge_id']} · {entry.get('citations')}")

    # Citations list
    citations_slot = result["slots"].get("source_citations", {})
    if citations_slot.get("entries"):
        with st.expander(citations_slot.get("label", "Trích dẫn sách"), expanded=False):
            st.caption(citations_slot.get("message", ""))
            for entry in citations_slot["entries"]:
                badge = book_badge_html(entry.get("book_code", ""))
                c_list = entry.get("citations", [])
                c_str = "; ".join(
                    (f"Phần {c['part_number']}, " if c.get("part_number") else "") + f"PDF tr. {c['pdf_page']}"
                    for c in c_list
                )
                st.markdown(f"{badge} ` {entry['knowledge_id']} ` — {c_str}", unsafe_allow_html=True)

    # =========================================================================
    # SECTION 2: Bản chất, Âm dương và Biểu hiện
    # =========================================================================
    st.markdown("### Bản chất, Âm dương và Biểu hiện")

    # Reference meaning from external skill (MUST keep st.text for test compatibility!)
    reference = result.get("reference_meaning")
    if reference:
        with st.expander("Ý nghĩa sao từ skill tham khảo", expanded=True):
            st.caption(reference.get("source", ""))
            st.caption("Mục trong tài liệu: " + str(reference.get("group_heading", "")))
            st.text(reference.get("text", ""))
            if reference.get("omitted_lines"):
                st.caption("Đã lược các dòng định mệnh, nhạy cảm hoặc không phù hợp.")

    meaning_keys = [
        "core_function",
        "yin_yang_five_element",
        "favorable_expression",
        "unfavorable_expression",
        "strength_by_branch",
        "by_palace",
    ]
    for key in meaning_keys:
        slot = result["slots"].get(key)
        if not slot:
            continue
        is_open = key in {"core_function", "strength_by_branch", "by_palace"}
        with st.expander(slot["label"], expanded=is_open):
            st.caption(slot["message"])
            for entry in slot.get("entries", []):
                if slot.get("status") == "seed_unverified":
                    st.write(entry.get("text", ""))
                    st.caption("Tham khảo, chưa đối chiếu sách KMS · " + str(entry.get("source", "")))
                    if entry.get("reference"):
                        st.link_button("Xem tài liệu tham khảo gián tiếp", entry["reference"])
                else:
                    b_code = entry.get("book_code", "")
                    badge = book_badge_html(b_code)
                    txt = entry.get("text") or entry.get("knowledge_id", "")
                    st.markdown(f"{badge} {txt}", unsafe_allow_html=True)
                    citations = entry.get("citations", [])
                    c_str = "; ".join(
                        (f"Phần {c['part_number']}, " if c.get("part_number") else "") + f"PDF tr. {c['pdf_page']}"
                        for c in citations
                    )
                    st.caption(f"Nguồn {b_code} · {entry.get('knowledge_id', '')} · {c_str}")

    # =========================================================================
    # SECTION 3: Tổ hợp sao, Tứ Hóa và Sát tinh
    # =========================================================================
    st.markdown("### Tổ hợp sao, Tứ Hóa và Sát tinh")
    combo_keys = [
        "supportive_combinations",
        "challenging_combinations",
        "transformation_behavior",
        "with_tuan_triet",
        "with_sat_tinh",
    ]
    for key in combo_keys:
        slot = result["slots"].get(key)
        if not slot:
            continue
        is_open = bool(slot.get("entries"))
        with st.expander(slot["label"], expanded=is_open):
            st.caption(slot["message"])
            for entry in slot.get("entries", []):
                if slot.get("status") == "seed_unverified":
                    st.write(entry.get("text", ""))
                    st.caption("Tham khảo, chưa đối chiếu sách KMS · " + str(entry.get("source", "")))
                    if entry.get("reference"):
                        st.link_button("Xem tài liệu tham khảo gián tiếp", entry["reference"])
                else:
                    b_code = entry.get("book_code", "")
                    badge = book_badge_html(b_code)
                    txt = entry.get("text") or entry.get("knowledge_id", "")
                    st.markdown(f"{badge} {txt}", unsafe_allow_html=True)
                    citations = entry.get("citations", [])
                    c_str = "; ".join(
                        (f"Phần {c['part_number']}, " if c.get("part_number") else "") + f"PDF tr. {c['pdf_page']}"
                        for c in citations
                    )
                    st.caption(f"Nguồn {b_code} · {entry.get('knowledge_id', '')} · {c_str}")

    # =========================================================================
    # SECTION 4: Ca nghiệm lý thực tế
    # =========================================================================
    st.markdown("### Ca nghiệm lý thực tế")
    case_slot = result["slots"].get("case_notes", {})
    with st.expander(case_slot.get("label", "Ca nghiệm lý"), expanded=True):
        st.caption(case_slot.get("message", ""))
        if case_slot.get("entries"):
            for entry in case_slot["entries"]:
                b_code = entry.get("book_code", "")
                badge = book_badge_html(b_code)
                st.markdown(f"{badge} {entry.get('text', '')}", unsafe_allow_html=True)
                st.caption(f"Nguồn {b_code} · {entry.get('knowledge_id', '')}")
        else:
            st.caption("Chưa có ca nghiệm lý đối chiếu trong kho tri thức hiện tại.")
else:
    st.info("Chọn một sao để xem bản ghi, điều kiện và trang nguồn. Mục chưa có dữ liệu sẽ được để rõ.")
