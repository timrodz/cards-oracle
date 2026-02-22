from types import SimpleNamespace

import pytest

from app.core.embeddings import utils


@pytest.fixture(autouse=True)
def _clear_provider_cache() -> None:
    utils.get_embedding_provider.cache_clear()


def test_get_embedding_provider_selects_sentence_transformers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = object()
    monkeypatch.setattr(
        utils,
        "transformer_settings",
        SimpleNamespace(
            provider="sentence_transformers",
            model_name="all-MiniLM-L6-v2",
            model_path="models/all-MiniLM-L6-v2",
            model_dimensions=384,
        ),
    )
    monkeypatch.setattr(
        utils,
        "SentenceTransformerEmbeddingProvider",
        lambda **_kwargs: expected,
    )

    assert utils.get_embedding_provider() is expected


def test_get_embedding_provider_selects_openai(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = object()
    monkeypatch.setattr(
        utils,
        "transformer_settings",
        SimpleNamespace(
            provider="openai",
            model_name="text-embedding-3-small",
            model_path="unused",
            model_dimensions=256,
        ),
    )
    monkeypatch.setattr(
        utils,
        "llm_settings",
        SimpleNamespace(
            llm_api_key="test-key",
            endpoint="https://api.openai.com/v1",
            timeout_seconds=30,
        ),
    )
    monkeypatch.setattr(utils, "OpenAIEmbeddingProvider", lambda **_kwargs: expected)

    assert utils.get_embedding_provider() is expected


def test_get_embedding_provider_unsupported_provider_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        utils,
        "transformer_settings",
        SimpleNamespace(
            provider="unsupported",
            model_name="x",
            model_path="y",
            model_dimensions=1,
        ),
    )

    with pytest.raises(
        ValueError,
        match="Unsupported EMBEDDING_PROVIDER: unsupported",
    ):
        utils.get_embedding_provider()
