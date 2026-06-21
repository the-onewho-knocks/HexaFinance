from loguru import logger

from core.exceptions import ProviderError
from providers.finance.finnhub_client import FinhubClient
from providers.finance.polygon_client import PolygonClient

class MarketTool:
    def __init__(self) -> None:
        self._polygon_client = PolygonClient()
        self._finnhub_client = FinhubClient()

    async def get_market_data(self, symbol: str) -> dict:
        result : dict = {"source": "finnhub+polygon"}

        try:
            quote = await self._finnhub_client.get_quote(symbol)
            result["quote"] = quote
        except ProviderError as exc:
            logger.warning(f"Quote fetch failed for {symbol}: {exc}")
            result["quote_error"] = str(exc)
            

        try:
            profile = await self._finnhub_client.get_profile(symbol)
            result["profile"] = profile
        except ProviderError as exc:
            logger.warning(f"Profile fetch failed for {symbol}: {exc}")
            result["profile_error"] = str(exc)


        try:
            details = await self._polygon_client.get_ticker_details(symbol)
            result["ticker_details"] = details
        except ProviderError as exc:
            logger.warning(f"Ticker details fetch failed for {symbol}: {exc}")
            result["ticker_details_error"] = str(exc)

        return result