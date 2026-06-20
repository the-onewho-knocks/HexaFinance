from loguru import logger

from rag.ingestion.embedding_pipeline import embed_and_index
from rag.ingestion.chunker import chunk_text
from vectorstore.collections import ensure_collections
from vectorstore.qdrant_client import get_qdrant_client


async def index_text(
    text: str,
    *,
    symbol: str,
    form_type: str = "10-K",
    collection_name: str = "sec_filings",
) -> int:
    chunks = chunk_text(text)
    if not chunks:
        return 0

    return await embed_and_index(
        chunks,
        symbol=symbol,
        form_type=form_type,
        collection_name=collection_name,
    )


async def delete_by_symbol(
    symbol: str,
    collection_name: str = "sec_filings",
) -> int:
    try:
        client = get_qdrant_client()
        results = await client.scroll(
            collection_name=collection_name,
            limit=100,
            with_payload=False,
            with_vectors=False,
        )

        ids = []
        for point in results[0]:
            payload = point.payload or {}
            if payload.get("symbol", "").upper() == symbol.upper():
                ids.append(point.id)

        if ids:
            await client.delete(
                collection_name=collection_name,
                points_selector=ids,
            )
            logger.info(f"Deleted {len(ids)} vectors for {symbol}")
            return len(ids)

        return 0
    except Exception as exc:
        logger.warning(f"Failed to delete vectors for {symbol}: {exc}")
        return 0


async def collection_stats(collection_name: str = "sec_filings") -> dict:
    try:
        client = get_qdrant_client()
        info = await client.get_collection(collection_name=collection_name)
        return {
            "name": collection_name,
            "vectors_count": info.vectors_count or 0,
            "points_count": info.points_count or 0,
            "status": str(info.status),
        }
    except Exception as exc:
        logger.warning(f"Failed to get collection stats: {exc}")
        return {
            "name": collection_name,
            "error": str(exc),
        }