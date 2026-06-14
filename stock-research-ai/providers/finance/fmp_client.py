import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings
from core.exceptions import ProviderError

BASE = "https://financialmodelingprep.com/api/v3"


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
    async def get_income_statement(self, symbol: str, limit: int = 4) -> list[dict]:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(
                f"{BASE}/income-statement/{symbol}",
                params=self._p({"limit": limit}),
            )
        if r.status_code != 200:
            raise ProviderError("fmp", f"income statement failed: {r.text}")
        return r.json()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(min=1, max=8),
    )
    async def get_balance_sheet(self, symbol: str, limit: int = 4) -> list[dict]:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(
                f"{BASE}/balance-sheet-statement/{symbol}",
                params=self._p({"limit": limit}),
            )
        if r.status_code != 200:
            raise ProviderError("fmp", f"balance sheet failed: {r.text}")
        return r.json()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(min=1, max=8),
    )
    async def get_ratios(self, symbol: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(
                f"{BASE}/ratios/{symbol}",
                params=self._p({"limit": 4}),
            )
        if r.status_code != 200:
            raise ProviderError("fmp", f"ratios failed: {r.text}")
        return r.json()

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
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(
                f"{BASE}/historical-price-full/{symbol}",
                params=self._p({"from": from_date, "to": to_date}),
            )
        if r.status_code != 200:
            raise ProviderError("fmp", f"price history failed: {r.text}")
        return r.json()