from typing import Any, Dict, List, Tuple, Union

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from loguru import logger

from app.core.config import elasticsearch_settings
from app.models.scryfall import ScryfallCard


async def index_cards(
    cards: List[ScryfallCard], es: AsyncElasticsearch
) -> Tuple[int, int]:
    """
    Indexes a list of ScryfallCard objects into Elasticsearch using bulk operations.
    Returns a tuple of (success_count, failure_count).
    """
    index_name = elasticsearch_settings.index_name

    actions: List[Dict[str, Any]] = []
    for card in cards:
        # Convert Pydantic model to dict for Elasticsearch
        card_data = card.model_dump()

        # Define the bulk action
        action = {
            "_op_type": "index",
            "_index": index_name,
            "_id": card.id,
            "_source": card_data,
        }
        actions.append(action)

    if not actions:
        return 0, 0

    try:
        # async_bulk with stats_only=True returns (success_count, failed_count)
        # We explicitly cast to ensure mypy is happy with the return types
        result: Tuple[int, Union[int, List[Any]]] = await async_bulk(
            client=es,
            actions=actions,
            stats_only=True,
            raise_on_error=False,
        )
        
        success, errors = result
        
        # Ensure errors is an int for the comparison and return
        error_count = errors if isinstance(errors, int) else len(errors)

        if error_count > 0:
            logger.warning(f"Indexed {success} cards with {error_count} failures.")
        else:
            logger.info(f"Successfully indexed all {success} cards.")

        return success, error_count
    except Exception as e:
        logger.error(f"Failed to perform bulk indexing: {e}")
        return 0, len(actions)
