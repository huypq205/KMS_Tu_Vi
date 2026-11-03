from pathlib import Path
import sqlite3
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine

from backend.app.db.models import Base
from backend.app.services.star_dossier import get_star_dossier, load_star_seed, SLOTS


@pytest.fixture
def corpus(tmp_path):
    path = tmp_path / 'corpus.db'
    engine = create_engine(f'sqlite:///{path}')
    Base.metadata.create_all(engine)
    with engine.begin() as c:
        from sqlalchemy import text
        for kid,book,content in [('K1','NPL','Vũ Khúc tại Ngọ cần xem điều kiện đồng cung.'),
                                 ('K2','DAU','Vũ Khúc có quan điểm riêng trong nguồn này.')]:
            c.execute(text('INSERT INTO knowledge_items (knowledge_id,book_code,text,subject,predicate,trust_tier,content_hash,version,updated_at) VALUES (:id,:book,:text,:subject,:predicate,1,:id,1,CURRENT_TIMESTAMP)'),
                      {'id':kid,'book':book,'text':content,'subject':'Vũ Khúc/Ngọ','predicate':'bản chất'})
            c.execute(text('INSERT INTO knowledge_pages(knowledge_id,pdf_page) VALUES (:id,12)'),{'id':kid})
    engine.dispose()
    return path


def test_canonical_slots_have_real_citations_and_separate_books(corpus):
    dossier = get_star_dossier('vu khuc', db_path=corpus, include_seeds=False)
    assert len(dossier['slots']) == 14
    entries = dossier['slots']['core_function']['entries']
    assert {e['book_code'] for e in entries} == {'NPL','DAU'}
    assert all(e['citations'][0]['pdf_page'] == 12 for e in entries)
    assert all(e['knowledge_id'] in {'K1','K2'} for e in entries)
    assert dossier['slots']['case_notes']['entries'] == []


def test_valid_star_without_data_keeps_empty_slots(tmp_path):
    dossier = get_star_dossier('thien ma', db_path=tmp_path/'absent.db', include_seeds=False)
    assert all(s['status'] == 'missing' and not s['entries'] for s in dossier['slots'].values())


def test_seed_never_overwrites_canonical_and_is_always_labeled(corpus, monkeypatch):
    monkeypatch.setenv('KMS_STAR_SEEDS_ENABLED','1')
    dossier = get_star_dossier('Vũ Khúc', db_path=corpus, include_seeds=True)
    assert dossier['slots']['core_function']['status'] == 'canonical'
    seed = dossier['slots']['yin_yang_five_element']
    assert seed['status'] == 'seed_unverified'
    assert 'chưa đối chiếu' in seed['message']
    assert all(e['status'] == 'seed_unverified' and e['source'] for e in seed['entries'])
    monkeypatch.setenv('KMS_STAR_SEEDS_ENABLED','0')
    assert get_star_dossier('Vũ Khúc', db_path=corpus, include_seeds=True)['slots']['yin_yang_five_element']['status'] == 'missing'


def test_all_twenty_seeds_pass_gate_and_unknown_star_fails():
    from backend.app.services.star_dossier import SEED_STARS
    assert len(SEED_STARS) == 20
    for name in SEED_STARS:
        assert load_star_seed(name)
    with pytest.raises(ValueError):
        get_star_dossier('../../not-a-star')


def test_dossier_api_aliases_and_404(corpus):
    from backend.app.main import app
    with patch('backend.app.api.governance.get_star_dossier', side_effect=lambda name, **kw: get_star_dossier(name, db_path=corpus, **kw)):
        client = TestClient(app)
        assert client.get('/api/stars/vu%20khuc/dossier').status_code == 200
        assert client.get('/api/v1/stars/not-a-star/dossier').status_code == 404


def test_dossier_alias_is_protected_and_database_error_is_explicit():
    from backend.app import main
    client = TestClient(main.app)
    with patch.object(main, '_API_KEY', 'secret'):
        assert client.get('/api/stars/vu%20khuc/dossier').status_code == 401
    with patch('backend.app.api.governance.get_star_dossier', side_effect=sqlite3.OperationalError('test')):
        assert client.get('/api/v1/stars/vu%20khuc/dossier').status_code == 503


def test_real_corpus_has_two_cited_dossiers():
    for name in ('Vũ Khúc','Cự Môn'):
        dossier = get_star_dossier(name, include_seeds=False)
        assert dossier['canonical_records'] > 0
        assert dossier['slots']['source_citations']['entries']


def test_streamlit_dossier_real_and_empty_views():
    from streamlit.testing.v1 import AppTest
    root = Path(__file__).resolve().parents[1]
    ui = AppTest.from_file(root/'frontend/star_dossier_ui.py', default_timeout=20).run()
    assert not ui.exception
    assert any('Hồ sơ sao' in title.value for title in ui.title)
    with patch('frontend.research_transport.api_get', return_value=get_star_dossier('Vũ Khúc')):
        ui.button(key='load_dossier').click().run()
    assert not ui.exception
    assert any('Nguồn' in x.value for x in ui.caption)
