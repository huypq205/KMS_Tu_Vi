# -*- coding: utf-8 -*-
"""Module trích xuất đặc trưng lá số Tử Vi (Horoscope Feature Extractor).

Nhiệm vụ:
1. An sao độc lập (không phụ thuộc Streamlit) từ thư viện vendor/lasotuvi.
2. Bóc tách tương quan Ngũ hành Bản mệnh vs Cục.
3. Xác định Tam phương Tứ chính (Mệnh - Tài - Quan - Di).
4. Nhận diện các bộ cách cục chính tinh nòng cốt (Tử Phủ Vũ Tướng, Sát Phá Tham, Cơ Nguyệt Đồng Lương, Cự Nhật, Vô Chính Diệu).
5. Phân loại chính tinh đắc/hãm, cát tinh, sát tinh.
6. Xác định vị trí và ý nghĩa của Tứ Hóa (Lộc, Quyền, Khoa, Kỵ).
7. Xác định Đại hạn 10 năm hiện tại theo tuổi và năm xem.
"""
from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path
from typing import Any
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.app.services.horoscope_confidence import (
    DEFAULT_GIO_SINH_SOURCE,
    DEFAULT_INPUT_CONFIDENCE,
    normalize_level,
)

ROOT = Path(__file__).resolve().parents[3]
VENDOR_PATH = ROOT / "vendor"
if str(VENDOR_PATH) not in sys.path:
    sys.path.insert(0, str(VENDOR_PATH))

from lasotuvi.AmDuong import (  # noqa: E402
    canChiNgay,
    diaChi,
    ngayThangNamCanChi,
    ngayThangNam,
    nguHanh,
    nguHanhNapAm,
    thienCan,
)
from lasotuvi.App import lapDiaBan  # noqa: E402
from lasotuvi.DiaBan import diaBan as diaBanClass  # noqa: E402
from lasotuvi import Sao as catalog  # noqa: E402

from backend.app.services.horoscope_annual import compute_luu_nien  # noqa: E402
from backend.app.services.tu_hoa_tables import (  # noqa: E402
    apply_natal_table, get_tu_hoa_table, table_metadata,
)

TIME_ZONE = 7

# --- BẢNG TRA NGŨ HÀNH & TƯƠNG SINH TƯƠNG KHẮC ---
NGU_HANH_LIST = ["Kim", "Mộc", "Thủy", "Hỏa", "Thổ"]

NGU_HANH_SINH = {
    "Kim": "Thủy",
    "Thủy": "Mộc",
    "Mộc": "Hỏa",
    "Hỏa": "Thổ",
    "Thổ": "Kim",
}

NGU_HANH_KHAC = {
    "Kim": "Mộc",
    "Mộc": "Thổ",
    "Thổ": "Thủy",
    "Thủy": "Hỏa",
    "Hỏa": "Kim",
}

# --- TỪ ĐIỂN TỨ HÓA ---
TU_HOA_DEF = {
    94: {
        "code": "HOA_LOC",
        "ten": "Hóa lộc",
        "nghia_ngan": "Tài lộc, cơ hội may mắn, sự gia tăng phát triển",
        "layman": "Nơi bạn dễ đón nhận cơ hội, nguồn lực tài chính và sự hỗ trợ tự nhiên từ cuộc sống.",
    },
    93: {
        "code": "HOA_QUYEN",
        "ten": "Hóa quyền",
        "nghia_ngan": "Quyền lực, quyền kiểm soát, tính chủ động quyết đoán",
        "layman": "Lĩnh vực bạn luôn muốn nắm quyền tự chủ, quyết đoán và có sức ảnh hưởng mạnh mẽ nhất.",
    },
    92: {
        "code": "HOA_KHOA",
        "ten": "Hóa khoa",
        "nghia_ngan": "Danh tiếng, tri thức, quý nhân giải trừ tai ách",
        "layman": "Điểm sáng về trí tuệ, danh dự, học thức và khả năng chuyển nguy thành an khi gặp khó.",
    },
    95: {
        "code": "HOA_KY",
        "ten": "Hóa kỵ",
        "nghia_ngan": "Trở ngại, điểm nghẽn, vướng mắc, bài học cuộc đời",
        "layman": "Nơi bạn phải trăn trở nhiều nhất, bài học lớn giúp bạn rèn luyện sự cẩn trọng và trưởng thành.",
    },
}

