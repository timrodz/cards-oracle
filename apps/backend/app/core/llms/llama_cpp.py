from collections.abc import Iterator
from pathlib import Path
from typing import Any

from loguru import logger

from app.core.llms.provider import LLMProvider


class LlamaCppProvider(LLMProvider):
    def __init__(
        self,
        model: str,
        model_path: str | None,
        timeout: int,
        endpoint: str | None,
        context_window_tokens: int,
    ) -> None:
        try:
            from llama_cpp import Llama  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - depends on install
            raise RuntimeError(
                "llama-cpp-python is required for LLM_PROVIDER=llama_cpp"
            ) from exc

        if not model_path:
            raise RuntimeError("LLM_MODEL_PATH is required for LLM_PROVIDER=llama_cpp")

        resolved_model_path = Path(model_path).expanduser()
        if not resolved_model_path.is_file():
            raise RuntimeError(
                f"LLM_MODEL_PATH does not point to a valid file: {resolved_model_path}"
            )

        if endpoint:
            logger.warning(
                "LLM_ENDPOINT is ignored for LLM_PROVIDER=llama_cpp "
                "(local in-process inference)"
            )
        if context_window_tokens < 512:
            raise RuntimeError(
                "LLM_CONTEXT_WINDOW_TOKENS must be >= 512 for LLM_PROVIDER=llama_cpp"
            )

        self._model = model
        self._timeout = timeout
        self._client = Llama(
            model_path=str(resolved_model_path),
            n_ctx=context_window_tokens,
            verbose=False,
        )

    def generate(self, prompt: str) -> str:
        try:
            response: Any = self._client.create_chat_completion(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:  # pragma: no cover - runtime dependency behavior
            raise RuntimeError(f"llama_cpp generate failed: {exc}") from exc

        choices = response.get("choices") if isinstance(response, dict) else None
        if not choices:
            return ""
        message = choices[0].get("message", {})
        content = message.get("content")
        return content if isinstance(content, str) else ""

    def stream(self, prompt: str) -> Iterator[str]:
        try:
            stream: Any = self._client.create_chat_completion(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
        except Exception as exc:  # pragma: no cover - runtime dependency behavior
            raise RuntimeError(f"llama_cpp chat stream failed: {exc}") from exc

        try:
            for chunk in stream:
                if not isinstance(chunk, dict):
                    continue
                choices = chunk.get("choices")
                if not choices:
                    continue
                delta = choices[0].get("delta", {})
                content = delta.get("content")
                if isinstance(content, str) and content:
                    yield content
        except Exception as exc:  # pragma: no cover - runtime dependency behavior
            raise RuntimeError(f"llama_cpp chat stream failed: {exc}") from exc
