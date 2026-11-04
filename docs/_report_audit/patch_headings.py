# -*- coding: utf-8 -*-
"""Make headings bold with per-level sizes in docs/build_report_docx.py."""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
path = Path("docs/build_report_docx.py")
text = path.read_text(encoding="utf-8")

new = '''def add_heading(doc, text, level):
    h = doc.add_heading("", level=level)
    sizes = {1: 14, 2: 13, 3: 12}
    add_inline(h, text, size=sizes.get(level, BODY_SIZE), base_bold=True)
    return h
'''

pat = re.compile(r"def add_heading\(doc, text, level\):\n.*?\n    return h\n", re.S)
m = pat.search(text)
if not m:
    print("PATTERN NOT FOUND")
elif "sizes = {1: 14" in m.group(0):
    print("ALREADY PATCHED")
else:
    text = text[:m.start()] + new + text[m.end():]
    path.write_text(text, encoding="utf-8")
    print("PATCHED")
