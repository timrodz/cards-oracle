from functools import lru_cache

from app.core.config import llm_settings, transformer_settings
from app.core.embeddings.openai import OpenAIEmbeddingProvider
from app.core.embeddings.provider import EmbeddingProvider
from app.core.embeddings.sentence_transformers import (
    SentenceTransformerEmbeddingProvider,
)


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    provider = transformer_settings.provider

    if provider == "sentence_transformers":
        return SentenceTransformerEmbeddingProvider(
            model_name=transformer_settings.model_name,
            model_path=transformer_settings.model_path,
            model_dimensions=transformer_settings.model_dimensions,
        )

    if provider == "openai":
        return OpenAIEmbeddingProvider(
            api_key=llm_settings.llm_api_key,
            model_name=transformer_settings.model_name,
            model_dimensions=transformer_settings.model_dimensions,
            endpoint=llm_settings.endpoint,
            timeout_seconds=llm_settings.timeout_seconds,
        )

    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {provider}")
