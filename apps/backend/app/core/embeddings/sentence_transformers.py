from functools import lru_cache
from pathlib import Path

import torch as torch_module
from loguru import logger
from sentence_transformers import SentenceTransformer

from app.core.embeddings.provider import EmbeddingProvider


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        *,
        model_name: str,
        model_path: Path,
        model_dimensions: int,
    ) -> None:
        self._model_dimensions = model_dimensions
        self._model = self._load_transformer(model_name=model_name, model_path=model_path)

    @staticmethod
    @lru_cache(maxsize=8)
    def _load_transformer(*, model_name: str, model_path: Path) -> SentenceTransformer:
        device = "cpu"
        if torch_module.cuda.is_available():
            device = "cuda"

        resolved_path = Path(model_path)
        if resolved_path.exists():
            logger.info(
                f"Loading embedding model from path: {resolved_path} (device={device})"
            )
            return SentenceTransformer(str(resolved_path), device=device)

        # Attempts to download the model if not available
        logger.info(
            f"Loading embedding model: {model_name} (device={device}, path={model_path})"
        )
        model = SentenceTransformer(model_name, device=device)
        resolved_path.mkdir(parents=True, exist_ok=True)
        model.save(str(resolved_path))
        return model

    def _validate_dimensions(self, vectors: list[list[float]]) -> None:
        for vector in vectors:
            if len(vector) != self._model_dimensions:
                raise RuntimeError(
                    "sentence_transformers embedding dimension mismatch: "
                    f"expected {self._model_dimensions}, got {len(vector)}"
                )

    def embed_text(self, text: str, *, normalize: bool) -> list[float]:
        vectors = self.embed_texts([text], normalize=normalize)
        return vectors[0]

    def embed_texts(self, texts: list[str], *, normalize: bool) -> list[list[float]]:
        if not texts:
            return []

        embeddings = self._model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=normalize,
        )
        vectors = embeddings.tolist()
        self._validate_dimensions(vectors)
        return vectors
