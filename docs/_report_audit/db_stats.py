# -*- coding: utf-8 -*-
"""Audit current kms.db numbers for the report refresh."""
import json
import os
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "processed" / "kms.db"

print("DB:", DB)
print("size_MB:", round(os.path.getsize(DB) / 1048576, 1))
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cur = con.cursor()


def show(label, sql):
    print(f"\n== {label} ==")
    try:
        for r in cur.execute(sql).fetchall():
            print(r)
    except Exception as e:  # noqa: BLE001
        print("ERR", e)


show("items by book", "select book_code, count(*) from knowledge_items group by book_code")
show("items by release_status",
     "select book_code, release_status, count(*) from knowledge_items "
     "group by book_code, release_status order by 1,2")
show("trust tier", "select trust_tier, count(*) from knowledge_items group by trust_tier order by 1")
show("trust tier x book",
     "select book_code, trust_tier, count(*) from knowledge_items group by 1,2 order by 1,2")
show("validation_status",
     "select validation_status, count(*) from knowledge_items group by 1 order by 2 desc")
show("review_flag", "select review_flag, count(*) from knowledge_items group by 1 order by 2 desc")
show("conflict_status", "select conflict_status, count(*) from knowledge_items group by 1")
show("dedupe_status", "select dedupe_status, count(*) from knowledge_items group by 1")
show("books", "select * from books")
show("import_runs", "select * from import_runs")
show("chunk_members", "select count(*), count(distinct chunk_id) from chunk_members")
show("book_parts", "select book_code, part_number, count(*) from book_parts group by 1,2")
show("audit_samples", "select * from audit_samples limit 3")
print("\n== audit_samples schema ==")
for r in cur.execute("pragma table_info(audit_samples)"):
    print(r)

print("\n== all table schemas ==")
tabs = [r[0] for r in cur.execute(
    "select name from sqlite_master where type='table' and name not like 'chunks_fts%' order by name")]
for t in tabs:
    cols = [c[1] for c in cur.execute(f'pragma table_info("{t}")')]
    print(f"{t:20s} {cols}")

print("\n== index_manifest ==")
man = ROOT / "data" / "processed" / "index_manifest.json"
if man.exists():
    print(json.dumps(json.loads(man.read_text(encoding="utf-8")), ensure_ascii=False, indent=1))
print("\n== import_summary ==")
p = ROOT / "data" / "reports" / "import_summary.json"
if p.exists():
    print(json.dumps(json.loads(p.read_text(encoding="utf-8")), ensure_ascii=False, indent=1)[:3000])
con.close()
