"""P0: schema fact thống nhất giữa backend và UI (chống KeyError 'dac_tinh')."""
from __future__ import annotations

import pytest

from backend.app.services.horoscope_analysis import build_star_facts
from backend.app.services.horoscope_annual import TU_HOA_BY_CAN
from backend.app.services.horoscope_service import read_horoscope
from tests.horoscope_support import make_features, make_request

REQUIRED = {
    "fact_id", "sao", "cung", "dia_chi", "dac_tinh", "nhom", "roles",
    "tuan", "triet", "ngu_hanh", "kind", "source_status", "source_refs",
}


@pytest.fixture(scope="module")
def report() -> dict:
    return read_horoscope(make_request())


def test_fact_has_every_key_the_ui_reads(report):
    facts = report["star_analysis"]
    assert facts
    for fact in facts:
        assert REQUIRED <= set(fact.keys())
        assert isinstance(fact["fact_id"], str)
        assert isinstance(fact["roles"], list)
        assert isinstance(fact["tuan"], bool)
        assert isinstance(fact["triet"], bool)
    natal = [f for f in facts if f["nhom"] in {"chinh_tinh", "cat_tinh"}]
    assert all(f["dac_tinh"] in {"M", "V", "Đ", "B", "H", "—"} for f in natal)


def test_tuan_triet_flags_come_from_the_palace(report):
    features = report["palaces"]
    assert any(p["tuan_trung"] for p in features), "lá số mẫu cần có ít nhất một cung Tuần"
    by_name = {p["ten"]: p for p in features}
    for fact in report["star_analysis"]:
        palace = by_name[fact["cung"]]
        assert fact["tuan"] is bool(palace["tuan_trung"])
        assert fact["triet"] is bool(palace["triet_lo"])


def test_stars_bearing_tu_hoa_have_the_role(report):
    features = make_features()
    can = features["thong_tin_co_ban"]["can_chi_nam"].split(" ")[0]
    hoa_stars = {name.casefold() for name in TU_HOA_BY_CAN[can].values()}
    hits = [f for f in report["star_analysis"] if f["sao"].casefold() in hoa_stars]
    assert len(hits) == 4, "lá số Ất Hợi phải có đúng 4 sao gốc mang Tứ Hóa"
    for fact in hits:
        assert "Tứ hóa" in fact["roles"]


def test_build_star_facts_without_context_is_still_complete():
    facts = build_star_facts(make_features(2026), {})
    assert facts
    assert all(REQUIRED <= set(f.keys()) for f in facts)
