import builtins
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from app.core.llms.llama_cpp import LlamaCppProvider


def _install_fake_llama_module(
    monkeypatch: pytest.MonkeyPatch, llama_cls: type[Any]
) -> None:
    fake_module = SimpleNamespace(Llama=llama_cls)
    monkeypatch.setitem(sys.modules, "llama_cpp", fake_module)


def test_missing_dependency_raises_runtime_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    model_file = tmp_path / "model.gguf"
    model_file.write_text("test")

    monkeypatch.delitem(sys.modules, "llama_cpp", raising=False)
    original_import = builtins.__import__

    def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "llama_cpp":
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(
        RuntimeError, match="llama-cpp-python is required for LLM_PROVIDER=llama_cpp"
    ):
        LlamaCppProvider("model-id", str(model_file), 60, None, 4096)


def test_missing_model_path_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeLlama:
        def __init__(self, **_kwargs: Any) -> None:
            pass

    _install_fake_llama_module(monkeypatch, FakeLlama)
    with pytest.raises(RuntimeError, match="LLM_MODEL_PATH is required"):
        LlamaCppProvider("model-id", None, 60, None, 4096)


def test_invalid_model_path_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeLlama:
        def __init__(self, **_kwargs: Any) -> None:
            pass

    _install_fake_llama_module(monkeypatch, FakeLlama)
    with pytest.raises(RuntimeError, match="LLM_MODEL_PATH does not point"):
        LlamaCppProvider("model-id", "/does/not/exist.gguf", 60, None, 4096)


def test_generate_returns_assistant_content(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    model_file = tmp_path / "model.gguf"
    model_file.write_text("test")

    class FakeLlama:
        def __init__(self, **_kwargs: Any) -> None:
            pass

        def create_chat_completion(self, **_kwargs: Any) -> dict[str, Any]:
            return {"choices": [{"message": {"content": "hello from llama"}}]}

    _install_fake_llama_module(monkeypatch, FakeLlama)
    provider = LlamaCppProvider("model-id", str(model_file), 60, None, 4096)
    assert provider.generate("prompt") == "hello from llama"


def test_stream_yields_text_chunks_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    model_file = tmp_path / "model.gguf"
    model_file.write_text("test")

    class FakeLlama:
        def __init__(self, **_kwargs: Any) -> None:
            pass

        def create_chat_completion(self, **_kwargs: Any) -> list[dict[str, Any]]:
            return [
                {"choices": []},
                {"choices": [{"delta": {"content": None}}]},
                {"choices": [{"delta": {"content": "foo"}}]},
                {"choices": [{"delta": {"content": ""}}]},
                {"choices": [{"delta": {"content": "bar"}}]},
            ]

    _install_fake_llama_module(monkeypatch, FakeLlama)
    provider = LlamaCppProvider("model-id", str(model_file), 60, None, 4096)
    assert list(provider.stream("prompt")) == ["foo", "bar"]


def test_generate_wraps_runtime_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    model_file = tmp_path / "model.gguf"
    model_file.write_text("test")

    class FakeLlama:
        def __init__(self, **_kwargs: Any) -> None:
            pass

        def create_chat_completion(self, **_kwargs: Any) -> dict[str, Any]:
            raise RuntimeError("boom")

    _install_fake_llama_module(monkeypatch, FakeLlama)
    provider = LlamaCppProvider("model-id", str(model_file), 60, None, 4096)
    with pytest.raises(RuntimeError, match="llama_cpp generate failed: boom"):
        provider.generate("prompt")


def test_stream_wraps_iteration_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    model_file = tmp_path / "model.gguf"
    model_file.write_text("test")

    class BrokenStream:
        def __iter__(self) -> "BrokenStream":
            return self

        def __next__(self) -> dict[str, Any]:
            raise RuntimeError("stream exploded")

    class FakeLlama:
        def __init__(self, **_kwargs: Any) -> None:
            pass

        def create_chat_completion(self, **_kwargs: Any) -> BrokenStream:
            return BrokenStream()

    _install_fake_llama_module(monkeypatch, FakeLlama)
    provider = LlamaCppProvider("model-id", str(model_file), 60, None, 4096)
    with pytest.raises(RuntimeError, match="llama_cpp chat stream failed: stream exploded"):
        list(provider.stream("prompt"))


def test_context_window_too_small_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    model_file = tmp_path / "model.gguf"
    model_file.write_text("test")

    class FakeLlama:
        def __init__(self, **_kwargs: Any) -> None:
            pass

    _install_fake_llama_module(monkeypatch, FakeLlama)
    with pytest.raises(RuntimeError, match="LLM_CONTEXT_WINDOW_TOKENS must be >= 512"):
        LlamaCppProvider("model-id", str(model_file), 60, None, 256)
