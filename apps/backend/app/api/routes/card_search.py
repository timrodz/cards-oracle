from elasticsearch import AsyncElasticsearch
from fastapi import APIRouter, Depends

from app.core.card_search import build_card_query
from app.core.config import elasticsearch_settings
from app.core.elasticsearch import get_es
from app.models.api import CardSearchParams, CardSearchResponse
from app.models.scryfall import ScryfallCard

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
