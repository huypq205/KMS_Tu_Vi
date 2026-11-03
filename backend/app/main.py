"""KMS Tử Vi — FastAPI app.

Hiện tại (Sprint 1) chỉ có endpoint tìm kiếm, chưa nối LLM.

Chạy:
    uvicorn backend.app.main:app --reload --port 8000
"""
from __future__ import annotations

import os
import threading
import time
from collections import deque

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from backend.app.core.config import EXCERPT_MAX_CHARS
from backend.app.schemas.search import Citation, SearchRequest, SearchResponse
from backend.app.schemas.chat import ChatAskRequest, ChatAskResponse
from backend.app.services.pages import format_page_label
from backend.app.services.retriever import Retriever
from backend.app.services.rag import RAGPipeline

_retriever_instance: Retriever | None = None
_pipeline_instance: RAGPipeline | None = None
_component_lock = threading.Lock()


def get_retriever() -> Retriever:
    """Retriever chia sẻ cho mọi request (vector store / embedder chỉ nạp 1 lần)."""
    global _retriever_instance
    if _retriever_instance is None:
        with _component_lock:
            if _retriever_instance is None:
                _retriever_instance = Retriever()
    return _retriever_instance


def get_rag_pipeline() -> RAGPipeline:
    """RAGPipeline chia sẻ, dùng chung Retriever với endpoint search."""
    global _pipeline_instance
    if _pipeline_instance is None:
        with _component_lock:
            if _pipeline_instance is None:
                _pipeline_instance = RAGPipeline(retriever=get_retriever())
    return _pipeline_instance

app = FastAPI(
    title="KMS Tử Vi",
    description="Tra cứu tri thức Tử Vi từ 3 sách nguồn (NPL, DAU, BD)",
    version="0.1.0",
)

# CORS theo danh sách origin (env KMS_CORS_ORIGINS, phân tách bằng dấu phẩy).
# Tránh wildcard: browser từ chối khi allow_origins=["*"] + allow_credentials=True.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "KMS_CORS_ORIGINS", "http://localhost:8501,http://localhost:8502"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials="*" not in CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Bảo mật đơn giản: API key tùy chọn + rate limit các endpoint nặng (LLM) ---
# KMS_API_KEY: rỗng (mặc định) = mở; khi đặt, mọi /api/v1/* (trừ /health) cần header X-API-Key.
# KMS_RATE_LIMIT_PER_MIN: giới hạn yêu cầu/phút cho /api/v1/horoscope* (0 = tắt).
_API_KEY = os.getenv("KMS_API_KEY", "").strip()
_RATE_LIMIT_PER_MIN = int(os.getenv("KMS_RATE_LIMIT_PER_MIN", "10"))
_rate_buckets: dict[str, deque] = {}
_rate_lock = threading.Lock()


def _rate_limited(ip: str, now: float) -> bool:
    bucket = _rate_buckets.setdefault(ip, deque())
    while bucket and now - bucket[0] > 60.0:
        bucket.popleft()
    if len(bucket) >= _RATE_LIMIT_PER_MIN:
        return True
    bucket.append(now)
    return False


@app.middleware("http")
async def security_middleware(request, call_next):
    path = request.url.path
    if path.startswith(("/api/v1/", "/api/stars/")) and not path.endswith("/health"):
        if _API_KEY and request.headers.get("X-API-Key", "") != _API_KEY:
            return JSONResponse(status_code=401, content={"detail": "Thiếu hoặc sai X-API-Key."})
        if _RATE_LIMIT_PER_MIN > 0 and path.startswith("/api/v1/horoscope"):
            ip = request.client.host if request.client else "unknown"
            with _rate_lock:
                if _rate_limited(ip, time.monotonic()):
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Quá nhiều yêu cầu trong 1 phút. Vui lòng thử lại sau."},
                    )
    return await call_next(request)


def _tier_badge_map() -> dict[int, str]:
    """Nhãn UI cho từng trust tier, đọc từ column_mapping.yaml."""
    from backend.app.core.config import MAPPING_PATH
    from backend.app.services.mapping import load_mapping

    mapping = load_mapping(MAPPING_PATH)
    defs = mapping.trust_tiers.get("definitions", {})
    return {
        int(tier): (spec or {}).get("ui_badge") or mapping.tier_label(int(tier))
        for tier, spec in defs.items()
    }


def load_enabled_tiers() -> set[int]:
    """Các trust tier được phép index (đọc từ column_mapping.yaml)."""
    from backend.app.core.config import MAPPING_PATH
    from backend.app.services.mapping import load_mapping

    return load_mapping(MAPPING_PATH).enabled_tiers


def tier_label(tier: int) -> str:
    """Nhãn mô tả của một trust tier."""
    from backend.app.core.config import MAPPING_PATH
    from backend.app.services.mapping import load_mapping

    return load_mapping(MAPPING_PATH).tier_label(tier)