# --- TỪ ĐIỂN SÁT TINH & CÁT TINH ---
LUC_SAT_TINH_IDS = {s.saoID: s.saoTen for s in (
    catalog.saoKinhDuong, catalog.saoDaLa, catalog.saoHoaTinh,
    catalog.saoLinhTinh, catalog.saoDiaKhong, catalog.saoDiaKiep,
)}
CAT_TINH_IDS = {s.saoID: s.saoTen for s in (
    catalog.saoVanXuong, catalog.saoVanKhuc, catalog.saoThienKhoi,
    catalog.saoThienViet, catalog.saoTaPhu, catalog.saoHuuBat,
    catalog.saoThienMa, catalog.saoLocTon, catalog.saoHoaKhoa,
    catalog.saoHoaQuyen, catalog.saoHoaLoc, catalog.saoAnQuang, catalog.saoThienQuy,
)}

# --- TỪ ĐIỂN TÊN CUNG ---
CUNG_DOMAIN = {
    "Mệnh": "Bản thân, cá tính bẩm sinh, tổng quan vận mệnh",
    "Phụ mẫu": "Cha mẹ, cấp trên, quan hệ với người đi trước",
    "Phúc đức": "Đời sống nội tâm, tinh thần, cội nguồn phúc trạch",
    "Điền trạch": "Nhà cửa, nơi cư trú, tích lũy bất động sản",
    "Quan lộc": "Sự nghiệp, con đường công danh, phong cách làm việc",
    "Nô bộc": "Bạn bè, đồng nghiệp, cộng sự, mạng lưới quan hệ",
    "Thiên di": "Môi trường xã hội, các chuyến đi xa, tương tác bên ngoài",
    "Tật ách": "Sức khỏe thể chất, thói quen sinh hoạt, ứng biến rủi ro",
    "Tài bạch": "Tiền tài, tư duy tài chính, khả năng quản lý dòng tiền",
    "Tử tức": "Con cái, học trò, đời sống sáng tạo cá nhân",
    "Phu thê": "Hôn nhân, mối quan hệ tình cảm, người bạn đời",
    "Huynh đệ": "Anh chị em ruột, người thân cận gắn bó",
}


def can_gio(can_ngay: int, chi: int) -> int:
    """Xác định thiên can của giờ từ can ngày và chi giờ."""
    can = ((can_ngay - 1) % 5) * 2 + chi
    return can - 10 if can > 10 else can


