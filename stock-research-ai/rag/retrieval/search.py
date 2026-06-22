from loguru import logger
from qdrant_client.models import Filter, FieldCondition, MatchValue

from providers.embeddings.embedding_provider import EmbeddingProvider
from vectorstore.qdrant_client import get_qdrant_client


_provider = EmbeddingProvider()


async def search_similar(
    query: str,
    *,
    collection_name: str = "sec_filings",
    symbol: str | None = None,
    limit: int = 5,
) -> list[dict]:
    try:
        query_vector = await _provider.embed_text(query)
    except Exception as exc:
        logger.warning(f"Query embedding failed: {exc}")
        return []

    client = get_qdrant_client()
    query_filter = None

    if symbol:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="symbol",
                    match=MatchValue(value=symbol),
                )
            ]
        )

    try:
        response = await client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
            query_filter=query_filter,
        )
        results = response.points
    except Exception as exc:
        logger.warning(f"Qdrant search failed: {exc}")
        return []

    hits = []
    for point in results:
        hits.append({
            "id": str(point.id),
            "score": point.score,
            "text": point.payload.get("text", ""),
            "symbol": point.payload.get("symbol"),
            "form_type": point.payload.get("form_type"),
        })

    return hits