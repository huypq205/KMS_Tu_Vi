"""Gán trust_tier theo quy tắc trong column_mapping.yaml (quy tắc đầu tiên khớp thắng)."""
from __future__ import annotations

from typing import Any

from .mapping import Mapping
from .knowledge_gate import has_flag, is_source_d_type


def _matches(value: Any, expected: Any) -> bool:
    """expected là chuỗi, hoặc danh sách = 'một trong các giá trị'."""
    if value is None:
        return False
    text = str(value)
    if isinstance(expected, (list, tuple, set)):
        return text in {str(e) for e in expected}
    return text == str(expected)


def _matches_condition(record: dict[str, Any], key: str, expected: Any) -> bool:
    """Khớp một điều kiện trong rule.

    Hậu tố `_contains` = giá trị chứa chuỗi con (vd `review_flag_contains:
    OCR_REVIEW_REQUIRED` -> review_flag chứa "OCR_REVIEW_REQUIRED").
    Hậu tố `_not_contains` = phủ định của trên.
    """
    if key.endswith("_not_contains"):
        base = key[: -len("_not_contains")]
        value = record.get(base)
        if value is None:
            return True
        return str(expected) not in str(value)

    if key.endswith("_contains"):
        base = key[: -len("_contains")]
        value = record.get(base)
        if value is None:
            return False
        return str(expected) in str(value)

    return _matches(record.get(key), expected)


def assign_tier(record: dict[str, Any], mapping: Mapping) -> int:
    """Gán tier cho một bản ghi knowledge. Trả về default_tier nếu không khớp rule nào."""
    # Mandatory quarantine outranks book-specific and user-configured rules.
    if is_source_d_type(record.get("source_type")) or has_flag(record.get("review_flag")):
        return 9
    rules = mapping.trust_tiers.get("rules", [])
    for rule in rules:
        tier = rule.get("tier")
        conditions = rule.get("when", {})
        if tier is None:
            continue
        if all(
            _matches_condition(record, key, expected)
            for key, expected in conditions.items()
        ):
            return int(tier)
    return mapping.default_tier


def rule_description(mapping: Mapping) -> list[dict[str, Any]]:
    """Mô tả quy tắc tier để ghi vào báo cáo."""
    out = []
    for rule in mapping.trust_tiers.get("rules", []):
        out.append({"tier": rule.get("tier"), "when": rule.get("when", {})})
    return out
