from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AfterValidator, AliasChoices, BaseModel, Field, MongoDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


def _validate_json_file_type(value: Path) -> Path:
    if value.suffix.lower() != ".json":
        raise ValueError(f"Expected a .json file path, got: {value}")
    return value


def _expand_user_path(value: Path) -> Path:
    return value.expanduser()


JsonFilePath = Annotated[Path, AfterValidator(_validate_json_file_type)]
NormalizedPath = Annotated[Path, AfterValidator(_expand_user_path)]
LlmProviderName = Literal["ollama", "zai", "llama_cpp"]
EmbeddingProviderName = Literal["sentence_transformers", "openai"]


class DatasetFileInput(BaseModel):
    dataset_file: JsonFilePath


class DatabaseSettings(BaseModel):
    uri: MongoDsn
    name: str
    cards_collection: str
    card_embeddings_collection: str
    batch_size: int


class EmbeddingSettings(BaseModel):
    provider: EmbeddingProviderName
    model_name: str
    model_path: NormalizedPath
    model_dimensions: int
    vector_limit: int

    @property
    def transformer_model_name(self) -> str:
        return self.model_name

    @property
    def transformer_model_path(self) -> NormalizedPath:
        return self.model_path

    @property
    def transformer_dimensions(self) -> int:
        return self.model_dimensions


class LlmSettings(BaseModel):
    rag_max_context_chars: int
    provider: LlmProviderName
    model_name: str
    model_path: str | None
    endpoint: str | None
    timeout_seconds: int
    context_window_tokens: int
    llm_api_key: str | None


class AppSettings(BaseModel):
    cors_origins: str
    embeddings_max_workers: int


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_cors_origins: str = "http://localhost:3000"
    app_embeddings_max_workers: int = 4

    mongodb_uri: MongoDsn = MongoDsn("mongodb://localhost:27017/?directConnection=true")
    mongodb_db_name: str = "mtg"
    mongodb_cards_collection: str = "cards"
    mongodb_card_embeddings_collection: str = "card_embeddings"
    mongodb_batch_size: int = 500

    embedding_provider: EmbeddingProviderName = "sentence_transformers"
    embedding_model_name: str = Field(
        default="mixedbread-ai/mxbai-embed-xsmall-v1",
        validation_alias=AliasChoices(
            "EMBEDDING_MODEL_NAME", "EMBEDDING_TRANSFORMER_MODEL_NAME"
        ),
    )
    embedding_model_path: NormalizedPath = Field(
        default=Path("models/mixedbread-ai/mxbai-embed-xsmall-v1"),
        validation_alias=AliasChoices(
            "EMBEDDING_MODEL_PATH", "EMBEDDING_TRANSFORMER_MODEL_PATH"
        ),
    )
    embedding_model_dimensions: int = Field(
        default=384,
        validation_alias=AliasChoices(
            "EMBEDDING_MODEL_DIMENSIONS", "EMBEDDING_TRANSFORMER_MODEL_DIMENSIONS"
        ),
    )
    embedding_vector_search_limit: int = Field(
        default=5,
        validation_alias=AliasChoices(
            "EMBEDDING_VECTOR_SEARCH_LIMIT", "EMBEDDING_TRANSFORMER_VECTOR_SEARCH_LIMIT"
        ),
    )

    llm_rag_max_context_chars: int = 4000
    llm_provider: LlmProviderName
    llm_model_name: str = "mistral"
    llm_model_path: str | None = None
    llm_endpoint: str | None = None
    llm_timeout_seconds: int = 120
    llm_context_window_tokens: int = 4096
    llm_api_key: str | None = None

    @property
    def database_settings(self) -> DatabaseSettings:
        return DatabaseSettings(
            uri=self.mongodb_uri,
            name=self.mongodb_db_name,
            cards_collection=self.mongodb_cards_collection,
            card_embeddings_collection=self.mongodb_card_embeddings_collection,
            batch_size=self.mongodb_batch_size,
        )

    @property
    def transformer_settings(self) -> EmbeddingSettings:
        return EmbeddingSettings(
            provider=self.embedding_provider,
            model_name=self.embedding_model_name,
            model_path=self.embedding_model_path,
            model_dimensions=self.embedding_model_dimensions,
            vector_limit=self.embedding_vector_search_limit,
        )

    @property
    def llm_settings(self) -> LlmSettings:
        return LlmSettings(
            rag_max_context_chars=self.llm_rag_max_context_chars,
            provider=self.llm_provider,
            model_name=self.llm_model_name,
            model_path=self.llm_model_path,
            endpoint=self.llm_endpoint,
            timeout_seconds=self.llm_timeout_seconds,
            context_window_tokens=self.llm_context_window_tokens,
            llm_api_key=self.llm_api_key,
        )

    @property
    def app_settings(self) -> AppSettings:
        return AppSettings(
            cors_origins=self.app_cors_origins,
            embeddings_max_workers=self.app_embeddings_max_workers,
        )


@lru_cache
def _get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


_settings = _get_settings()
app_settings = _settings.app_settings
db_settings = _settings.database_settings
transformer_settings = _settings.transformer_settings
llm_settings = _settings.llm_settings
