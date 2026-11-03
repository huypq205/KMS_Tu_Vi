"""P2b (Plan_Fix_Mai_Anh_v2): chuẩn hóa quan hệ cung.

Phép tính vị trí thuần túy trên ``cung_so`` 1..12, theo đúng thứ tự địa chi
của vendor (1 = Tý, 2 = Sửu, ..., 12 = Hợi):

- đồng cung (chính nó);
- xung chiếu / đối cung (cách 6);
- hai cung tam hợp (cách 4 và 8);
- hai cung giáp (trước và sau, vòng qua Tý/Hợi).

Module **không** luận giải ý nghĩa của quan hệ — phần đó thuộc quy tắc nguồn
(P2). Module cũng không thay đổi bảng trạng thái sao hay bảng Tứ Hóa; trạng
thái miếu/vượng/đắc/bình/hãm chỉ được **đọc** từ ``saoDacTinh`` của vendor,
thiếu thì trả ``MISSING`` ("thieu"), không suy đoán.

Mã quan hệ ``REL_*`` trùng bộ giá trị ``quan_he`` của danh mục P2
(``cach_cuc_catalog.RELATIONSHIPS``) để P3 so khớp trực tiếp; ``khong`` là
"không có quan hệ" nên không nằm trong danh mục quy tắc.

Tên chi/cung được chuẩn hóa trước khi so sánh (bỏ dấu, không phân biệt
hoa/thường, gộp khoảng trắng). Khi một cách viết không dấu là **mơ hồ**
(ví dụ "ty" có thể là Tý hoặc Tỵ), hàm trả ``None`` thay vì đoán.
"""
from __future__ import annotations

import unicodedata
from typing import Any, Iterator

from backend.app.schemas.horoscope_contract import MISSING
from backend.app.services.tu_hoa_tables import normalize_star

# Thứ tự cung_so của vendor/lasotuvi: 1 = Tý ... 12 = Hợi.
CHI_NAMES: tuple[str, ...] = (
    "Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ",
    "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi",
)

# 12 tên cung theo CUNG_DOMAIN của horoscope_features (không import để tránh vòng lặp).
PALACE_ROLES: tuple[str, ...] = (
    "Mệnh", "Phụ mẫu", "Phúc đức", "Điền trạch", "Quan lộc", "Nô bộc",
    "Thiên di", "Tật ách", "Tài bạch", "Tử tức", "Phu thê", "Huynh đệ",
)
PALACE_ROLE_CODES: dict[str, str] = {
    "Mệnh": "menh",
    "Phụ mẫu": "phu_mau",
    "Phúc đức": "phuc_duc",
    "Điền trạch": "dien_trach",
    "Quan lộc": "quan_loc",
    "Nô bộc": "no_boc",
    "Thiên di": "thien_di",
    "Tật ách": "tat_ach",
    "Tài bạch": "tai_bach",
    "Tử tức": "tu_tuc",
    "Phu thê": "phu_the",
    "Huynh đệ": "huynh_de",
}

REL_DONG_CUNG = "dong_cung"
REL_TAM_HOP = "tam_hop"
REL_XUNG_CHIEU = "xung_chieu"
REL_GIAP_CUNG = "giap_cung"
REL_KHONG = "khong"
RELATIONS: tuple[str, ...] = (
    REL_DONG_CUNG, REL_TAM_HOP, REL_XUNG_CHIEU, REL_GIAP_CUNG, REL_KHONG,
)

# Mã trạng thái sao của vendor (Sao.anDacTinh) -> mã chuẩn của hợp đồng.
# Đây là bản đọc duy nhất; P2b không thêm/sửa bảng miếu vượng.
DAC_TINH_CODES: dict[str, str] = {
    "M": "mieu",
    "V": "vuong",
    "Đ": "dac",
    "B": "binh",
    "H": "ham",
}
DAC_TINH_LABELS: dict[str, str] = {
    "mieu": "Miếu",
    "vuong": "Vượng",
    "dac": "Đắc",
    "binh": "Bình",
    "ham": "Hãm",
}

# Quan hệ vị trí -> loại chứng cứ (trùng EvidenceType của backend).
EVIDENCE_KIND_BY_RELATION: dict[str, str] = {
    REL_DONG_CUNG: "toa_thu",
    REL_XUNG_CHIEU: "xung_chieu",
    REL_TAM_HOP: "tam_hop",
    REL_GIAP_CUNG: "giap_cung",
    REL_KHONG: "toa_thu",
}

_STAR_GROUP_KEYS = ("chinh_tinh", "cat_tinh", "sat_tinh", "phu_tinh_khac", "risk_stars")


