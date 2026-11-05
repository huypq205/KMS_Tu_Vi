# -*- coding: utf-8 -*-
"""Verify the rebuilt DOCX: structure, stray markdown, table sanity."""
import re
import sys

from docx import Document

sys.stdout.reconfigure(encoding="utf-8")
DOC = r"docs\REPORT_KMS_TU_VI.docx"
d = Document(DOC)

print("paragraphs:", len(d.paragraphs), "tables:", len(d.tables))
print("\n== Headings ==")
for p in d.paragraphs:
    if p.style.name.startswith("Heading"):
        print(f"  [{p.style.name}] {p.text}")

print("\n== First 14 paragraphs (cover) ==")
for p in d.paragraphs[:14]:
    if p.text.strip():
        print("  ", repr(p.text[:110]))

all_text = "\n".join(p.text for p in d.paragraphs)
for t in d.tables:
    for row in t.rows:
        for c in row.cells:
            all_text += "\n" + c.text

print("\n== Stray markdown markers ==")
for marker, pat in [
    ("bold **", r"\*\*"),
    ("backtick", r"`"),
    ("md link", r"\]\("),
    ("md heading ##", r"(?m)^#{1,4} "),
    ("table pipe", r"(?m)^\|"),
]:
    hits = re.findall(pat, all_text)
    print(f"  {marker}: {len(hits)}")

print("\n== Longest code lines (diagram width check) ==")
# code paragraphs are those in Normal with Consolas runs
longest = []
for p in d.paragraphs:
    fonts = {r.font.name for r in p.runs}
    if fonts == {"Consolas"}:
        for line in p.text.split("\n"):
            longest.append((len(line), line))
longest.sort(reverse=True)
for n, line in longest[:6]:
    print(f"  {n:3d} | {line[:110]}")

print("\n== Table sizes ==")
for i, t in enumerate(d.tables):
    widths = len(t.columns)
    print(f"  table {i:2d}: {len(t.rows)} rows x {widths} cols | header={t.rows[0].cells[0].text[:28]!r}")

print("\n== Keyword presence ==")
checks = [
    "05/11/2026", "17 endpoint", "2.298", "2.307", "351 xfailed",
    "KMS_HOROSCOPE_PROVIDER", "reading_mode", "cach_cuc_detector",
    "Mức tập trung tín hiệu", "0,5882", "30/4.350", "PHỤ LỤC E", "2.665",
]
for c in checks:
    print(f"  {'OK ' if c in all_text else 'MISS'} {c}")
