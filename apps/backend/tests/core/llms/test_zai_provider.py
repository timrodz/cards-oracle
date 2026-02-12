import sys
from types import SimpleNamespace

import pytest

from app.core.llms.zai import ZaiProvider


def _install_fake_zai_module(monkeypatch: pytest.MonkeyPatch, client_cls: type) -> None:
    fake_module = SimpleNamespace(ZaiClient=client_cls)
    monkeypatch.setitem(sys.modules, "zai", fake_module)


def test_generate_returns_first_choice_message_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeClient:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=self._create),
            )

        def _create(self, **_kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content="hello from zai"),
                    )
                ]
            )

    _install_fake_zai_module(monkeypatch, FakeClient)

    provider = ZaiProvider("test-key", model="glm-4.7", timeout=60)
    assert provider.generate("test prompt") == "hello from zai"


def test_stream_yields_only_non_empty_delta_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeClient:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=self._create),
            )

        def _create(self, **_kwargs):
            return [
                SimpleNamespace(choices=[]),
                SimpleNamespace(
                    choices=[SimpleNamespace(delta=SimpleNamespace(content=None))]
                ),
                SimpleNamespace(
                    choices=[SimpleNamespace(delta=SimpleNamespace(content="foo"))]
                ),
                SimpleNamespace(
                    choices=[SimpleNamespace(delta=SimpleNamespace(content=""))]
                ),
                SimpleNamespace(
                    choices=[SimpleNamespace(delta=SimpleNamespace(content="bar"))]
                ),
            ]

    _install_fake_zai_module(monkeypatch, FakeClient)

    provider = ZaiProvider("test-key", model="glm-4.7", timeout=60)
    assert list(provider.stream("test prompt")) == ["foo", "bar"]


def test_missing_api_key_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=lambda **_args: None),
            )

    _install_fake_zai_module(monkeypatch, FakeClient)
    with pytest.raises(RuntimeError, match="LLM_API_KEY is required"):
        ZaiProvider("", model="glm-4.7")


def test_generate_wraps_sdk_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=self._create),
            )

        def _create(self, **_kwargs):
            raise RuntimeError("boom")

    _install_fake_zai_module(monkeypatch, FakeClient)

    provider = ZaiProvider("test-key", model="glm-4.7", timeout=60)
    with pytest.raises(RuntimeError, match="zai generate failed: boom"):
        provider.generate("test prompt")


def test_stream_wraps_iteration_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenStream:
        def __iter__(self):
            return self

        def __next__(self):
            raise RuntimeError("stream exploded")

    class FakeClient:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=self._create),
            )

        def _create(self, **_kwargs):
            return BrokenStream()

    _install_fake_zai_module(monkeypatch, FakeClient)

    provider = ZaiProvider("test-key", model="glm-4.7", timeout=60)
    with pytest.raises(RuntimeError, match="zai chat stream failed: stream exploded"):
        list(provider.stream("test prompt"))
