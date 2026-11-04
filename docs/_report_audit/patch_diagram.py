# -*- coding: utf-8 -*-
"""Replace the §3.1 architecture diagram with an aligned tree diagram (idempotent)."""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
path = Path("docs/REPORT_KMS_TU_VI.md")
text = path.read_text(encoding="utf-8")

diagram = """```text
NGUỒN TRI THỨC: 3 sách Tử Vi (NPL · BD · DAU)
+ tài liệu tham khảo từ bộ skill (ngoài canonical, có gán nguồn)
        │
        │  BUILD — import_excel.py + knowledge_gate.py (T7)
        ▼
├─ HOLD — data/processed/kms.db (17 bảng nghiệp vụ + 6 bảng FTS5)
│    10.456 knowledge_items · 10.492 evidences · 4.350 chunks
│    chunk_members 8.680 · audit_samples 300 · trust tier 1/2/3/9
│    chunks_fts 4.350 · Qdrant vector 30/4.350 chunk đã embed
        │
        │  POOL — truy xuất, không gọi LLM
        ▼
├─ Retriever hybrid: FTS5 + dense + RRF k=60, top-10 mỗi sách
│  RAG bridge: AND tên sao đầy đủ, tier 1–3, tối đa 22 chunk
│  Hồ sơ sao 14 nhóm · Vận năm 4 tầng · Nhật ký nghiệm lý
        │
        │  USE — gọi LLM có kiểm soát (hoặc không gọi LLM)
        ▼
├─ 3 mức đọc: du_lieu · giai_thich · chuyen_sau
│  Provider: mock | gemini | deepseek | groq (chuỗi dự phòng)
│  Kiểm soát: chứng cứ + phản chứng · 4 bậc tin cậy · C/D
│  Citation validator · lọc nội dung nhạy cảm · cache v8
        │
        ▼
GIAO DIỆN — app.py, 3 trang:
  Luận giải lá số (7 khối + lá số 12 cung) · Hồ sơ sao · Nhật ký nghiệm lý
```"""

pat = re.compile(r"### 3\.1\. Sơ đồ luồng tri thức\n\n```.*?\n```", re.S)
m = pat.search(text)
if not m:
    print("PATTERN NOT FOUND")
elif "├─ HOLD" in m.group(0):
    print("ALREADY PATCHED")
else:
    text = text[:m.start()] + "### 3.1. Sơ đồ luồng tri thức\n\n" + diagram + text[m.end():]
    path.write_text(text, encoding="utf-8")
    print("PATCHED")
