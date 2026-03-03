# PRD: Elasticsearch Card Search

## Introduction

Add a structured card search system powered by Elasticsearch that complements the existing MongoDB-based RAG search. While the RAG endpoint (`/search`) handles natural-language questions about cards, this new endpoint (`/cards/search`) provides fast, structured filtering — fuzzy name matching with optional filters for converted mana cost, set, and release date. Elasticsearch is added as a Docker Compose service, and card data is automatically synced from MongoDB on ingestion.

## Goals

- Provide a fast, structured card search endpoint separate from RAG
- Support fuzzy name matching as the primary search mechanism
- Allow optional filtering by `cmc`, `set`, and `released_at`
- Automatically index cards into Elasticsearch whenever cards are ingested into MongoDB
- Return full `ScryfallCard` objects in search results
- Keep Elasticsearch deployment self-contained via Docker Compose

## User Stories

### US-001: Add Elasticsearch to Docker Compose
**Description:** As a developer, I need an Elasticsearch instance running alongside MongoDB so the backend can index and query card data.

**Acceptance Criteria:**
- [ ] `docker-compose.yml` includes an `elasticsearch` service (single-node, development mode)
- [ ] Elasticsearch is accessible on a configurable port (default `9200`)
- [ ] Elasticsearch data is persisted via a named Docker volume
- [ ] Backend service `depends_on` Elasticsearch with a health check
- [ ] `docker compose up` starts Elasticsearch alongside existing services without errors

### US-002: Elasticsearch configuration and client setup
**Description:** As a developer, I need Elasticsearch connection settings managed through `app/core/config.py` and a reusable client so the rest of the application can interact with the ES cluster.

**Acceptance Criteria:**
- [ ] New env vars added to `.env.example`: `ELASTICSEARCH_URL` (default `http://elasticsearch:9200`)
- [ ] `ElasticsearchSettings` model added to `app/core/config.py` with `url` field
- [ ] `elasticsearch_settings` exported from `config.py` like other settings
- [ ] A reusable ES client accessor is available (e.g., via FastAPI dependency or `app/core/elasticsearch.py`)
- [ ] ES client connects on app startup (in `lifespan`) and closes on shutdown
- [ ] `elasticsearch` Python package added to project dependencies
- [ ] `ruff`, `mypy`, `pytest` pass

### US-003: Define Elasticsearch index mapping for cards
**Description:** As a developer, I need a well-defined ES index mapping for the `cards` index so that name search is fuzzy-capable and filters work on exact/range fields.

**Acceptance Criteria:**
- [ ] Index name is configurable (default: `cards`)
- [ ] `name` field is mapped as `text` (with standard analyzer for fuzzy/partial matching)
- [ ] `cmc` field is mapped as `float` (for exact and range filtering)
- [ ] `set` field is mapped as `keyword` (exact match filtering)
- [ ] `released_at` field is mapped as `date` (for range filtering)
- [ ] All other `ScryfallCardBase` fields are included in the mapping so full card objects can be returned
- [ ] Index mapping is defined as a Pydantic model or typed dict in `app/models/` or `app/core/`
- [ ] Index is created on app startup if it does not already exist
- [ ] `ruff`, `mypy`, `pytest` pass

### US-004: Dedicated Elasticsearch indexing endpoint
**Description:** As a developer, I want a dedicated endpoint to index cards into Elasticsearch from the existing MongoDB collection, so I can sync the search index with the database.

**Acceptance Criteria:**
- [ ] New route `POST /cards/search/index` in `app/api/routes/card_search.py`
- [ ] Endpoint reads all records from the MongoDB `cards` collection
- [ ] Cards are bulk-indexed into Elasticsearch using the card's Scryfall `id` as the document `_id`
- [ ] Indexing errors for individual cards are logged but do not abort the batch
- [ ] Re-indexing the same cards updates existing ES documents
- [ ] The existing `POST /data-pipeline/ingestion/json-records` no longer triggers Elasticsearch indexing
- [ ] `ruff`, `mypy`, `pytest` pass

### US-005: Implement `GET /cards/search` endpoint
**Description:** As a user, I want to search for cards by name with optional filters so I can quickly find specific cards.

**Acceptance Criteria:**
- [ ] New route file `app/api/routes/card_search.py` with router mounted at `/cards/search`
- [ ] `GET /cards/search` accepts query params:
  - `query` (required, `str`, `min_length=1`) — fuzzy-matched against card `name`
  - `cmc` (optional, `float`) — exact match filter on converted mana cost
  - `set` (optional, `str`) — exact match filter on set code
  - `released_at_from` (optional, `str` / ISO date) — range filter lower bound
  - `released_at_to` (optional, `str` / ISO date) — range filter upper bound
  - `page` (optional, `int`, default `1`) — pagination page number
  - `page_size` (optional, `int`, default `20`, max `100`) — results per page
