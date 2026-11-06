"""Independent, voluntary anonymous validation journal."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from backend.app.schemas.case_validation import ChartSnapshot
from frontend import research_transport as api
from frontend.research_ui import setup
from frontend.ui_fixture import is_fixture_mode, load_fixture

setup("Nhật ký nghiệm lý")
st.write("Lưu nhận định trước khi đối chiếu, giữ cả lần không khớp và lịch sử sửa đổi.")
st.caption("Chỉ dùng mã ca ẩn danh. Không nhập tên, ngày sinh, địa chỉ hay thông tin nhận diện vào các ghi chú.")


def render_notice(message: str, kind: str = "warning") -> None:
    css_cls = "notice notice-error" if kind == "error" else "notice"
    st.markdown(f'<div class="{css_cls}">{message}</div>', unsafe_allow_html=True)


def render_empty_state(title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="journal-empty-state">
            <div class="journal-empty-title">{title}</div>
            <div class="journal-empty-desc">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def call(method: str, path: str, payload: dict | None = None):
    # Fixture fallback when KMS_UI_FIXTURE=1
    if is_fixture_mode():
        if path == "/api/v1/validation/statistics":
            try:
                fixture_stats = load_fixture("sample_stats")
            except Exception:
                fixture_stats = {}
            return {
                "eligible_cases": 32,
                "minimum_cases": 30,
                "counts": {
                    "clear_match": 14,
                    "partial_match": 10,
                    "no_match": 6,
                    "not_verifiable": 2,
                },
                "message": "Số lượt đối chiếu theo kết quả (Chế độ mẫu KMS_UI_FIXTURE=1).",
                "corpus_records": fixture_stats.get("total_records", 10456),
            }
        elif path.startswith("/api/v1/validation/cases/") and method == "get":
            cid = path.split("/")[-1]
            return {
                "case_id": cid or "TV-2026-001",
                "input_confidence": "A",
                "created_at": "2026-01-15T08:00:00Z",
                "chart_snapshot": {
                    "palaces": [
                        {"cung_so": i, "ten_cung": f"Cung {i}", "stars": ["Tử Vi", "Thiên Phủ"] if i == 1 else []}
                        for i in range(1, 13)
                    ],
                    "facts": [{"fact_id": "F1", "text": "Tử Vi Thiên Phủ đồng cung tại Dần"}],
                    "tu_hoa_table": "lasotuvi",
                },
                "predictions": [
                    {
                        "prediction_id": "p-001",
                        "noi_dung": "Năm 2027 có thay đổi vị trí công việc theo hướng mở rộng quy mô chuyên môn.",
                        "khoa_thoi_gian": "2027",
                        "muc_tin_cay": "manh",
                        "loai_ket_luan": "thoi_diem",
                        "chung_cu_ids": ["F1"],
                        "phan_chung": "Chưa đối chiếu đại vận phụ trợ.",
                        "supersedes": None,
                        "revision_reason": None,
                        "locked_at": "2026-01-16T09:00:00Z",
                    }
                ],
                "events": [
                    {
                        "event_id": "e-001",
                        "prediction_id": "p-001",
                        "year": 2027,
                        "category": "career",
                        "mo_ta": "Được bổ nhiệm vị trí quản lý dự án mới.",
                        "prediction_result": "clear_match",
                        "revealed_at": "2027-12-10T15:00:00Z",
                    }
                ],
            }

    try:
        return api.api_get(path) if method == "get" else api.api_post(path, payload or {})
    except Exception as exc:
        render_notice(f"Không thực hiện được thao tác: {exc}", kind="error")
        return None


def report_snapshot(report: dict) -> dict:
    palaces = []
    for p in report.get("palaces", []):
        stars = [s["ten"] for k in ("chinh_tinh", "sat_tinh", "cat_tinh", "phu_tinh_khac") for s in p.get(k, [])]
        palaces.append({"cung_so": p["cung_so"], "ten_cung": p.get("ten"), "stars": stars})
    facts = [
        {"fact_id": str(f["fact_id"]), "text": " · ".join(str(f.get(k, "")) for k in ("sao", "cung", "dia_chi", "trang_thai", "kind"))}
        for f in report.get("star_analysis", [])
    ]
    return ChartSnapshot.model_validate({
        "palaces": palaces,
        "facts": facts,
        "tu_hoa_table": (report.get("thong_tin_co_ban", {}).get("tu_hoa_table") or {}).get("id", "lasotuvi"),
    }).model_dump()


# --------------------------------------------------------------------------
# PANEL 1: QUẢN LÝ HỒ SƠ CA NGHIỆM LÝ
# --------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<div class="journal-panel">', unsafe_allow_html=True)
    st.subheader("Hồ sơ ca")

    col_search, col_btn = st.columns([4, 1])
    with col_search:
        cid = st.text_input("Mã ca", placeholder="TV-2026-001", key="journal_case_id")
    with col_btn:
        st.write("")
        if st.button("Mở ca đã lưu", key="journal_open", use_container_width=True):
            if cid:
                case = call("get", f"/api/v1/validation/cases/{cid}")
                if case:
                    st.session_state["journal_case"] = case
            else:
                render_notice("Vui lòng nhập mã ca trước khi mở.", kind="error")

    active_case = st.session_state.get("journal_case")

    if not active_case:
        st.write("---")
        st.caption("Hoặc khởi tạo ca mới và cố định dữ kiện lá số:")
        report = st.session_state.get("report")
        candidate = None
        if report:
            try:
                candidate = report_snapshot(report)
            except (ValueError, KeyError, TypeError):
                render_notice("Bài đọc hiện tại chưa có snapshot hợp lệ.", kind="warning")

        if candidate:
            st.caption("Có thể dùng dữ kiện sao của bài đọc hiện tại; tên và ngày sinh không được đưa vào nhật ký.")
            st.download_button(
                "Xem bản chụp ẩn danh",
                json.dumps(candidate, ensure_ascii=False, indent=2),
                "chart_snapshot.json",
                "application/json",
            )

        upload = st.file_uploader("Hoặc mở bản chụp ẩn danh đã xuất", type=["json"], key="journal_upload")
        inherited = (report or {}).get("thong_tin_co_ban", {}).get("input_confidence", "A")
        confidence = st.selectbox(
            "Độ tin cậy đầu vào",
            ["A", "B", "C", "D"],
            index=["A", "B", "C", "D"].index(inherited) if inherited in ["A", "B", "C", "D"] else 0,
            disabled=bool(candidate and not upload),
            key="journal_confidence",
        )

        if st.button("Tạo ca và cố định lá số", key="journal_create", type="primary"):
            try:
                snapshot = json.loads(upload.getvalue()) if upload else candidate
                if not snapshot:
                    raise ValueError("Cần tạo bài đọc hoặc mở bản chụp trước.")
                data = call("post", "/api/v1/validation/cases", {
                    "case_id": cid,
                    "chart_snapshot": snapshot,
                    "input_confidence": confidence,
                })
                if data:
                    st.session_state["journal_case"] = {**data, "predictions": [], "events": []}
                    st.success("Đã tạo ca thành công. Bản chụp lá số đã được cố định.")
                    st.rerun()
            except (ValueError, TypeError) as exc:
                render_notice(str(exc), kind="error")
    else:
        st.markdown(
            f"""
            <div style="display: flex; gap: 16px; margin: 12px 0; padding: 10px 14px; background: var(--raised); border: 1px solid var(--border); border-radius: var(--radius-control);">
                <div><span style="font-size: 11px; color: var(--muted); display: block;">Mã ca</span><strong>{active_case['case_id']}</strong></div>
                <div><span style="font-size: 11px; color: var(--muted); display: block;">Độ tin cậy</span><strong>{active_case['input_confidence']}</strong></div>
                <div><span style="font-size: 11px; color: var(--muted); display: block;">Số nhận định</span><strong>{len(active_case.get('predictions', []))}</strong></div>
                <div><span style="font-size: 11px; color: var(--muted); display: block;">Số đối chiếu</span><strong>{len(active_case.get('events', []))}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Xem chi tiết dữ kiện bản chụp đã cố định"):
            st.json(active_case["chart_snapshot"])

    st.markdown("</div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# PANEL 2: NHẬN ĐỊNH & KHÓA DỰ ĐOÁN
# --------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<div class="journal-panel">', unsafe_allow_html=True)
    st.subheader("Nhận định & Khóa dự đoán")

    if not active_case:
        render_empty_state("Chưa mở hồ sơ ca nghiệm lý", "Mở hoặc tạo ca ở phần trên để bắt đầu ghi nhận định dự đoán.")
    else:
        with st.form("journal_prediction"):
            content = st.text_area("Nhận định có điều kiện", max_chars=3000)
            period = st.text_input("Năm hoặc khoảng năm", placeholder="2027 hoặc 2027-2028")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                level = st.selectbox("Mức tin cậy", ["yeu", "trung_binh", "manh", "rat_manh"])
            with col_c2:
                kind = st.selectbox("Loại kết luận", ["cau_truc", "thoi_diem"])

            available_facts = [f["fact_id"] for f in active_case["chart_snapshot"].get("facts", [])]
            evidence = st.multiselect("Chứng cứ trong bản chụp", available_facts)
            counter = st.text_area("Phản chứng và điều kiện còn thiếu", max_chars=2000)

            locked_pids = [p["prediction_id"] for p in active_case.get("predictions", []) if p.get("locked_at")]
            supersedes = st.selectbox("Phiên bản thay thế (nếu có)", [""] + locked_pids)
            reason = st.text_input("Lý do tạo phiên bản mới", max_chars=2000)
            save = st.form_submit_button("Lưu bản nháp nhận định")

        if save:
            payload = {
                "noi_dung": content,
                "khoa_thoi_gian": period,
                "muc_tin_cay": level,
                "loai_ket_luan": kind,
                "chung_cu_ids": evidence,
                "phan_chung": counter,
            }
            path = f"/api/v1/validation/cases/{active_case['case_id']}/predictions"
            if supersedes:
                path = f"/api/v1/validation/predictions/{supersedes}/revisions"
                payload = {"prediction": payload, "reason": reason}
            if call("post", path, payload):
                st.session_state["journal_case"] = call("get", f"/api/v1/validation/cases/{active_case['case_id']}")
                st.rerun()

        predictions = active_case.get("predictions", [])
        if not predictions:
            render_empty_state("Chưa có nhận định nào", "Hãy nhập nhận định đầu tiên vào biểu mẫu phía trên.")
        else:
            st.write("---")
            st.caption("Danh sách nhận định:")
            for p in predictions:
                status_badge = "Đã khóa" if p.get("locked_at") else "Bản nháp"
                with st.expander(f"{status_badge} · {p['prediction_id'][:8]}", expanded=True):
                    st.write(p["noi_dung"])
                    st.caption(f"Thời gian: {p['khoa_thoi_gian']} · Mức tin cậy: {p['muc_tin_cay']} · Chứng cứ: {', '.join(p.get('chung_cu_ids', []))}")
                    if p.get("phan_chung"):
                        st.write(f"Phản chứng: {p['phan_chung']}")
                    if p.get("supersedes"):
                        st.caption(f"Thay thế {p['supersedes']} · Lý do: {p.get('revision_reason', '')}")
                    if p.get("locked_at"):
                        st.caption(f"Khóa lúc: {p['locked_at']}")
                    else:
                        if st.button("Khóa nhận định này", key=f"lock_{p['prediction_id']}"):
                            if call("post", f"/api/v1/validation/predictions/{p['prediction_id']}/lock"):
                                st.session_state["journal_case"] = call("get", f"/api/v1/validation/cases/{active_case['case_id']}")
                                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# PANEL 3: ĐỐI CHIẾU SỰ KIỆN THỰC TẾ
# --------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<div class="journal-panel">', unsafe_allow_html=True)
    st.subheader("Đối chiếu sự kiện")

    if not active_case:
        render_empty_state("Chưa mở hồ sơ ca nghiệm lý", "Mở ca đã có nhận định được khóa để đối chiếu với biến cố thực tế.")
    else:
        graded = {e["prediction_id"] for e in active_case.get("events", [])}
        eligible = [p["prediction_id"] for p in active_case.get("predictions", []) if p.get("locked_at") and p["prediction_id"] not in graded]

        if eligible:
            with st.form("journal_event"):
                pid = st.selectbox("Dự đoán đã khóa", eligible)
                year = st.number_input("Năm sự kiện", 1900, 2100, 2026)
                category = st.selectbox("Nhóm sự kiện", ["career", "finance", "marriage", "children", "family", "health", "relocation", "other"])
                desc = st.text_area("Diễn biến thực tế (ẩn danh)", max_chars=3000)
                result = st.selectbox("Kết quả đối chiếu", ["clear_match", "partial_match", "no_match", "not_verifiable"])
                reveal = st.form_submit_button("Lưu đối chiếu và giữ nguyên kết quả")

            if reveal:
                ev_data = {
                    "prediction_id": pid,
                    "year": year,
                    "category": category,
                    "mo_ta": desc,
                    "prediction_result": result,
                }
                if call("post", f"/api/v1/validation/cases/{active_case['case_id']}/events", ev_data):
                    st.session_state["journal_case"] = call("get", f"/api/v1/validation/cases/{active_case['case_id']}")
                    st.rerun()
        else:
            render_empty_state("Chưa có dự đoán đủ điều kiện đối chiếu", "Cần ít nhất một nhận định đã được khóa và chưa có đối chiếu sự kiện.")

        events = active_case.get("events", [])
        if events:
            st.write("---")
            st.caption("Lịch sử biến cố thực tế đã đối chiếu:")
            for e in events:
                res_cls = "badge-positive" if e["prediction_result"] == "clear_match" else "badge-warning" if e["prediction_result"] == "partial_match" else "badge-negative"
                st.markdown(
                    f"""
                    <div style="padding: 10px 14px; background: var(--raised); border: 1px solid var(--border); border-radius: var(--radius-control); margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <strong>Năm {e['year']} · Nhóm: {e['category']}</strong>
                            <span class="badge {res_cls}">{e['prediction_result']}</span>
                        </div>
                        <div style="font-size: var(--font-size-body); color: var(--text);">{e['mo_ta']}</div>
                        <div style="font-size: var(--font-size-small); color: var(--muted); margin-top: 4px;">Ghi nhận lúc: {e.get('revealed_at', '')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("</div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# PANEL 4: THỐNG KÊ & KIỂM CHỨNG MẪU
# --------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<div class="journal-panel">', unsafe_allow_html=True)
    st.subheader("Thống kê mẫu")
    st.write("Chỉ hiển thị tổng hợp khi đủ 30 ca khác nhau đã có đối chiếu. Nhiều nhận định của một ca vẫn chỉ tính một ca.")

    if st.button("Xem tình trạng mẫu", key="journal_stats"):
        stats = call("get", "/api/v1/validation/statistics")
        if stats:
            st.write(stats.get("message", ""))
            st.caption(f"{stats.get('eligible_cases', 0)} ca đã đối chiếu")
            if stats.get("counts") is not None:
                st.table([{"Kết quả": k, "Số lượt": v} for k, v in stats["counts"].items()])

    st.markdown("</div>", unsafe_allow_html=True)