@app.get("/api/v1/health")
def health() -> dict:
    from backend.app.db.session import engine
    from sqlalchemy import text as sql_text

    try:
        with engine.connect() as conn:
            items = conn.execute(
                sql_text("SELECT count(*) FROM knowledge_items")
            ).scalar()
            chunks = conn.execute(sql_text("SELECT count(*) FROM chunks")).scalar()
        return {"status": "ok", "knowledge_items": items, "chunks": chunks}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@app.post("/api/v1/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
    retriever = get_retriever()
    hits = retriever.search(
        req.query,
        top_k=req.top_k,
        book_codes=req.book_codes,
        use_dense=req.use_dense,
        use_fts=req.use_fts,
    )

    citations = []
    results = []
    tier_badges = _tier_badge_map()
    for i, hit in enumerate(hits, start=1):
        excerpt = (hit.text or "")[:EXCERPT_MAX_CHARS]
        page_label = format_page_label(
            hit.book_code, hit.part_number, hit.pdf_page_start
        )
        citations.append(
            Citation(
                index=i,
                chunk_id=hit.chunk_id,
                book_code=hit.book_code,
                chapter=hit.chapter,
                part_number=hit.part_number,
                pdf_page_start=hit.pdf_page_start,
                pdf_page_end=hit.pdf_page_end,
                trust_tier=hit.trust_tier,
                ui_badge=tier_badges.get(hit.trust_tier),
                page_label=page_label,
                excerpt=excerpt,
                knowledge_ids=hit.knowledge_ids,
            )
        )
        data = hit.to_dict()
        data["index"] = i
        data["page_label"] = page_label
        data["ui_badge"] = tier_badges.get(hit.trust_tier)
        results.append(data)

    return SearchResponse(
        query=req.query,
        status="ok" if results else "no_result",
        results=results,
        citations=citations,
        meta={
            "count": len(results),
            "books": sorted({h.book_code for h in hits}),
            "enabled_tiers": sorted(retriever.enabled_tiers),
        },
    )


@app.get("/api/v1/stats")
def stats() -> dict:
    """Thống kê tổng bản ghi và phân bố trust tier (Tab 3 của UI)."""
    from sqlalchemy import text as sql_text

    from backend.app.db.session import engine
    from backend.app.services.fts import fts_count

    try:
        with engine.connect() as conn:
            total = conn.execute(
                sql_text("SELECT count(*) FROM knowledge_items")
            ).scalar()
            by_tier = conn.execute(
                sql_text(
                    "SELECT trust_tier, count(*) FROM knowledge_items "
                    "GROUP BY trust_tier ORDER BY trust_tier"
                )
            ).all()
            by_book = conn.execute(
                sql_text(
                    "SELECT book_code, count(*) FROM knowledge_items "
                    "GROUP BY book_code ORDER BY book_code"
                )
            ).all()
            chunk_count = conn.execute(
                sql_text("SELECT count(*) FROM chunks")
            ).scalar()
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}

    badge_map = _tier_badge_map()
    enabled = sorted(load_enabled_tiers())
    return {
        "status": "ok",
        "total_records": total,
        "by_tier": [
            {
                "trust_tier": int(t),
                "count": int(c),
                "label": tier_label(int(t)),
                "ui_badge": badge_map.get(int(t)),
                "enabled": int(t) in enabled,
            }
            for t, c in by_tier
        ],
        "by_book": [{"book_code": b, "count": int(c)} for b, c in by_book],
        "chunks": chunk_count,
        "fts_rows": fts_count(),
    }


@app.post("/api/v1/chat/ask", response_model=ChatAskResponse)
def chat_ask(req: ChatAskRequest) -> ChatAskResponse:
    pipeline = get_rag_pipeline()
    return pipeline.ask(
        question=req.question,
        top_k=req.top_k,
        book_codes=req.book_codes,
        request_id=req.request_id,
    )


# ---------------------------------------------------------------------------
# Tử Vi Horoscope — endpoint mới, tách biệt với KMS RAG pipeline
# ---------------------------------------------------------------------------
from backend.app.schemas.horoscope import HoroscopeAskRequest, HoroscopeRequest  # noqa: E402


@app.post("/api/v1/horoscope/read", summary="Xem lá số tử vi", tags=["Horoscope"])
def horoscope_read(req: HoroscopeRequest) -> dict:
    from backend.app.services.horoscope_service import read_horoscope
    return read_horoscope(req)


@app.post("/api/v1/horoscope/ask", summary="Hỏi nhanh theo chủ đề, có nguồn sách", tags=["Horoscope"])
def horoscope_ask(req: HoroscopeAskRequest) -> dict:
    from backend.app.services.horoscope_ask import ask_horoscope
    return ask_horoscope(req)


@app.post("/api/v1/horoscope/read-stream", tags=["Horoscope"])
def horoscope_read_stream(req: HoroscopeRequest):
    import json
    from fastapi.responses import StreamingResponse
    from backend.app.services.horoscope_service import reading_events

    def stream():
        for event in reading_events(req):
            yield json.dumps(event, ensure_ascii=False) + '\n'
    return StreamingResponse(stream(), media_type='application/x-ndjson',
                             headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


from backend.app.api.governance import router as governance_router
app.include_router(governance_router)
from backend.app.api.case_validation import router as case_validation_router
app.include_router(case_validation_router)
