"""T4: independent, frozen reference vectors; never derive expectations from vendor.

Known source disagreements are strict xfails, with a separate observation test
so a new vendor regression cannot be hidden by an existing xfail.
"""
from __future__ import annotations

import json
from pathlib import Path
import unicodedata

import pytest

from backend.app.services.horoscope_features import generate_raw_horoscope


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "an_sao_vectors.json"
DATA = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
VECTORS = DATA["vectors"]
ISSUES = DATA["issues"]
BRANCHES = DATA["branches"]
REFERENCE_STARS = {field.removeprefix("star:") for v in VECTORS for field in v["expected"] if field.startswith("star:")}


def normalized(value):
    value = unicodedata.normalize("NFC", value).casefold().replace("tỵ", "tị")
    return {"tả phù": "tả phụ", "thiên hỷ": "thiên hỉ"}.get(value, value)


@pytest.fixture(scope="module", params=VECTORS, ids=lambda v: v["id"])
def chart(request):
    vector = request.param
    return vector, generate_raw_horoscope(**vector["birth"], tu_hoa_table_id="lasotuvi")


def observations(raw):
    palaces = raw["thap_ni_cung"]
    stars = {}
    for palace in palaces:
        for star in palace["saos"]:
            name = normalized(star["saoTen"])
            if name not in REFERENCE_STARS:
                continue
            assert name not in stars, f"Duplicate star: {name}"
            stars[name] = BRANCHES[palace["cung_so"] - 1]
    by_branch = {normalized(p["chuan_ten"]): p for p in palaces}
    birth_branch = BRANCHES.index(normalized(raw["chi_nam"]).capitalize())
    # cungTieuHan labels the annual branch, not a numerical age.
    minor = [
        next(BRANCHES[p["cung_so"] - 1] for p in palaces
             if normalized(p["tieu_han_chi"]) == normalized(BRANCHES[(birth_branch + age) % 12]))
        for age in range(12)
    ]
    result = {
        "can_nam": raw["can_nam"], "chi_nam": normalized(raw["chi_nam"]).capitalize(),
        "cuc": raw["tu_cuc"],
        "menh": BRANCHES[raw["cung_menh_so"] - 1],
        "than": BRANCHES[raw["cung_than_so"] - 1],
        "tuan": [BRANCHES[p["cung_so"] - 1] for p in palaces if p["tuan_trung"]],
        "triet": [BRANCHES[p["cung_so"] - 1] for p in palaces if p["triet_lo"]],
        "dai_han": {b: by_branch[normalized(b)]["tu_dai_han"] for b in BRANCHES},
        "tieu_han": minor,
    }
    result.update({f"star:{name}": branch for name, branch in stars.items()})
    return result


CASES = []
KNOWN = []
for vector in VECTORS:
    for field, expected in vector["expected"].items():
        discrepancy = vector.get("discrepancies", {}).get(field)
        marks = ()
        if discrepancy:
            issue = ISSUES[discrepancy["issue"]]
            marks = pytest.mark.xfail(strict=True, reason=f"{discrepancy['issue']}: {issue['url']}")
            KNOWN.append(pytest.param(vector, field, discrepancy, id=f"{vector['id']}-{field}"))
        CASES.append(pytest.param(vector, field, expected, marks=marks, id=f"{vector['id']}-{field}"))


@pytest.fixture(scope="module")
def observed():
    # Only actual charts are cached here. Golden values remain static JSON.
    return {v["id"]: observations(generate_raw_horoscope(**v["birth"], tu_hoa_table_id="lasotuvi")) for v in VECTORS}


@pytest.mark.parametrize("vector,field,expected", CASES)
def test_reference_position(vector, field, expected, observed):
    assert observed[vector["id"]][field] == expected


@pytest.mark.parametrize("vector,field,discrepancy", KNOWN)
def test_known_discrepancy_has_not_changed(vector, field, discrepancy, observed):
    assert discrepancy["observed"] != vector["expected"][field]
    assert observed[vector["id"]][field] == discrepancy["observed"], (
        "Previously recorded mismatch changed; review against KMS books and update issue."
    )


def test_reference_fixture_coverage():
    assert len(VECTORS) >= 30
    assert len({v["id"] for v in VECTORS}) == len(VECTORS)
    assert {v["expected"]["cuc"] for v in VECTORS} == {2, 3, 4, 5, 6}
    assert {v["expected"]["can_nam"] for v in VECTORS} == set(DATA["stems"])
    assert {v["expected"]["chi_nam"] for v in VECTORS} == set(BRANCHES)
    assert len({tuple(v["expected"]["tuan"]) for v in VECTORS}) == 6
    assert {v["birth"]["nn"] % 2 for v in VECTORS} == {0, 1}
    assert {(v["birth"]["tt"], v["birth"]["chi_gio"]) for v in VECTORS} >= {
        (month, hour) for month in range(1, 13) for hour in (1, 12)
    }
    assert {(v["birth"]["nnnn"] % 2, v["birth"]["gioi_tinh"]) for v in VECTORS} >= {
        (parity, sex) for parity in (0, 1) for sex in (1, 2)
    }
    for vector in VECTORS:
        assert not vector["birth"]["duong_lich"], "Reference uses lunar birth inputs."
        assert vector["source_sections"]
        assert {"tuan", "triet", "dai_han", "tieu_han"} <= vector["expected"].keys()
        for field, discrepancy in vector.get("discrepancies", {}).items():
            assert field in vector["expected"]
            issue = ISSUES[discrepancy["issue"]]
            if issue["publication_status"] == "pending_approval":
                local_issue = Path(__file__).resolve().parents[1] / issue["url"].split("#")[0]
                assert local_issue.is_file()
            else:
                assert issue["url"].startswith("https://github.com/huypq205/KMS_Tu_Vi/issues/")


def test_chart_contains_each_principal_star_once(chart):
    _, raw = chart
    principal = [s["saoID"] for p in raw["thap_ni_cung"] for s in p["saos"] if s["saoLoai"] == 1]
    assert sorted(principal) == list(range(1, 15))


def test_two_constellations_follow_reference_offsets(chart):
    """§6 relative positions remain checkable when §5 has no precise day table."""
    _, raw = chart
    actual = observations(raw)
    positions = {name: BRANCHES.index(branch) for name, branch in actual.items() if name.startswith("star:")}
    for anchor, offsets in (
        ("tử vi", {"thiên cơ": -1, "thái dương": -3, "vũ khúc": -4, "thiên đồng": -5, "liêm trinh": 4}),
        ("thiên phủ", {"thái âm": 1, "tham lang": 2, "cự môn": 3, "thiên tướng": 4, "thiên lương": 5, "thất sát": 6, "phá quân": 10}),
    ):
        for name, offset in offsets.items():
            assert positions[f"star:{name}"] == (positions[f"star:{anchor}"] + offset) % 12
    assert positions["star:thiên phủ"] == (4 - positions["star:tử vi"]) % 12
