import sys
from types import SimpleNamespace

import pytest

from app.core.embeddings.openai import OpenAIEmbeddingProvider


class _FakeEmbeddingsAPI:
    def __init__(self, data: list[list[float]], *, should_raise: bool = False) -> None:
        self._data = data
        self._should_raise = should_raise
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self._should_raise:
            raise RuntimeError("boom")
        return SimpleNamespace(
            data=[SimpleNamespace(embedding=embedding) for embedding in self._data]
        )


class _FakeOpenAIClient:
    instances: list["_FakeOpenAIClient"] = []
    embeddings_data: list[list[float]] = [[3.0, 4.0]]
    should_raise: bool = False

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.embeddings = _FakeEmbeddingsAPI(
            self.embeddings_data,
            should_raise=self.should_raise,
        )
        self.__class__.instances.append(self)


def _install_fake_openai_module(monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeOpenAIClient.instances.clear()
    _FakeOpenAIClient.embeddings_data = [[3.0, 4.0]]
    _FakeOpenAIClient.should_raise = False
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=_FakeOpenAIClient))


def test_openai_embedding_provider_requires_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_openai_module(monkeypatch)

    with pytest.raises(RuntimeError, match="LLM_API_KEY is required"):
        OpenAIEmbeddingProvider(
            api_key=None,
            model_name="text-embedding-3-small",
            model_dimensions=2,
            endpoint=None,
            timeout_seconds=60,
        )


def test_openai_embedding_provider_sends_dimensions_and_normalizes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_openai_module(monkeypatch)

    provider = OpenAIEmbeddingProvider(
        api_key="test-key",
        model_name="text-embedding-3-small",
        model_dimensions=2,
        endpoint="https://api.openai.com/v1",
        timeout_seconds=45,
    )

    result = provider.embed_text("hello", normalize=True)
    assert result == pytest.approx([0.6, 0.8], rel=1e-6)

    instance = _FakeOpenAIClient.instances[0]
    assert instance.kwargs["api_key"] == "test-key"
    assert instance.kwargs["base_url"] == "https://api.openai.com/v1"
    assert instance.kwargs["timeout"] == 45

    call = instance.embeddings.calls[0]
    assert call["model"] == "text-embedding-3-small"
    assert call["input"] == ["hello"]
    assert call["dimensions"] == 2
    assert call["encoding_format"] == "float"


def test_openai_embedding_provider_raises_on_dimension_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_openai_module(monkeypatch)
    _FakeOpenAIClient.embeddings_data = [[1.0, 2.0, 3.0]]

    provider = OpenAIEmbeddingProvider(
        api_key="test-key",
        model_name="text-embedding-3-small",
        model_dimensions=2,
        endpoint=None,
        timeout_seconds=60,
    )

    with pytest.raises(RuntimeError, match="dimension mismatch"):
        provider.embed_text("hello", normalize=False)


def test_openai_embedding_provider_wraps_client_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_openai_module(monkeypatch)
    _FakeOpenAIClient.should_raise = True

    provider = OpenAIEmbeddingProvider(
        api_key="test-key",
        model_name="text-embedding-3-small",
        model_dimensions=2,
        endpoint=None,
        timeout_seconds=60,
    )

    with pytest.raises(RuntimeError, match="openai embeddings failed"):
        provider.embed_text("hello", normalize=False)
