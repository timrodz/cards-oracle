from typing import Any, Dict, List

from app.models.api import CardSearchParams


def build_card_query(params: CardSearchParams) -> Dict[str, Any]:
    """
    Translates CardSearchParams into an Elasticsearch DSL query.
    """
    must_clauses: List[Dict[str, Any]] = []
    filter_clauses: List[Dict[str, Any]] = []

    if params.query:
        must_clauses.append(
            {"match": {"name": {"query": params.query, "fuzziness": "AUTO"}}}
        )
    else:
        must_clauses.append({"match_all": {}})

    if params.cmc is not None:
        filter_clauses.append({"term": {"cmc": params.cmc}})

    if params.set:
        filter_clauses.append({"term": {"set": params.set}})

    if params.released_at_from or params.released_at_to:
        date_range: Dict[str, Any] = {}
        if params.released_at_from:
            date_range["gte"] = params.released_at_from
        if params.released_at_to:
            date_range["lte"] = params.released_at_to
        filter_clauses.append({"range": {"released_at": date_range}})

    query: Dict[str, Any] = {"bool": {"must": must_clauses, "filter": filter_clauses}}

    # Handle pagination
    from_offset = (params.page - 1) * params.page_size

    return {"query": query, "from": from_offset, "size": params.page_size}
