"""T5: distinct table provenance, vendor compatibility and consistent school selection."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest
import yaml

from backend.app.services import tu_hoa_tables as tables
from backend.app.services.horoscope_analysis import build_star_facts
from backend.app.services.horoscope_annual import compute_luu_nien
from backend.app.services.horoscope_features import (
    generate_raw_horoscope, extract_horoscope_features,
    lapDiaBan, diaBanClass,
)
from backend.app.services.horoscope_interpreter import build_horoscope_user_prompt
from backend.app.services.horoscope_ask import build_ask_user_prompt
from backend.app.schemas.horoscope import HoroscopeAskRequest
from scripts.compare_tu_hoa_tables import compare_tables, read_vendor_table
from tests.horoscope_support import TU_HOA_TABLE_FIELDS


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def default_table(monkeypatch):
    monkeypatch.delenv('KMS_TU_HOA_TABLE', raising=False)


def natal(year):
    return generate_raw_horoscope(1, 1, year, 1, 1, False)


def star_palace(raw, star_id):
    return next(p['cung_so'] for p in raw['thap_ni_cung']
                if any(s['saoID'] == star_id for s in p['saos']))


def test_all_ten_vendor_rows_match_default_config():
    table = tables.get_tu_hoa_table()
    assert table['id'] == 'lasotuvi'
    assert table['by_can'] == read_vendor_table()
    assert len(table['by_can']) == 10
    assert all(set(row) == set(tables.TU_HOA_CODES) for row in table['by_can'].values())


def test_compare_keeps_exactly_three_documented_differences():
    report = compare_tables()
    assert report['vendor_config_matches'] is True
    assert {(d['can'], d['code'], d['vendor'], d['reference']) for d in report['differences']} == {
        ('Canh', 'HOA_KHOA', 'Thiên Đồng', 'Thái Âm'),
        ('Canh', 'HOA_KY', 'Thái Âm', 'Thiên Đồng'),
        ('Nhâm', 'HOA_KHOA', 'Thiên Phủ', 'Tả Phụ'),
    }


@pytest.mark.parametrize('year', range(1984, 1994))
def test_default_natal_positions_match_unmodified_vendor(year):
    vendor = lapDiaBan(diaBanClass, 1, 1, year, 1, 1, False, 7)
    expected = {s['saoID']: p.cungSo for p in vendor.thapNhiCung[1:]
                for s in p.cungSao if s['saoID'] in tables.TU_HOA_STAR_IDS.values()}
    raw = natal(year)
    assert {sid: star_palace(raw, sid) for sid in tables.TU_HOA_STAR_IDS.values()} == expected


@pytest.mark.parametrize('year,khoa_parent,ky_parent', [(1990, 8, 3), (1992, 61, 4)])
def test_selected_table_changes_natal_and_annual_consistently(monkeypatch, year, khoa_parent, ky_parent):
    monkeypatch.setenv('KMS_TU_HOA_TABLE', 'hung_ngm_reference')
    raw = natal(year)
    assert star_palace(raw, 92) == star_palace(raw, khoa_parent)
    assert star_palace(raw, 95) == star_palace(raw, ky_parent)
    features = extract_horoscope_features(raw, year)
    info = features['thong_tin_co_ban']['tu_hoa_table']
    assert set(info) == TU_HOA_TABLE_FIELDS
    assert info['id'] == 'hung_ngm_reference'
    assert info['verification_status'] == 'reference_unverified'
    annual = features['luu_nien']
    assert annual['tu_hoa_table'] == info
    khoa = next(x for x in annual['luu_tu_hoa'] if x['code'] == 'HOA_KHOA')
    assert khoa['cung_so'] == star_palace(raw, khoa_parent)
    natal_khoa = next(x for x in features['tu_hoa'] if x['code'] == 'HOA_KHOA')
    assert natal_khoa['ten_sao'] == khoa['ten_sao']
    assert next(p.cungSo for p in raw['db'].thapNhiCung[1:]
                if any(s['saoID'] == 92 for s in p.cungSao)) == khoa['cung_so']
    parent_name = khoa['ten_sao']
    facts = build_star_facts(features)
    parent_fact = next(f for f in facts if tables.normalize_star(f['sao']) == tables.normalize_star(parent_name)
                       and f['nhom'] != 'luu_nien')
    assert 'Tứ hóa' in parent_fact['roles']


def test_raw_metadata_keeps_features_on_original_table_after_env_change(monkeypatch):
    raw = natal(1992)
    monkeypatch.setenv('KMS_TU_HOA_TABLE', 'hung_ngm_reference')
    features = extract_horoscope_features(raw, 1992)
    assert features['thong_tin_co_ban']['tu_hoa_table']['id'] == 'lasotuvi'
    assert features['luu_nien']['tu_hoa_table']['id'] == 'lasotuvi'
    khoa = next(x for x in features['luu_nien']['luu_tu_hoa'] if x['code'] == 'HOA_KHOA')
    assert khoa['ten_sao'] == 'Thiên Phủ'
    facts = build_star_facts(features)
    phu = next(f for f in facts if tables.normalize_star(f['sao']) == 'thien phu' and f['nhom'] != 'luu_nien')
    assert 'Tứ hóa' in phu['roles']


def test_reference_finds_ta_phu_despite_vendor_spelling_and_preserves_snapshot(monkeypatch):
    default = natal(1992)
    before = deepcopy(default['thap_ni_cung'])
    monkeypatch.setenv('KMS_TU_HOA_TABLE', 'hung_ngm_reference')
    reference = natal(1992)
    annual = compute_luu_nien(reference['thap_ni_cung'], 1992)
    khoa = next(x for x in annual['luu_tu_hoa'] if x['code'] == 'HOA_KHOA')
    assert khoa['ten_sao'] == 'Tả Phụ'
    assert khoa['cung_so'] == star_palace(reference, 61)
    assert default['thap_ni_cung'] == before
    for sid in tables.TU_HOA_STAR_IDS.values():
        assert sum(s['saoID'] == sid for p in reference['thap_ni_cung'] for s in p['saos']) == 1


def test_prompt_ask_and_ui_identify_selected_table(monkeypatch):
    from frontend.horoscope_view import annual_panel, tu_hoa_table_caption
    monkeypatch.setenv('KMS_TU_HOA_TABLE', 'hung_ngm_reference')
    features = extract_horoscope_features(natal(1992), 1992)
    info = features['thong_tin_co_ban']['tu_hoa_table']
    assert info['school'] in build_horoscope_user_prompt(features, '')
    ask = HoroscopeAskRequest(ngay=1, thang=1, nam=1992, chi_gio=1, question='Tứ Hóa ở đâu?', provider='mock')
    assert info['school'] in build_ask_user_prompt(features, [], [], ask, 'van_han')
    assert info['school'] in tu_hoa_table_caption(info)
    assert info['school'] in annual_panel(features['nam_xem'], features['luu_nien'])
    assert 'chưa đối chiếu' in tu_hoa_table_caption(info)
    assert tu_hoa_table_caption({}) == ''


def test_school_is_escaped_in_ui():
    from frontend.horoscope_view import annual_panel
    html = annual_panel({}, {'tu_hoa_table': {'school': '<script>bad()</script>'}})
    assert '<script>' not in html
    assert '&lt;script&gt;' in html


@pytest.mark.parametrize('table_id', ['lasotuvi', 'hung_ngm_reference'])
def test_streamlit_displays_the_table_in_the_report(monkeypatch, table_id):
    from streamlit.testing.v1 import AppTest
    from tests.test_horoscope_frontend import _submit_mock_report
    monkeypatch.setenv('KMS_TU_HOA_TABLE', table_id)
    app = AppTest.from_file(ROOT / 'frontend/horoscope_ui.py', default_timeout=20).run()
    payload = _submit_mock_report(app, target_year=2026)
    info = payload['thong_tin_co_ban']['tu_hoa_table']
    assert info['id'] == table_id
    assert any(info['school'] in item.value for item in app.markdown)


@pytest.mark.parametrize('change', ['missing_can', 'bad_star', 'missing_school', 'short_row', 'bad_default'])
def test_invalid_configuration_is_rejected(tmp_path, change):
    config = yaml.safe_load(tables.CONFIG_PATH.read_text(encoding='utf-8'))
    table = config['tables']['lasotuvi']
    if change == 'missing_can':
        del table['by_can']['Giáp']
    elif change == 'bad_star':
        table['by_can']['Giáp'][0] = 'Sao không tồn tại'
    elif change == 'missing_school':
        del table['school']
    elif change == 'short_row':
        table['by_can']['Giáp'].pop()
    else:
        config['default_table'] = 'missing'
    p = tmp_path / 'tables.yaml'
    p.write_text(yaml.safe_dump(config, allow_unicode=True), encoding='utf-8')
    with pytest.raises(ValueError):
        tables.load_tu_hoa_config(p)


def test_unknown_table_is_not_silently_replaced(monkeypatch):
    monkeypatch.setenv('KMS_TU_HOA_TABLE', 'typo')
    with pytest.raises(ValueError, match='typo'):
        natal(1992)


def test_crosscheck_can_explicitly_keep_vendor_table(monkeypatch):
    monkeypatch.setenv('KMS_TU_HOA_TABLE', 'hung_ngm_reference')
    raw = generate_raw_horoscope(1, 1, 1992, 1, 1, False, tu_hoa_table_id='lasotuvi')
    assert raw['tu_hoa_table']['id'] == 'lasotuvi'
    assert star_palace(raw, 92) == star_palace(raw, 7)


def test_table_metadata_changes_cache_key(monkeypatch):
    from backend.app.services.horoscope_service import read_horoscope
    from tests.horoscope_support import make_request
    request = make_request(target_year=2026, provider='auto')
    with patch('backend.app.services.horoscope_service.horoscope_cache.lookup') as lookup:
        lookup.return_value = {'reading': {}, 'generation': {}}
        first = read_horoscope(request)
        first_key = lookup.call_args.args[0]
        monkeypatch.setenv('KMS_TU_HOA_TABLE', 'hung_ngm_reference')
        second = read_horoscope(request)
        second_key = lookup.call_args.args[0]
    assert first['status'] == second['status'] == 'ok'
    assert first_key != second_key


def test_cli_runs_from_another_directory(tmp_path):
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/compare_tu_hoa_tables.py'), '--json'],
                            cwd=tmp_path, capture_output=True, text=True, encoding='utf-8', check=True)
    report = json.loads(result.stdout)
    assert report['vendor_config_matches']
    assert len(report['differences']) == 3
