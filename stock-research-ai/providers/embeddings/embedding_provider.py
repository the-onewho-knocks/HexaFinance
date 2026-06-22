from google import genai
from loguru import logger

from core.cache import cache_get, cache_set
from core.config import settings


class EmbeddingProvider:
    def __init__(self):
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = "models/gemini-embedding-2"

    async def embed_text(self, text: str) -> list[float]:
        cache_key = f"emb:{hash(text)}"
        cached = await cache_get("embed", cache_key)
        if cached:
            return cached

        try:
            result = self._client.models.embed_content(
                model=self._model,
                contents=text,
            )
            vector = result.embeddings[0].values
            await cache_set("embed", cache_key, vector, ttl=86400)
            return vector
        except Exception as exc:
            logger.warning(f"Embedding failed: {exc}")
            raise

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        cache_key = f"emb_batch:{hash(''.join(texts))}"
        cached = await cache_get("embed", cache_key)
        if cached:
            return cached

        try:
            result = self._client.models.embed_content(
                model=self._model,
                contents=texts,
            )
            vectors = [e.values for e in result.embeddings]
            await cache_set("embed", cache_key, vectors, ttl=86400)
            return vectors
        except Exception as exc:
            logger.warning(f"Batch embedding failed: {exc}")
            raise