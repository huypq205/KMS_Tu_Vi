"""P2b (Plan_Fix_Mai_Anh_v2): chuẩn hóa quan hệ cung.

Phép tính vị trí thuần túy trên ``cung_so`` 1..12 (1 = Tý ... 12 = Hợi):
đồng cung, xung chiếu, hai cung tam hợp, hai cung giáp — đủ 12 cung, đặc
biệt điểm vòng qua Tý/Hợi.

Kiểm tra thêm:
- mã quan hệ trùng bộ giá trị ``quan_he`` của danh mục cách cục P2;
- chuẩn hóa tên chi/cung (không đoán khi mơ hồ);
- đọc miếu/vượng/đắc/bình/hãm từ ``saoDacTinh``, thiếu thì trả "thieu";
- ``get_tam_phuong_tu_chinh`` giữ nguyên hành vi sau khi tách module.

Ranh giới P2b: không đổi bảng trạng thái sao hay bảng Tứ Hóa.
"""
from __future__ import annotations

from copy import deepcopy

import pytest

from backend.app.core.evidence_types import EvidenceType
from backend.app.schemas.horoscope_contract import MISSING
from backend.app.services.cach_cuc_catalog import RELATIONSHIPS
from backend.app.services.horoscope_analysis import _palace_evidence_kind
from backend.app.services.horoscope_features import get_tam_phuong_tu_chinh
from backend.app.services.palace_relations import (
    CHI_NAMES,
    DAC_TINH_CODES,
    EVIDENCE_KIND_BY_RELATION,
    REL_DONG_CUNG,
    REL_GIAP_CUNG,
    REL_KHONG,
    REL_TAM_HOP,
    REL_XUNG_CHIEU,
    RELATIONS,
    cac_cung_lien_quan,
    chi_name_of,
    cung_so_of_chi,
    dac_tinh_in_palace,
    doi_cung,
    evidence_kind,
    giap_cung,
    normalize_chi_name,
    normalize_palace_role,
    palace_so_by_role,
    quan_he,
    resolve_anchor,
    tam_hop,
    tam_phuong,
)


# --- P2b.TC-01: đối cung đủ 12 cung, đối xứng, vòng qua Tý/Hợi ---------------
def test_tc01_doi_cung_du_12_cung_va_vong_qua_ty_hoi():
    assert [doi_cung(n) for n in range(1, 13)] == [7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6]
    for n in range(1, 13):
        assert 1 <= doi_cung(n) <= 12
        assert doi_cung(n) != n
        assert doi_cung(doi_cung(n)) == n
    # Vòng qua Tý (1) và Hợi (12)
    assert doi_cung(1) == 7
    assert doi_cung(7) == 1
    assert doi_cung(6) == 12
    assert doi_cung(12) == 6


# --- P2b.TC-02: tam hợp = 4 nhóm rời nhau, phủ kín 12 cung ---------------
def test_tc02_tam_hop_bon_nhom_kin_12_cung_va_wrap():
    groups = {frozenset((n,) + tam_hop(n)) for n in range(1, 13)}
    assert len(groups) == 4
    assert set().union(*groups) == set(range(1, 13))
    for n in range(1, 13):
        a, b = tam_hop(n)
        assert a != b
        assert n not in (a, b)
        assert doi_cung(n) not in (a, b)
        assert set(tam_hop(a)) == {n, b}
        assert set(tam_hop(b)) == {n, a}
    # Hợi (12) -> Mão (4), Mùi (8): đúng nhóm tam hợp Mộc
    assert tam_hop(12) == (4, 8)


# --- P2b.TC-03: giáp cung đủ 12 cung, vòng qua Tý/Hợi ----------------------
def test_tc03_giap_cung_du_12_cung_va_vong_qua_ty_hoi():
    expected = [(12, 2), (1, 3), (2, 4), (3, 5), (4, 6), (5, 7),
                (6, 8), (7, 9), (8, 10), (9, 11), (10, 12), (11, 1)]
    assert [giap_cung(n) for n in range(1, 13)] == expected
    assert giap_cung(1) == (12, 2)
    assert giap_cung(12) == (11, 1)
    for n in range(1, 13):
        a, b = giap_cung(n)
        assert n not in (a, b)
        assert doi_cung(n) not in (a, b)
        assert n in giap_cung(a)
        assert n in giap_cung(b)


