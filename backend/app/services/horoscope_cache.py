"""Cache bài luận giải Horoscope theo (lá số, năm xem, provider, model, ngữ cảnh).

Nguyên tắc:
- Chỉ lưu bài do Gemini tạo thành công; không lưu fallback/lỗi/timeout.
- Khóa cache gồm thông tin sinh, năm xem hiệu lực, provider, model, hash ngữ cảnh
  (thứ tự chunk_id) và phiên bản index sách, nên đổi năm hoặc đổi nguồn sách sẽ
  tự động cache miss.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select, update

from backend.app.core.config import ENABLE_HOROSCOPE_CACHE
from backend.app.db.models import HoroscopeCache
from backend.app.db.session import init_db, session_scope

logger = logging.getLogger(__name__)

# Tăng khi cấu trúc bài đọc đổi (ví dụ thêm muc_tin_cay, loi_chung_cu) để cache
# cũ tự miss, tránh trả bài thiếu trường mới cho UI.
CACHE_SCHEMA_VERSION = 3


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def context_hash(context: dict[str, Any] | None) -> str:
    """Hash thứ tự chunk_id đã truy xuất, để đổi nguồn là đổi khóa cache."""
    ids = [str(hit.get('chunk_id', '')) for hit in (context or {}).get('reference_list', [])]
    return hashlib.sha256('|'.join(ids).encode('utf-8')).hexdigest()[:32]


def compute_key(birth: dict[str, Any], provider: str, model: str, ctx_hash: str,
                index_version: str) -> str:
    """SHA-256 của toàn bộ ngữ cảnh quyết định nội dung bài đọc.

    ``index_version`` lấy từ manifest sách: khi re-index, mọi cache cũ tự miss
    dù câu hỏi/năm xem không đổi.
    """
    blob = json.dumps(
        {'birth': birth, 'provider': provider, 'model': model, 'context': ctx_hash,
         'index_version': index_version, 'schema_version': CACHE_SCHEMA_VERSION},
        sort_keys=True, ensure_ascii=False,
    )
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()


def hash_payload(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()


def lookup(cache_key: str) -> dict[str, Any] | None:
    """Trả {'reading', 'generation'} nếu trúng cache; None nếu không."""
    if not ENABLE_HOROSCOPE_CACHE:
        return None
    try:
        init_db()
        with session_scope() as session:
            entry = session.execute(
                select(HoroscopeCache).where(HoroscopeCache.cache_key == cache_key)
            ).scalar_one_or_none()
            if entry is None:
                return None
            session.execute(
                update(HoroscopeCache)
                .where(HoroscopeCache.cache_key == cache_key)
                .values(hit_count=entry.hit_count + 1, last_hit_at=_utcnow())
            )
            data = json.loads(entry.response_json)
            return data if isinstance(data, dict) else None
    except Exception as exc:  # cache hỏng không được chặn luồng chính
        logger.warning('Lỗi đọc horoscope_cache: %s', exc)
        return None


def save(cache_key: str, payload_hash: str, target_year: int, model: str,
         reading: dict[str, Any], generation: dict[str, Any]) -> bool:
    """Lưu bài đọc thành công. Không bao giờ lưu fallback/mock."""
    if not ENABLE_HOROSCOPE_CACHE:
        return False
    if generation.get('actual_provider') != 'gemini' or generation.get('specificity_low'):
        return False
    blob = json.dumps({'reading': reading, 'generation': generation}, ensure_ascii=False)
    try:
        init_db()
        with session_scope() as session:
            entry = session.execute(
                select(HoroscopeCache).where(HoroscopeCache.cache_key == cache_key)
            ).scalar_one_or_none()
            if entry is not None:
                entry.response_json = blob
                entry.last_hit_at = _utcnow()
            else:
                session.add(HoroscopeCache(
                    cache_key=cache_key, payload_hash=payload_hash, target_year=target_year,
                    model_name=model, response_json=blob, hit_count=0,
                    created_at=_utcnow(), last_hit_at=_utcnow(),
                ))
        return True
    except Exception as exc:
        logger.warning('Lỗi lưu horoscope_cache: %s', exc)
        return False


def clear() -> int:
    """Xóa toàn bộ cache Horoscope (dùng cho test và bảo trì)."""
    try:
        init_db()
        with session_scope() as session:
            return session.execute(delete(HoroscopeCache)).rowcount
    except Exception as exc:
        logger.warning('Lỗi xóa horoscope_cache: %s', exc)
        return 0
