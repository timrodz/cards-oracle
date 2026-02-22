from typing import Any, Iterator, Optional

from app.core.llms.provider import LLMProvider


class ZaiProvider(LLMProvider):
    def __init__(
        self, api_key: str | None, *, model: str, timeout: Optional[int] = None
    ) -> None:
        try:
            from zai import ZaiClient  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - depends on install
            raise RuntimeError("zai is required for LLM_PROVIDER=zai") from exc

        if not api_key:
            raise RuntimeError("LLM_API_KEY is required for LLM_PROVIDER=zai")

        self._client = ZaiClient(api_key=api_key, timeout=timeout)
        self._model = model

    def generate(self, prompt: str) -> str:
        try:
            response: Any = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            raise RuntimeError(f"zai generate failed: {exc}") from exc

        if not response.choices:
            return ""
        return response.choices[0].message.content or ""

    def stream(self, prompt: str) -> Iterator[str]:
        try:
            stream: Any = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
        except Exception as exc:
            raise RuntimeError(f"zai chat stream failed: {exc}") from exc

        try:
            for chunk in stream:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as exc:
            raise RuntimeError(f"zai chat stream failed: {exc}") from exc
