from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams
from core.config import settings
from loguru import logger

_client: AsyncQdrantClient | None = None

def get_qdrant_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        kwargs = {"url": settings.qdrant_url}
        if settings.qdrant_api_key:
            kwargs["api_key"] = settings.qdrant_api_key
        _client = AsyncQdrantClient(**kwargs)
        logger.info(f"Qdrant client initialised → {settings.qdrant_url}")
    return _client