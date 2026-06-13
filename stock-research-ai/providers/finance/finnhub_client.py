import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from core.config import settings
from core.exceptions import ProviderError
from loguru import logger

BASE = "https://finnhub.io/api/v1"

class FinhubClient:
    def __init__(self):
        self._key = settings.finnhub_api_key

    @retry(
            stop = stop_after_attempt(5), 
            wait=wait_exponential(min=1 , max=8)
            )
    async def get_company_news(self , symbol:str , from_date:str , to_date:str) -> list[dict]:
        url = f"{BASE}/company-news"
        params = {"symbol": symbol, "from": from_date, "to": to_date , "token":self._key}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url , params=params)
        if resp.status_code != 200:
            raise ProviderError("finnhub error" , f"news failed : {resp.text}")
        return resp.json()
    
    
    @retry(
        stop = stop_after_attempt(5),
        wait = wait_exponential(min = 1 , max = 8)
    )
    async def get_quote(self , symbol:str) -> dict:
        url = f"{BASE}/quote"
        params = {"symbol": symbol , "token":self._key}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url , params=params)
        if resp.status_code != 200:
            raise ProviderError("finnhub error" , f"quote failed : {resp.text}")
        return resp.json()
    
    
    @retry(
        stop = stop_after_attempt(5),
        wait = wait_exponential(min = 1 , max = 8)
    )
    async def get_company_profile(self , symbol:str) -> dict:
        url = f"{BASE}/stock/profile2"
        params = {"symbol": symbol , "token":self._key}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url , params=params)
        if resp.status_code != 200:
            raise ProviderError("finnhub" , f"profile failed : {resp.text}")
        return resp.json()