# --- P2b.TC-04: quan_he đối xứng + đếm đúng 5 loại cho mỗi cung ------------
def test_tc04_quan_he_doi_xung_va_dem_dung():
    # Mã quan hệ dùng được trực tiếp với danh mục P2 (P3 so khớp rule["quan_he"]).
    assert {REL_DONG_CUNG, REL_TAM_HOP, REL_XUNG_CHIEU, REL_GIAP_CUNG} <= set(RELATIONSHIPS)
    assert REL_KHONG not in RELATIONSHIPS
    assert set(RELATIONS) == {REL_DONG_CUNG, REL_TAM_HOP, REL_XUNG_CHIEU,
                              REL_GIAP_CUNG, REL_KHONG}

    for n in range(1, 13):
        counts = {REL_DONG_CUNG: 0, REL_TAM_HOP: 0, REL_XUNG_CHIEU: 0,
                  REL_GIAP_CUNG: 0, REL_KHONG: 0}
        for m in range(1, 13):
            rel = quan_he(n, m)
            assert rel == quan_he(m, n), (n, m)
            counts[rel] += 1
        # 1 đồng cung + 1 xung chiếu + 2 tam hợp + 2 giáp + 6 không liên hệ = 12
        assert counts == {REL_DONG_CUNG: 1, REL_TAM_HOP: 2, REL_XUNG_CHIEU: 1,
                          REL_GIAP_CUNG: 2, REL_KHONG: 6}

    assert quan_he(1, 1) == REL_DONG_CUNG
    assert quan_he(1, 7) == REL_XUNG_CHIEU
    assert quan_he(1, 5) == REL_TAM_HOP
    assert quan_he(1, 12) == REL_GIAP_CUNG
    assert quan_he(1, 4) == REL_KHONG


# --- P2b.TC-05: tam_phuong đủ 4 cung, giữ khóa cũ, wrap Hợi ----------------
def test_tc05_tam_phuong_giu_dung_khoa_cu_va_wrap():
    t12 = tam_phuong(12)
    assert t12["chinh_cung"] == 12
    assert t12["doi_cung"] == 6
    assert set(t12["tam_hop"]) == {4, 8}
    assert t12["all_cung_sos"] == [12, 6, 4, 8]
    assert set(t12["giap_cung"]) == {11, 1}

    for n in range(1, 13):
        t = tam_phuong(n)
        assert len(t["all_cung_sos"]) == 4
        assert len(set(t["all_cung_sos"])) == 4
        assert set(t["all_cung_sos"]) == {n, doi_cung(n), *tam_hop(n)}
        assert t["all_cung_sos"][0] == n
        assert t["all_cung_sos"][1] == doi_cung(n)


def test_tc05b_get_tam_phuong_tu_chinh_giu_nguyen_hanh_vi():
    cung_map = {i: {"cung_so": i, "chuan_ten": CHI_NAMES[i - 1], "saos": []}
                for i in range(1, 13)}

    legacy = get_tam_phuong_tu_chinh(1, cung_map)
    assert set(legacy) == {"chinh_cung", "doi_cung", "tam_hop", "all_cung_sos"}
    assert legacy["chinh_cung"]["cung_so"] == 1
    assert legacy["doi_cung"]["cung_so"] == 7
    assert [c["cung_so"] for c in legacy["tam_hop"]] == [5, 9]
    assert legacy["all_cung_sos"] == [1, 7, 5, 9]

    legacy12 = get_tam_phuong_tu_chinh(12, cung_map)
    assert legacy12["doi_cung"]["cung_so"] == 6
    assert [c["cung_so"] for c in legacy12["tam_hop"]] == [4, 8]
    assert legacy12["all_cung_sos"] == [12, 6, 4, 8]

    # Danh sách cung thay vì map vẫn chạy; cung thiếu trả {} như cũ.
    as_list = list(cung_map.values())
    assert get_tam_phuong_tu_chinh(1, as_list)["doi_cung"]["cung_so"] == 7
    sparse = get_tam_phuong_tu_chinh(1, {1: {"cung_so": 1}})
    assert sparse["doi_cung"] == {}
    assert sparse["tam_hop"] == [{}, {}]


# --- P2b.TC-06: chuẩn hóa tên chi, không đoán khi mơ hồ --------------------
def test_tc06_chuan_hoa_ten_chi_khong_doan_khi_mo_ho():
    for so, ten in enumerate(CHI_NAMES, start=1):
        assert chi_name_of(so) == ten
        assert cung_so_of_chi(ten) == so
        assert normalize_chi_name(ten) == ten

    # Biến thể đã biết trong code cũ: "Tị" (dấu nặng dưới i) = "Tỵ".
    assert normalize_chi_name("Tị") == "Tỵ"
    assert cung_so_of_chi("Tị") == 6

    # Khác hoa/thường hoặc bỏ dấu vẫn nhận khi không mơ hồ.
    assert cung_so_of_chi("tý") == 1
    assert cung_so_of_chi("TÝ") == 1
    assert cung_so_of_chi("TỴ") == 6
    assert cung_so_of_chi("suu") == 2
    assert cung_so_of_chi("SUU") == 2
    assert cung_so_of_chi("  dan  ") == 3
    assert cung_so_of_chi("hoi") == 12

    # "ty" không dấu mơ hồ giữa Tý và Tỵ -> không đoán.
    assert cung_so_of_chi("ty") is None
    assert cung_so_of_chi("TY") is None
    assert normalize_chi_name("ty") is None
    assert cung_so_of_chi("ti") is None
    assert cung_so_of_chi("khong-ton-tai") is None
    assert cung_so_of_chi("") is None
    assert cung_so_of_chi(None) is None

    for bad in (0, 13, -1, 12.5, "1", None, True, False):
        with pytest.raises(ValueError):
            chi_name_of(bad)


