"""T8: a frozen forecast must survive failed predictions and later revisions."""
import json
from pathlib import Path
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.app.db.models import Base
from backend.app.schemas.case_validation import CaseInput, PredictionInput, EventInput
from backend.app.services.case_validation import (
    create_case, add_prediction, lock_prediction, revise_prediction,
    reveal_event, get_case, statistics, install_immutability,
)


def snapshot():
    return {'palaces': [{'cung_so':i,'stars':['Vũ Khúc'] if i==1 else []} for i in range(1,13)],
            'facts':[{'fact_id':'F1','text':'Vũ Khúc tại cung 1'}], 'tu_hoa_table':'lasotuvi'}


@pytest.fixture
def session(tmp_path):
    engine=create_engine('sqlite:///'+str(tmp_path/'cases.db'))
    Base.metadata.create_all(engine)
    install_immutability(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def make_case(session, number=1):
    cid=f'TV-2026-{number:03}'
    create_case(session,CaseInput(case_id=cid,chart_snapshot=snapshot(),input_confidence='A'))
    return cid


def prediction(**kw):
    return PredictionInput(noi_dung='Cần theo dõi thay đổi công việc trong năm.',
       khoa_thoi_gian='2027', muc_tin_cay='trung_binh', chung_cu_ids=['F1'],
       phan_chung='Chưa có lưu nguyệt.', **kw)


def test_lock_revision_and_failed_result_are_retained(session):
    cid=make_case(session)
    first=add_prediction(session,cid,prediction())
    lock_prediction(session,first['prediction_id'])
    with pytest.raises(ValueError,match='khóa'):
        lock_prediction(session,first['prediction_id'])
    second=revise_prediction(session,first['prediction_id'],prediction(), 'Bổ sung điều kiện')
    assert second['supersedes']==first['prediction_id'] and second['locked_at'] is None
    reveal_event(session,cid,EventInput(prediction_id=first['prediction_id'],year=2027,
       category='career',mo_ta='Không có thay đổi như dự đoán.',prediction_result='no_match'))
    case=get_case(session,cid)
    assert len(case['predictions'])==2
    assert case['events'][0]['prediction_result']=='no_match'
    assert case['predictions'][0]['noi_dung']==first['noi_dung']


def test_database_blocks_locked_updates_deletes_and_snapshot_edits(session):
    cid=make_case(session)
    p=add_prediction(session,cid,prediction()); lock_prediction(session,p['prediction_id'])
    session.commit()
    for statement,params in [
      ('UPDATE predictions SET noi_dung=:v WHERE prediction_id=:id',{'v':'changed','id':p['prediction_id']}),
      ('DELETE FROM predictions WHERE prediction_id=:id',{'id':p['prediction_id']}),
      ('UPDATE validation_cases SET chart_snapshot=:v WHERE case_id=:id',{'v':'{}','id':cid}),
    ]:
        with pytest.raises(IntegrityError): session.execute(text(statement),params)
        session.rollback()


@pytest.mark.parametrize('field,value',[('category','invalid'),('prediction_result','success')])
def test_event_enums(field,value):
    data=dict(prediction_id='p',year=2027,category='career',mo_ta='Sự kiện',prediction_result='clear_match')
    data[field]=value
    with pytest.raises(ValueError): EventInput(**data)


def test_anonymity_ids_evidence_and_confidence_are_validated(session):
    with pytest.raises(ValueError): CaseInput(case_id='John',chart_snapshot=snapshot(),input_confidence='A')
    private=snapshot();private['name']='Real person'
    with pytest.raises(ValueError): CaseInput(case_id='TV-2026-001',chart_snapshot=private,input_confidence='A')
    cid=make_case(session)
    bad=prediction().model_copy(update={'chung_cu_ids':['invented']})
    with pytest.raises(ValueError,match='chứng cứ'): add_prediction(session,cid,bad)
    create_case(session,CaseInput(case_id='TV-2026-002',chart_snapshot=snapshot(),input_confidence='D'))
    with pytest.raises(ValueError,match='C/D'): add_prediction(session,'TV-2026-002',prediction())
    disguised=prediction().model_copy(update={'loai_ket_luan':'cau_truc','noi_dung':'Năm 2027 sẽ kết hôn.'})
    with pytest.raises(ValueError,match='C/D'): add_prediction(session,'TV-2026-002',disguised)


def test_event_requires_same_case_locked_prediction_and_retains_history(session):
    cid=make_case(session);other=make_case(session,2)
    p=add_prediction(session,cid,prediction())
    event=EventInput(prediction_id=p['prediction_id'],year=2027,category='finance',
                     mo_ta='Sự kiện',prediction_result='partial_match')
    with pytest.raises(ValueError,match='khóa'): reveal_event(session,cid,event)
    lock_prediction(session,p['prediction_id'])
    with pytest.raises(ValueError): reveal_event(session,other,event)
    reveal_event(session,cid,event);session.commit()
    with pytest.raises(ValueError,match='đã'): reveal_event(session,cid,event)
    with pytest.raises(IntegrityError): session.execute(text('DELETE FROM events'))
    session.rollback()


def test_statistics_hidden_at_29_and_shown_at_30_distinct_graded_cases(session):
    for i in range(1,31):
        cid=make_case(session,i);p=add_prediction(session,cid,prediction())
        lock_prediction(session,p['prediction_id'])
        reveal_event(session,cid,EventInput(prediction_id=p['prediction_id'],year=2027,
           category='career',mo_ta='Không khớp',prediction_result='no_match'))
        if i==29:
            assert statistics(session)['counts'] is None
    stats=statistics(session)
    assert stats['eligible_cases']==30 and stats['counts']['no_match']==30
    assert '%' not in json.dumps(stats,ensure_ascii=False)


def test_case_api_and_journal_ui(session):
    from backend.app.main import app
    from backend.app.api.case_validation import case_session
    app.dependency_overrides[case_session]=lambda: session
    try:
        client=TestClient(app)
        response=client.post('/api/v1/validation/cases',json={
            'case_id':'TV-2026-001','chart_snapshot':snapshot(),'input_confidence':'A'})
        assert response.status_code==201,response.text
        assert client.get('/api/v1/validation/cases/TV-2026-001').status_code==200
        assert client.get('/api/v1/validation/statistics').json()['counts'] is None
        assert client.get('/api/v1/validation/cases/missing').status_code==404
    finally: app.dependency_overrides.clear()
    from streamlit.testing.v1 import AppTest
    ui=AppTest.from_file(Path(__file__).resolve().parents[1]/'frontend/case_validation_ui.py', default_timeout=20).run()
    assert not ui.exception
    assert any('nghiệm lý' in t.value for t in ui.title)


def test_post_reveal_revision_cannot_be_scored_in_hindsight(session):
    cid=make_case(session);p=add_prediction(session,cid,prediction())
    lock_prediction(session,p['prediction_id'])
    event=dict(year=2027,category='career',mo_ta='Không khớp',prediction_result='no_match')
    reveal_event(session,cid,EventInput(prediction_id=p['prediction_id'],**event))
    revision=revise_prediction(session,p['prediction_id'],prediction(),'Sau khi biết kết quả')
    lock_prediction(session,revision['prediction_id'])
    with pytest.raises(ValueError,match='Đã biết'):
        reveal_event(session,cid,EventInput(prediction_id=revision['prediction_id'],**event))


def test_case_api_full_workflow_and_rejected_timestamp(session):
    from backend.app.main import app
    from backend.app.api.case_validation import case_session
    app.dependency_overrides[case_session]=lambda:session
    try:
        client=TestClient(app);cid=make_case(session)
        endpoint=f'/api/v1/validation/cases/{cid}'
        payload=prediction().model_dump()
        assert client.post(endpoint+'/predictions',json={**payload,'locked_at':'2020-01-01'}).status_code==422
        p=client.post(endpoint+'/predictions',json=payload).json()
        assert client.post('/api/v1/validation/predictions/'+p['prediction_id']+'/lock').status_code==200
        assert client.post('/api/v1/validation/predictions/'+p['prediction_id']+'/lock').status_code==409
        assert client.post(endpoint+'/events',json={'prediction_id':p['prediction_id'],'year':2027,
            'category':'career','mo_ta':'Không khớp','prediction_result':'no_match'}).status_code==201
        assert client.get(endpoint).json()['events'][0]['prediction_result']=='no_match'
    finally: app.dependency_overrides.clear()


def test_empty_cases_do_not_unlock_statistics(session):
    for i in range(1,31): make_case(session,i)
    assert statistics(session)['eligible_cases']==0
    assert statistics(session)['counts'] is None
