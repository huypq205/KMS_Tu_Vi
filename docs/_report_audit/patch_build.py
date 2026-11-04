# -*- coding: utf-8 -*-
"""Apply the nested-bold/code fix to docs/build_report_docx.py (idempotent)."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
path = Path("docs/build_report_docx.py")
text = path.read_text(encoding="utf-8")

old = '''        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            _add_plain(p, tok[2:-2], size=size, bold=True, italic=base_italic,
                       color=color)
'''
new = '''        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            # Recurse so code/italic nested inside ** (e.g. **`xfail`**) is handled.
            add_inline(p, tok[2:-2], size=size, base_bold=True,
                       base_italic=base_italic, color=color)
'''

if new in text:
    print("ALREADY PATCHED")
elif old in text:
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("PATCHED")
else:
    print("PATTERN NOT FOUND")
