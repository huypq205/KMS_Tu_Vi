"""Compare all 40 vendor entries with the attributed reference table, offline."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.services.tu_hoa_tables import (  # noqa: E402
    STEMS, TU_HOA_CODES, get_tu_hoa_table, normalize_star, PARENT_STARS,
)


def read_vendor_table() -> dict[str, dict[str, str]]:
    """Read AST assignments in lapDiaBan; do not execute code or duplicate its table."""
    app = ast.parse((ROOT / 'vendor/lasotuvi/App.py').read_text(encoding='utf-8'))
    catalog = ast.parse((ROOT / 'vendor/lasotuvi/Sao.py').read_text(encoding='utf-8'))
    canonical = {normalize_star(name): name for name in PARENT_STARS}
    star_names = {}
    for node in catalog.body:
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name) and node.value.func.id == 'Sao'
                and len(node.value.args) >= 2 and isinstance(node.value.args[1], ast.Constant)):
            star_names[node.targets[0].id] = node.value.args[1].value
    function = next(n for n in app.body if isinstance(n, ast.FunctionDef) and n.name == 'lapDiaBan')
    position_names = {}
    for n in ast.walk(function):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'nhapSao'
                and n.args and isinstance(n.args[0], ast.Name)):
            for star in n.args[1:]:
                if isinstance(star, ast.Name) and star.id in star_names:
                    name = normalize_star(star_names[star.id])
                    if name in canonical:
                        position_names[n.args[0].id] = canonical[name]
    variables = dict(zip(('viTriHoaLoc', 'viTriHoaQuyen', 'viTriHoaKhoa', 'viTriHoaKy'), TU_HOA_CODES))
    result = {}
    for node in ast.walk(function):
        if (not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare)
                or not isinstance(node.test.left, ast.Name) or node.test.left.id != 'canNam'
                or len(node.test.ops) != 1 or not isinstance(node.test.ops[0], ast.Eq)
                or not isinstance(node.test.comparators[0], ast.Constant)):
            continue
        can_index = node.test.comparators[0].value
        row = {}
        for assignment in node.body:
            if (isinstance(assignment, ast.Assign) and isinstance(assignment.targets[0], ast.Name)
                    and assignment.targets[0].id in variables and isinstance(assignment.value, ast.Name)):
                row[variables[assignment.targets[0].id]] = position_names[assignment.value.id]
        if row:
            if set(row) != set(TU_HOA_CODES) or not 1 <= can_index <= 10 or STEMS[can_index - 1] in result:
                raise ValueError('Vendor Tứ Hóa AST no longer matches the expected structure.')
            result[STEMS[can_index - 1]] = row
    if set(result) != set(STEMS):
        raise ValueError('Could not read all ten vendor Tứ Hóa rows.')
    return result


def compare_tables() -> dict:
    vendor = read_vendor_table()
    baseline = get_tu_hoa_table('lasotuvi')
    reference = get_tu_hoa_table('hung_ngm_reference')
    return {
        'vendor_source': baseline['source'], 'reference_source': reference['source'],
        'vendor_config_matches': vendor == baseline['by_can'],
        'compared_entries': 40,
        'differences': [{'can': can, 'code': code, 'vendor': vendor[can][code],
                         'reference': reference['by_can'][can][code]}
                        for can in STEMS for code in TU_HOA_CODES
                        if vendor[can][code] != reference['by_can'][can][code]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true', help='Output structured UTF-8 JSON.')
    args = parser.parse_args()
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    report = compare_tables()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Đối chiếu {report['compared_entries']} mục / 10 Can; {len(report['differences'])} khác biệt.")
        for diff in report['differences']:
            print(f"{diff['can']} {diff['code']}: vendor={diff['vendor']} | tham khảo={diff['reference']}")
        print(f"Config lasotuvi khớp vendor: {report['vendor_config_matches']}")
        print('Hai bảng giữ riêng; mặc định dùng lasotuvi. Chưa phân xử bằng sách KMS.')
    return 0 if report['vendor_config_matches'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
