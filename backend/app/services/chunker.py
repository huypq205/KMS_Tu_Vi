"""T05 — Chunker cho 3 sách theo quy tắc plan §4.1.

- NPL: 1 bản ghi = 1 chunk (đã có cấu trúc, độ dài ổn định)
- DAU & BD: gộp bản ghi liền kề cùng sách theo thứ tự knowledge_id,
  nhóm theo (part_number, pdf_page, chapter), đạt min_chars (150) -
  max_chars (600). PAGE_OR_PARAGRAPH_CONTINUATION gộp sang trang kế tiếp
  nếu cùng chương.
"""
from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from sqlalchemy import func

from backend.app.db.session import session_scope
from backend.app.db.models import KnowledgeItem, KnowledgePage
from backend.app.services.mapping import load_mapping
from backend.app.services.normalize import nfc
from backend.app.services.pages import parse_page_refs
from backend.app.services.normalize import content_hash
from backend.app.services.knowledge_gate import HYPOTHESIS_FLAG


@dataclass
class ChunkSpec:
    chunk_id: str
    book_code: str
    chapter: str
    embed_text: str
    knowledge_ids: list[str]
    trust_tier: int
    part_number: str | None
    pdf_page_start: int | None
    pdf_page_end: int | None
    chunking_version: str = "v0.1"
    embedding_model: str = "BAAI/bge-m3"
    content_hash: str = ""


def build_chunks() -> list[ChunkSpec]:
    # SỬA LẤY CẤU HÌNH: parents[4] từ chunker.py để trỏ tới project root (d:\Ki7\KMS)
    mapping = load_mapping(Path(__file__).resolve().parents[3] / "configs" / "column_mapping.yaml")
    enabled = mapping.enabled_tiers
    chunking = mapping.chunking
    min_chars = chunking.get("min_chars", 150)
    max_chars = chunking.get("max_chars", 600)

    with session_scope() as session:
        # chỉ lấy các knowledge_item đã qualifying (tier trong enabled, có evidence)
        items = session.query(KnowledgeItem).filter(
            KnowledgeItem.trust_tier.in_(enabled),
            KnowledgeItem.trust_tier != 9,
            ~func.upper(func.coalesce(KnowledgeItem.review_flag, "")).contains(HYPOTHESIS_FLAG),
            KnowledgeItem.evidences.any()
        ).order_by(KnowledgeItem.book_code, KnowledgeItem.knowledge_id).all()

        # tra cứu pages
        pages_by_kid: dict[str, list[KnowledgePage]] = {}
        for p in session.query(KnowledgePage).all():
            pages_by_kid.setdefault(p.knowledge_id, []).append(p)

        # nhóm theo sách
        chunks: list[ChunkSpec] = []
        for book_code in ["NPL", "BD", "DAU"]:
            book_items = [i for i in items if i.book_code == book_code]
            if book_code == "NPL":
                chunks.extend(_chunk_npl(book_items, mapping, pages_by_kid))
            else:
                chunks.extend(_chunk_merge_adjacent(book_items, mapping, pages_by_kid, min_chars, max_chars))

        return chunks


def _page_numbers(pages: list[KnowledgePage]) -> tuple[int | None, int | None]:
    """(trang đầu, trang cuối) từ các dòng knowledge_pages."""
    nums = [p.pdf_page for p in pages if p.pdf_page is not None]
    if not nums:
        return None, None
    return min(nums), max(nums)


def _chunk_npl(items: list[KnowledgeItem], mapping, pages_by_kid: dict) -> list[ChunkSpec]:
    chunks: list[ChunkSpec] = []
    for item in items:
        pages = pages_by_kid.get(item.knowledge_id, [])
        start, end = _page_numbers(pages)
        part = pages[0].part_number if pages else None
        embed_text = nfc(f"{item.chapter or ''} | {item.subject or ''} | {item.text or ''}")
        c = ChunkSpec(
            chunk_id=f"ck-{item.knowledge_id}",
            book_code=item.book_code,
            chapter=item.chapter or "",
            embed_text=embed_text,
            knowledge_ids=[item.knowledge_id],
            trust_tier=item.trust_tier,
            part_number=part,
            pdf_page_start=start,
            pdf_page_end=end,
            content_hash=content_hash(embed_text),
        )
        chunks.append(c)
    return chunks


def _chunk_merge_adjacent(
    items: list[KnowledgeItem],
    mapping,
    pages_by_kid: dict,
    min_chars: int,
    max_chars: int,
) -> list[ChunkSpec]:
    # nhóm theo (part_number, pdf_page, chapter)
    groups: dict[tuple, list[KnowledgeItem]] = defaultdict(list)
    for item in items:
        pages = pages_by_kid.get(item.knowledge_id, [])
        if not pages:
            continue
        ref = pages[0]
        key = (ref.part_number, ref.pdf_page, item.chapter)
        groups[key].append(item)

    chunks: list[ChunkSpec] = []
    for (part, page, chapter), grp in groups.items():
        grp.sort(key=lambda x: x.knowledge_id)

        buffer: list[KnowledgeItem] = []
        buffer_len = 0

        def flush():
            nonlocal buffer, buffer_len
            if not buffer:
                return
            combined = nfc(
                " ".join(
                    nfc(f"{i.chapter or ''} | {i.subject or ''} | {i.text or ''}")
                    for i in buffer
                )
            )
            all_pages = [p for i in buffer for p in pages_by_kid.get(i.knowledge_id, [])]
            pdf_start, pdf_end = _page_numbers(all_pages)
            c = ChunkSpec(
                chunk_id=f"ck-{hashlib.sha256(combined.encode()).hexdigest()[:16]}",
                book_code=grp[0].book_code,
                chapter=chapter,
                embed_text=combined,
                knowledge_ids=[i.knowledge_id for i in buffer],
                trust_tier=max(i.trust_tier for i in buffer),
                part_number=part,
                pdf_page_start=pdf_start,
                pdf_page_end=pdf_end,
                content_hash=content_hash(combined),
            )
            chunks.append(c)
            buffer = []
            buffer_len = 0

        for item in grp:
            embed = nfc(f"{item.chapter or ''} | {item.subject or ''} | {item.text or ''}")
            buf_len = len(embed)
            # nếu item này dài hơn max_chars thì tạo chunk riêng
            if buf_len > max_chars:
                flush()
                c = ChunkSpec(
                    chunk_id=f"ck-{hashlib.sha256(embed.encode()).hexdigest()[:16]}",
                    book_code=item.book_code,
                    chapter=item.chapter or "",
                    embed_text=embed,
                    knowledge_ids=[item.knowledge_id],
                    trust_tier=item.trust_tier,
                    part_number=part,
                    pdf_page_start=page,
                    pdf_page_end=page,
                    content_hash=content_hash(embed),
                )
                chunks.append(c)
                continue
            # gộp tiếp nếu chưa vượt max_chars
            if buffer_len + buf_len > max_chars:
                flush()
            buffer.append(item)
            buffer_len += buf_len

        flush()

    return chunks


if __name__ == "__main__":
    chunks = build_chunks()
    print(f"Built {len(chunks)} chunks")
    for book in ["NPL", "BD", "DAU"]:
        book_chunks = [c for c in chunks if c.book_code == book]
        if book_chunks:
            sizes = [len(c.embed_text) for c in book_chunks]
            avg = sum(sizes) / len(sizes)
            members = sum(len(c.knowledge_ids) for c in book_chunks)
            print(
                f"  {book}: {len(book_chunks)} chunks, avg {avg:.0f} chars, "
                f"min {min(sizes)} max {max(sizes)}, {members} bản ghi gốc"
            )
