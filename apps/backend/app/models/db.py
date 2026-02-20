from pydantic import BaseModel, ConfigDict, Field
from pydantic_mongo import PydanticObjectId

from app.models.scryfall import ScryfallCardBase


class MongoCollectionRecord(BaseModel):
    mongo_id: PydanticObjectId = Field(alias="_id")

    model_config = ConfigDict(extra="allow")


class EmptyEmbeddingRecord(BaseModel):
    mongo_id: PydanticObjectId = Field(alias="_id")
    summary: str
    embeddings: list[float] = []


class GeneratedEmbeddingRecord(BaseModel):
    mongo_id: PydanticObjectId = Field(alias="_id")
    summary: str
    embeddings: list[float] = []


class CardEmbeddingRecord(BaseModel):
    mongo_id: PydanticObjectId = Field(alias="_id")
    source_id: str
    summary: str
    embeddings: list[float] = []


class ScryfallCardRecord(ScryfallCardBase):
    mongo_id: PydanticObjectId = Field(alias="_id")
