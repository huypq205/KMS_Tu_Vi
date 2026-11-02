"""T3: từ điển loại chứng cứ, gắn kind cho fact và phản chứng bắt buộc."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

from backend.app.core.evidence_types import (
    EVIDENCE_LABELS,
    EVIDENCE_TYPE_VALUES,
    NO_COUNTER_EVIDENCE,
)
from backend.app.services import horoscope_interpreter as interpreter
from backend.app.services.horoscope_analysis import CHI_ORDER, build_star_facts
from backend.app.services.horoscope_interpreter import (
    check_evidence_labels,
    generate_mock_reading,
    interpret_horoscope,
    response_schema,
)
from backend.app.services.horoscope_rag_bridge import (
    format_context_for_prompt,
    retrieve_horoscope_context,
)
from tests.horoscope_support import gemini_response, make_features, valid_reading


def _reading(features: dict, fact_count: int = 3):
    context = retrieve_horoscope_context(features, 2)
    facts = build_star_facts(features, context)
    return valid_reading(facts, "2026 Bính Ngọ", fact_count=fact_count), facts, context


# 1. Từ điển và mapping kind ------------------------------------------------

def test_evidence_dictionary_has_ten_labels():
    assert len(EVIDENCE_TYPE_VALUES) == 10
    assert set(EVIDENCE_TYPE_VALUES) == set(EVIDENCE_LABELS)
    assert all(label.strip() for label in EVIDENCE_LABELS.values())


def test_facts_carry_kind_matching_palace_relation():
    features = make_features(2026)
    facts = build_star_facts(features, {})
    kinds = {fact["kind"] for fact in facts}
    assert {"toa_thu", "tam_hop", "xung_chieu", "giap_cung", "tu_hoa", "van_han"} <= kinds
    assert kinds <= set(EVIDENCE_TYPE_VALUES)

    tam = features["tam_phuong_tu_chinh_menh"]
    assert any(f["kind"] == "toa_thu" and f["dia_chi"] == tam["chinh_cung"] for f in facts)
    assert any(f["kind"] == "tam_hop" and f["dia_chi"] in tam["tam_hop"] for f in facts)
    assert any(f["kind"] == "xung_chieu" and f["dia_chi"] == tam["doi_cung"] for f in facts)

    index = CHI_ORDER.index(tam["chinh_cung"])
    neighbours = {CHI_ORDER[(index - 1) % 12], CHI_ORDER[(index + 1) % 12]}
    assert any(f["kind"] == "giap_cung" and f["dia_chi"] in neighbours for f in facts)


def test_tu_hoa_facts_and_annual_facts_get_their_own_kinds():
    features = make_features(2026)
    facts = build_star_facts(features, {})
    assert all(f["kind"] == "tu_hoa" for f in facts if "Tứ hóa" in f["roles"])
    assert all(f["kind"] == "tu_hoa" for f in facts if f["nhom"] == "luu_nien" and "(" in f["sao"])
    assert next(f for f in facts if f["sao"] == "Thái Tuế")["kind"] == "van_han"


# 2. Schema và prompt --------------------------------------------------------

def test_schema_requires_evidence_fields_and_enum():
    item = response_schema()["properties"]["luan_diem"]["items"]
    assert item["properties"]["loi_chung_cu"]["items"]["enum"] == list(EVIDENCE_TYPE_VALUES)
    assert item["properties"]["loi_chung_cu"]["minItems"] == 1
    assert "loi_chung_cu" in item["required"]
    assert "phan_chung" in item["required"]


def test_prompt_defines_evidence_types_and_counter_evidence():
    for value in EVIDENCE_TYPE_VALUES:
        assert value in interpreter.HOROSCOPE_SYSTEM_PROMPT
    assert NO_COUNTER_EVIDENCE in interpreter.HOROSCOPE_SYSTEM_PROMPT

    prompt = interpreter.build_horoscope_user_prompt(make_features(2026), "nguồn thử")
    assert "loi_chung_cu" in prompt
    assert "phan_chung" in prompt


# 3. Validator ---------------------------------------------------------------

def test_valid_reading_with_evidence_labels_passes():
    reading, facts, _ = _reading(make_features(2026))
    assert check_evidence_labels(reading, facts) is None


def test_missing_or_empty_support_labels_are_rejected():
    reading, facts, _ = _reading(make_features(2026))
    reading["luan_diem"][0].pop("loi_chung_cu")
    assert check_evidence_labels(reading, facts)

    reading, facts, _ = _reading(make_features(2026))
    reading["luan_diem"][0]["loi_chung_cu"] = []
    assert check_evidence_labels(reading, facts)


def test_unknown_evidence_label_is_rejected():
    reading, facts, _ = _reading(make_features(2026))
    reading["luan_diem"][0]["loi_chung_cu"] = ["khong_hop_le"]
    assert check_evidence_labels(reading, facts)


def test_support_label_must_match_cited_fact_kind():
    features = make_features(2026)
    reading, facts, _ = _reading(features)
    fact = next(f for f in facts if f["kind"] == "toa_thu" and f["source_refs"])
    point = reading["luan_diem"][0]
    point["fact_ids"] = [fact["fact_id"]]
    point["source_refs"] = [fact["source_refs"][0]]
    point["loi_chung_cu"] = ["van_han"]
    assert check_evidence_labels(reading, facts)

    point["loi_chung_cu"] = ["toa_thu", "suy_luan"]
    assert check_evidence_labels(reading, facts) is None


def test_empty_counter_evidence_is_rejected():
    reading, facts, _ = _reading(make_features(2026))
    reading["luan_diem"][0]["phan_chung"] = "   "
    assert check_evidence_labels(reading, facts)

    reading["luan_diem"][0]["phan_chung"] = NO_COUNTER_EVIDENCE
    assert check_evidence_labels(reading, facts) is None


# 4. Retry flow --------------------------------------------------------------

def test_missing_evidence_fields_retry_once_with_instruction():
    features = make_features(2026)
    reading, facts, context = _reading(features)
    bad = json.loads(json.dumps(reading))
    for point in bad["luan_diem"]:
        point.pop("loi_chung_cu")

    with patch.object(interpreter, "GEMINI_API_KEY", "test-key"), patch.object(
        interpreter, "HOROSCOPE_FALLBACK_MODELS", (),
    ), patch(
        "backend.app.services.horoscope_interpreter.requests.post",
        side_effect=[gemini_response(bad), gemini_response(reading)],
    ) as post:
        result = interpret_horoscope(features, format_context_for_prompt(context), "auto", context)

    assert post.call_count == 2
    retry_prompt = post.call_args_list[1].kwargs["json"]["contents"][0]["parts"][0]["text"]
    assert "loi_chung_cu" in retry_prompt and "phan_chung" in retry_prompt
    assert result["_generation"]["actual_provider"] == "gemini"
    assert check_evidence_labels(result, facts) is None


def test_missing_evidence_after_retry_falls_back_to_mock():
    features = make_features(2026)
    reading, _, context = _reading(features)
    bad = json.loads(json.dumps(reading))
    for point in bad["luan_diem"]:
        point["phan_chung"] = ""

    with patch.object(interpreter, "GEMINI_API_KEY", "test-key"), patch.object(
        interpreter, "HOROSCOPE_FALLBACK_MODELS", (),
    ), patch(
        "backend.app.services.horoscope_interpreter.requests.post",
        side_effect=[gemini_response(bad), gemini_response(bad)],
    ) as post:
        result = interpret_horoscope(features, format_context_for_prompt(context), "auto", context)

    assert post.call_count == 2
    assert result["_generation"]["is_mock"] is True
    assert result["_generation"]["reason"] == "invalid_response"


# 5. Mock reading ------------------------------------------------------------

def test_mock_reading_has_labeled_evidence_and_counter_evidence():
    features = make_features(2026)
    context = retrieve_horoscope_context(features, 2)
    facts = build_star_facts(features, context)
    reading = generate_mock_reading(features, context)

    assert reading["luan_diem"]
    assert all(point["loi_chung_cu"] for point in reading["luan_diem"])
    assert all(point["phan_chung"] for point in reading["luan_diem"])
    assert check_evidence_labels(reading, facts) is None


# 6. UI ----------------------------------------------------------------------

def test_ui_evidence_table_has_support_and_counter_columns():
    from frontend.horoscope_view import EVIDENCE_LABELS as UI_LABELS
    from frontend.horoscope_view import evidence_table

    assert set(UI_LABELS) == set(EVIDENCE_TYPE_VALUES)
    reading, facts, _ = _reading(make_features(2026))
    html = evidence_table(reading["luan_diem"], {f["fact_id"]: f for f in facts})
    assert "Dấu hiệu thuận" in html
    assert "Dấu hiệu nghịch" in html
    assert NO_COUNTER_EVIDENCE in html
    assert "evidence-chip" in html

    escaped = evidence_table([{
        "nhan_dinh": "<script>alert(1)</script>",
        "gioi_han": "Thử.",
        "muc_tin_cay": "yeu",
        "loi_chung_cu": ["suy_luan"],
        "phan_chung": NO_COUNTER_EVIDENCE,
        "fact_ids": [],
        "source_refs": [],
    }])
    assert "&lt;script&gt;" in escaped and "<script>" not in escaped


def test_ui_renders_evidence_table_from_mock_report():
    from streamlit.testing.v1 import AppTest
    from backend.app.main import horoscope_read
    from tests.horoscope_support import make_request

    app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20,
    ).run()
    payload = horoscope_read(make_request(provider="mock"))
    payload["ho_ten"] = "Lê An"
    response = Mock()
    response.iter_lines.return_value = iter([
        json.dumps({"event": "prepared", "report": payload}),
        json.dumps({"event": "result", "report": payload}),
    ])
    with patch("requests.post", return_value=response):
        app.sidebar.button[0].click().run()
    assert not app.exception
    rendered = " ".join(item.value for item in app.markdown)
    assert "Dấu hiệu thuận" in rendered
    assert "Dấu hiệu nghịch" in rendered
    assert "evidence-chip" in rendered