- [ ] Query params are validated via a Pydantic model in `app/models/api.py`
- [ ] Response returns a list of full `ScryfallCard` objects plus pagination metadata (`total`, `page`, `page_size`)
- [ ] Response model is defined in `app/models/api.py`
- [ ] Empty results return an empty list, not an error
- [ ] Route is registered in `app/api/main.py`
- [ ] `ruff`, `mypy`, `pytest` pass

### US-006: Elasticsearch query builder for card search
**Description:** As a developer, I need a query builder that constructs the Elasticsearch query from the validated search params, keeping route handlers thin.

**Acceptance Criteria:**
- [ ] Query building logic lives in `app/core/` (e.g., `app/core/card_search.py`), not in the route handler
- [ ] `query` param is translated to an ES `match` query on `name` with `fuzziness: "AUTO"`
- [ ] Optional filters (`cmc`, `set`, `released_at` range) are combined via a `bool` query with `must` (name match) and `filter` (structured filters)
- [ ] Pagination is handled via ES `from` / `size` parameters
- [ ] The builder returns typed results (Pydantic models), not raw dicts
- [ ] `ruff`, `mypy`, `pytest` pass

### US-007: Add tests for card search
**Description:** As a developer, I want tests covering the search endpoint and query builder so regressions are caught early.

**Acceptance Criteria:**
- [ ] Unit tests for the query builder: name-only query, name + single filter, name + all filters, pagination
- [ ] Unit tests validate the Elasticsearch query structure (mocked ES client)
- [ ] Integration test for `GET /cards/search` using FastAPI `TestClient` with mocked ES responses
- [ ] Integration test for `POST /cards/search/index` to verify separate indexing
- [ ] Tests live under `tests/core/test_card_search.py` and `tests/api/routes/test_card_search.py`
- [ ] `pytest` passes

## Functional Requirements

- FR-1: Elasticsearch runs as a Docker Compose service alongside MongoDB, with a health check and persistent volume
- FR-2: Elasticsearch connection URL is configurable via environment variable (`ELASTICSEARCH_URL`)
- FR-3: The ES client is initialized during app startup (`lifespan`) and closed on shutdown
- FR-4: A `cards` index is created on startup with appropriate mappings if it does not exist
- FR-5: A dedicated endpoint `POST /cards/search/index` handles bulk-indexing of cards from MongoDB into ES
- FR-6: `GET /cards/search?query={name}` performs a fuzzy match on card name and returns full `ScryfallCard` objects
- FR-7: Optional query params `cmc`, `set`, `released_at_from`, `released_at_to` narrow results via exact match or range filters
- FR-8: Results are paginated with `page` and `page_size` params; response includes `total` count
- FR-9: All search logic lives in `app/core/`, keeping the route handler thin
- FR-10: Errors during individual card indexing are logged but do not block the batch
- FR-11: `POST /data-pipeline/ingestion/json-records` only indexes data into MongoDB collection

## Non-Goals

- No replacement of the existing RAG `/search` endpoint — this is a complementary system
- No full-text search across all card fields (only `name` is fuzzy-searched; other fields are filters)
- No Elasticsearch-based autocomplete or typeahead (future enhancement)
- No Kibana or Elasticsearch monitoring dashboard
- No authentication/security layer on the Elasticsearch instance (development only)
- No frontend changes in this scope

## Technical Considerations

- **ES Python client:** Use the official `elasticsearch` Python package (async or sync depending on pattern — existing codebase uses `asyncio.to_thread` for blocking calls, follow the same pattern)
- **Index mapping:** All `ScryfallCardBase` fields must be indexed so full objects can be returned directly from ES without a MongoDB round-trip
- **Bulk indexing:** Use the `elasticsearch.helpers.bulk` API for efficient batch indexing during ingestion
- **Idempotent upserts:** Use the Scryfall card `id` as the ES document `_id` so re-ingestion updates rather than duplicates
- **Docker Compose:** Use `elasticsearch:8.x` image with `discovery.type=single-node`, `xpack.security.enabled=false` for local dev
- **Existing patterns:** Follow the provider/interface patterns in `app/core/` and Pydantic models in `app/models/`; use `loguru` for logging

## Success Metrics

- `GET /cards/search?query=Lightning+Bolt` returns the correct card in the top results
- Fuzzy matching handles typos (e.g., `Lightnng Bolt` still finds `Lightning Bolt`)
- Filtering by `set=lea` narrows results to Limited Edition Alpha
- Filtering by `cmc=1` returns only 1-CMC cards matching the name query
- Date range filtering correctly bounds results by `released_at`
- Bulk indexing 30k+ cards completes without errors
- All existing tests continue to pass (`ruff`, `mypy`, `pytest`)

## Open Questions

- Should there be a dedicated admin endpoint to trigger a full ES re-index independently of card ingestion?
- Should we add a `sort_by` param (e.g., sort by relevance, name, release date, cmc)?
- What fuzziness level is ideal — `AUTO` (Elasticsearch default) or a fixed edit distance?
- Should duplicate card printings (same `oracle_id`, different `set`) be deduplicated in results?
