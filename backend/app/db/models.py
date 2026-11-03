"""Schema SQLAlchemy cho KMS Tử Vi (plan §3.1).

Dùng create_all, không Alembic (MVP).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "books"

    book_code: Mapped[str] = mapped_column(String(16), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(512))
    author: Mapped[str | None] = mapped_column(String(256))
    total_pages: Mapped[int | None] = mapped_column(Integer)
    source_status: Mapped[str | None] = mapped_column(String(64))

    parts: Mapped[list["BookPart"]] = relationship(back_populates="book")


class BookPart(Base):
    __tablename__ = "book_parts"
    __table_args__ = (UniqueConstraint("source_id", "part_number", name="uq_part"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(String(64), index=True)
    part_number: Mapped[str] = mapped_column(String(32))
    pdf_file: Mapped[str | None] = mapped_column(String(512))
    total_pdf_pages: Mapped[int | None] = mapped_column(Integer)
    book_code: Mapped[str | None] = mapped_column(
        ForeignKey("books.book_code", ondelete="CASCADE"), index=True
    )

    book: Mapped[Book | None] = relationship(back_populates="parts")


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    knowledge_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    book_code: Mapped[str] = mapped_column(String(16), index=True)
    knowledge_type: Mapped[str | None] = mapped_column(String(64))
    taxonomy_code: Mapped[str | None] = mapped_column(String(64), index=True)
    subject: Mapped[str | None] = mapped_column(Text)
    predicate: Mapped[str | None] = mapped_column(Text)
    object: Mapped[str | None] = mapped_column(Text)
    condition_context: Mapped[str | None] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    chapter: Mapped[str | None] = mapped_column(String(512))
    source_certainty: Mapped[str | None] = mapped_column(String(32))
    review_flag: Mapped[str | None] = mapped_column(String(64), index=True)
    release_status: Mapped[str | None] = mapped_column(String(64))
    validation_status: Mapped[str | None] = mapped_column(String(64))
    conflict_status: Mapped[str | None] = mapped_column(String(64))
    dedupe_status: Mapped[str | None] = mapped_column(String(64))
    trust_tier: Mapped[int] = mapped_column(Integer, index=True)
    duplicate_text_group: Mapped[str | None] = mapped_column(String(64), index=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    pages: Mapped[list["KnowledgePage"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )
    evidences: Mapped[list["Evidence"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )


class KnowledgePage(Base):
    __tablename__ = "knowledge_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    knowledge_id: Mapped[str] = mapped_column(
        ForeignKey("knowledge_items.knowledge_id", ondelete="CASCADE"), index=True
    )
    part_number: Mapped[str | None] = mapped_column(String(32))
    pdf_page: Mapped[int | None] = mapped_column(Integer)

    item: Mapped[KnowledgeItem] = relationship(back_populates="pages")


class Evidence(Base):
    __tablename__ = "evidences"

    evidence_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    knowledge_id: Mapped[str] = mapped_column(
        ForeignKey("knowledge_items.knowledge_id", ondelete="CASCADE"), index=True
    )
    book_code: Mapped[str | None] = mapped_column(String(16), index=True)
    part_number: Mapped[str | None] = mapped_column(String(32))
    pdf_page: Mapped[int | None] = mapped_column(Integer)
    printed_page: Mapped[str | None] = mapped_column(String(64))
    original_text: Mapped[str | None] = mapped_column(Text)
    ocr_legibility: Mapped[str | None] = mapped_column(String(32))
    evidence_method: Mapped[str | None] = mapped_column(String(64))
    origin: Mapped[str | None] = mapped_column(String(64))
    source_review_status: Mapped[str | None] = mapped_column(String(64))
    verification_status: Mapped[str] = mapped_column(String(32), default="unverified")
    reviewer: Mapped[str | None] = mapped_column(String(128))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    review_note: Mapped[str | None] = mapped_column(Text)

    item: Mapped[KnowledgeItem] = relationship(back_populates="evidences")


class IdRedirect(Base):
    __tablename__ = "id_redirects"

    original_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    active_id: Mapped[str] = mapped_column(String(64), index=True)
    reason: Mapped[str | None] = mapped_column(String(256))


class Chunk(Base):
    __tablename__ = "chunks"

    chunk_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    book_code: Mapped[str] = mapped_column(String(16), index=True)
    chapter: Mapped[str | None] = mapped_column(String(512))
    chunk_text: Mapped[str] = mapped_column(Text)
    embed_text: Mapped[str] = mapped_column(Text)
    trust_tier: Mapped[int] = mapped_column(Integer, index=True)
    part_number: Mapped[str | None] = mapped_column(String(32))
    pdf_page_start: Mapped[int | None] = mapped_column(Integer)
    pdf_page_end: Mapped[int | None] = mapped_column(Integer)
    chunking_version: Mapped[str] = mapped_column(String(32))
    embedding_model: Mapped[str] = mapped_column(String(128))
    indexed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)

    members: Mapped[list["ChunkMember"]] = relationship(
        back_populates="chunk", cascade="all, delete-orphan"
    )


class ChunkMember(Base):
    __tablename__ = "chunk_members"
    __table_args__ = (UniqueConstraint("chunk_id", "knowledge_id", name="uq_chunk_member"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chunk_id: Mapped[str] = mapped_column(
        ForeignKey("chunks.chunk_id", ondelete="CASCADE"), index=True
    )
    knowledge_id: Mapped[str] = mapped_column(String(64), index=True)
    position: Mapped[int] = mapped_column(Integer)

    chunk: Mapped[Chunk] = relationship(back_populates="members")


class TermAlias(Base):
    __tablename__ = "term_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    term: Mapped[str] = mapped_column(String(256), index=True)
    alias: Mapped[str] = mapped_column(String(256), index=True)
    entity_type: Mapped[str | None] = mapped_column(String(64))
    taxonomy_code: Mapped[str | None] = mapped_column(String(64))
    alias_source: Mapped[str] = mapped_column(String(16), default="excel")


class ImportRun(Base):
    __tablename__ = "import_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    file_name: Mapped[str] = mapped_column(String(512))
    file_sha256: Mapped[str] = mapped_column(String(64), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    rows_read: Mapped[int] = mapped_column(Integer, default=0)
    rows_imported: Mapped[int] = mapped_column(Integer, default=0)
    rows_rejected: Mapped[int] = mapped_column(Integer, default=0)
    report_path: Mapped[str | None] = mapped_column(String(512))


class AuditSample(Base):
    __tablename__ = "audit_samples"

    sample_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    knowledge_id: Mapped[str] = mapped_column(String(64), index=True)
    book_code: Mapped[str] = mapped_column(String(16), index=True)
    auditor: Mapped[str | None] = mapped_column(String(128))
    text_matches_source: Mapped[str | None] = mapped_column(String(16))
    page_correct: Mapped[str | None] = mapped_column(String(16))
    ocr_error: Mapped[str | None] = mapped_column(String(16))
    note: Mapped[str | None] = mapped_column(Text)
    audited_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class EvaluationCase(Base):
    __tablename__ = "evaluation_cases"

    case_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    question: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(64))
    expected_knowledge_ids: Mapped[str] = mapped_column(Text)  # JSON list
    expected_status: Mapped[str] = mapped_column(String(32), default="answered")
    author: Mapped[str | None] = mapped_column(String(128))


class QueryCache(Base):
    __tablename__ = "query_cache"

    cache_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    question: Mapped[str] = mapped_column(Text)
    normalized_question: Mapped[str] = mapped_column(Text, index=True)
    book_codes: Mapped[str | None] = mapped_column(String(64))
    model_name: Mapped[str] = mapped_column(String(64))
    prompt_hash: Mapped[str] = mapped_column(String(16))
    index_version: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    response_json: Mapped[str] = mapped_column(Text)
    hit_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_hit_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class HoroscopeCache(Base):
    """Cache bài luận giải đã tạo thành công (không lưu lỗi/fallback)."""

    __tablename__ = "horoscope_cache"

    cache_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload_hash: Mapped[str] = mapped_column(String(64))
    target_year: Mapped[int] = mapped_column(Integer, index=True)
    model_name: Mapped[str] = mapped_column(String(64))
    response_json: Mapped[str] = mapped_column(Text)
    hit_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_hit_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ValidationCase(Base):
    __tablename__ = 'validation_cases'
    case_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    chart_snapshot: Mapped[str] = mapped_column(Text)
    input_confidence: Mapped[str] = mapped_column(String(1))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Prediction(Base):
    __tablename__ = 'predictions'
    prediction_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey('validation_cases.case_id'), index=True)
    noi_dung: Mapped[str] = mapped_column(Text)
    khoa_thoi_gian: Mapped[str] = mapped_column(String(16))
    muc_tin_cay: Mapped[str] = mapped_column(String(16))
    loai_ket_luan: Mapped[str] = mapped_column(String(16))
    chung_cu_ids: Mapped[str] = mapped_column(Text)
    phan_chung: Mapped[str] = mapped_column(Text)
    supersedes: Mapped[str | None] = mapped_column(ForeignKey('predictions.prediction_id'))
    revision_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime)


class ValidationEvent(Base):
    __tablename__ = 'events'
    event_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey('validation_cases.case_id'), index=True)
    prediction_id: Mapped[str] = mapped_column(ForeignKey('predictions.prediction_id'), unique=True)
    year: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(16))
    mo_ta: Mapped[str] = mapped_column(Text)
    prediction_result: Mapped[str] = mapped_column(String(24))
    revealed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
