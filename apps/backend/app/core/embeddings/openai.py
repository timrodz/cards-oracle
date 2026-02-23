import random
import time
from typing import Any

from loguru import logger

from app.core.embeddings.normalize import normalize_l2
from app.core.embeddings.provider import EmbeddingProvider


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        *,
        api_key: str | None,
        model_name: str,
        model_dimensions: int,
        endpoint: str | None,
        timeout_seconds: int,
        max_retries: int = 5,
        backoff_base_seconds: float = 0.5,
        backoff_max_seconds: float = 8.0,
    ) -> None:
        try:
            from openai import (  # type: ignore[import-not-found]
                APIConnectionError,
                APIStatusError,
                APITimeoutError,
                OpenAI,
                RateLimitError,
            )
        except ImportError as exc:  # pragma: no cover - depends on install
            raise RuntimeError(
                "openai is required for EMBEDDING_PROVIDER=openai"
            ) from exc

        if not api_key:
            raise RuntimeError("LLM_API_KEY is required for EMBEDDING_PROVIDER=openai")

        client_kwargs: dict[str, Any] = {
            "api_key": api_key,
            "timeout": timeout_seconds,
        }
        if endpoint:
            client_kwargs["base_url"] = endpoint

        self._client = OpenAI(**client_kwargs)
        self._model_name = model_name
        self._model_dimensions = model_dimensions
        self._max_retries = max_retries
        self._backoff_base_seconds = backoff_base_seconds
        self._backoff_max_seconds = backoff_max_seconds
        self._retryable_errors = (
            RateLimitError,
            APIConnectionError,
            APITimeoutError,
            APIStatusError,
        )
        self._api_status_error = APIStatusError

    def _validate_dimensions(self, vectors: list[list[float]]) -> None:
        for vector in vectors:
            if len(vector) != self._model_dimensions:
                raise RuntimeError(
                    "openai embedding dimension mismatch: "
                    f"expected {self._model_dimensions}, got {len(vector)}"
                )

    def embed_text(self, text: str, *, normalize: bool) -> list[float]:
        vectors = self.embed_texts([text], normalize=normalize)
        return vectors[0]

    def _is_retryable_error(self, *, error: Exception) -> bool:
        if not isinstance(error, self._retryable_errors):
            return False

        if isinstance(error, self._api_status_error):
            status_code = getattr(error, "status_code", None)
            return status_code in {408, 409, 429, 500, 502, 503, 504}

        return True

    def _compute_backoff_seconds(self, *, attempt: int) -> float:
        exponential = self._backoff_base_seconds * (2 ** (attempt - 1))
        bounded = min(exponential, self._backoff_max_seconds)
        jitter = random.uniform(0.0, bounded * 0.2)
        return bounded + jitter

    def embed_texts(self, texts: list[str], *, normalize: bool) -> list[list[float]]:
        if not texts:
            return []

        response = None
        for attempt in range(1, self._max_retries + 1):
            try:
                response = self._client.embeddings.create(
                    model=self._model_name,
                    input=texts,
                    dimensions=self._model_dimensions,
                    encoding_format="float",
                )
                break
            except Exception as exc:
                if (
                    not self._is_retryable_error(error=exc)
                    or attempt == self._max_retries
                ):
                    raise RuntimeError(f"openai embeddings failed: {exc}") from exc

                backoff_seconds = self._compute_backoff_seconds(attempt=attempt)
                logger.warning(
                    "openai embeddings attempt "
                    f"{attempt}/{self._max_retries} failed; retrying in "
                    f"{backoff_seconds:.2f}s"
                )
                time.sleep(backoff_seconds)

        if response is None:
            raise RuntimeError("openai embeddings failed: no response received")

        sorted_data = sorted(response.data, key=lambda x: x.index)
        vectors = [list(item.embedding) for item in sorted_data]
        self._validate_dimensions(vectors)

        if normalize:
            return [normalize_l2(vector) for vector in vectors]
        return vectors
