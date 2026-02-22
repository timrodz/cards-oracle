from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.llms import utils


def test_get_llm_provider_selects_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = object()
    monkeypatch.setattr(
        utils,
        "llm_settings",
        SimpleNamespace(
            provider="ollama",
            model_name="mistral",
            model_path=None,
            timeout_seconds=60,
            context_window_tokens=4096,
            endpoint=None,
        ),
    )
    monkeypatch.setattr(utils, "OllamaProvider", lambda **_kwargs: expected)

    assert utils.get_llm_provider() is expected


def test_get_llm_provider_selects_zai(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = object()
    monkeypatch.setattr(
        utils,
        "llm_settings",
        SimpleNamespace(
            provider="zai",
            model_name="glm-4.7",
            model_path=None,
            timeout_seconds=60,
            context_window_tokens=4096,
            llm_api_key="test-key",
        ),
    )
    monkeypatch.setattr(utils, "ZaiProvider", lambda *_args, **_kwargs: expected)

    assert utils.get_llm_provider() is expected


def test_get_llm_provider_unsupported_provider_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        utils,
        "llm_settings",
        SimpleNamespace(
            provider="unknown",
            model_name="x",
            model_path=None,
            timeout_seconds=60,
            context_window_tokens=4096,
            endpoint=None,
            llm_api_key=None,
        ),
    )

    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER: unknown"):
        utils.get_llm_provider()


def test_settings_requires_llm_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    with pytest.raises(ValidationError, match="llm_provider"):
        Settings(_env_file=None)


def test_settings_expanduser_for_embedding_model_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", "/tmp/test-home")
    settings = Settings(
        _env_file=None,
        llm_provider="ollama",
        embedding_model_path="~/src/ai/embedding/sentence-transformers/all-MiniLM-L6-v2",
    )

    assert settings.embedding_model_path == Path(
        "/tmp/test-home/src/ai/embedding/sentence-transformers/all-MiniLM-L6-v2"
    )


def test_settings_allow_relative_embedding_model_path() -> None:
    settings = Settings(
        _env_file=None,
        llm_provider="ollama",
        embedding_model_path="models/sentence-transformers/all-MiniLM-L6-v2",
    )

    assert settings.embedding_model_path == Path(
        "models/sentence-transformers/all-MiniLM-L6-v2"
    )


def test_settings_default_embedding_provider_is_sentence_transformers() -> None:
    settings = Settings(_env_file=None, llm_provider="ollama")

    assert settings.embedding_provider == "sentence_transformers"


def test_settings_support_legacy_embedding_transformer_env_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EMBEDDING_TRANSFORMER_MODEL_NAME", "legacy-transformer")
    monkeypatch.setenv("EMBEDDING_TRANSFORMER_MODEL_DIMENSIONS", "512")
    settings = Settings(_env_file=None, llm_provider="ollama")

    assert settings.embedding_model_name == "legacy-transformer"
    assert settings.embedding_model_dimensions == 512