def generate_raw_horoscope(
    nn: int, tt: int, nnnn: int, chi_gio: int, gioi_tinh: int, duong_lich: bool = True,
    *, tu_hoa_table_id: str | None = None,
) -> dict[str, Any]:
    """An sao lá số Tử Vi hoàn chỉnh từ thư viện vendor/lasotuvi (thuần Python).
    
    Quy ước giới tính:
    - Input gioi_tinh: 1 (Nam), 2 hoặc -1 (Nữ)
    - Vendor lasotuvi: 1 (Nam), -1 (Nữ)
    """
    # Chuẩn hóa cho vendor/lasotuvi engine
    gt_engine = 1 if gioi_tinh == 1 else -1

    db = lapDiaBan(
        diaBanClass, nn, tt, nnnn, chi_gio, gt_engine, duong_lich, TIME_ZONE
    )
    can_thang, can_nam, chi_nam = ngayThangNamCanChi(
        nn, tt, nnnn, duong_lich, TIME_ZONE
    )
    can_ngay, chi_ngay = canChiNgay(nn, tt, nnnn, duong_lich, TIME_ZONE)
    _, _, lunar_year, _ = ngayThangNam(nn, tt, nnnn, duong_lich, TIME_ZONE)

    # Tính số cục
    can_thang_gieng = (can_nam * 2 + 1) % 10
    can_thang_menh = (((db.cungMenh - 3) % 12) + can_thang_gieng) % 10
    cuc_char = nguHanhNapAm(db.cungMenh, can_thang_menh or 10)
    cuc = nguHanh(cuc_char)

    thap_ni_cung = []
    for c in db.thapNhiCung[1:]:
        thap_ni_cung.append(
            {
                "cung_so": c.cungSo,
                "chuan_ten": c.cungTen,
                "hanh_cung": c.hanhCung,
                "ten_cung": getattr(c, "cungChu", ""),
                "co_thanh": c.cungThan,
                "tu_dai_han": getattr(c, "cungDaiHan", None),
                "tieu_han_chi": getattr(c, "cungTieuHan", None),
                "tuan_trung": getattr(c, "tuanTrung", False),
                "triet_lo": getattr(c, "trietLo", False),
                "saos": deepcopy(c.cungSao),
            }
        )

    tu_hoa_table = get_tu_hoa_table(tu_hoa_table_id)
    apply_natal_table(thap_ni_cung, thienCan[can_nam]["tenCan"], tu_hoa_table)
    for palace in thap_ni_cung:
        db.thapNhiCung[palace["cung_so"]].cungSao = deepcopy(palace["saos"])
    return {
        "db": db,
        "tu_hoa_table": table_metadata(tu_hoa_table),
        "cung_menh_so": db.cungMenh,
        "cung_than_so": db.cungThan,
        "tu_cuc": cuc["cuc"],
        "ten_cuc": cuc["tenCuc"],
        "ban_menh": nguHanhNapAm(chi_nam, can_nam, True).replace("Ð", "Đ"),
        "can_nam": thienCan[can_nam]["tenCan"],
        "chi_nam": diaChi[chi_nam]["tenChi"],
        "nam_sinh": nnnn,
        "nam_sinh_am": lunar_year,
        "duong_lich": duong_lich,
        "gioi_tinh": "Nam" if gioi_tinh == 1 else "Nữ",
        "thap_ni_cung": thap_ni_cung,
    }


def _extract_ngu_hanh(text: str) -> str:
    """Trích xuất hành ngũ hành (Kim, Mộc, Thủy, Hỏa, Thổ) từ chuỗi mô tả."""
    t = text.lower()
    for nh in NGU_HANH_LIST:
        if nh.lower() in t:
            return nh
    return "Thổ"


def analyze_menh_cuc(ban_menh_str: str, cuc_str: str) -> dict[str, Any]:
    """Phân tích tương quan Ngũ hành giữa Bản Mệnh và Cục."""
    hanh_menh = _extract_ngu_hanh(ban_menh_str)
    hanh_cuc = _extract_ngu_hanh(cuc_str)

    if hanh_menh == hanh_cuc:
        rel = "MENH_CUC_TI_HOA"
        title = "Mệnh Cục Tị Hòa"
        layman = (
            "Bản thân bạn hòa hợp tự nhiên với môi trường xung quanh. "
            "Cuộc sống diễn ra bình ổn, dễ thích nghi, ít gặp những xung đột hay biến cố quá đột ngột."
        )
    elif NGU_HANH_SINH.get(hanh_cuc) == hanh_menh:
        rel = "CUC_SINH_MENH"
        title = "Cục Sinh Mệnh"
        layman = (
            "Bạn được hoàn cảnh và môi trường ưu ái nâng đỡ thuận lợi. "
            "Dễ gặp may mắn, có quý nhân trợ lực, bước đi trong sự nghiệp và cuộc sống khá êm đềm."
        )
    elif NGU_HANH_SINH.get(hanh_menh) == hanh_cuc:
        rel = "MENH_SINH_CUC"
        title = "Mệnh Sinh Cục"
        layman = (
            "Bạn là người giàu tâm huyết, luôn phải lo toan gánh vác và cống hiến cho công việc, tập thể. "
            "Cần chú ý giữ gìn năng lượng, tránh ôm đồm trách nhiệm quá mức."
        )
    elif NGU_HANH_KHAC.get(hanh_menh) == hanh_cuc:
        rel = "MENH_KHAC_CUC"
        title = "Mệnh Khắc Cục"
        layman = (
            "Bạn sở hữu ý chí tự lập kiên cường và khả năng vượt khó vươn lên mạnh mẽ. "
            "Dù hoàn cảnh có thách thức, bạn vẫn chủ động định đoạt và làm chủ được cuộc đời mình."
        )
    else:
        rel = "CUC_KHAC_MENH"
        title = "Cục Khắc Mệnh"
        layman = (
            "Môi trường xung quanh đôi khi tạo ra nhiều thử thách và áp lực để trui rèn bạn. "
            "Cần sự kiên trì, bình tĩnh ứng biến thay vì nóng vội đối đầu."
        )

    return {
        "relation_type": rel,
        "hanh_menh": hanh_menh,
        "hanh_cuc": hanh_cuc,
        "title": title,
        "meaning_layman": layman,
    }


