import asyncio
import json
from typing import Annotated, Any, Dict

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import TypeAdapter, ValidationError
from starlette.concurrency import iterate_in_threadpool
from typing_extensions import Iterator

from app.core.rag.search import RagSearch
from app.models.api import SearchResponse, StreamErrorEvent, StreamEvent

router = APIRouter(prefix="/search", tags=["RAG"])

stream_event_adapter: TypeAdapter[StreamEvent] = TypeAdapter(StreamEvent)

rag_search = RagSearch()


def _encode_event_stream(event: Dict[str, Any]) -> str:
    try:
        validated_event = stream_event_adapter.validate_python(event)
        payload = json.dumps(validated_event.model_dump(exclude_none=True))
    except ValidationError as exc:
        fallback = StreamErrorEvent(
            type="error", message=f"Invalid stream event payload: {exc}"
        )
        payload = json.dumps(fallback.model_dump(exclude_none=True))
    return f"data: {payload}\n\n"


def _search_rag_stream(query: str, normalize_embeddings: bool) -> Iterator[str]:
    for event in rag_search.search_stream(
        query, normalize_embeddings=normalize_embeddings
    ):
        yield _encode_event_stream(event)


@router.get("/", response_model=SearchResponse)
async def search(
    question: Annotated[str, Query(..., min_length=1)],
    normalize_embeddings: Annotated[bool, Query()] = True,
) -> Dict[str, Any]:
    result = await asyncio.to_thread(
        rag_search.search, question, normalize_embeddings=normalize_embeddings
    )
    return SearchResponse.model_validate(result).model_dump(exclude_none=True)


# TODO: response_model for streamed endpoint
@router.get("/stream")
async def stream_search(
    question: Annotated[str, Query(..., min_length=1)],
    normalize_embeddings: Annotated[bool, Query()] = True,
) -> StreamingResponse:
    stream = _search_rag_stream(question, normalize_embeddings=normalize_embeddings)
    return StreamingResponse(
        iterate_in_threadpool(stream), media_type="text/event-stream"
    )
