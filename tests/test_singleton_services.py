"""Tối ưu G1 — tài nguyên nặng phải là singleton cấp tiến trình.

- Vector store (Qdrant local / numpy) chỉ mở 1 lần, không mở lại mỗi request/mỗi sách.
- Embedding adapter (model bge-m3) chỉ tạo 1 lần.
- Retriever và RAGPipeline được các endpoint chia sẻ chung.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path
from types import ModuleType
import pytest


@pytest.fixture
def isolated_store(monkeypatch):
    """Test factory lifetime without opening production Qdrant files."""
    import backend.app.services.vector_store as vs
    calls=[]
    class CountingStore:
        def __init__(self): calls.append(1)
    module=ModuleType('backend.app.services.vector_store_qdrant')
    module.QdrantVectorStore=CountingStore
    monkeypatch.setitem(sys.modules,module.__name__,module)
    monkeypatch.setattr(vs,'VECTOR_STORE','qdrant')
    monkeypatch.setattr(vs,'_store_instance',None)
    return vs,calls


def test_get_vector_store_is_singleton(isolated_store):
    vs,_=isolated_store
    a = vs.get_vector_store()
    b = vs.get_vector_store()
    assert a is b


def test_vector_store_instantiated_once(isolated_store):
    vs,calls=isolated_store
    vs.get_vector_store()
    vs.get_vector_store()
    vs.get_vector_store()
    assert len(calls) == 1


def test_get_embedding_adapter_is_singleton(monkeypatch):
    import backend.app.services.embeddings as emb

    class FakeAdapter:
        instances = 0

        def __init__(self, *args, **kwargs):
            type(self).instances += 1

    monkeypatch.setattr(emb, "EmbeddingAdapter", FakeAdapter)
    monkeypatch.setattr(emb, "_adapter_instance", None, raising=False)
    a = emb.get_embedding_adapter()
    b = emb.get_embedding_adapter()
    assert a is b
    assert FakeAdapter.instances == 1


def test_retriever_uses_shared_adapter(monkeypatch):
    import backend.app.services.embeddings as emb
    from backend.app.services.retriever import Retriever

    fake = object()
    monkeypatch.setattr(emb, "_adapter_instance", fake)
    r = Retriever()
    assert r.embedder is fake
    assert Retriever().embedder is fake


def test_main_retriever_and_pipeline_are_shared():
    from backend.app import main

    r1, r2 = main.get_retriever(), main.get_retriever()
    assert r1 is r2
    p1, p2 = main.get_rag_pipeline(), main.get_rag_pipeline()
    assert p1 is p2
    assert p1.retriever is r1


def test_embedding_factory_import_does_not_require_model_package():
    code='''import sys
sys.modules['sentence_transformers']=None
from backend.app.services import embeddings
class Fake:
    pass
embeddings.EmbeddingAdapter=Fake
assert embeddings.get_embedding_adapter() is embeddings.get_embedding_adapter()
'''
    result=subprocess.run([sys.executable,'-c',code],cwd=Path(__file__).resolve().parents[1],
                          capture_output=True,text=True)
    assert result.returncode==0,result.stderr