def get_tam_phuong_tu_chinh(
    cung_so: int, cung_data: dict[int, dict] | list[dict]
) -> dict[str, Any]:
    """Trích xuất 4 cung cấu thành Tam phương Tứ chính của một cung (chính diện, đối xung, 2 tam hợp)."""
    if isinstance(cung_data, list):
        cung_map = {c["cung_so"]: c for c in cung_data}
    else:
        cung_map = cung_data

    chinh = cung_map.get(cung_so, {})
    doi_so = (cung_so + 6 - 1) % 12 + 1
    doi = cung_map.get(doi_so, {})

    th1_so = (cung_so + 4 - 1) % 12 + 1
    th2_so = (cung_so + 8 - 1) % 12 + 1
    th1 = cung_map.get(th1_so, {})
    th2 = cung_map.get(th2_so, {})

    return {
        "chinh_cung": chinh,
        "doi_cung": doi,
        "tam_hop": [th1, th2],
        "all_cung_sos": [cung_so, doi_so, th1_so, th2_so],
    }


def detect_star_group(saos: list[dict[str, Any]]) -> dict[str, Any]:
    """Nhận diện bộ chính tinh cốt lõi (Cách cục nòng cốt của cung Mệnh)."""
    chinh_tinh = [s["saoTen"].lower() for s in saos if s.get("saoLoai") == 1]

    if not chinh_tinh:
        return {
            "code": "VO_CHINH_DIEU",
            "name": "Mệnh Vô Chính Diệu",
            "stars": [],
            "layman": (
                "Cung Mệnh không có chính tinh. Bạn là người mềm dẻo, linh hoạt, "
                "khả năng thích ứng với môi trường rất cao, biết lắng nghe và mượn sức người khác rất khéo léo."
            ),
        }

    spt_set = {"thất sát", "phá quân", "tham lang"}
    tpvt_set = {"tử vi", "thiên phủ", "vũ khúc", "thiên tướng", "liêm trinh"}
    cndl_set = {"thiên cơ", "thái âm", "thiên đồng", "thiên lương"}
    cn_set = {"cự môn", "thái dương"}

    ct_set = set(chinh_tinh)

    if ct_set.intersection(spt_set):
        return {
            "code": "SAT_PHA_THAM",
            "name": "Bộ Sát - Phá - Tham",
            "stars": [s["saoTen"] for s in saos if s.get("saoLoai") == 1],
            "layman": (
                "Đại diện cho mẫu người hành động, dám nghĩ dám làm, tiên phong đột phá. "
                "Thích sự đổi mới, chấp nhận thử thách lớn và khao khát khẳng định giá trị bản thân."
            ),
        }

    if ct_set.intersection(cn_set) and len(ct_set.intersection(cn_set)) == len(ct_set):
        return {
            "code": "CU_NHAT",
            "name": "Bộ Cự - Nhật",
            "stars": [s["saoTen"] for s in saos if s.get("saoLoai") == 1],
            "layman": (
                "Đại diện cho tư duy phản biện sắc bén, khả năng ăn nói, truyền thông và đối ngoại. "
                "Hợp với các công việc cần thuyết phục, phân tích, giảng dạy hoặc quan hệ công chúng."
            ),
        }

    if ct_set.intersection(cndl_set):
        return {
            "code": "CO_NGUYET_DONG_LUONG",
            "name": "Bộ Cơ - Nguyệt - Đồng - Lương",
            "stars": [s["saoTen"] for s in saos if s.get("saoLoai") == 1],
            "layman": (
                "Đại diện cho trí tuệ điềm tĩnh, thiện tâm, giỏi lên kế hoạch và cẩn trọng. "
                "Thích sự ổn định, phù hợp làm chuyên gia, cố vấn, giáo dục, tài chính hoặc quản trị nội bộ."
            ),
        }

    if ct_set.intersection(tpvt_set):
        return {
            "code": "TU_PHU_VU_TUONG",
            "name": "Bộ Tử - Phủ - Vũ - Tướng",
            "stars": [s["saoTen"] for s in saos if s.get("saoLoai") == 1],
            "layman": (
                "Đại diện cho tư chất lãnh đạo, phong thái đĩnh đạc, quản lý bao quát và tính thực tế cao. "
                "Có uy tín tự nhiên, phù hợp làm quản lý, chủ doanh nghiệp hoặc các vị trí điều phối then chốt."
            ),
        }

    return {
        "code": "HON_HOP",
        "name": "Cách Cục Hỗn Hợp",
        "stars": [s["saoTen"] for s in saos if s.get("saoLoai") == 1],
        "layman": "Sự kết hợp đa dạng các nguồn năng lượng, mang lại cho bạn tính cách phong phú và đa tài.",
    }


