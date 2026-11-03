"""Cấu hình runtime. Nạp .env thủ công (không phụ thuộc python-dotenv)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env()

# --- đường dẫn ---
EXCEL_PATH = Path(os.getenv("KMS_EXCEL", ROOT / "data/raw/TuVi_KMS_3Books_CANONICAL_MASTER_DEDUP_v1.0.xlsx"))
MAPPING_PATH = Path(os.getenv("KMS_MAPPING", ROOT / "configs/column_mapping.yaml"))
RETRIEVAL_CONFIG = Path(os.getenv("KMS_RETRIEVAL_CONFIG", ROOT / "configs/retrieval.yaml"))
DB_PATH = Path(os.getenv("KMS_DB", ROOT / "data/processed/kms.db"))
QDRANT_PATH = Path(os.getenv("KMS_QDRANT", ROOT / "data/qdrant"))
REPORTS_DIR = Path(os.getenv("KMS_REPORTS", ROOT / "data/reports"))
MANIFEST_PATH = Path(os.getenv("KMS_MANIFEST", ROOT / "data/processed/index_manifest.json"))

# --- embedding / vector ---
EMBEDDING_MODEL = os.getenv("KMS_EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DIM = int(os.getenv("KMS_EMBEDDING_DIM", "1024"))
VECTOR_STORE = os.getenv("KMS_VECTOR_STORE", "qdrant")  # qdrant | numpy
# R4: embedding provider — "local" (sentence-transformers) | "gemini" (Gemini API)
EMBEDDING_PROVIDER = os.getenv("KMS_EMBEDDING_PROVIDER", "local")

# --- LLM ---
LLM_PROVIDER = os.getenv("KMS_LLM_PROVIDER", "gemini")  # gemini | mock
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("KMS_GEMINI_MODEL", "gemini-3.8-flash")
LLM_MAX_TOKENS = int(os.getenv("KMS_LLM_MAX_TOKENS", "2048"))
LLM_TEMPERATURE = float(os.getenv("KMS_LLM_TEMPERATURE", "0.0"))
ENABLE_QUERY_CACHE = os.getenv("KMS_ENABLE_QUERY_CACHE", "true").lower() in ("true", "1", "yes")

# --- horoscope ---
# Horoscope uses a separate model and bounded request, leaving the KMS chat setting intact.
HOROSCOPE_MODEL = os.getenv("KMS_HOROSCOPE_MODEL", "gemini-3.5-flash-lite")
HOROSCOPE_TIMEOUT_SECONDS = min(60.0, max(5.0, float(os.getenv("KMS_HOROSCOPE_TIMEOUT_SECONDS", "45"))))
HOROSCOPE_MAX_TOKENS = int(os.getenv("KMS_HOROSCOPE_MAX_TOKENS", "2500"))
HOROSCOPE_MAX_TOKENS_GIAI_THICH = int(os.getenv("KMS_HOROSCOPE_MAX_TOKENS_GIAI_THICH", "3500"))
HOROSCOPE_MAX_TOKENS_CHUYEN_SAU = int(os.getenv("KMS_HOROSCOPE_MAX_TOKENS_CHUYEN_SAU", "8192"))
# Model dự phòng, thử lần lượt khi model chính quá tải/lỗi tạm thời (phân tách bằng dấu phẩy).
HOROSCOPE_FALLBACK_MODELS = tuple(
    model.strip() for model in os.getenv("KMS_HOROSCOPE_FALLBACK_MODELS", "").split(",") if model.strip()
)
ENABLE_HOROSCOPE_CACHE = os.getenv("KMS_ENABLE_HOROSCOPE_CACHE", "true").lower() in ("true", "1", "yes")

# --- trích dẫn ---
EXCERPT_MAX_CHARS = int(os.getenv("KMS_EXCERPT_MAX_CHARS", "300"))


def ensure_dirs() -> None:
    for path in (DB_PATH.parent, QDRANT_PATH, REPORTS_DIR, MANIFEST_PATH.parent):
        path.mkdir(parents=True, exist_ok=True)