def test_tc06b_chuan_hoa_ten_cung_va_cung_neo_duoc_neu_ro():
    assert normalize_palace_role("Mệnh") == "menh"
    assert normalize_palace_role("QUAN LỘC") == "quan_loc"
    assert normalize_palace_role("quan loc") == "quan_loc"
    assert normalize_palace_role("Tài Bạch") == "tai_bach"
    assert normalize_palace_role("Phụ  mẫu") == "phu_mau"
    assert normalize_palace_role("không có") is None
    assert normalize_palace_role(None) is None

    palaces = [
        {"cung_so": 1, "ten": "Mệnh", "chuan_ten": "Tý"},
        {"cung_so": 5, "ten": "Quan lộc", "chuan_ten": "Thìn"},
        {"cung_so": 9, "ten": "Tài bạch", "chuan_ten": "Thân"},
    ]
    assert palace_so_by_role(palaces, "Quan Lộc") == 5
    assert palace_so_by_role(palaces, "tai bach") == 9
    assert palace_so_by_role(palaces, "Phu thê") is None

    # Cung neo nhận số cung, tên chi hoặc tên cung — cùng một kết quả.
    assert resolve_anchor(palaces, "Mệnh") == 1
    assert resolve_anchor(palaces, "Quan Lộc") == 5
    assert resolve_anchor(palaces, "Tý") == 1
    assert resolve_anchor(palaces, 12) == 12
    with pytest.raises(ValueError):
        resolve_anchor(palaces, "Phu thê")
    with pytest.raises(ValueError):
        resolve_anchor(palaces, 13)


# --- P2b.TC-07: loại chứng cứ vị trí quanh cung neo ------------------------
def test_tc07_evidence_kind_du_12_cung_va_giu_hanh_vi_cu():
    mapping = {
        REL_DONG_CUNG: EvidenceType.TOA_THU.value,
        REL_XUNG_CHIEU: EvidenceType.XUNG_CHIEU.value,
        REL_TAM_HOP: EvidenceType.TAM_HOP.value,
        REL_GIAP_CUNG: EvidenceType.GIAP_CUNG.value,
        REL_KHONG: EvidenceType.TOA_THU.value,
    }
    assert mapping == EVIDENCE_KIND_BY_RELATION
    for anchor in range(1, 13):
        for target in range(1, 13):
            assert evidence_kind(anchor, target) == mapping[quan_he(anchor, target)]

    # Nhận cả tên chi, chuẩn hóa dấu; không đoán tên mơ hồ/không hợp lệ.
    assert evidence_kind("Tý", "Ngọ") == EvidenceType.XUNG_CHIEU.value
    assert evidence_kind("Tý", "Thìn") == EvidenceType.TAM_HOP.value
    assert evidence_kind("Tỵ", "Ngọ") == EvidenceType.GIAP_CUNG.value
    assert evidence_kind("Tị", "Ngọ") == EvidenceType.GIAP_CUNG.value
    assert evidence_kind("", 7) == EvidenceType.TOA_THU.value
    assert evidence_kind("Tý", "ty") == EvidenceType.TOA_THU.value

    # Hàm cũ trong horoscope_analysis giữ nguyên kết quả đã có test.
    assert _palace_evidence_kind("Ngọ", {"chinh_cung": "Tị"}) == "giap_cung"
    assert _palace_evidence_kind("Ngọ", {"chinh_cung": "Tý"}) == "xung_chieu"
    assert _palace_evidence_kind("Thìn", {"chinh_cung": "Tý"}) == "tam_hop"
    assert _palace_evidence_kind("Tý", {"chinh_cung": "Tý"}) == "toa_thu"
    assert _palace_evidence_kind("Ngọ", {}) == "toa_thu"