def categorize_stars_in_palace(saos: list[dict[str, Any]]) -> dict[str, list[dict]]:
    """Phân loại chính tinh (kèm đắc hãm), lục sát tinh và các cát tinh trong cung."""
    chinh_tinh = []
    sat_tinh = []
    cat_tinh = []
    phu_tinh_khac = []
    risk_stars = []

    for s in saos:
        sid = s.get("saoID")
        loai = s.get("saoLoai", 2)
        ten = s.get("saoTen", "")
        dac = s.get("saoDacTinh") or "—"

        star_info = {
            "id": sid,
            "ten": ten,
            "dac_tinh": dac,
            "loai": loai,
        }
        # Catalog groups >= 11 are caution groups, not a prediction of an event.
        if sid in LUC_SAT_TINH_IDS or loai >= 11:
            risk_stars.append(star_info)

        if loai == 1:
            chinh_tinh.append(star_info)
        elif sid in LUC_SAT_TINH_IDS:
            sat_tinh.append(star_info)
        elif sid in CAT_TINH_IDS:
            cat_tinh.append(star_info)
        else:
            phu_tinh_khac.append(star_info)

    return {
        "chinh_tinh": chinh_tinh,
        "sat_tinh": sat_tinh,
        "cat_tinh": cat_tinh,
        "phu_tinh_khac": phu_tinh_khac,
        "risk_stars": risk_stars,
    }


def describe_palace(c: dict[str, Any]) -> dict[str, Any]:
    return {
        "cung_so": c["cung_so"], "ten": c.get("ten_cung", ""),
        "chuan_ten": c.get("chuan_ten", ""),
        "tuan_trung": bool(c.get("tuan_trung")), "triet_lo": bool(c.get("triet_lo")),
        **categorize_stars_in_palace(c.get("saos", [])),
    }


def analyze_year(cungs: list[dict], year: int, birth_lunar_year: int) -> dict[str, Any]:
    """Select the vendor's natal minor-period mapping by the requested lunar year branch.

    Does not re-an stars or pretend natal stars are annual moving stars.
    The selected year denotes the complete Can Chi lunar year, not Jan 1–Dec 31.
    """
    can = thienCan[(year - 4) % 10 + 1]["tenCan"]
    chi = diaChi[(year - 4) % 12 + 1]["tenChi"]
    palace = next((c for c in cungs if c.get("tieu_han_chi") == chi), None)
    return {
        "year": year, "can_chi": f"{can} {chi}", "tuoi_am": year - birth_lunar_year + 1,
        "tieu_han": describe_palace(palace) if palace else None,
        "method": "Tiểu hạn theo ánh xạ cungTieuHan của vendor/lasotuvi, chọn theo chi năm âm lịch.",
        "limitations": "Các sao tại cung tiểu hạn là sao gốc của lá số; lưu niên (vòng Thái Tuế, lưu Tứ Hóa) được an riêng trong khối luu_nien. Năm được hiểu theo năm âm lịch Can Chi, không theo ngày 01/01.",
    }