def _fold(text: str) -> str:
    """Bỏ dấu, không phân biệt hoa/thường, gộp khoảng trắng (dùng nội bộ)."""
    value = unicodedata.normalize("NFD", str(text).casefold())
    value = "".join(c for c in value if unicodedata.category(c) != "Mn")
    value = value.replace("đ", "d")
    return " ".join(value.split())


def _build_chi_index() -> tuple[dict[str, int], dict[str, int], set[str]]:
    exact: dict[str, int] = {}
    folded: dict[str, int] = {}
    ambiguous: set[str] = set()
    for so, ten in enumerate(CHI_NAMES, start=1):
        exact[ten.casefold()] = so
        key = _fold(ten)
        if key in folded:
            # "Tý" và "Tỵ" cùng thành "ty": không được đoán.
            ambiguous.add(key)
        folded[key] = so
    for key in ambiguous:
        folded.pop(key, None)
    # Biến thể đã biết trong code cũ (horoscope_analysis): "Tị" = "Tỵ".
    exact["tị"] = 6
    return exact, folded, ambiguous


_CHI_EXACT, _CHI_FOLDED, _CHI_AMBIGUOUS = _build_chi_index()
_ROLE_BY_KEY: dict[str, str] = {_fold(role): code for role, code in PALACE_ROLE_CODES.items()}


def _check_palace(cung_so: int) -> int:
    """Validate cung_so 1..12; bool/không phải int/ngoài khoảng đều raise ValueError."""
    if isinstance(cung_so, bool) or not isinstance(cung_so, int):
        raise ValueError(f"cung_so phải là số nguyên 1..12, nhận: {cung_so!r}")
    if not 1 <= cung_so <= 12:
        raise ValueError(f"cung_so phải nằm trong 1..12, nhận: {cung_so!r}")
    return cung_so


