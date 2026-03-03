from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.embedding import Similarity
from app.models.scryfall import ScryfallCard


class HealthCheckResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    hello: str = Field(alias="Hello")


class OperationMessageResponse(BaseModel):
    message: str


class CardSearchParams(BaseModel):
    query: str | None = Field(default=None)
    cmc: float | None = Field(default=None, ge=0)
    set: str | None = Field(default=None)
    released_at_from: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    released_at_to: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class CardSearchResponse(BaseModel):
    items: list[ScryfallCard]
    total: int
    page: int
    page_size: int


class SearchQueryParams(BaseModel):
    question: str = Field(min_length=1)
    normalize_embeddings: bool = True


class IngestJsonDatasetParams(BaseModel):
    collection: str = Field(min_length=1)
    limit: int | None = Field(default=None, ge=1)


class CreateEmbeddingChunksParams(BaseModel):
    source_collection: str = Field(min_length=1)
    target_collection: str = Field(min_length=1)
    chunk_mappings: str = Field(min_length=1)
    limit: int | None = Field(default=None, ge=1)


class GenerateEmbeddingsParams(BaseModel):
    collection: str = Field(min_length=1)
    limit: int | None = Field(default=None, ge=1)
    normalize_embeddings: bool = True


class CreateSearchIndexParams(BaseModel):
    collection: str = Field(min_length=1)
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
