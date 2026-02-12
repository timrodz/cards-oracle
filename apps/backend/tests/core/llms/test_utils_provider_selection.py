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
            timeout_seconds=60,
            endpoint=None,
        ),
    )
    monkeypatch.setattr(utils, "OllamaProvider", lambda *_args: expected)

    assert utils.get_llm_provider() is expected


def test_get_llm_provider_selects_zai(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = object()
    monkeypatch.setattr(
        utils,
        "llm_settings",
        SimpleNamespace(
            provider="zai",
            model_name="glm-4.7",
            timeout_seconds=60,
            endpoint="https://api.z.ai/api/paas/v4/",
            zai_api_key="test-key",
        ),
    )
    monkeypatch.setattr(utils, "ZaiProvider", lambda *_args: expected)

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
            timeout_seconds=60,
            endpoint=None,
        ),
    )

    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER: unknown"):
        utils.get_llm_provider()


def test_settings_requires_llm_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    with pytest.raises(ValidationError, match="llm_provider"):
        Settings(_env_file=None)
