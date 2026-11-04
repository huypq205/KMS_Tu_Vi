# -*- coding: utf-8 -*-
"""Locate stray backticks / '## ' text and inspect code blocks in the DOCX."""
import sys

from docx import Document

sys.stdout.reconfigure(encoding="utf-8")
d = Document(r"docs\REPORT_KMS_TU_VI.docx")


def texts():
    for i, p in enumerate(d.paragraphs):
        yield f"P{i:03d}[{p.style.name}]", p.text
    for ti, t in enumerate(d.tables):
        for ri, row in enumerate(t.rows):
            for ci, c in enumerate(row.cells):
                for p in c.paragraphs:
                    yield f"T{ti}R{ri}C{ci}", p.text


print("== paragraphs/cells containing backtick ==")
for ref, t in texts():
    if "`" in t:
        print(f"  {ref}: {t[:160]!r}")

print("\n== paragraphs/cells starting with '#' ==")
for ref, t in texts():
    if t.lstrip().startswith("#"):
        print(f"  {ref}: {t[:120]!r}")

print("\n== code-block paragraphs (mixed mono) ==")
for i, p in enumerate(d.paragraphs):
    fonts = {r.font.name for r in p.runs if r.text.strip()}
    if fonts == {"Consolas"}:
        lines = p.text.split("\n")
        print(f"  P{i:03d}: {len(lines)} visual lines, max len {max((len(x) for x in lines), default=0)}")
        for line in lines[:4]:
            print(f"      |{line}")
