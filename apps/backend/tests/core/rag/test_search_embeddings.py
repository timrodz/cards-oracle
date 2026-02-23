from app.core.rag.search import RagSearch


class _FakeEmbeddingProvider:
    def __init__(self) -> None:
        self.last_normalize: bool | None = None

    def embed_text(self, _text: str, *, normalize: bool) -> list[float]:
        self.last_normalize = normalize
        return [0.1, 0.2]


def test_search_uses_requested_embedding_normalization(monkeypatch) -> None:
    fake_embedder = _FakeEmbeddingProvider()
    monkeypatch.setattr(
        "app.core.rag.search.get_embedding_provider",
        lambda: fake_embedder,
    )
    monkeypatch.setattr(
        RagSearch,
        "_RagSearch__vector_search",
        lambda _self, query_vector: [],
    )

    rag_search = RagSearch(db=None)  # type: ignore
    assert rag_search.search("hello", normalize_embeddings=False) is None
    assert fake_embedder.last_normalize is False


def test_search_stream_uses_requested_embedding_normalization(monkeypatch) -> None:
    fake_embedder = _FakeEmbeddingProvider()
    monkeypatch.setattr(
        "app.core.rag.search.get_embedding_provider",
        lambda: fake_embedder,
    )
    monkeypatch.setattr(
        RagSearch,
        "_RagSearch__vector_search",
        lambda _self, query_vector: [],
    )

    rag_search = RagSearch(db=None)  # type: ignore
    _ = list(rag_search.search_stream("hello", normalize_embeddings=False))
    assert fake_embedder.last_normalize is False
