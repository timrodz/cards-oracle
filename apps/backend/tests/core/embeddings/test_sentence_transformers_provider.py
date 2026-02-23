from pathlib import Path

import pytest

from app.core.embeddings import sentence_transformers as st_provider_module
from app.core.embeddings.sentence_transformers import (
    SentenceTransformerEmbeddingProvider,
)


class _FakeArray:
    def __init__(self, values: list[list[float]]) -> None:
        self._values = values

    def tolist(self) -> list[list[float]]:
        return self._values


class _FakeSentenceTransformer:
    return_values: list[list[float]] = [[1.0, 2.0]]
    last_encode_kwargs: dict[str, object] | None = None

    def __init__(self, _model_ref: str, device: str) -> None:
        self.device = device

    def encode(self, _texts: list[str], **kwargs):
        self.__class__.last_encode_kwargs = kwargs
        return _FakeArray(self.return_values)

    def save(self, _path: str) -> None:
        return


def _set_fake_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    SentenceTransformerEmbeddingProvider._load_transformer.cache_clear()
    _FakeSentenceTransformer.return_values = [[1.0, 2.0]]
    _FakeSentenceTransformer.last_encode_kwargs = None
    monkeypatch.setattr(
        st_provider_module,
        "SentenceTransformer",
        _FakeSentenceTransformer,
    )
    monkeypatch.setattr(
        st_provider_module.torch_module.cuda,
        "is_available",
        lambda: False,
    )


def test_sentence_transformer_embedding_provider_passes_normalize_flag(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_fake_dependencies(monkeypatch)

    provider = SentenceTransformerEmbeddingProvider(
        model_name="all-MiniLM-L6-v2",
        model_path=tmp_path,
        model_dimensions=2,
    )

    vectors = provider.embed_texts(["a"], normalize=True)
    assert vectors == [[1.0, 2.0]]
    assert _FakeSentenceTransformer.last_encode_kwargs is not None
    assert _FakeSentenceTransformer.last_encode_kwargs["normalize_embeddings"] is True


def test_sentence_transformer_embedding_provider_raises_on_dimension_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_fake_dependencies(monkeypatch)
    _FakeSentenceTransformer.return_values = [[1.0, 2.0, 3.0]]

    provider = SentenceTransformerEmbeddingProvider(
        model_name="all-MiniLM-L6-v2",
        model_path=tmp_path,
        model_dimensions=2,
    )

    with pytest.raises(RuntimeError, match="dimension mismatch"):
        provider.embed_text("a", normalize=False)
