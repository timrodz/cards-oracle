import json
from typing import Any, Iterator, List

from loguru import logger

from app.core.config import llm_settings, transformer_settings
from app.core.db import database
from app.core.llms.utils import (
    get_llm_provider,
    parse_llm_response,
    parse_source_id_response,
)
from app.data_pipeline.sentence_transformers import (
    embed_text,
    load_transformer,
)
from app.models.api import (
    SearchResponse,
    SearchResult,
    StreamChunkEvent,
    StreamDoneEvent,
    StreamFoundCardEvent,
    StreamMetaEvent,
    StreamSeekingCardEvent,
)
from app.models.embedding import CardEmbeddingVectorSearchResult


class RagSearch:
    def __vector_search(
        self,
        query_vector: List[float],
    ) -> List[SearchResult]:
        vector_limit = transformer_settings.vector_limit

        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "queryVector": query_vector,
                    "path": "embeddings",
                    "exact": True,
                    "limit": vector_limit,
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "source_id": 1,
                    "summary": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]
        raw_results = list(database.embeddings_collection.aggregate(pipeline))
        results: List[SearchResult] = []
        for raw_result in raw_results:
            embedding_record = CardEmbeddingVectorSearchResult.model_validate(
                raw_result
            )
            results.append(
                SearchResult(
                    source_id=embedding_record.source_id,
                    summary=embedding_record.summary,
                    score=embedding_record.score,
                )
            )
        logger.debug(results)
        return results

    def __build_context(
        self, *, results: List[SearchResult], max_chars: int, include_source_ids: bool
    ) -> str:
        sections: List[str] = []
        total = 0
        for result in results:
            header = ""
            if include_source_ids:
                source_id = result.source_id
                header = f"source_id: {source_id}\n" if source_id else ""
            section = f"{header}{result.summary}"
            if total + len(section) > max_chars:
                remaining = max_chars - total
                if remaining > 0:
                    sections.append(section[:remaining])
                break
            sections.append(section)
            total += len(section)
        return "\n".join(sections).strip()

    def __build_prompt(self, *, question: str, context: str, require_json: bool) -> str:
        instructions = (
            "Answer the question using the provided context. "
            "If the context is insufficient, say so and suggest what to ask next."
        )
        if require_json:
            instructions = f"""{instructions}
                If you can confidently pinpoint a single specific card from the context,
                include its source_id in the response. Only use source_id values that
                appear in the context. If not confident, set source_id to null.
                Return only JSON with keys: answer (string), source_id (string|null)
                """
        payload = {
            "role": "You help users find cards for Magic: The Gathering.",
            "instructions": instructions,
            "context": context,
            "question": question,
        }
        return json.dumps(payload)

    def __build_source_id_prompt(
        self, *, question: str, context: str, answer: str
    ) -> str:
        payload = {
            "role": "You identify the best matching card from provided context.",
            "instructions": (
                """
                Given the question, context, and answer, choose the single best
                source_id if the answer clearly refers to one card.
                Only use source_id values that appear in the context.
                If not confident, set source_id to null.
                Return only JSON with key: source_id (string|null).
                Example response: { source_id: "77c6fa74-5543-42ac-9ead-0e890b188e99" }
                """
            ),
            "context": context,
            "question": question,
            "answer": answer,
        }
        return json.dumps(payload)

    def search(
        self, question: str, *, normalize_embeddings: bool = True
    ) -> SearchResponse | None:
        embedder = load_transformer()
        query_embeddings = embed_text(
            model=embedder,
            text=question,
            normalize=normalize_embeddings,
        )
        results = self.__vector_search(
            query_vector=query_embeddings,
        )

        if not results:
            logger.warning(f"Vector search produced 0 results for question {question}")
            return None

        context = self.__build_context(
            results=results,
            max_chars=llm_settings.rag_max_context_chars,
            include_source_ids=True,
        )
        if not context:
            logger.warning("Unable to build context")
            return None

        prompt = self.__build_prompt(
            question=question, context=context, require_json=True
        )
        provider = get_llm_provider()
        response = provider.generate(prompt)
        clean_response, source_id = parse_llm_response(response)
        logger.debug(clean_response)
        return SearchResponse(
            answer=clean_response,
            source_id=source_id,
        )

    def search_stream(
        self, question: str, *, normalize_embeddings: bool
    ) -> Iterator[dict[str, Any]]:
        embedder = load_transformer()
        query_embeddings = embed_text(
            model=embedder,
            text=question,
            normalize=True,
        )

        results = self.__vector_search(
            query_vector=query_embeddings,
        )
        if not results:
            yield StreamMetaEvent(type="meta", results=[], context="").model_dump(
                exclude_none=True
            )
            yield StreamDoneEvent(type="done").model_dump(exclude_none=True)
            return

        context = self.__build_context(
            results=results,
            max_chars=llm_settings.rag_max_context_chars,
            include_source_ids=False,
        )
        if not context:
            yield StreamMetaEvent(type="meta", results=results, context="").model_dump(
                exclude_none=True
            )
            yield StreamDoneEvent(type="done").model_dump(exclude_none=True)
            return

        prompt = self.__build_prompt(
            question=question, context=context, require_json=False
        )
        provider = get_llm_provider()
        yield StreamMetaEvent(type="meta", results=results, context=context).model_dump(
            exclude_none=True
        )

        streamed_parts: List[str] = []
        for chunk in provider.stream(prompt):
            streamed_parts.append(chunk)
            yield StreamChunkEvent(type="chunk", content=chunk).model_dump(
                exclude_none=True
            )

        if streamed_parts:
            full_response = "".join(streamed_parts)
            source_context = self.__build_context(
                results=results,
                max_chars=llm_settings.rag_max_context_chars,
                include_source_ids=True,
            )
            source_prompt = self.__build_source_id_prompt(
                question=question,
                context=source_context,
                answer=full_response,
            )
            yield StreamSeekingCardEvent(type="seeking_card").model_dump(
                exclude_none=True
            )
            source_response = provider.generate(source_prompt)
            source_id = parse_source_id_response(source_response)
            if source_id:
                yield StreamFoundCardEvent(type="found_card", id=source_id).model_dump(
                    exclude_none=True
                )
        yield StreamDoneEvent(type="done").model_dump(exclude_none=True)
