"""T08 — Hybrid retriever: FTS5 (keyword) + Dense (vector), kết hợp bằng RRF.

Chiến lược (plan §4.2):
  - Lấy top-N từ mỗi sách riêng (để sách nhỏ không bị sách lớn áp đảo)
  - Gộp kết quả FTS5 + dense bằng Reciprocal Rank Fusion
  - Lọc trust_tier theo cấu hình enabled_tiers

RRF: score(d) = sum over rankers of 1 / (k + rank(d)),  k = 60 (mặc định)
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select

from backend.app.db.models import Chunk, ChunkMember, KnowledgeItem
from backend.app.db.session import session_scope
from backend.app.services.fts import search_fts
from backend.app.services.mapping import load_mapping
from backend.app.core.config import RETRIEVAL_CONFIG

BOOK_CODES = ["NPL", "DAU", "BD"]
RRF_K = 60


@dataclass
class RetrievedChunk:
    chunk_id: str
    book_code: str
    chapter: str
    text: str
    trust_tier: int
    part_number: str | None
    pdf_page_start: int | None
    pdf_page_end: int | None
    score: float
    rrf_score: float
    knowledge_ids: list[str] = field(default_factory=list)
    sources: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "book_code": self.book_code,
            "chapter": self.chapter,
            "text": self.text,
            "trust_tier": self.trust_tier,
            "part_number": self.part_number,
            "pdf_page_start": self.pdf_page_start,
            "pdf_page_end": self.pdf_page_end,
            "score": round(self.score, 4),
            "rrf_score": round(self.rrf_score, 6),
            "knowledge_ids": self.knowledge_ids,
        }


class Retriever:
    def __init__(self, top_n_per_book: int = 10, rrf_k: int = RRF_K):
        self.top_n_per_book = top_n_per_book
        self.rrf_k = rrf_k
        self.mapping = load_mapping(RETRIEVAL_CONFIG.parent / "column_mapping.yaml")
        self.enabled_tiers = self.mapping.enabled_tiers
        self._store = None

    # Adapter embedding là singleton toàn tiến trình (model nặng chỉ nạp 1 lần)
    @property
    def embedder(self):
        from backend.app.services.embeddings import get_embedding_adapter

        return get_embedding_adapter()

    def _dense_search(
        self, query: str, top_k: int, book_code: str | None
    ) -> list[tuple[str, float]]:
        # vector store rỗng (chưa embed) -> bỏ qua dense, không nạp model vô ích
        try:
            from backend.app.services.vector_store import get_vector_store

            if get_vector_store().count() == 0:
                return []
        except Exception:
            pass
        try:
            adapter = self.embedder
            return adapter.search(query, top_k, book_code)
        except Exception as exc:  # vector store chưa sẵn sàng -> bỏ qua dense
            print(f"[retriever] dense search bỏ qua: {exc}")
            return []

    def _rrf(
        self, rankings: list[list[tuple[str, float]]]
    ) -> dict[str, float]:
        """Reciprocal Rank Fusion trên nhiều danh sách xếp hạng."""
        fused: dict[str, float] = {}
        for ranking in rankings:
            for rank, (doc_id, _score) in enumerate(ranking, start=1):
                fused[doc_id] = fused.get(doc_id, 0.0) + 1.0 / (self.rrf_k + rank)
        return fused

    def search(
        self,
        query: str,
        top_k: int = 10,
        book_codes: list[str] | None = None,
        use_dense: bool = True,
        use_fts: bool = True,
    ) -> list[RetrievedChunk]:
        books = book_codes or BOOK_CODES
        all_fused: dict[str, float] = {}
        best_raw: dict[str, float] = {}

        for book in books:
            fts_hits = (
                search_fts(
                    query,
                    top_k=self.top_n_per_book,
                    book_code=book,
                    trust_tiers=self.enabled_tiers,
                )
                if use_fts
                else []
            )
            # bm25 càng nhỏ càng tốt -> đảo thành score dương để thống nhất
            fts_ranking = [(cid, -score) for cid, score in fts_hits]

            dense_hits = (
                self._dense_search(query, self.top_n_per_book, book)
                if use_dense
                else []
            )

            fused = self._rrf([fts_ranking, dense_hits])
            for doc_id, score in fused.items():
                all_fused[doc_id] = all_fused.get(doc_id, 0.0) + score
            for cid, score in fts_ranking + dense_hits:
                best_raw[cid] = max(best_raw.get(cid, -1e9), score)

        if not all_fused:
            return []

        # lấy metadata từ DB
        ordered = sorted(all_fused.items(), key=lambda kv: -kv[1])[: top_k]
        chunk_ids = [cid for cid, _ in ordered]
        rrf_map = dict(ordered)

        with session_scope() as session:
            rows = session.execute(
                select(Chunk).where(Chunk.chunk_id.in_(chunk_ids))
            ).scalars().all()
            members: dict[str, list[str]] = {}
            for cm in session.execute(
                select(ChunkMember).where(ChunkMember.chunk_id.in_(chunk_ids))
            ).scalars():
                members.setdefault(cm.chunk_id, []).append(cm.knowledge_id)

            results = []
            for row in rows:
                results.append(
                    RetrievedChunk(
                        chunk_id=row.chunk_id,
                        book_code=row.book_code,
                        chapter=row.chapter or "",
                        text=row.chunk_text,
                        trust_tier=row.trust_tier,
                        part_number=row.part_number,
                        pdf_page_start=row.pdf_page_start,
                        pdf_page_end=row.pdf_page_end,
                        score=best_raw.get(row.chunk_id, 0.0),
                        rrf_score=rrf_map.get(row.chunk_id, 0.0),
                        knowledge_ids=members.get(row.chunk_id, []),
                    )
                )

        results.sort(key=lambda c: -c.rrf_score)
        return results

    def get_knowledge_items(self, knowledge_ids: list[str]) -> dict[str, KnowledgeItem]:
        if not knowledge_ids:
            return {}
        with session_scope() as session:
            rows = session.execute(
                select(KnowledgeItem).where(
                    KnowledgeItem.knowledge_id.in_(knowledge_ids)
                )
            ).scalars().all()
            return {r.knowledge_id: r for r in rows}


if __name__ == "__main__":
    import json

    r = Retriever()
    for hit in r.search("tu vi la gi", top_k=5):
        print(json.dumps(hit.to_dict(), ensure_ascii=False)[:300])
