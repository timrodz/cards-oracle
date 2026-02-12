from typing import Literal

from pydantic import BaseModel

Similarity = Literal["dot_product", "cosine", "euclidean"]
MongoSimilarity = Literal["dotProduct", "cosine", "euclidean"]


class CardEmbeddingVectorSearchResult(BaseModel):
    source_id: str
    summary: str
    score: float


def similarity_to_mongo(similarity: Similarity) -> MongoSimilarity:
    if similarity == "dot_product":
        return "dotProduct"
    return similarity
