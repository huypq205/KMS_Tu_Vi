# -*- coding: utf-8 -*-
"""Improve table layout in docs/build_report_docx.py (idempotent).

Adds: content-proportional fixed column widths, repeating header row,
row-level cannot-split, and compact cell paragraph spacing.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
path = Path("docs/build_report_docx.py")
text = path.read_text(encoding="utf-8")

new_func = '''def _add_table_layout(tbl, parsed, usable_cm=16.0):
    """Chia độ rộng cột theo nội dung, lặp dòng tiêu đề, không tách hàng."""
    ncol = len(parsed[0])
    weights = []
    for j in range(ncol):
        longest = max(
            len((row[j] if j < len(row) else "").strip()) for row in parsed
        )
        weights.append(max(6.0, min(longest, 90)) ** 0.5)
    total = sum(weights)
    widths = [usable_cm * w / total for w in weights]

    tbl.autofit = False
    tblPr = tbl._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)

    for j, width in enumerate(widths):
        tbl.columns[j].width = Cm(width)
        for row in tbl.rows:
            row.cells[j].width = Cm(width)

    for row in tbl.rows:
        trPr = row._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
    hdr_trPr = tbl.rows[0]._tr.get_or_add_trPr()
    hdr_trPr.append(OxmlElement("w:tblHeader"))


def add_md_table(doc, rows):
    parsed = []
    for row in rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if all(_SEP_RE.fullmatch(c or "") for c in cells):
            continue
        parsed.append(cells)
    if not parsed:
        return
    ncol = len(parsed[0])
    tbl = doc.add_table(rows=1 + len(parsed) - 1, cols=ncol)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    font_size = 10.5 if ncol <= 4 else 9.5
    header, data = parsed[0], parsed[1:]
    for j in range(ncol):
        cell = tbl.cell(0, j)
        cell.text = ""
        _shade_cell(cell, "D9E1F2")
        add_inline(cell.paragraphs[0], header[j] if j < len(header) else "",
                   size=font_size, base_bold=True)
    for i, dr in enumerate(data):
        for j in range(ncol):
            cell = tbl.cell(i + 1, j)
            cell.text = ""
            add_inline(cell.paragraphs[0], dr[j] if j < len(dr) else "",
                       size=font_size)
    for row in tbl.rows:
        for cell in row.cells:
            for par in cell.paragraphs:
                par.paragraph_format.space_before = Pt(1)
                par.paragraph_format.space_after = Pt(1)
                par.paragraph_format.line_spacing = 1.15
    _add_table_layout(tbl, parsed)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


'''

pat = re.compile(r"def add_md_table\(doc, rows\):.*?(?=\ndef add_toc_field)", re.S)
if "_add_table_layout" in text:
    print("ALREADY PATCHED")
elif pat.search(text):
    text = pat.sub(new_func, text, count=1)
    path.write_text(text, encoding="utf-8")
    print("PATCHED")
else:
    print("PATTERN NOT FOUND")
