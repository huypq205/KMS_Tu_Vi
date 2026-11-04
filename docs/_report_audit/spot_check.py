# -*- coding: utf-8 -*-
"""Spot-check headline numbers used in the updated report."""
import collections
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

import yaml  # noqa: E402

with open("configs/cach_cuc_catalog.yaml", encoding="utf-8") as fh:
    cat = yaml.safe_load(fh)
rules = cat.get("rules", [])
print("cach_cuc rules:", len(rules))
print("nhom:", collections.Counter(r.get("nhom") for r in rules))
print("trang_thai:", collections.Counter(r.get("trang_thai") for r in rules))
print("san_sang_thuc_thi:", sum(1 for r in rules if r.get("san_sang_thuc_thi")))
print("ung_vien_ban_dau:", sum(1 for r in rules if r.get("ung_vien_ban_dau")))
print("nhay_cam:", sum(1 for r in rules if r.get("noi_dung_nhay_cam")))
print("catalog keys:", list(cat.keys()))

with open("configs/tu_hoa_tables.yaml", encoding="utf-8") as fh:
    th = yaml.safe_load(fh)
print("\ntu_hoa keys:", list(th.keys()))
print("tables:", list((th.get("tables") or {}).keys()), "default:", th.get("default_table"))
for name, spec in (th.get("tables") or {}).items():
    print(name, "by_can" in spec, len(spec.get("by_can") or {}))

with open("configs/column_mapping.yaml", encoding="utf-8") as fh:
    cm = yaml.safe_load(fh)
print("\nenabled_tiers:", cm.get("trust_tiers", {}).get("enabled_tiers"))
print("tier rules:", len(cm.get("trust_tiers", {}).get("rules") or []))
print("default_tier:", cm.get("trust_tiers", {}).get("default_tier"))

from backend.app.core.evidence_types import EVIDENCE_TYPE_VALUES  # noqa: E402
print("\nevidence types:", len(EVIDENCE_TYPE_VALUES), list(EVIDENCE_TYPE_VALUES))

from backend.app.services.star_dossier import SLOTS, SEED_STARS, KNOWN_STARS  # noqa: E402
print("\nSLOTS:", len(SLOTS), "SEED_STARS:", len(SEED_STARS), "KNOWN_STARS:", len(KNOWN_STARS))

from backend.app.services.star_meanings_reference import load_meanings  # noqa: E402
try:
    m = load_meanings()
    print("star meanings loaded:", len(m) if hasattr(m, "__len__") else m)
except Exception as exc:  # noqa: BLE001
    print("star meanings load error:", exc)

import sqlite3  # noqa: E402

con = sqlite3.connect("file:data/processed/kms.db?mode=ro", uri=True)
tabs = [r[0] for r in con.execute(
    "select name from sqlite_master where type='table' and name not like 'chunks_fts%'")]
print("\nDB tables (excluding fts shadow):", len(tabs))
print(tabs)
con.close()
