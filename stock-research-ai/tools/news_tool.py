from datetime import date, timedelta
from loguru import logger

from providers.finance.finnhub_client import FinhubClient


class NewsTool:
    def __init__(self):
        self._client = FinhubClient()

    async def get_news(self, symbol: str, days: int = 7) -> dict:
        to_date = date.today().isoformat()
        from_date = (date.today() - timedelta(days=days)).isoformat()

        try:
            articles = await self._client.get_company_news(
                symbol,
                from_date,
                to_date,
            )
            return {
                "articles": articles[:20],
                "total": len(articles),
                "source": "finnhub",
            }

        except Exception as exc:
            logger.warning(f"News fetch failed for {symbol}: {exc}")
            return {
                "articles": [],
                "total": 0,
                "source": "finnhub",
                "error": str(exc),
            }