"""Regression cases from lecturer feedback: specificity, yearly scope and bounded AI."""
import json
import sqlite3
from unittest.mock import Mock, patch

import pytest
import requests

from backend.app.services import horoscope_features as features
from backend.app.services import horoscope_interpreter as interpreter
from backend.app.services import horoscope_rag_bridge as bridge


def chart(year=2026, birth=(15, 8, 1995, 5, 1)):
    return features.extract_horoscope_features(features.generate_raw_horoscope(*birth), year)


def test_catalog_ids_use_actual_vendor_and_keep_adverse_star_conditions():
    from lasotuvi import Sao
    stars = [vars(getattr(Sao, name)).copy() for name in
             ['saoTaPhu', 'saoHuuBat', 'saoThienMa', 'saoLocTon', 'saoHoaKy', 'saoDiaKhong']]
    result = features.categorize_stars_in_palace(stars)
    assert {61, 62, 98, 27} <= {s['id'] for s in result['cat_tinh']}
    assert 95 in {s['id'] for s in result['risk_stars']}
    assert features.LUC_SAT_TINH_IDS[53] == Sao.saoDiaKhong.saoTen


def test_birth_year_and_lunar_boundary_are_preserved_in_prompt():
    f = chart()
    assert f['thong_tin_co_ban']['nam_sinh'] == 1995
    assert '(Năm 1995)' in interpreter.build_horoscope_user_prompt(f, '')
    early = chart(birth=(1, 1, 1990, 1, 1))
    assert early['thong_tin_co_ban']['nam_sinh_am'] == 1989
    assert early['nam_xem']['tuoi_am'] == 38


def test_two_years_inside_one_decade_select_different_actual_minor_palaces():
    a, b = chart(2026), chart(2027)
    assert a['dai_han_hien_tai']['cung_so'] == b['dai_han_hien_tai']['cung_so']
    assert a['nam_xem']['tieu_han']['cung_so'] != b['nam_xem']['tieu_han']['cung_so']
    assert a['nam_xem']['can_chi'] == 'Bính Ngọ'
    assert b['nam_xem']['can_chi'] == 'Đinh Mùi'
    assert len(a['palaces']) == 12
    assert all('tuan_trung' in p and 'risk_stars' in p for p in a['palaces'])
    assert interpreter.generate_mock_reading(a)['van_han_hien_tai'] != interpreter.generate_mock_reading(b)['van_han_hien_tai']