# --- P2b.TC-08: liệt kê cung liên quan của một cung neo -------------------
def test_tc08_cac_cung_lien_quan_du_12_cung():
    assert cac_cung_lien_quan(1) == {
        "chinh_cung": 1,
        "dong_cung": [1],
        "xung_chieu": [7],
        "tam_hop": [5, 9],
        "giap_cung": [12, 2],
        "khong": [3, 4, 6, 8, 10, 11],
    }
    for n in range(1, 13):
        groups = cac_cung_lien_quan(n)
        assert groups["chinh_cung"] == n
        flat = (groups["dong_cung"] + groups["xung_chieu"] + groups["tam_hop"]
                + groups["giap_cung"] + groups["khong"])
        assert sorted(flat) == list(range(1, 13))


# --- P2b.TC-09: đọc trạng thái sao từ saoDacTinh, thiếu trả "thieu" -------
def _palace_with_stars() -> dict:
    return {
        "cung_so": 1,
        "saos": [
            {"saoTen": "Tử Vi", "saoDacTinh": "M"},
            {"saoTen": "Thiên cơ", "saoDacTinh": "V"},
            {"saoTen": "Cự môn", "saoDacTinh": "H"},
            {"saoTen": "Thiên Đồng", "saoDacTinh": "B"},
            {"saoTen": "Vũ khúc", "saoDacTinh": "Đ"},
        ],
    }


def test_tc09_doc_trang_thai_mieu_vuong_dac_binh_ham():
    assert set(DAC_TINH_CODES) == {"M", "V", "Đ", "B", "H"}
    palace = _palace_with_stars()
    assert dac_tinh_in_palace(palace, "Tử Vi") == "mieu"
    assert dac_tinh_in_palace(palace, "tử vi") == "mieu"
    assert dac_tinh_in_palace(palace, "Thiên Cơ") == "vuong"
    assert dac_tinh_in_palace(palace, "Cự Môn") == "ham"
    assert dac_tinh_in_palace(palace, "Thiên Đồng") == "binh"
    assert dac_tinh_in_palace(palace, "Vũ Khúc") == "dac"


def test_tc09b_thieu_du_lieu_tra_thieu_khong_suy():
    assert dac_tinh_in_palace({}, "Tử Vi") == MISSING
    assert dac_tinh_in_palace(None, "Tử Vi") == MISSING
    assert dac_tinh_in_palace({"saos": [{"saoTen": "Tử Vi"}]}, "Tử Vi") == MISSING
    assert dac_tinh_in_palace({"saos": [{"saoTen": "Tử Vi", "saoDacTinh": None}]},
                              "Tử Vi") == MISSING
    assert dac_tinh_in_palace({"saos": [{"saoTen": "Tử Vi", "saoDacTinh": ""}]},
                              "Tử Vi") == MISSING
    assert dac_tinh_in_palace({"saos": [{"saoTen": "Tử Vi", "saoDacTinh": "X"}]},
                              "Tử Vi") == MISSING
    # Sao không nằm trong cung: thiếu, không lấy từ cung khác.
    assert dac_tinh_in_palace({"saos": [{"saoTen": "Thiên Cơ", "saoDacTinh": "M"}]},
                              "Tử Vi") == MISSING
    # Dạng palace đã chuẩn hóa (describe_palace) vẫn đọc được.
    described = {"cung_so": 1, "chinh_tinh": [{"ten": "Tử Vi", "dac_tinh": "M"}]}
    assert dac_tinh_in_palace(described, "Tử Vi") == "mieu"


# --- P2b.TC-10: không sửa dữ liệu gốc / bảng trạng thái trong gói này -----
def test_tc10_khong_sua_du_lieu_goc():
    palace = _palace_with_stars()
    before = deepcopy(palace)
    dac_tinh_in_palace(palace, "Tử Vi")
    assert palace == before

    import backend.app.services.palace_relations as module
    # Chỉ đọc mã vendor hiện có; P2b không thêm bảng miếu/vượng mới.
    assert module.DAC_TINH_CODES == {"M": "mieu", "V": "vuong", "Đ": "dac",
                                     "B": "binh", "H": "ham"}
    assert not hasattr(module, "DAC_TINH_TABLE")


# --- P2b.TC-11: cung_so không hợp lệ bị báo lỗi rõ -------------------------
@pytest.mark.parametrize("bad", [0, 13, -1, 12.5, "1", None, True, False])
def test_tc11_cung_so_khong_hop_le_bao_loi(bad):
    for fn in (doi_cung, tam_hop, giap_cung, tam_phuong, cac_cung_lien_quan):
        with pytest.raises(ValueError):
            fn(bad)
    with pytest.raises(ValueError):
        quan_he(bad, 1)
    with pytest.raises(ValueError):
        quan_he(1, bad)
    with pytest.raises(ValueError):
        get_tam_phuong_tu_chinh(bad, {i: {"cung_so": i} for i in range(1, 13)})
