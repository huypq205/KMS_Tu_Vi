"""Embedding adapter: encode text, upsert Qdrant."""
from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from backend.app.core.config import EMBEDDING_MODEL, EMBEDDING_DIM
from backend.app.db.models import Chunk
from backend.app.services.vector_store import get_vector_store


class EmbeddingAdapter:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
        self.store = get_vector_store()

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Encode danh sách văn bản thành vector (đã chuẩn hóa L2)."""
        vecs = self.model.encode(texts, batch_size=64, normalize_embeddings=True)
        return [v.tolist() for v in vecs]

    def upsert_chunks(self, chunks: list[Chunk]) -> None:
        """Upsert chunks vào vector store."""
        for c in chunks:
            vec = self.model.encode(c.embed_text, normalize_embeddings=True)
            c.embed_text = "".join(f"{int(x*10000):05d}" for x in vec)  # lưu dưới dạng hex
        self.store.upsert(chunks)

    def search(self, query: str, top_k: int, book_code: str | None = None) -> list[tuple[str, float]]:
        """Truy xuất top_k chunk theo vector."""
        vec = self.model.encode(query, normalize_embeddings=True)
        return self.store.search(vec, top_k, book_code)

    def close(self):
        self.store.close()


_adapter_instance: "EmbeddingAdapter | None" = None
_adapter_lock = threading.Lock()


def get_embedding_adapter() -> "EmbeddingAdapter":
    """Adapter embedding chia sẻ toàn tiến trình: model chỉ được nạp 1 lần."""
    global _adapter_instance
    if _adapter_instance is None:
        with _adapter_lock:
            if _adapter_instance is None:
                _adapter_instance = EmbeddingAdapter()
    return _adapter_instance


if __name__ == "__main__":
    adapter = get_embedding_adapter()
    print(f"Model: {EMBEDDING_MODEL}")
    print(f"Dim: {EMBEDDING_DIM}")
    print(f"Store: {type(adapter.store).__name__}")
    print(f"Count: {adapter.store.count()}")