def extract_tu_hoa(
    thap_ni_cung: list[dict[str, Any]], can: str | None = None, table_id: str | None = None,
) -> list[dict[str, Any]]:
    """Trích xuất 4 hóa tinh (Lộc, Quyền, Khoa, Kỵ), cung đóng và ý nghĩa."""
    res = []
    parents = get_tu_hoa_table(table_id)["by_can"].get(can, {}) if can else {}
    for sid, spec in TU_HOA_DEF.items():
        hit_cung = None
        for c in thap_ni_cung:
            if any(s.get("saoID") == sid for s in c.get("saos", [])):
                hit_cung = c
                break

        if hit_cung:
            chinh_saos = [
                s["saoTen"] for s in hit_cung.get("saos", []) if s.get("saoLoai") == 1
            ]
            res.append(
                {
                    "sao_id": sid,
                    "code": spec["code"],
                    "ten": spec["ten"],
                    "ten_sao": parents.get(spec["code"], ""),
                    "cung_ten": hit_cung.get("ten_cung") or hit_cung["chuan_ten"],
                    "dia_chi": hit_cung["chuan_ten"],
                    "linh_vuc": CUNG_DOMAIN.get(hit_cung.get("ten_cung", ""), ""),
                    "dong_cung_chinh_tinh": " · ".join(chinh_saos)
                    if chinh_saos
                    else "Vô chính diệu",
                    "nghia_ngan": spec["nghia_ngan"],
                    "layman": spec["layman"],
                }
            )
    return res


def find_current_dai_han(
    thap_ni_cung: list[dict[str, Any]], current_age: int
) -> dict[str, Any] | None:
    """Xác định Đại hạn 10 năm hiện tại theo độ tuổi."""
    for c in thap_ni_cung:
        tu = c.get("tu_dai_han")
        if tu is not None and tu <= current_age <= tu + 9:
            chinh = [
                f'{s["saoTen"]} ({s.get("saoDacTinh") or "—"})'
                for s in c.get("saos", [])
                if s.get("saoLoai") == 1
            ]
            return {
                "cung_so": c["cung_so"],
                "cung_ten": c["chuan_ten"],
                "ten_linh_vuc": c.get("ten_cung", ""),
                "tu_tuoi": tu,
                "den_tuoi": tu + 9,
                "tuoi_hien_tai": current_age,
                "chinh_tinh": " · ".join(chinh) if chinh else "Vô chính diệu",
                "layman": (
                    f"Bạn đang ở trong đại hạn 10 năm từ {tu} đến {tu + 9} tuổi tại cung {c['chuan_ten']}. "
                    "Đây là giai đoạn trọng tâm ảnh hưởng trực tiếp đến bước tiến sự nghiệp và đời sống cá nhân."
                ),
            }
    return None


