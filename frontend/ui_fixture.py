"""KMS Tử Vi — UI Fixture Provider.

Allows offline UI testing and inspection when KMS_UI_FIXTURE=1 without
modifying production backend behaviors.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any, Generator

ROOT_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT_DIR / "tests" / "fixtures" / "ui"


def is_fixture_mode() -> bool:
    """Returns True if KMS_UI_FIXTURE environment variable is enabled ('1')."""
    return os.getenv("KMS_UI_FIXTURE", "").strip() == "1"


def load_fixture(name: str) -> dict[str, Any] | list[Any]:
    """Loads a JSON fixture by name from tests/fixtures/ui/{name}.json."""
    if not name.endswith(".json"):
        name = f"{name}.json"

    file_path = FIXTURES_DIR / name
    if not file_path.exists():
        raise FileNotFoundError(f"Fixture file not found: {file_path}")

    return json.loads(file_path.read_text(encoding="utf-8"))


def mock_reading_events(
    payload: dict[str, Any] | None = None,
) -> Generator[dict[str, Any], None, None]:
    """Simulates the NDJSON event stream of /api/v1/horoscope/read-stream using sample_report.json."""
    raw_report = load_fixture("sample_report")
    report = copy.deepcopy(raw_report) if isinstance(raw_report, dict) else {}

    if payload and isinstance(payload, dict):
        if "ho_ten" in payload and payload["ho_ten"]:
            report["ho_ten"] = payload["ho_ten"]

    yield {
        "event": "progress",
        "elapsed_ms": 35,
        "message": "Nạp dữ kiện bản mẫu lá số (KMS_UI_FIXTURE)...",
    }
    yield {
        "event": "chart_ready",
        "report": report,
    }
    yield {
        "event": "prepared",
        "report": report,
    }
    yield {
        "event": "result",
        "report": report,
    }


def mock_ask_horoscope(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Returns sample_ask.json fixture for quick horoscope questions."""
    raw_ask = load_fixture("sample_ask")
    ask_data = copy.deepcopy(raw_ask) if isinstance(raw_ask, dict) else {}
    if payload and isinstance(payload, dict):
        if "question" in payload:
            ask_data["question"] = payload["question"]
        if "topic" in payload:
            ask_data["topic"] = payload["topic"]
    return ask_data


def mock_stats() -> dict[str, Any]:
    """Returns sample_stats.json fixture."""
    data = load_fixture("sample_stats")
    return copy.deepcopy(data) if isinstance(data, dict) else {}


def mock_search(query: str | None = None) -> dict[str, Any]:
    """Returns sample_search.json fixture."""
    data = load_fixture("sample_search")
    search_data = copy.deepcopy(data) if isinstance(data, dict) else {}
    if query:
        search_data["query"] = query
    return search_data


def mock_dossier(star: str | None = None) -> dict[str, Any]:
    """Returns sample_dossier.json fixture."""
    data = load_fixture("sample_dossier")
    dossier_data = copy.deepcopy(data) if isinstance(data, dict) else {}
    if star:
        dossier_data["name"] = star
    return dossier_data
