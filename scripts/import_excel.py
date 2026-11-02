#!/usr/bin/env python3
"""T04 — import Excel canonical master vào SQLite, idempotent.

Đọc mapping từ configs/column_mapping.yaml, nạp books/book_parts/knowledge_items/
knowledge_pages/evidences/id_redirects/vocabulary, gán trust_tier, đánh dấu nhóm
trùng văn bản, và sinh báo cáo trong data/reports/.

Idempotent: import lần hai cùng file (cùng SHA-256) không tạo bản ghi trùng;
khác SHA thì so content_hash để upsert và tăng version.

Chạy:
    python scripts/import_excel.py
    python scripts/import_excel.py --excel data/raw/<file>.xlsx
    python scripts/import_excel.py --excel data/raw/<file>.xlsx --gate
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
from sqlalchemy import delete, select

from backend.app.core.config import DB_PATH, EXCEL_PATH, MAPPING_PATH, REPORTS_DIR
from backend.app.db.models import (
    Book,
    BookPart,
    Chunk,
    ChunkMember,
    Evidence,
    IdRedirect,
    ImportRun,
    KnowledgeItem,
    KnowledgePage,
    TermAlias,
)
from backend.app.db.session import init_db, session_scope
from backend.app.services.excel_reader import find_excel, read_section
from backend.app.services.mapping import load_mapping
from backend.app.services.normalize import content_hash, nfc, sha256_file
from backend.app.services.pages import parse_page_refs
from backend.app.services.tiering import assign_tier
from backend.app.services.knowledge_gate import (
    GateReport, existing_knowledge_ids, is_source_d_type, validate_path, validate_records,
)

REQUIRED_FIELDS = {
    "knowledge_items": ("knowledge_id", "book_code", "text"),
}


def _clean(value) -> str | None:
    """pandas đọc NaN cho ô rỗng — chuẩn hóa thành None."""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = nfc(value)
    return text or None


def import_books(session, excel: Path, mapping) -> int:
    df = read_section(excel, mapping, "sources")
    count = 0
    for _, row in df.iterrows():
        code = _clean(row.get("book_code"))
        if not code:
            continue
        book = session.get(Book, code)
        if book is not None and is_source_d_type(row.get("source_type")):
            # A hypothesis source may reference a book code, but must not replace
            # that book's bibliographic identity with a forum/video title.
            continue
        if book is None:
            book = Book(book_code=code)
            session.add(book)
        book.source_id = _clean(row.get("source_id")) or ""
        book.title = _clean(row.get("title")) or code
        book.author = _clean(row.get("author"))
        pages = row.get("total_pages")
        book.total_pages = int(pages) if pd.notna(pages) else None
        book.source_status = _clean(row.get("source_status"))
        count += 1
    return count


def import_book_parts(session, excel: Path, mapping) -> int:
    df = read_section(excel, mapping, "source_parts")
    # sheet SOURCE_PARTS không có Book_Code — suy ra từ source_id qua bảng books
    book_by_source = {b.source_id: b.book_code for b in session.scalars(select(Book))}
    count = 0
    for _, row in df.iterrows():
        source_id = _clean(row.get("source_id"))
        part = _clean(row.get("part_number"))
        if not source_id or not part:
            continue
        pages = row.get("total_pdf_pages")
        existing = session.scalar(
            select(BookPart).where(
                BookPart.source_id == source_id, BookPart.part_number == part
            )
        )
        if existing is None:
            existing = BookPart(source_id=source_id, part_number=part)
            session.add(existing)
        existing.pdf_file = _clean(row.get("pdf_file"))
        existing.total_pdf_pages = int(pages) if pd.notna(pages) else None
        existing.book_code = book_by_source.get(source_id)
        count += 1
    return count


def import_redirects(session, excel: Path, mapping) -> int:
    df = read_section(excel, mapping, "id_redirects")
    count = 0
    for _, row in df.iterrows():
        original = _clean(row.get("original_id"))
        active = _clean(row.get("active_id"))
        if not original or not active:
            continue
        if session.get(IdRedirect, original) is None:
            session.add(
                IdRedirect(
                    original_id=original,
                    active_id=active,
                    reason=_clean(row.get("reason")),
                )
            )
            count += 1
    return count


def import_vocabulary(session, excel: Path, mapping) -> int:
    df = read_section(excel, mapping, "vocabulary")
    separator = mapping.sections["vocabulary"].columns.get("alias_separator", ";")
    count = 0
    for _, row in df.iterrows():
        term = _clean(row.get("term"))
        if not term:
            continue
        aliases = _clean(row.get("aliases"))
        if aliases:
            for alias in aliases.split(separator):
                alias = alias.strip()
                if alias:
                    session.add(
                        TermAlias(
                            term=term,
                            alias=alias,
                            entity_type=_clean(row.get("entity_type")),
                            taxonomy_code=_clean(row.get("taxonomy_code")),
                            alias_source="excel",
                        )
                    )
                    count += 1
    return count


def import_knowledge(session, excel: Path, mapping, *, gate: bool = False) -> dict:
    """Nạp knowledge_items + knowledge_pages + evidences. Trả thống kê & báo cáo."""
    df = read_section(excel, mapping, "knowledge_items")
    ev_df = read_section(excel, mapping, "evidence")
    sources = read_section(excel, mapping, "sources").to_dict("records")
    existing = {k.knowledge_id: k for k in session.scalars(select(KnowledgeItem))}

    # evidence theo knowledge_id (tra redirect cho ID đã gộp)
    redirect_map: dict[str, str] = {}
    for r in session.scalars(select(IdRedirect)):
        redirect_map[r.original_id] = r.active_id
    for _, r in read_section(excel, mapping, "id_redirects").iterrows():
        original, active = _clean(r.get("original_id")), _clean(r.get("active_id"))
        if original and active:
            redirect_map[original] = active

    # Validate before touching existing knowledge, evidence or chunks. Source-D
    # release policy is mandatory even when the optional new-knowledge gate is off.
    records = [{**row, "_row": index + 2, "_origin": str(excel)}
               for index, row in enumerate(df.to_dict("records"))]
    policy = validate_records(records, sources, ev_df.to_dict("records"),
                              redirects=redirect_map, existing_ids=existing if gate else
                              {_clean(r.get("knowledge_id")) for r in records}, mapping=mapping)
    if gate:
        policy.require_valid()
    else:
        GateReport(errors=[e for e in policy.errors if e.code.startswith("source_d_")]).require_valid()

    ev_by_kid: dict[str, list[dict]] = defaultdict(list)
    for _, row in ev_df.iterrows():
        kid = _clean(row.get("knowledge_id"))
        if not kid:
            continue
        kid = redirect_map.get(kid, kid)
        ev_by_kid[kid].append(
            {
                "evidence_id": _clean(row.get("evidence_id")) or "",
                "part_number": _clean(row.get("part_number")),
                "pdf_page": row.get("pdf_page"),
                "printed_page": _clean(row.get("printed_page")),
                "original_text": _clean(row.get("original_text")),
                "ocr_legibility": _clean(row.get("ocr_legibility")),
                "evidence_method": _clean(row.get("evidence_method")),
                "origin": _clean(row.get("origin")),
                "source_review_status": _clean(row.get("review_status")),
            }
        )

    # nhóm trùng văn bản (trong cùng sách)
    hash_by_book: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for _, row in df.iterrows():
        book = _clean(row.get("book_code")) or ""
        kid = _clean(row.get("knowledge_id")) or ""
        h = content_hash(row.get("text"))
        hash_by_book[book][h].append(kid)

    dup_group: dict[str, str] = {}
    for book, groups in hash_by_book.items():
        for h, ids in groups.items():
            if len(ids) > 1:
                gid = f"{book}-{h[:12]}"
                for kid in ids:
                    dup_group[kid] = gid

    imported = 0
    rejected = 0
    tier_counts: dict[int, int] = defaultdict(int)
    short_records: list[dict] = []
    unparsed_pages: list[dict] = []
    per_book: dict[str, int] = defaultdict(int)

    for _, row in df.iterrows():
        kid = _clean(row.get("knowledge_id"))
        book = _clean(row.get("book_code"))
        text = _clean(row.get("text"))
        pages_raw = _clean(row.get("pdf_pages_raw"))

        if not kid or not book or not text:
            rejected += 1
            continue

        refs = parse_page_refs(pages_raw, book, mapping)
        if not refs:
            unparsed_pages.append(
                {"knowledge_id": kid, "book_code": book, "pdf_pages_raw": pages_raw}
            )

        record = {
            "book_code": book,
            "review_flag": _clean(row.get("review_flag")),
        }
        tier = assign_tier(record, mapping)
        tier_counts[tier] += 1
        per_book[book] += 1

        h = content_hash(text)
        if len(text) < 40:
            short_records.append(
                {"knowledge_id": kid, "book_code": book, "chars": len(text), "tier": tier}
            )

        item = existing.get(kid)
        if item is None:
            item = KnowledgeItem(knowledge_id=kid, book_code=book, text=text)
            session.add(item)
            imported += 1
        else:
            if item.content_hash != h:
                item.version = (item.version or 1) + 1
            item.text = text
            imported += 1

        item.knowledge_type = _clean(row.get("knowledge_type"))
        item.taxonomy_code = _clean(row.get("taxonomy_code"))
        item.subject = _clean(row.get("subject"))
        item.predicate = _clean(row.get("predicate"))
        item.object = _clean(row.get("object"))
        item.condition_context = _clean(row.get("condition_context"))
        item.chapter = _clean(row.get("chapter"))
        item.source_certainty = _clean(row.get("source_certainty"))
        item.review_flag = record["review_flag"]
        item.release_status = _clean(row.get("release_status"))
        item.validation_status = _clean(row.get("validation_status"))
        item.conflict_status = _clean(row.get("conflict_status"))
        item.dedupe_status = _clean(row.get("dedupe_status"))
        item.trust_tier = tier
        item.duplicate_text_group = dup_group.get(kid)
        item.content_hash = h
        item.updated_at = datetime.now(timezone.utc)

        # pages: thay thế (1 bản ghi có thể nhiều trang)
        session.execute(delete(KnowledgePage).where(KnowledgePage.knowledge_id == kid))
        for ref in refs:
            session.add(
                KnowledgePage(
                    knowledge_id=kid,
                    part_number=ref.part_number,
                    pdf_page=ref.pdf_page,
                )
            )

        # evidence: thay thế
        session.execute(delete(Evidence).where(Evidence.knowledge_id == kid))
        for ev in ev_by_kid.get(kid, []):
            page = ev["pdf_page"]
            session.add(
                Evidence(
                    evidence_id=ev["evidence_id"],
                    knowledge_id=kid,
                    book_code=book,
                    part_number=ev["part_number"],
                    pdf_page=int(page) if pd.notna(page) else None,
                    printed_page=ev["printed_page"],
                    original_text=ev["original_text"],
                    ocr_legibility=ev["ocr_legibility"],
                    evidence_method=ev["evidence_method"],
                    origin=ev["origin"],
                    source_review_status=ev["source_review_status"],
                    verification_status="unverified",
                )
            )

    # chunk cũ không còn hợp lệ (sẽ build lại ở T05) — xoá để tránh chunk mồ côi
    session.execute(delete(ChunkMember))
    session.execute(delete(Chunk))

    return {
        "imported": imported,
        "rejected": rejected,
        "tier_counts": dict(tier_counts),
        "per_book": dict(per_book),
        "short_records": short_records,
        "unparsed_pages": unparsed_pages,
        "duplicate_groups": len({g for g in dup_group.values()}),
    }


def write_reports(stats: dict, mapping, report_dir: Path) -> dict:
    report_dir.mkdir(parents=True, exist_ok=True)

    tier_df = pd.DataFrame(
        [{"trust_tier": t, "count": c, "label": mapping.tier_label(t)}
         for t, c in sorted(stats["tier_counts"].items())]
    )
    tier_df.to_csv(report_dir / "tier_report.csv", index=False, encoding="utf-8")

    pd.DataFrame(stats["short_records"]).to_csv(
        report_dir / "short_records.csv", index=False, encoding="utf-8"
    )
    pd.DataFrame(stats["unparsed_pages"]).to_csv(
        report_dir / "unparsed_pages.csv", index=False, encoding="utf-8"
    )

    summary = {
        "imported": stats["imported"],
        "rejected": stats["rejected"],
        "per_book": stats["per_book"],
        "tier_counts": {str(k): v for k, v in stats["tier_counts"].items()},
        "enabled_tiers": sorted(mapping.enabled_tiers),
        "duplicate_text_groups": stats["duplicate_groups"],
        "short_records": len(stats["short_records"]),
        "unparsed_pages": len(stats["unparsed_pages"]),
    }
    (report_dir / "import_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def check_counts(mapping, per_book: dict) -> bool:
    """Đối chiếu số lượng với expected_counts — lệch thì cảnh báo."""
    ok = True
    for book, expected in mapping.expected_counts.items():
        if book == "total":
            continue
        actual = per_book.get(book, 0)
        flag = "OK" if actual == expected else "LỆCH"
        if actual != expected:
            ok = False
        print(f"  {book}: {actual} / kỳ vọng {expected}  [{flag}]")
    expected_total = mapping.expected_counts.get("total")
    if expected_total:
        actual_total = sum(per_book.values())
        flag = "OK" if actual_total == expected_total else "LỆCH"
        if actual_total != expected_total:
            ok = False
        print(f"  TOTAL: {actual_total} / kỳ vọng {expected_total}  [{flag}]")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="Import Excel canonical vào SQLite")
    ap.add_argument("--excel", type=Path, default=None)
    ap.add_argument("--mapping", type=Path, default=MAPPING_PATH)
    ap.add_argument("--report-dir", type=Path, default=REPORTS_DIR)
    ap.add_argument("--gate", action="store_true",
                    help="Kiểm tra tri thức mới trước khi ghi DB; nguồn FORUM/VIDEO luôn bị kiểm soát.")
    ap.add_argument(
        "--allow-count-mismatch",
        action="store_true",
        help="Không dừng khi số lượng lệch expected_counts",
    )
    args = ap.parse_args()

    mapping = load_mapping(args.mapping)
    excel = find_excel(args.excel, mapping)
    file_hash = sha256_file(excel)

    print(f"Excel: {excel}")
    print(f"SHA-256: {file_hash}")

    if args.gate:
        baseline = existing_knowledge_ids(DB_PATH) if DB_PATH.exists() else ()
        preflight = validate_path(excel, mapping=mapping, existing_ids=baseline)
        if not preflight.ok:
            for error in preflight.errors:
                print(f"{error.origin}:{error.row or '?'} {error.knowledge_id} [{error.code}] {error.message}")
            return 1

    init_db()
    with session_scope() as session:
        n_books = import_books(session, excel, mapping)
        session.flush()
        n_parts = import_book_parts(session, excel, mapping)

        print("\nĐối chiếu số lượng bản ghi:")
        stats = import_knowledge(session, excel, mapping, gate=args.gate)
        counts_ok = check_counts(mapping, stats["per_book"])

        n_redirects = import_redirects(session, excel, mapping)
        n_alias = import_vocabulary(session, excel, mapping)
        session.flush()

        # import_runs: ghi lại lần import
        run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        session.add(
            ImportRun(
                run_id=run_id,
                file_name=excel.name,
                file_sha256=file_hash,
                finished_at=datetime.now(timezone.utc),
                rows_read=stats["imported"] + stats["rejected"],
                rows_imported=stats["imported"],
                rows_rejected=stats["rejected"],
                report_path=str(args.report_dir / "import_summary.json"),
            )
        )

    summary = write_reports(stats, mapping, args.report_dir)

    print(f"\nSách: {n_books}, parts: {n_parts}, redirects: {n_redirects}, alias: {n_alias}")
    print(f"Bản ghi: {summary['imported']} (loại {summary['rejected']})")
    print(f"Tier: {summary['tier_counts']}  |  enabled: {summary['enabled_tiers']}")
    print(f"Nhóm trùng văn bản: {summary['duplicate_text_groups']}")
    print(f"Báo cáo: {args.report_dir}")

    if not counts_ok and not args.allow_count_mismatch:
        print("\nSố lượng lệch expected_counts — dừng. Dùng --allow-count-mismatch để tiếp.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
