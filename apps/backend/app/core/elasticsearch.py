from elasticsearch import AsyncElasticsearch
from fastapi import Request
from loguru import logger

from app.core.config import elasticsearch_settings


def get_elasticsearch_client() -> AsyncElasticsearch:
    """
    Creates and returns an AsyncElasticsearch client instance.
    Includes headers for compatibility with v8 server when using v9 client.
    """
    url = elasticsearch_settings.url
    logger.info(f"Creating Elasticsearch client for {url}")
    return AsyncElasticsearch(
        url,
        headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=8"},
    )


async def get_es(request: Request) -> AsyncElasticsearch:
    """
    Dependency to get the Elasticsearch client from the application state.
    """
    return request.app.state.es


CARD_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "oracle_id": {"type": "keyword"},
            "name": {"type": "text", "analyzer": "standard"},
            "released_at": {"type": "date"},
            "cmc": {"type": "float"},
            "type_line": {"type": "text"},
            "oracle_text": {"type": "text"},
            "colors": {"type": "keyword"},
            "color_identity": {"type": "keyword"},
            "keywords": {"type": "keyword"},
            "set": {"type": "keyword"},
            "set_name": {"type": "text"},
            "rarity": {"type": "keyword"},
            "collector_number": {"type": "keyword"},
            "artist": {"type": "keyword"},
            "lang": {"type": "keyword"},
            "layout": {"type": "keyword"},
            "mana_cost": {"type": "keyword"},
        }
    }
}


async def init_elasticsearch(es: AsyncElasticsearch):
    """
    Initializes the Elasticsearch index with the defined mapping if it doesn't exist.
    """
    index_name = elasticsearch_settings.index_name
    try:
        exists = await es.indices.exists(index=index_name)
        if not exists:
            logger.info(f"Creating Elasticsearch index: {index_name}")
            await es.indices.create(index=index_name, body=CARD_INDEX_MAPPING)
        else:
            logger.info(f"Elasticsearch index already exists: {index_name}")
    except Exception as e:
        logger.error(f"Failed to initialize Elasticsearch: {e}")
        # We don't want to crash the app if ES is not ready yet, 
        # but in a production app we might want to retry or fail.
