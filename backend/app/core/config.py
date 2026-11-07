"""Cấu hình runtime. Nạp .env thủ công (không phụ thuộc python-dotenv)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _load_env(env_path: Path | None = None) -> None:
    env = env_path if env_path is not None else (ROOT / ".env")
    if not env.is_file():
        return
    preserve = os.getenv("KMS_PRESERVE_SYSTEM_ENV", "").strip().lower() in ("1", "true", "yes")
    lines = env.read_text(encoding="utf-8-sig").splitlines()
    if not preserve:
        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.startswith("#") or "=" not in line_str:
                continue
            key, val = line_str.split("=", 1)
            if key.strip() == "KMS_PRESERVE_SYSTEM_ENV" and val.strip().strip('"').strip("'").lower() in ("1", "true", "yes"):
                preserve = True
                break
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            k = key.strip()
            v = value.strip().strip('"').strip("'")
            if not k:
                continue
            if preserve:
                os.environ.setdefault(k, v)
            else:
                os.environ[k] = v


_load_env()

PRESERVE_SYSTEM_ENV = os.getenv("KMS_PRESERVE_SYSTEM_ENV", "").strip().lower() in ("1", "true", "yes")

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
LLM_PROVIDER = os.getenv("KMS_LLM_PROVIDER", "auto")  # auto (gemini chính -> groq dự phòng) | gemini | groq | mock
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
HOROSCOPE_PROVIDER = os.getenv("KMS_HOROSCOPE_PROVIDER", "auto")  # auto (gemini chính -> groq dự phòng) | gemini | groq | mock
GEMINI_MODEL = os.getenv("KMS_GEMINI_MODEL", "gemini-3.8-flash")
LLM_MAX_TOKENS = int(os.getenv("KMS_LLM_MAX_TOKENS", "2048"))
LLM_TEMPERATURE = float(os.getenv("KMS_LLM_TEMPERATURE", "0.0"))
ENABLE_QUERY_CACHE = os.getenv("KMS_ENABLE_QUERY_CACHE", "true").lower() in ("true", "1", "yes")

# --- horoscope ---
# Horoscope uses a separate model and bounded request, leaving the KMS chat setting intact.
HOROSCOPE_MODEL = os.getenv("KMS_HOROSCOPE_MODEL", "gemini-3.5-flash-lite")
HOROSCOPE_TIMEOUT_SECONDS = min(60.0, max(5.0, float(os.getenv("KMS_HOROSCOPE_TIMEOUT_SECONDS", "45"))))
HOROSCOPE_MAX_TOKENS = int(os.getenv("KMS_HOROSCOPE_MAX_TOKENS", "12288"))
HOROSCOPE_MAX_TOKENS_GIAI_THICH = int(os.getenv("KMS_HOROSCOPE_MAX_TOKENS_GIAI_THICH", "12288"))
HOROSCOPE_MAX_TOKENS_CHUYEN_SAU = int(os.getenv("KMS_HOROSCOPE_MAX_TOKENS_CHUYEN_SAU", "12288"))
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
