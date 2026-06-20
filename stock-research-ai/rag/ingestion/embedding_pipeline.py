from uuid import uuid4

from loguru import logger

from providers.embeddings.embedding_provider import EmbeddingProvider
from vectorstore.collections import ensure_collections
from vectorstore.qdrant_client import get_qdrant_client


_provider = EmbeddingProvider()


async def embed_and_index(
    chunks: list[str],
    *,
    symbol: str,
    form_type: str = "10-K",
    collection_name: str | None = None,
) -> int:
    if not chunks:
        return 0

    try:
        await ensure_collections()
    except Exception as exc:
        logger.warning(f"Could not ensure collections: {exc}")
        return 0

    client = get_qdrant_client()
    target = collection_name or "sec_filings"

    try:
        embeddings = await _provider.embed_batch(chunks)
    except Exception as exc:
        logger.warning(f"Embedding failed: {exc}")
        return 0

    points = []
    for i, (text, vector) in enumerate(zip(chunks, embeddings)):
        points.append({
            "id": str(uuid4()),
            "vector": vector,
            "payload": {
                "text": text,
                "symbol": symbol,
                "form_type": form_type,
                "chunk_index": i,
            },
        })

    try:
        await client.upsert(
            collection_name=target,
            points=points,
        )
        logger.info(
            f"Indexed {len(points)} chunks for {symbol} in '{target}'"
        )
    except Exception as exc:
        logger.warning(f"Qdrant upsert failed: {exc}")
        return 0

    return len(points)