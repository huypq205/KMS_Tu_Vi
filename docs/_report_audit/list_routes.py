# -*- coding: utf-8 -*-
"""List FastAPI routes for the report (ground truth)."""
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

from backend.app.main import app  # noqa: E402

rows = []
for r in app.routes:
    methods = ",".join(sorted(getattr(r, "methods", []) or []))
    if methods:
        rows.append((methods, r.path))
rows.sort(key=lambda x: (x[1], x[0]))
for m, p in rows:
    print(f"{m:18s} {p}")
print("total_api_routes:", len([1 for m, p in rows if p.startswith("/api")]))
