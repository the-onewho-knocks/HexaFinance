import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from core.config import settings
from core.exceptions import ProviderError

BASE = "https://api.polygon.io/v2"

class PolygonClient:
    def __init__(self):
        self._key = settings.polygon_api_key

    @retry(stop=stop_after_attempt(5),
        wait=wait_exponential(min=1, max=8)
    )
    async def get_aggregates(
        self, symbol: str, from_date: str, 
        to_date: str,
        multiplier: int = 1, timespan: str = "day"
    ):
        url = f"{BASE}/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(url, params={"apiKey": self._key , "adjusted":"true" , "sort":"asc"})
        if r.status_code != 200:
            raise ProviderError("polygon error", f"aggregates failed: {r.text}")
        return r.json()
    
    @retry(stop=stop_after_attempt(5),
        wait=wait_exponential(min=1, max=8)
    )
    async def get_ticker_details(self , symbol:str)->dict:
        url = f"https://api.polygon.io/v3/reference/tickers/{symbol}"
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(url , params={"apiKey":self._key})  
        if r.status_code != 200:
            raise ProviderError("polygon error", f"ticker details failed: {r.text}")
        return r.json()