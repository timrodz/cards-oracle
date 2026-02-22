import sys
from types import SimpleNamespace

import pytest

import app.core.embeddings.openai as openai_provider_module
from app.core.embeddings.openai import OpenAIEmbeddingProvider


class _FakeRateLimitError(Exception):
    pass


class _FakeAPIConnectionError(Exception):
    pass


class _FakeAPITimeoutError(Exception):
    pass


class _FakeAPIStatusError(Exception):
    def __init__(self, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class _FakeEmbeddingsAPI:
    def __init__(self, data: list[list[float]]) -> None:
        self._data = data
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if _FakeOpenAIClient.errors_to_raise:
            raise _FakeOpenAIClient.errors_to_raise.pop(0)
        return SimpleNamespace(
            data=[
                SimpleNamespace(index=index, embedding=embedding)
                for index, embedding in enumerate(self._data)
            ]
        )


class _FakeOpenAIClient:
    instances: list["_FakeOpenAIClient"] = []
    embeddings_data: list[list[float]] = [[3.0, 4.0]]
    errors_to_raise: list[Exception] = []

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.embeddings = _FakeEmbeddingsAPI(self.embeddings_data)
        self.__class__.instances.append(self)


def _install_fake_openai_module(monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeOpenAIClient.instances.clear()
    _FakeOpenAIClient.embeddings_data = [[3.0, 4.0]]
    _FakeOpenAIClient.errors_to_raise = []
    monkeypatch.setitem(
        sys.modules,
        "openai",
        SimpleNamespace(
            OpenAI=_FakeOpenAIClient,
            RateLimitError=_FakeRateLimitError,
            APIConnectionError=_FakeAPIConnectionError,
            APITimeoutError=_FakeAPITimeoutError,
            APIStatusError=_FakeAPIStatusError,
        ),
    )


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


def test_openai_embedding_provider_retries_on_rate_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_openai_module(monkeypatch)
    _FakeOpenAIClient.errors_to_raise = [
        _FakeRateLimitError("rate limit"),
        _FakeRateLimitError("rate limit"),
    ]
    sleep_calls: list[float] = []
    monkeypatch.setattr(openai_provider_module.time, "sleep", sleep_calls.append)

    provider = OpenAIEmbeddingProvider(
        api_key="test-key",
        model_name="text-embedding-3-small",
        model_dimensions=2,
        endpoint=None,
        timeout_seconds=60,
    )

    result = provider.embed_text("hello", normalize=False)
    assert result == [3.0, 4.0]

    instance = _FakeOpenAIClient.instances[0]
    assert len(instance.embeddings.calls) == 3
    assert len(sleep_calls) == 2


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
    _FakeOpenAIClient.errors_to_raise = [RuntimeError("boom")]

    provider = OpenAIEmbeddingProvider(
        api_key="test-key",
        model_name="text-embedding-3-small",
        model_dimensions=2,
        endpoint=None,
        timeout_seconds=60,
    )

    with pytest.raises(RuntimeError, match="openai embeddings failed"):
        provider.embed_text("hello", normalize=False)
