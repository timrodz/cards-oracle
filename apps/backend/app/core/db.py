from loguru import logger
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel

from app.core.config import db_settings, transformer_settings
from app.models.embedding import Similarity, similarity_to_mongo


class Database:
    def __init__(self):
        uri = db_settings.uri.encoded_string()
        db_client = MongoClient(uri)
        db_name = db_settings.name
        db = db_client[db_name]
        self.db = db

        self.cards_collection = db[db_settings.cards_collection]
        self.embeddings_collection = db[db_settings.card_embeddings_collection]

    def get_collection(self, name: str):
        return self.db[name]

    def get_collection_properties(
        self, *, collection_name: str, sample_size: int = 100
    ) -> list[str]:
        collection = self.get_collection(collection_name)
        properties: set[str] = set()
        cursor = collection.find().limit(sample_size)
        for document in cursor:
            properties.update(_flatten_document_keys(document=document))
        return sorted(properties)

    def create_vector_search_index(
        self,
        *,
        collection_name: str,
        collection_embeddings_field: str,
        similarity: Similarity,
    ) -> None:
        num_dimensions = transformer_settings.transformer_dimensions
        mongo_similarity = similarity_to_mongo(similarity)
        search_index_model = SearchIndexModel(
            name="vector_index",
            type="vectorSearch",
            definition={
                "fields": [
                    {
                        "type": "vector",
                        "numDimensions": num_dimensions,
                        "path": collection_embeddings_field,
                        "similarity": mongo_similarity,
                    }
                ]
            },
        )
        collection = database.get_collection(collection_name)
        logger.info(
            f"Creating search index for {collection_name} on field {collection_embeddings_field} with similarity {mongo_similarity}"
        )
        collection.create_search_index(model=search_index_model)
        logger.info("Search index created")


def _flatten_document_keys(*, document: dict, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    for key, value in document.items():
        full_key = key if prefix == "" else f"{prefix}.{key}"
        keys.add(full_key)

        if isinstance(value, dict):
            keys.update(_flatten_document_keys(document=value, prefix=full_key))
            continue

        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    keys.update(_flatten_document_keys(document=item, prefix=full_key))

    return keys


database = Database()
