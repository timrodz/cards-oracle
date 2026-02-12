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

    def create_vector_search_index(
        self,
        *,
        collection_name: str,
        collection_field: str,
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
                        "path": collection_field,
                        "similarity": mongo_similarity,
                    }
                ]
            },
        )
        collection = database.get_collection(collection_name)
        logger.info(
            f"Creating search index for {collection_name} on field {collection_field} with similarity {mongo_similarity}"
        )
        collection.create_search_index(model=search_index_model)
        logger.info("Search index created")


database = Database()
