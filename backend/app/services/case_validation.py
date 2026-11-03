"""Append-only case validation; source data and the horoscope flow are untouched."""
import json
from uuid import uuid4
from sqlalchemy import select, func
from backend.app.db.models import ValidationCase, Prediction, ValidationEvent, utcnow
from backend.app.schemas.case_validation import CaseInput, PredictionInput, EventInput
from backend.app.services.horoscope_confidence import contains_timing_claim

RESULTS=('clear_match','partial_match','no_match','not_verifiable')


def install_immutability(engine):
    """SQLite enforces the same freeze even outside the API/service."""
    with engine.begin() as conn:
        for table,condition in [('predictions','OLD.locked_at IS NOT NULL'),
                                ('validation_cases','1'),('events','1')]:
            for action in ('UPDATE','DELETE'):
                conn.exec_driver_sql(f'''CREATE TRIGGER IF NOT EXISTS freeze_{table}_{action.lower()}
                  BEFORE {action} ON {table} WHEN {condition}
                  BEGIN SELECT RAISE(ABORT, 'locked journal record is immutable'); END''')


def _as_dict(row):
    data={c.name:getattr(row,c.name) for c in row.__table__.columns}
    for key in ('chart_snapshot','chung_cu_ids'):
        if key in data: data[key]=json.loads(data[key])
    for key,value in data.items():
        if hasattr(value,'isoformat'): data[key]=value.isoformat()
    return data


def _case(session,cid):
    case=session.get(ValidationCase,cid)
    if case is None: raise LookupError('Không tìm thấy ca.')
    return case


def _prediction(session,pid):
    p=session.get(Prediction,pid)
    if p is None: raise LookupError('Không tìm thấy dự đoán.')
    return p


def create_case(session, data:CaseInput):
    if session.get(ValidationCase,data.case_id): raise ValueError('Mã ca đã tồn tại.')
    row=ValidationCase(case_id=data.case_id,chart_snapshot=data.chart_snapshot.model_dump_json(),
                       input_confidence=data.input_confidence)
    session.add(row); session.flush()
    return _as_dict(row)


def add_prediction(session,cid,data:PredictionInput, *, supersedes=None, reason=None):
    case=_case(session,cid)
    if case.input_confidence in ('C','D') and (data.loai_ket_luan=='thoi_diem'
            or contains_timing_claim(data.noi_dung)):
        raise ValueError('Đầu vào C/D chỉ được ghi kết luận cấu trúc.')
    known={f['fact_id'] for f in json.loads(case.chart_snapshot)['facts']}
    ids=set(data.chung_cu_ids)
    minimum={'rat_manh':3,'manh':3,'trung_binh':1,'yeu':1}[data.muc_tin_cay]
    if not ids <= known or len(ids)<minimum:
        raise ValueError('Thiếu hoặc không nhận diện được chứng cứ trong snapshot.')
    years=[int(x) for x in data.khoa_thoi_gian.split('-')]
    if min(years)<1900 or max(years)>2100 or years[0]>years[-1]:
        raise ValueError('Khoảng năm phải nằm trong 1900–2100 và tăng dần.')
    row=Prediction(prediction_id=uuid4().hex,case_id=cid,**data.model_dump(exclude={'chung_cu_ids'}),
                   chung_cu_ids=json.dumps(sorted(ids)),supersedes=supersedes,revision_reason=reason)
    session.add(row);session.flush()
    return _as_dict(row)


def lock_prediction(session,pid):
    row=_prediction(session,pid)
    if row.locked_at is not None: raise ValueError('Dự đoán đã khóa; hãy tạo phiên bản mới.')
    row.locked_at=utcnow();session.flush()
    return _as_dict(row)


def revise_prediction(session,pid,data,reason):
    row=_prediction(session,pid)
    if row.locked_at is None: raise ValueError('Chỉ tạo phiên bản thay thế cho dự đoán đã khóa.')
    if not reason or len(reason.strip())<3: raise ValueError('Cần lý do thay đổi.')
    return add_prediction(session,row.case_id,data,supersedes=pid,reason=reason.strip())


def reveal_event(session,cid,data:EventInput):
    _case(session,cid)
    p=_prediction(session,data.prediction_id)
    if p.case_id!=cid: raise ValueError('Dự đoán không thuộc ca này.')
    if p.locked_at is None: raise ValueError('Phải khóa dự đoán trước khi tiết lộ sự kiện.')
    if session.scalar(select(ValidationEvent).where(ValidationEvent.prediction_id==p.prediction_id)):
        raise ValueError('Dự đoán đã được đối chiếu; giữ nguyên kết quả cũ.')
    years=[int(y) for y in p.khoa_thoi_gian.split('-')]
    if not years[0]<=data.year<=years[-1]: raise ValueError('Sự kiện nằm ngoài khoảng năm đã khóa.')
    # A revision locked after this case/year was revealed cannot be scored in hindsight.
    prior=session.scalar(select(func.min(ValidationEvent.revealed_at)).where(
        ValidationEvent.case_id==cid,ValidationEvent.year==data.year))
    if prior and p.locked_at.replace(tzinfo=None)>=prior.replace(tzinfo=None):
        raise ValueError('Đã biết sự kiện của năm này trước khi khóa phiên bản này.')
    row=ValidationEvent(event_id=uuid4().hex,case_id=cid,**data.model_dump())
    session.add(row);session.flush()
    return _as_dict(row)


def get_case(session,cid):
    data=_as_dict(_case(session,cid))
    data['predictions']=[_as_dict(p) for p in session.scalars(select(Prediction).where(
        Prediction.case_id==cid).order_by(Prediction.created_at,Prediction.prediction_id))]
    data['events']=[_as_dict(e) for e in session.scalars(select(ValidationEvent).where(
        ValidationEvent.case_id==cid).order_by(ValidationEvent.revealed_at))]
    return data


def statistics(session):
    eligible=session.scalar(select(func.count(func.distinct(ValidationEvent.case_id)))) or 0
    counts=None
    if eligible>=30:
        counts={result:session.scalar(select(func.count()).select_from(ValidationEvent).where(
            ValidationEvent.prediction_result==result)) or 0 for result in RESULTS}
    return {'eligible_cases':eligible,'minimum_cases':30,'counts':counts,
            'message':'Chưa đủ mẫu (cần ít nhất 30 ca đã đối chiếu).' if counts is None else
            'Số lượt đối chiếu theo kết quả; dữ liệu tự ghi nhận, chưa chứng minh khả năng dự báo.'}
