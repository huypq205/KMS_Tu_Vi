"""Explicit, independent journal endpoints. Server timestamps cannot be supplied."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from backend.app.db.session import init_db, session_scope, engine
from backend.app.schemas.case_validation import CaseInput, PredictionInput, EventInput, RevisionInput
from backend.app.services import case_validation as service

router=APIRouter(prefix='/api/v1/validation',tags=['Validation journal'])


def case_session():
    try:
        init_db()
        service.install_immutability(engine)
    except SQLAlchemyError as exc:
        raise HTTPException(503,detail='Kho nghiệm lý chưa sẵn sàng.') from exc
    with session_scope() as session:
        yield session


def _run(fn,*args):
    try: return fn(*args)
    except LookupError as exc: raise HTTPException(404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(409,detail=str(exc)) from exc
    except IntegrityError as exc: raise HTTPException(409,detail='Bản ghi đã có hoặc đã bị khóa.') from exc
    except SQLAlchemyError as exc: raise HTTPException(503,detail='Kho nghiệm lý chưa sẵn sàng.') from exc


@router.post('/cases',status_code=201)
def create(data:CaseInput,session=Depends(case_session)):
    return _run(service.create_case,session,data)


@router.get('/statistics')
def statistics(session=Depends(case_session)):
    return _run(service.statistics,session)


@router.get('/cases/{cid}')
def read(cid:str,session=Depends(case_session)):
    return _run(service.get_case,session,cid)


@router.post('/cases/{cid}/predictions',status_code=201)
def predict(cid:str,data:PredictionInput,session=Depends(case_session)):
    return _run(service.add_prediction,session,cid,data)


@router.post('/predictions/{pid}/lock')
def lock(pid:str,session=Depends(case_session)):
    return _run(service.lock_prediction,session,pid)


@router.post('/predictions/{pid}/revisions',status_code=201)
def revise(pid:str,data:RevisionInput,session=Depends(case_session)):
    return _run(service.revise_prediction,session,pid,data.prediction,data.reason)


@router.post('/cases/{cid}/events',status_code=201)
def reveal(cid:str,data:EventInput,session=Depends(case_session)):
    return _run(service.reveal_event,session,cid,data)