def extract_horoscope_features(
    raw_laso: dict[str, Any],
    target_year: int | None = None,
    input_confidence: str = DEFAULT_INPUT_CONFIDENCE,
    gio_sinh_source: str = DEFAULT_GIO_SINH_SOURCE,
    gio_sinh_error_phut: int | None = None,
) -> dict[str, Any]:
    """Hàm tổng hợp bóc tách toàn bộ đặc trưng của một lá số Tử Vi.

    Ba tham số cuối ghi lại độ tin cậy/nguồn/sai số giờ sinh để prompt và UI
    biết giới hạn dữ liệu đầu vào (mức C/D chỉ luận cấu trúc).
    """
    cungs = raw_laso["thap_ni_cung"]
    by_cung_so = {c["cung_so"]: c for c in cungs}
    by_chuan_ten = {c["chuan_ten"]: c for c in cungs}

    # 1. Tương quan Bản Mệnh vs Cục
    menh_cuc = analyze_menh_cuc(raw_laso["ban_menh"], raw_laso["ten_cuc"])

    # 2. Cung Mệnh và Cung Thân
    cung_menh_so = raw_laso["cung_menh_so"]
    cung_than_so = raw_laso["cung_than_so"]
    menh_cung = by_cung_so.get(cung_menh_so, {})
    than_cung = by_cung_so.get(cung_than_so, {})

    # 3. Tam phương tứ chính của Cung Mệnh
    tptc_menh = get_tam_phuong_tu_chinh(cung_menh_so, by_cung_so)

    # 4. Nhận diện Bộ sao chính tinh cung Mệnh
    all_menh_stars = menh_cung.get("saos", [])
    star_group = detect_star_group(all_menh_stars)

    # 5. Phân loại sao tại Mệnh và Thân
    menh_stars_cat = categorize_stars_in_palace(all_menh_stars)
    than_stars_cat = categorize_stars_in_palace(than_cung.get("saos", []))

    # 6. Tứ Hóa
    tu_hoa_table = get_tu_hoa_table((raw_laso.get("tu_hoa_table") or {}).get("id"))
    tu_hoa = extract_tu_hoa(cungs, raw_laso["can_nam"], tu_hoa_table["id"])

    # 7. Tuổi và Đại Hạn hiện tại
    nam_sinh = raw_laso.get("nam_sinh_am", raw_laso.get("nam_sinh", 2000))
    current_year = target_year or datetime.now(ZoneInfo("Asia/Bangkok")).year
    current_age = current_year - nam_sinh + 1  # Tuổi âm lịch truyền thống
    current_dai_han = find_current_dai_han(cungs, current_age)
    nam_xem = analyze_year(cungs, current_year, nam_sinh)
    tieu_han = nam_xem.get("tieu_han") or {}
    luu_nien = compute_luu_nien(
        cungs, current_year, cung_menh_so, cung_than_so,
        (current_dai_han or {}).get("cung_so"), tieu_han.get("cung_so"),
        tu_hoa_table_id=tu_hoa_table["id"],
    )

    # 8. Bóc tách 5 cung chính quan trọng đối với người xem
    important_cung_names = ["Mệnh", "Quan lộc", "Tài bạch", "Phu thê", "Thiên di"]
    cung_chinh = []
    for ten in important_cung_names:
        c = next((item for item in cungs if item.get("ten_cung", "").casefold() == ten.casefold()), None)
        if c:
            cat = categorize_stars_in_palace(c.get("saos", []))
            cung_chinh.append({
                "ten": "Tài Bạch" if ten == "Tài bạch" else ten,
                "cung_so": c["cung_so"],
                "chuan_ten": c["chuan_ten"],
                "y_nghia_linh_vuc": CUNG_DOMAIN.get(ten, ""),
                "chinh_tinh": [f"{s['ten']} ({s['dac_tinh']})" for s in cat["chinh_tinh"]],
                "sat_tinh": [s["ten"] for s in cat["sat_tinh"]],
                "cat_tinh": [s["ten"] for s in cat["cat_tinh"]],
            })

    from backend.app.services.horoscope_annual import build_year_comparison
    return {
        "annual_comparison": build_year_comparison(raw_laso,current_year),
        "thong_tin_co_ban": {
            "nam_sinh": raw_laso["nam_sinh"],
            "nam_sinh_am": nam_sinh,
            "duong_lich": raw_laso.get("duong_lich", True),
            "gioi_tinh": raw_laso["gioi_tinh"],
            "can_chi_nam": f"{raw_laso['can_nam']} {raw_laso['chi_nam']}",
            "ban_menh": raw_laso["ban_menh"],
            "ten_cuc": raw_laso["ten_cuc"],
            "cung_menh": menh_cung.get("chuan_ten", ""),
            "cung_than": than_cung.get("chuan_ten", ""),
            "cung_than_so": cung_than_so,
            "input_confidence": normalize_level(input_confidence),
            "gio_sinh_source": gio_sinh_source,
            "gio_sinh_error_phut": gio_sinh_error_phut,
            "tu_hoa_table": table_metadata(tu_hoa_table),
        },
        "cung_domains": dict(CUNG_DOMAIN),
        "menh_cuc": menh_cuc,
        "star_group": star_group,
        "menh_stars": menh_stars_cat,
        "than_stars": than_stars_cat,
        "tam_phuong_tu_chinh_menh": {
            "chinh_cung": menh_cung.get("chuan_ten", ""),
            "doi_cung": tptc_menh["doi_cung"].get("chuan_ten", ""),
            "tam_hop": [c.get("chuan_ten", "") for c in tptc_menh["tam_hop"]],
            "cung_data": [describe_palace(by_cung_so[i]) for i in tptc_menh['all_cung_sos']],
        },
        "tu_hoa": tu_hoa,
        "dai_han_hien_tai": current_dai_han,
        "cung_chinh": cung_chinh,
        "palaces": [describe_palace(c) for c in cungs],
        "nam_xem": nam_xem,
        "luu_nien": luu_nien,
    }
