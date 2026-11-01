"""Vector store abstraction (Qdrant local persistent / numpy fallback)."""
from __future__ import annotations

import json
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np

from backend.app.core.config import VECTOR_STORE, QDRANT_PATH, EMBEDDING_DIM
from backend.app.db.models import Chunk


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, chunks: list[Chunk]) -> None:
        pass

    @abstractmethod
    def search(self, query_vec: np.ndarray, top_k: int, book_code: str | None = None) -> list[tuple[str, float]]:
        """Trả về (chunk_id, score)."""
        pass

    @abstractmethod
    def delete(self, chunk_ids: list[str]) -> None:
        pass

    @abstractmethod
    def count(self) -> int:
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class NumpyVectorStore(VectorStore):
    """Fallback đơn giản: lưu vector trong file .npy, metadata trong .jsonl."""

    def __init__(self, path: Path, dim: int):
        self.path = path
        self.dim = dim
        self.vecs_file = path / "vectors.npy"
        self.meta_file = path / "metadata.jsonl"
        self._vecs: np.ndarray | None = None
        self._ids: list[str] = []
        self._meta: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if self.vecs_file.exists():
            self._vecs = np.load(self.vecs_file)
            with open(self.meta_file, "r", encoding="utf-8") as f:
                for line in f:
                    m = json.loads(line)
                    self._ids.append(m["chunk_id"])
                    self._meta[m["chunk_id"]] = m

    def upsert(self, chunks: list[Chunk]) -> None:
        for c in chunks:
            vec = np.frombuffer(bytes.fromhex(c.embed_text), dtype="float32")
            if vec.shape != (self.dim,):
                raise ValueError(f"dim mismatch: {vec.shape} vs {self.dim}")
            if c.chunk_id in self._meta:
                idx = self._ids.index(c.chunk_id)
                self._vecs[idx] = vec
            else:
                self._ids.append(c.chunk_id)
                if self._vecs is None:
                    self._vecs = vec.reshape(1, -1)
                else:
                    self._vecs = np.vstack([self._vecs, vec])
            self._meta[c.chunk_id] = {"chunk_id": c.chunk_id, "book_code": c.book_code}
        self._save()

    def _save(self) -> None:
        if self._vecs is not None:
            np.save(self.vecs_file, self._vecs)
        with open(self.meta_file, "w", encoding="utf-8") as f:
            for m in self._meta.values():
                f.write(json.dumps(m, ensure_ascii=False) + "\n")

    def search(self, query_vec: np.ndarray, top_k: int, book_code: str | None = None) -> list[tuple[str, float]]:
        if self._vecs is None or len(self._ids) == 0:
            return []
        scores = self._vecs @ query_vec
        if book_code:
            mask = np.array([self._meta[i]["book_code"] == book_code for i in self._ids])
            scores = np.where(mask, scores, -1.0)
        order = np.argsort(-scores)[:top_k]
        return [(self._ids[i], float(scores[i])) for i in order if scores[i] > -1.0]

    def delete(self, chunk_ids: list[str]) -> None:
        keep = [i for i in self._ids if i not in chunk_ids]
        if len(keep) == len(self._ids):
            return
        idx = [self._ids.index(c) for c in keep]
        self._vecs = self._vecs[idx] if self._vecs is not None else None
        self._ids = keep
        self._meta = {k: v for k, v in self._meta.items() if k in keep}
        self._save()

    def count(self) -> int:
        return len(self._ids)

    def close(self) -> None:
        pass


_store_instance: VectorStore | None = None
_store_lock = threading.Lock()


def get_vector_store() -> VectorStore:
    """Vector store chia sẻ toàn tiến trình (mở Qdrant local / nạp numpy 1 lần)."""
    global _store_instance
    if _store_instance is not None:
        return _store_instance
    with _store_lock:
        if _store_instance is None:
            if VECTOR_STORE == "qdrant":
                try:
                    from backend.app.services.vector_store_qdrant import QdrantVectorStore
                    _store_instance = QdrantVectorStore()
                except Exception:
                    _store_instance = NumpyVectorStore(QDRANT_PATH, EMBEDDING_DIM)
            else:
                _store_instance = NumpyVectorStore(QDRANT_PATH, EMBEDDING_DIM)
    return _store_instance