@pytest.fixture
def corpus(tmp_path):
    path = tmp_path / 'sources.db'
    with sqlite3.connect(path) as conn:
        conn.executescript('''
            CREATE TABLE chunks (chunk_id TEXT, book_code TEXT, chapter TEXT, chunk_text TEXT,
              part_number TEXT, pdf_page_start INTEGER, pdf_page_end INTEGER, trust_tier INTEGER);
            CREATE VIRTUAL TABLE chunks_fts USING fts5(chunk_id UNINDEXED, text);
        ''')
        rows = [('correct', 'Vũ khúc Thiên tướng tại cung Quan lộc', 1),
                ('wrong', 'Văn khúc tại cung Quan lộc', 1),
                ('other_pair', 'Vũ khúc Phá quân tại cung Quan lộc', 1),
                ('excluded', 'Vũ khúc Thiên tướng tại cung Quan lộc', 9)]
        for cid, text, tier in rows:
            conn.execute('INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (cid, 'NPL', '', text, None, 1, 1, tier))
            conn.execute('INSERT INTO chunks_fts VALUES (?, ?)', (cid, bridge.strip_accents(text).lower()))
    return path


def test_retrieval_requires_named_stars_not_shared_syllables_and_excludes_tier9(corpus):
    hits = bridge.search_fts_sqlite('Vũ khúc Thiên tướng cung Quan lộc', db_path=corpus)
    assert [h['chunk_id'] for h in hits] == ['correct']
    assert not bridge.search_fts_sqlite('Địa không Thiên tướng', db_path=corpus)
    assert not bridge.search_fts_sqlite('Vũ khúc Triệt', db_path=corpus)


def test_retrieval_evaluates_later_specific_queries_instead_of_stopping_at_first_hits():
    f = chart()
    with patch.object(bridge, 'search_fts_sqlite', return_value=[]) as search:
        bridge.retrieve_horoscope_context(f)
    called = [c.args[0] for c in search.call_args_list]
    for query in bridge.generate_horoscope_queries(f)['ban_menh']:
        assert query in called
    assert any('Kình dương' in q for q in called)


def test_local_report_changes_with_palace_stars_instead_of_constant_finance_relationships():
    a, b = chart(), chart(birth=(20, 3, 2000, 8, 2))
    ra, rb = interpreter.generate_mock_reading(a), interpreter.generate_mock_reading(b)
    assert ra['tai_chinh'] != rb['tai_chinh']
    assert ra['tinh_cam'] != rb['tinh_cam']


def test_gemini_busy_is_one_bounded_attempt_with_explicit_reason():
    response = Mock(status_code=503)
    response.json.return_value = {'error': {'message': 'busy'}}
    with patch.object(interpreter, 'GEMINI_API_KEY', 'test-secret'), \
            patch.object(interpreter, 'HOROSCOPE_FALLBACK_MODELS', ()), \
            patch('requests.post', return_value=response) as post:
        result = interpreter.interpret_horoscope(chart(), '', provider='auto')
    assert post.call_count == 1
    assert post.call_args.kwargs['timeout'][1] <= 60
    assert result['_generation']['reason'] == 'busy'
    assert result['_generation']['attempts'] == 1
    assert 'test-secret' not in json.dumps(result)


@pytest.mark.parametrize('primary_status', [503, 429])
def test_overloaded_primary_model_falls_back_before_mock(primary_status):
    from backend.app.services.horoscope_analysis import build_star_facts
    f = chart()
    context = bridge.retrieve_horoscope_context(f)
    facts = build_star_facts(f, context)
    fact = next(s for s in facts if s['source_refs'])
    reading = interpreter.generate_mock_reading(f)
    reading['luan_diem'] = [{'nhan_dinh': 'Một nhận định có điều kiện.', 'gioi_han': 'Cần kiểm tra tổ hợp.',
                             'muc_tin_cay': 'trung_binh', 'loai_ket_luan': 'cau_truc',
                             'loi_chung_cu': [fact.get('kind', 'toa_thu')],
                             'phan_chung': 'Không ghi nhận phản chứng trong nguồn đã lấy.',
                             'fact_ids': [fact['fact_id']], 'source_refs': fact['source_refs'][:1]}]
    unavailable = Mock(status_code=primary_status)
    unavailable.json.return_value = {'error': {'message': 'unavailable'}}
    ok = Mock(status_code=200)
    ok.json.return_value = {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': json.dumps(reading)}]}}]}
    with patch.object(interpreter, 'GEMINI_API_KEY', 'test-secret'), \
            patch.object(interpreter, 'HOROSCOPE_FALLBACK_MODELS', ('gemini-fallback',)), \
            patch.object(interpreter, 'check_specificity', return_value=None), \
            patch('requests.post', side_effect=[unavailable, ok]) as post:
        actual = interpreter.interpret_horoscope(f, bridge.format_context_for_prompt(context), 'auto', context)
    assert actual['_generation']['actual_provider'] == 'gemini'
    assert actual['_generation']['model'] == 'gemini-fallback'
    assert post.call_count == 2
    assert 'gemini-fallback' in post.call_args_list[1].args[0]


def test_forced_gemini_does_not_silently_substitute_mock():
    with patch.object(interpreter, 'GEMINI_API_KEY', 'test-secret'), patch('requests.post', side_effect=requests.Timeout):
        with pytest.raises(interpreter.HoroscopeGenerationError) as error:
            interpreter.interpret_horoscope(chart(), '', provider='gemini')
    assert error.value.code == 'timeout'


def test_complete_ai_response_requires_real_fact_and_source_links():
    from backend.app.services.horoscope_analysis import build_star_facts
    f = chart()
    context = bridge.retrieve_horoscope_context(f)
    facts = build_star_facts(f, context)
    fact = next(s for s in facts if s['source_refs'])
    reading = interpreter.generate_mock_reading(f)
    reading['luan_diem'] = [{'nhan_dinh': 'Một nhận định có điều kiện.', 'gioi_han': 'Cần kiểm tra tổ hợp.',
                             'muc_tin_cay': 'trung_binh', 'loai_ket_luan': 'cau_truc',
                             'loi_chung_cu': [fact.get('kind', 'toa_thu')],
                             'phan_chung': 'Không ghi nhận phản chứng trong nguồn đã lấy.',
                             'fact_ids': [fact['fact_id']], 'source_refs': fact['source_refs'][:1]}]
    interpreter.validate_reading(reading, facts, context)
    response = Mock(status_code=200)
    response.json.return_value = {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': json.dumps(reading)}]}}]}
    with patch.object(interpreter, 'GEMINI_API_KEY', 'test-secret'), patch('requests.post', return_value=response):
        actual = interpreter.interpret_horoscope(f, bridge.format_context_for_prompt(context), 'gemini', context)
    assert actual['_generation']['is_mock'] is False
    reading['luan_diem'][0]['source_refs'] = [9999]
    with pytest.raises(interpreter.HoroscopeGenerationError):
        interpreter.validate_reading(reading, facts, context)
    with pytest.raises(interpreter.HoroscopeGenerationError):
        interpreter.validate_reading({'tieu_de': 'JSON hợp lệ nhưng thiếu bài'}, facts, context)


def test_stream_error_is_terminal_and_does_not_claim_ai_success():
    from backend.app.services.horoscope_service import reading_events
    from backend.app.schemas.horoscope import HoroscopeRequest
    req = HoroscopeRequest(ngay=15, thang=8, nam=1995, chi_gio=5, provider='gemini')
    with patch('backend.app.services.horoscope_service.interpret_horoscope',
               side_effect=interpreter.HoroscopeGenerationError('busy')):
        events = list(reading_events(req))
    assert events[-1]['event'] == 'error'
    assert events[-1]['code'] == 'busy'
    assert not any(e['event'] == 'result' for e in events)


def test_stream_sends_heartbeat_during_generation_without_another_ai_attempt():
    import time
    from backend.app.services.horoscope_service import reading_events
    from backend.app.schemas.horoscope import HoroscopeRequest
    req = HoroscopeRequest(ngay=15, thang=8, nam=1995, chi_gio=5, provider='mock')
    def slow_local(*args):
        time.sleep(1.1)
        return {'_generation': {'actual_provider': 'mock', 'is_mock': True, 'reason': 'requested'}}
    with patch('backend.app.services.horoscope_service.interpret_horoscope', side_effect=slow_local) as call:
        events = list(reading_events(req))
    beats = [e for e in events if e.get('stage') == 'generation']
    assert len(beats) >= 2
    assert beats[-1]['elapsed_ms'] > beats[0]['elapsed_ms']
    assert call.call_count == 1


def test_twelve_years_cover_twelve_vendor_minor_palaces_without_rean_natal_stars():
    raw = features.generate_raw_horoscope(15, 8, 1995, 5, 1)
    years = [features.extract_horoscope_features(raw, y) for y in range(2026, 2038)]
    assert len({f['nam_xem']['tieu_han']['cung_so'] for f in years}) == 12
    assert years[0]['palaces'] == years[-1]['palaces']


def test_disconnected_progress_stream_cannot_replace_previous_report():
    from frontend.horoscope_transport import reading_events
    response = Mock()
    response.iter_lines.return_value = [b'{"event":"progress","message":"waiting"}']
    with patch('requests.post', return_value=response):
        with pytest.raises(ValueError, match='trước khi hoàn tất'):
            list(reading_events('http://example.test', {}))
    response.close.assert_called_once()


def test_stream_returns_chart_year_and_sources_before_ai_and_has_stage_timings():
    from fastapi.testclient import TestClient
    from backend.app.main import app
    with TestClient(app) as client:
        response = client.post('/api/v1/horoscope/read-stream', json={
            'ngay': 15, 'thang': 8, 'nam': 1995, 'chi_gio': 5, 'provider': 'mock', 'target_year': 2027})
    assert response.status_code == 200
    events = [json.loads(line) for line in response.text.splitlines()]
    kinds = [e['event'] for e in events]
    assert kinds.index('prepared') < kinds.index('result')
    report = next(e['report'] for e in events if e['event'] == 'prepared')
    assert len(report['la_so']['thap_ni_cung']) == 12
    assert report['annual']['year'] == 2027
    assert report['star_analysis']
    final = events[-1]['report']
    assert final['status'] == 'ok'
    assert all(v >= 0 for v in final['meta']['timings_ms'].values())
    refs = {c['ref_id'] for c in final['citations']}
    assert all(set(f['source_refs']) <= refs for f in final['star_analysis'])
