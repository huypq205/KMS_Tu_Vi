#!/usr/bin/env python3
"""Read-only T7 gate for REPO_*.csv exports or the canonical Excel workbook."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.config import MAPPING_PATH  # noqa: E402
from backend.app.services.knowledge_gate import (  # noqa: E402
    GateError, GateReport, existing_knowledge_ids, validate_path,
)
from backend.app.services.mapping import load_mapping  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--mapping', type=Path, default=MAPPING_PATH)
    parser.add_argument('--existing-db', type=Path, help='Read-only baseline; only NEW ids need one of three bases.')
    parser.add_argument('--json', action='store_true', help='Output structured errors with ids, row numbers and origins.')
    args = parser.parse_args()
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        baseline = existing_knowledge_ids(args.existing_db) if args.existing_db else ()
        report = validate_path(args.input, mapping=load_mapping(args.mapping), existing_ids=baseline)
    except (OSError, ValueError, sqlite3.Error) as exc:
        report = GateReport(errors=[GateError('input_error', str(exc), origin=str(args.input))])
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"Knowledge gate: {'PASSED' if report.ok else 'FAILED'}; checked={report.checked}; "
              f'new={report.new_records}; quarantined={len(report.quarantined_ids)}; errors={len(report.errors)}')
        for error in report.errors:
            print(f'{error.origin}:{error.row or "?"} {error.knowledge_id} [{error.code}] {error.message}')
    return 0 if report.ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
