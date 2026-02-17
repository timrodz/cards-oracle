from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.embedding import Similarity


class HealthCheckResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    hello: str = Field(alias="Hello")


class OperationMessageResponse(BaseModel):
    message: str


class SearchQueryParams(BaseModel):
    question: str = Field(min_length=1)
    normalize_embeddings: bool = True


class IngestJsonDatasetParams(BaseModel):
    collection: str = Field(min_length=1)
    limit: int | None = Field(default=None, ge=1)


class CreateJsonEmbeddingParams(BaseModel):
    source_collection: str = Field(min_length=1)
    target_collection: str = Field(min_length=1)
    chunk_mappings: str | None = Field(default=None, min_length=1)
    limit: int | None = Field(default=None, ge=1)
    normalize: bool = True


class CreateSearchIndexParams(BaseModel):
    collection_name: str = Field(min_length=1)
    collection_embeddings_field: str = Field(min_length=1)
    similarity: Similarity = "dot_product"


class SearchResult(BaseModel):
    source_id: str
    summary: str
    score: float


class SearchResponse(BaseModel):
    answer: str
    source_id: str | None = None


class StreamMetaEvent(BaseModel):
    type: Literal["meta"]
    results: list[SearchResult]
    context: str
    answer: str | None = None


class StreamChunkEvent(BaseModel):
    type: Literal["chunk"]
    content: str


class StreamErrorEvent(BaseModel):
    type: Literal["error"]
    message: str
    query: str | None = None


class StreamSeekingCardEvent(BaseModel):
    type: Literal["seeking_card"]


class StreamFoundCardEvent(BaseModel):
    type: Literal["found_card"]
    id: str


class StreamDoneEvent(BaseModel):
    type: Literal["done"]


StreamEvent = (
    StreamMetaEvent
    | StreamChunkEvent
    | StreamErrorEvent
    | StreamSeekingCardEvent
    | StreamFoundCardEvent
    | StreamDoneEvent
)
