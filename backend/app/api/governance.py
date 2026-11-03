"""Source-aware research endpoints; no LLM calls."""
from fastapi import APIRouter, HTTPException
import sqlite3
from backend.app.services.star_dossier import get_star_dossier, UnknownStar
from backend.app.schemas.horoscope import HoroscopeRequest

router = APIRouter()


@router.post('/api/v1/horoscope/annual')
def annual_report(data: HoroscopeRequest):
    from backend.app.services.horoscope_features import generate_raw_horoscope, extract_horoscope_features
    from backend.app.services.horoscope_analysis import build_star_facts
    from backend.app.services.horoscope_annual import build_annual_report
    try:
        raw=generate_raw_horoscope(data.ngay,data.thang,data.nam,data.chi_gio,data.gioi_tinh,data.duong_lich)
        features=extract_horoscope_features(raw,data.target_year,data.input_confidence,
                                           data.gio_sinh_source,data.gio_sinh_error_phut)
        facts=build_star_facts(features)
        return {'annual_report':build_annual_report(features,facts),'facts':facts,
                'input_confidence':data.input_confidence,'source_status':'Dữ kiện an sao; chưa truy xuất diễn giải từ sách.'}
    except (ValueError,KeyError,TypeError) as exc:
        raise HTTPException(422,detail='Dữ liệu lịch hoặc lá số chưa hợp lệ.') from exc


@router.get('/api/stars/{name}/dossier')
@router.get('/api/v1/stars/{name}/dossier')
def star_dossier(name: str, include_seeds: bool = False):
    try:
        return get_star_dossier(name, include_seeds=include_seeds)
    except UnknownStar as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (sqlite3.Error, ValueError) as exc:
        raise HTTPException(status_code=503, detail='Kho tri thức hoặc seed chưa sẵn sàng. Vui lòng thử lại.') from exc
