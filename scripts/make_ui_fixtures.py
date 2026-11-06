"""Script to generate UI fixtures for KMS Tu Vi frontend tests and offline inspection.

Uses backend services directly to generate genuine schemas:
- tests/fixtures/ui/sample_search.json
- tests/fixtures/ui/sample_stats.json
- tests/fixtures/ui/sample_dossier.json
- tests/fixtures/ui/sample_ask.json
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

# Configure stdout for Windows console UTF-8 support
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

FIXTURES_DIR = ROOT_DIR / "tests" / "fixtures" / "ui"


def generate_search_fixture() -> dict:
    """Generates genuine search fixture using backend search service."""
    from backend.app.main import search
    from backend.app.schemas.search import SearchRequest

    req = SearchRequest(query="Tử Vi", top_k=5)
    res = search(req)
    # SearchResponse is a Pydantic model
    return res.model_dump()


def generate_stats_fixture() -> dict:
    """Generates genuine stats fixture from SQLite database."""
    from backend.app.main import stats

    return stats()


def generate_dossier_fixture() -> dict:
    """Generates genuine star dossier fixture for Tử Vi."""
    from backend.app.services.star_dossier import get_star_dossier

    return get_star_dossier("Tử Vi", include_seeds=True)


def generate_ask_fixture() -> dict:
    """Generates genuine quick ask fixture using mock provider."""
    from backend.app.services.horoscope_ask import ask_horoscope
    from backend.app.schemas.horoscope import HoroscopeAskRequest

    req = HoroscopeAskRequest(
        ngay=15,
        thang=8,
        nam=1995,
        chi_gio=5,
        topic="su_nghiep",
        question="Công danh sự nghiệp năm nay thế nào?",
        provider="mock",
    )
    return ask_horoscope(req)


def make_all_fixtures() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    fixtures = [
        ("sample_search.json", generate_search_fixture),
        ("sample_stats.json", generate_stats_fixture),
        ("sample_dossier.json", generate_dossier_fixture),
        ("sample_ask.json", generate_ask_fixture),
    ]

    print("Generating UI fixtures in tests/fixtures/ui/...")
    for filename, generator in fixtures:
        dest_path = FIXTURES_DIR / filename
        data = generator()
        dest_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  - Generated {filename} ({dest_path.stat().st_size:,} bytes)")

    print("All fixtures generated successfully.")


if __name__ == "__main__":
    make_all_fixtures()
