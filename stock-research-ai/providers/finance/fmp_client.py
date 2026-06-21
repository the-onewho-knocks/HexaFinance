import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings
from core.exceptions import ProviderError

BASE = "https://financialmodelingprep.com/stable"


class FMPClient:
    def __init__(self):
        self._key = settings.fmp_api_key

    def _p(self, extra: dict | None = None) -> dict:
        params = {"apikey": self._key}

        if extra:
            params.update(extra)

        return params

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(min=1, max=8),
    )
    async def get_income_statement(
        self,
        symbol: str,
        limit: int = 4,
    ) -> list[dict]:
        async with httpx.AsyncClient(
            timeout=15,
            follow_redirects=True,
        ) as client:
            response = await client.get(
                f"{BASE}/income-statement",
                params=self._p(
                    {
                        "symbol": symbol,
                        "limit": limit,
                    }
                ),
            )

        if response.status_code != 200:
            raise ProviderError(
                "fmp",
                f"income statement failed: {response.text}",
            )

        return response.json()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(min=1, max=8),
    )
    async def get_balance_sheet(
        self,
        symbol: str,
        limit: int = 4,
    ) -> list[dict]:
        async with httpx.AsyncClient(
            timeout=15,
            follow_redirects=True,
        ) as client:
            response = await client.get(
                f"{BASE}/balance-sheet-statement",
                params=self._p(
                    {
                        "symbol": symbol,
                        "limit": limit,
                    }
                ),
            )

        if response.status_code != 200:
            raise ProviderError(
                "fmp",
                f"balance sheet failed: {response.text}",
            )

        return response.json()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(min=1, max=8),
    )
    async def get_ratios(
        self,
        symbol: str,
        limit: int = 4,
    ) -> list[dict]:
        async with httpx.AsyncClient(
            timeout=15,
            follow_redirects=True,
        ) as client:
            response = await client.get(
                f"{BASE}/ratios",
                params=self._p(
                    {
                        "symbol": symbol,
                        "limit": limit,
                    }
                ),
            )

        if response.status_code != 200:
            raise ProviderError(
                "fmp",
                f"ratios failed: {response.text}",
            )

        return response.json()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(min=1, max=8),
    )
    async def get_price_history(
        self,
        symbol: str,
        from_date: str,
        to_date: str,
    ) -> dict:
        async with httpx.AsyncClient(
            timeout=15,
            follow_redirects=True,
        ) as client:
            response = await client.get(
                f"{BASE}/historical-price-eod/full",
                params=self._p(
                    {
                        "symbol": symbol,
                        "from": from_date,
                        "to": to_date,
                    }
                ),
            )

        if response.status_code != 200:
            raise ProviderError(
                "fmp",
                f"price history failed: {response.text}",
            )

        return response.json()