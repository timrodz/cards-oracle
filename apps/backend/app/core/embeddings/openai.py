from typing import Any

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
    ) -> None:
        try:
            from openai import OpenAI  # type: ignore[import-not-found]
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

    def embed_texts(self, texts: list[str], *, normalize: bool) -> list[list[float]]:
        if not texts:
            return []

        try:
            response = self._client.embeddings.create(
                model=self._model_name,
                input=texts,
                dimensions=self._model_dimensions,
                encoding_format="float",
            )
        except Exception as exc:  # pragma: no cover - runtime dependency behavior
            raise RuntimeError(f"openai embeddings failed: {exc}") from exc

        vectors = [list(item.embedding) for item in response.data]
        self._validate_dimensions(vectors)

        if normalize:
            return [normalize_l2(vector) for vector in vectors]
        return vectors
