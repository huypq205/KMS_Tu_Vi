# -*- coding: utf-8 -*-
"""Final content fixes for the report markdown (idempotent)."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
path = Path("docs/REPORT_KMS_TU_Vi.md") if False else Path("docs/REPORT_KMS_TU_VI.md")
text = path.read_text(encoding="utf-8")

fixes = [
    (
        "| Sản phẩm | Nội dung | API | Không dùng AI |",
        "| Sản phẩm | Nội dung | API | Dùng LLM |",
    ),
    (
        "| Hỏi đáp theo sách | Trả lời tách theo 3 sách, có trích dẫn | `POST /api/v1/chat/ask` | Không (dùng LLM) |",
        "| Hỏi đáp theo sách | Trả lời tách theo 3 sách, có trích dẫn | `POST /api/v1/chat/ask` | Có |",
    ),
    (
        "| Luận giải lá số | Bài luận 7 khối + dẫn `fact_id`/nguồn | `POST /api/v1/horoscope/read` | Không (dùng LLM) |",
        "| Luận giải lá số | Bài luận 7 khối + dẫn `fact_id`/nguồn | `POST /api/v1/horoscope/read` | Có |",
    ),
    (
        "| Báo cáo sử dụng AI | `docs/BAO_CAO_SU_DUNG_AI.md` (một phần đã lỗi thời — xem Phụ lục C) |",
        "| Báo cáo sử dụng AI | `docs/BAO_CAO_SU_DUNG_AI.md` |",
    ),
]

changed = 0
for old, new in fixes:
    if old in text:
        text = text.replace(old, new, 1)
        changed += 1
    elif new in text:
        print(f"ALREADY: {new[:50]}...")
    else:
        print(f"NOT FOUND: {old[:70]}...")

if changed:
    path.write_text(text, encoding="utf-8")
print("changed:", changed)