def _resolve_position(value: Any) -> int | None:
    """Đổi cung_so hoặc tên chi (đã chuẩn hóa) về cung_so; không hợp lệ -> None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if 1 <= value <= 12 else None
    if isinstance(value, str):
        return cung_so_of_chi(value)
    return None


def chi_name_of(cung_so: int) -> str:
    """Tên địa chi của cung_so (1 -> Tý, 12 -> Hợi)."""
    return CHI_NAMES[_check_palace(cung_so) - 1]


def cung_so_of_chi(name: str | None) -> int | None:
    """Cung_so của tên chi; trả None khi tên lạ hoặc cách viết mơ hồ ("ty")."""
    if not isinstance(name, str):
        return None
    key = name.strip().casefold()
    if key in _CHI_EXACT:
        return _CHI_EXACT[key]
    return _CHI_FOLDED.get(_fold(name))


def normalize_chi_name(name: str | None) -> str | None:
    """Tên địa chi chuẩn ("Tỵ"); None khi không nhận diện được hoặc mơ hồ."""
    so = cung_so_of_chi(name)
    return CHI_NAMES[so - 1] if so is not None else None


def normalize_palace_role(name: str | None) -> str | None:
    """Mã cung chuẩn ("quan_loc") từ tên cung; None khi không nhận diện được."""
    if not isinstance(name, str):
        return None
    return _ROLE_BY_KEY.get(_fold(name))


def palace_so_by_role(palaces: list[dict[str, Any]] | None, role: str | None) -> int | None:
    """Cung_so của cung giữ vai trò (Mệnh, Quan lộc...) trong danh sách cung của lá số."""
    code = normalize_palace_role(role)
    if code is None:
        return None
    for palace in palaces or []:
        if not isinstance(palace, dict):
            continue
        ten = palace.get("ten") or palace.get("ten_cung") or ""
        if normalize_palace_role(ten) != code:
            continue
        so = palace.get("cung_so")
        if isinstance(so, int) and not isinstance(so, bool) and 1 <= so <= 12:
            return so
    return None


def resolve_anchor(palaces: list[dict[str, Any]] | None, anchor: int | str) -> int:
    """Chuẩn hóa cung neo: nhận cung_so, tên chi ("Tý") hoặc tên cung ("Quan Lộc").

    Raise ValueError khi không xác định được — không mặc định về Mệnh.
    """
    if isinstance(anchor, bool):
        raise ValueError(f"cung neo không hợp lệ: {anchor!r}")
    if isinstance(anchor, int):
        return _check_palace(anchor)
    if isinstance(anchor, str):
        so = cung_so_of_chi(anchor)
        if so is not None:
            return so
        so = palace_so_by_role(palaces, anchor)
        if so is not None:
            return so
    raise ValueError(f"cung neo không hợp lệ hoặc không có trong lá số: {anchor!r}")


def doi_cung(cung_so: int) -> int:
    """Cung xung chiếu / đối cung (cách 6)."""
    return (_check_palace(cung_so) + 5) % 12 + 1


def tam_hop(cung_so: int) -> tuple[int, int]:
    """Hai cung tam hợp (cách 4 và 8), giữ thứ tự +4, +8 như code cũ."""
    n = _check_palace(cung_so)
    return ((n + 3) % 12 + 1, (n + 7) % 12 + 1)


def giap_cung(cung_so: int) -> tuple[int, int]:
    """Hai cung giáp (trước và sau), vòng qua Tý/Hợi."""
    n = _check_palace(cung_so)
    return ((n - 2) % 12 + 1, n % 12 + 1)


def tam_phuong(cung_so: int) -> dict[str, Any]:
    """Bộ 4 cung Tam phương Tứ chính của cung_so, giữ khóa mà code cũ trả về."""
    n = _check_palace(cung_so)
    doi = doi_cung(n)
    th1, th2 = tam_hop(n)
    return {
        "chinh_cung": n,
        "doi_cung": doi,
        "tam_hop": (th1, th2),
        "giap_cung": giap_cung(n),
        "all_cung_sos": [n, doi, th1, th2],
    }


def quan_he(cung_a: int, cung_b: int) -> str:
    """Mã quan hệ vị trí giữa hai cung (đối xứng), dùng trực tiếp với rule["quan_he"]."""
    a = _check_palace(cung_a)
    b = _check_palace(cung_b)
    if a == b:
        return REL_DONG_CUNG
    if b == doi_cung(a):
        return REL_XUNG_CHIEU
    if b in tam_hop(a):
        return REL_TAM_HOP
    if b in giap_cung(a):
        return REL_GIAP_CUNG
    return REL_KHONG


def cac_cung_lien_quan(cung_so: int) -> dict[str, Any]:
    """Nhóm cung liên quan của cung neo, tách theo từng mã quan hệ."""
    n = _check_palace(cung_so)
    dong = [n]
    xung = [doi_cung(n)]
    hop = list(tam_hop(n))
    giap = list(giap_cung(n))
    da_co = set(dong + xung + hop + giap)
    khong = [so for so in range(1, 13) if so not in da_co]
    return {
        "chinh_cung": n,
        "dong_cung": dong,
        "xung_chieu": xung,
        "tam_hop": hop,
        "giap_cung": giap,
        "khong": khong,
    }


def evidence_kind(anchor: int | str, target: int | str) -> str:
    """Loại chứng cứ vị trí của ``target`` so với cung neo ``anchor``.

    Nhận cung_so hoặc tên chi đã chuẩn hóa; không xác định được thì trả
    ``toa_thu`` (giữ đúng hành vi cũ của ``_palace_evidence_kind``).
    """
    a = _resolve_position(anchor)
    t = _resolve_position(target)
    if a is None or t is None or a == t:
        return "toa_thu"
    return EVIDENCE_KIND_BY_RELATION[quan_he(a, t)]


def _iter_stars(palace: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Sao trong cung: ưu tiên ``saos`` gốc, sau đó các nhóm đã chuẩn hóa."""
    saos = palace.get("saos")
    if isinstance(saos, list):
        for star in saos:
            if isinstance(star, dict):
                yield star
        return
    for key in _STAR_GROUP_KEYS:
        group = palace.get(key)
        if isinstance(group, list):
            for star in group:
                if isinstance(star, dict):
                    yield star


def _normalize_dac_tinh(value: Any) -> str:
    """Mã trạng thái chuẩn từ saoDacTinh; thiếu/không rõ -> MISSING (không suy)."""
    if value is None:
        return MISSING
    raw = str(value).strip()
    if not raw:
        return MISSING
    if raw in DAC_TINH_CODES:
        return DAC_TINH_CODES[raw]
    folded = _fold(raw)
    for code, state in DAC_TINH_CODES.items():
        if folded in (_fold(code), _fold(state), _fold(DAC_TINH_LABELS[state])):
            return state
    return MISSING


def dac_tinh_in_palace(palace: dict[str, Any] | None, star_name: str) -> str:
    """Đọc trạng thái miếu/vượng/đắc/bình/hãm của một sao trong cung.

    Trả ``MISSING`` ("thieu") khi: cung/sao không có, sao không nằm trong cung,
    thiếu ``saoDacTinh``/``dac_tinh``, hoặc mã trạng thái lạ. Không lấy trạng
    thái từ cung khác và không suy đoán.
    """
    if not isinstance(palace, dict) or not isinstance(star_name, str) or not star_name.strip():
        return MISSING
    target = normalize_star(star_name)
    if not target:
        return MISSING
    for star in _iter_stars(palace):
        ten = star.get("saoTen") or star.get("ten") or ""
        if not isinstance(ten, str) or normalize_star(ten) != target:
            continue
        value = star.get("saoDacTinh") if "saoDacTinh" in star else star.get("dac_tinh")
        return _normalize_dac_tinh(value)
    return MISSING
