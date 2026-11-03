"""Source-aware research endpoints; no LLM calls."""
from fastapi import APIRouter, HTTPException
import sqlite3
from backend.app.services.star_dossier import get_star_dossier, UnknownStar

router = APIRouter()


@router.get('/api/stars/{name}/dossier')
@router.get('/api/v1/stars/{name}/dossier')
def star_dossier(name: str, include_seeds: bool = False):
    try:
        return get_star_dossier(name, include_seeds=include_seeds)
    except UnknownStar as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (sqlite3.Error, ValueError) as exc:
        raise HTTPException(status_code=503, detail='Kho tri thức hoặc seed chưa sẵn sàng. Vui lòng thử lại.') from exc
