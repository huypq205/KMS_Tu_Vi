"""Lập lá số Tử Vi — Streamlit UI (dùng thư viện lasotuvi, MIT, doanguyen).

User nhập ngày/giờ sinh + giới tính -> an sao (vị trí 108 tinh, tứ hóa,
tuần/triệt, đại hạn, tiểu hạn) và hiển thị lưới 12 cung.

Phạm vi: chỉ LẬP lá số và HIỂN THỊ dữ liệu sao. Không luận giải,
không đưa kết luận về vận mệnh cá nhân.

Chạy:
    streamlit run frontend/lasoban.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "frontend"))

from lasotuvi.AmDuong import (  # noqa: E402
    canChiNgay,
    diaChi,
    ngayThangNamCanChi,
    nguHanh,
    nguHanhNapAm,
    thienCan,
)
from lasotuvi.App import lapDiaBan  # noqa: E402
from lasotuvi.DiaBan import diaBan as diaBanClass  # noqa: E402

from phan_tich import phan_tich, phan_tich_html  # noqa: E402

TIME_ZONE = 7

# giờ chi: (ten, khung giờ, số chi)
GIO_CHI = [
    ("Tý (23:00 – 01:00)", 1),
    ("Sửu (01:00 – 03:00)", 2),
    ("Dần (03:00 – 05:00)", 3),
    ("Mão (05:00 – 07:00)", 4),
    ("Thìn (07:00 – 09:00)", 5),
    ("Tỵ (09:00 – 11:00)", 6),
    ("Ngọ (11:00 – 13:00)", 7),
    ("Mùi (13:00 – 15:00)", 8),
    ("Thân (15:00 – 17:00)", 9),
    ("Dậu (17:00 – 19:00)", 10),
    ("Tuất (19:00 – 21:00)", 11),
    ("Hợi (21:00 – 23:00)", 12),
]

from frontend.laso_renderer import luoi_html, sao_html  # noqa: E402
from frontend.ui_themes import apply_theme  # noqa: E402


def can_gio(canNgay: int, chi: int) -> int:
    """Can của giờ từ can ngày + chi giờ (cộng thêm 12 -> can 1..10)."""
    can = ((canNgay - 1) % 5) * 2 + chi
    return can - 10 if can > 10 else can


@st.cache_data
def lap_laso(nn: int, tt: int, nnnn: int, chi_gio: int,
             gioi_tinh: int, duong_lich: bool) -> dict:
    db = lapDiaBan(diaBanClass, nn, tt, nnnn, chi_gio,
                   gioi_tinh, duong_lich, TIME_ZONE)
    can_thang, can_nam, chi_nam = ngayThangNamCanChi(
        nn, tt, nnnn, duong_lich, TIME_ZONE)
    can_ngay, chi_ngay = canChiNgay(nn, tt, nnnn, duong_lich, TIME_ZONE)

    # số cục (cùng cách tính trong App.py: timCuc)
    can_thang_gieng = (can_nam * 2 + 1) % 10
    can_thang_menh = (((db.cungMenh - 3) % 12) + can_thang_gieng) % 10
    cuc_char = nguHanhNapAm(db.cungMenh, can_thang_menh or 10)
    cuc = nguHanh(cuc_char)

    thap_ni_cung = []
    for c in db.thapNhiCung[1:]:
        thap_ni_cung.append({
            "cung_so": c.cungSo,
            "chuan_ten": c.cungTen,
            "hanh_cung": c.hanhCung,
            "ten_cung": getattr(c, "cungChu", ""),
            "co_thanh": c.cungThan,
            "tu_dai_han": getattr(c, "cungDaiHan", None),
            "tieu_han_chi": getattr(c, "cungTieuHan", None),
            "tuan_trung": getattr(c, "tuanTrung", False),
            "triet_lo": getattr(c, "trietLo", False),
            "saos": c.cungSao,
        })

    return {
        "db": db,
        "cung_menh": db.cungMenh,
        "cung_than": db.cungThan,
        "tu_cu": cuc["cuc"],
        "ten_cu": cuc["tenCuc"],
        "ban_menh": nguHanhNapAm(can_nam, chi_nam, True),
        "can_nam": thienCan[can_nam]["tenCan"],
        "chi_nam": diaChi[chi_nam]["tenChi"],
        "tu_tuc_4_can": [
            f"{thienCan[can_ngay]['tenCan']}{diaChi[chi_ngay]['tenChi']}",
            f"{thienCan[can_thang]['tenCan']}{diaChi[chi_nam]['tenChi']}",
            f"{thienCan[can_nam]['tenCan']}{diaChi[chi_nam]['tenChi']}",
            f"{thienCan[can_gio(can_ngay, chi_gio)]['tenCan']}"
            f"{diaChi[chi_gio]['tenChi']}",
        ],
        "gioi_tinh": "Nam" if gioi_tinh == 1 else "Nữ",
        "thap_ni_cung": thap_ni_cung,
    }


# ---------------------------------------------------------------------------
st.set_page_config(page_title="Lập lá số Tử Vi", layout="wide")
apply_theme()

st.title("Lập lá số Tử Vi")
st.caption(
    "Ứng dụng **chỉ an sao và hiển thị dữ liệu lá số** theo thuật toán của "
    "thư viện [lasotuvi](https://github.com/doanguyen/lasotuvi) (MIT). "
    "Không luận giải, không dự đoán hay tư vấn cá nhân."
)

with st.form("form_laso"):
    st.subheader("Thông tin sinh")
    c1, c2 = st.columns(2)
    with c1:
        ten = st.text_input("Họ tên (tuỳ chọn)", "")
        lich = st.radio("Lịch", ["Dương lịch", "Âm lịch"],
                         horizontal=True, key="lich")
        dd = st.number_input("Ngày", min_value=1, max_value=30, value=15)
        mm = st.number_input("Tháng", min_value=1, max_value=12, value=3)
        yyyy = st.number_input("Năm", min_value=1900, max_value=2099, value=1990)
    with c2:
        gioi = st.radio("Giới tính", ["Nam", "Nữ"], horizontal=True)
        gio = st.selectbox("Giờ sinh", GIO_CHI,
                           format_func=lambda x: x[0])
        st.write("Giờ ranh giới (ví dụ 10:58 → Tỵ, 11:02 → Ngọ): dùng giờ "
                 "chuẩn, quy hết xuống khung giờ liền trước.")
    submitted = st.form_submit_button("Lập lá số")

if submitted:
    duong = (lich == "Dương lịch")
    gt = 1 if gioi == "Nam" else -1
    try:
        info = lap_laso(int(dd), int(mm), int(yyyy), gio[1], gt, duong)
    except Exception as exc:
        st.error(f"Lỗi lập lá số: {exc}")
        st.stop()

    # --- thông tin tổng quan ---
    st.subheader(f"Lá số của {ten or 'chủ thể'} — {info['gioi_tinh']}")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Bản mệnh", info["ban_menh"])
    c2.metric("Cục", info["ten_cu"])
    c3.metric("Cung Mệnh", diaChi[info["cung_menh"]]["tenChi"])
    c4.metric("Cung Thân", diaChi[info["cung_than"]]["tenChi"])
    c5.metric("Nam sinh (can–chi)", f"{info['can_nam']} {info['chi_nam']}")

    tc, tth, tn, tg = info["tu_tuc_4_can"]
    st.caption(f"Tứ trụ: **Ngày** {tc} · **Tháng** {tth} · **Năm** {tn} · "
               f"**Giờ** {tg}")
    st.caption("Chú thích sắc thái sao: "
               "M=Miếu, V=Vượng, Đ=Đắc, B=Bình, H=Hãm "
               "(theo bảng đặc tính trong lasotuvi). "
               "Sao tốt màu xanh, sao hung màu đỏ.")

    # --- lưới 12 cung ---
    st.markdown('<div class="horoscope-chart">' + luoi_html(info["thap_ni_cung"]) + '</div>', unsafe_allow_html=True)

    # --- phân tích (rule-based, offline) ---
    st.subheader("Phân tích cấu trúc lá số")
    st.caption(
        "Suy ra theo nguyên tắc Tử Vi truyền thống (chủ mệnh, tứ hóa, "
        "tuần/triệt, đại hạn, các cung chính) — đọc thẳng từ dữ liệu lá số "
        "ở trên; mang tính tham khảo, không phải luận giải cá nhân."
    )
    st.markdown(phan_tich_html(phan_tich(info)), unsafe_allow_html=True)

    # --- xuất dữ liệu ---
    payload = {
        "input": {
            "ten": ten, "gioi_tinh": info["gioi_tinh"],
            "lich": lich, "ngay": int(dd), "thang": int(mm),
            "nam": int(yyyy),
            "gio_chi": diaChi[gio[1]]["tenChi"],
        },
        "tong_quan": {
            "ban_menh": info["ban_menh"], "cuc": info["ten_cu"],
            "cung_menh_chi": diaChi[info["cung_menh"]]["tenChi"],
            "cung_than_chi": diaChi[info["cung_than"]]["tenChi"],
            "tu_tru": dict(zip(["ngay", "thang", "nam", "gio"],
                               info["tu_tuc_4_can"])),
        },
        "cung": info["thap_ni_cung"],
        "nguon_thu_tin": "https://github.com/doanguyen/lasotuvi (MIT)",
    }
    st.download_button(
        "Tải lá số (JSON)",
        json.dumps(payload, ensure_ascii=False, indent=2),
        file_name="la_so_tuvi.json",
        mime="application/json",
    )
