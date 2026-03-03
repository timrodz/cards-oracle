import asyncio
from typing import Annotated

from elasticsearch import AsyncElasticsearch
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pymongo.errors import AutoReconnect, OperationFailure

from app.core.card_search import build_card_query
from app.core.config import db_settings, elasticsearch_settings
from app.core.db import Database, get_db
from app.core.elasticsearch import get_es
from app.models.api import (
    CardSearchParams,
    CardSearchResponse,
    OperationMessageResponse,
)
from app.models.db import ScryfallCardRecord
from app.models.scryfall import ScryfallCard
from app.services.card_indexer import index_cards

router = APIRouter(
    prefix="/cards/search",
    tags=["Cards", "Search"],
)


@router.get("/", response_model=CardSearchResponse)
async def search_cards(
    params: CardSearchParams = Depends(),
    es: AsyncElasticsearch = Depends(get_es),
) -> CardSearchResponse:
    """
    Search for cards using structured queries and fuzzy name matching in Elasticsearch.
    """
    index_name = elasticsearch_settings.index_name

    # Build the Elasticsearch DSL query from request parameters
    query_body = build_card_query(params)

    # Execute the search
    response = await es.search(index=index_name, body=query_body)

    # Extract hits and total count
    hits = response["hits"]["hits"]
    total = response["hits"]["total"]["value"]

    # Parse hits into ScryfallCard models
    items = [ScryfallCard(**hit["_source"]) for hit in hits]

    return CardSearchResponse(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


@router.post("/index", response_model=OperationMessageResponse)
async def index_cards_from_db(
    db: Annotated[Database, Depends(get_db)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
) -> OperationMessageResponse:
    """
    Index cards into Elasticsearch by reading all records from the MongoDB cards collection.
    """
    logger.info("Indexing cards from MongoDB cards collection into Elasticsearch")

    max_retries = 5
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            cards_collection = db.get_collection(db_settings.cards_collection)
            cursor = cards_collection.find({})

            total_success = 0
            total_failed = 0
            batch_size = db_settings.batch_size
            current_batch = []

            for record in cursor:
                try:
                    # Parse MongoDB record into ScryfallCardRecord (which includes mongo_id)
                    rec = ScryfallCardRecord.model_validate(record)
                    current_batch.append(rec)
                except Exception as e:
                    logger.warning(f"Failed to parse MongoDB record: {e}")
                    total_failed += 1

                if len(current_batch) >= batch_size:
                    success, failed = await index_cards(current_batch, es)
                    total_success += success
                    total_failed += failed
                    current_batch = []

            if current_batch:
                success, failed = await index_cards(current_batch, es)
                total_success += success
                total_failed += failed

            return OperationMessageResponse(
                message=f"Indexing completed: {total_success} succeeded, {total_failed} failed."
            )
        except (AutoReconnect, OperationFailure) as e:
            # Check for error code 13436 (NotPrimaryOrSecondary) specifically
            is_node_state_error = isinstance(e, OperationFailure) and e.code == 13436
            if is_node_state_error or isinstance(e, AutoReconnect):
                if attempt < max_retries - 1:
                    logger.warning(
                        f"MongoDB node not ready (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {retry_delay}s..."
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
            
            logger.error(f"MongoDB operation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Indexing from DB failed: {e}")
            raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

    # Should not reach here
    raise HTTPException(status_code=503, detail="Database is currently unavailable.")
