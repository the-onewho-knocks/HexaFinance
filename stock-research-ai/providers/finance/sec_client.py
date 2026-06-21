import httpx

from core.exceptions import ProviderError

BASE = "https://efts.sec.gov/LATEST/search-index"


class SECClient:
    """Thin wrapper around SEC EDGAR full-text search."""

    HEADERS = {
        "User-Agent": "StockResearchAI drj2905@gmail.com",
        "Accept-Encoding": "gzip, deflate",
        "Host": "efts.sec.gov",
    }

    async def search_filings(
        self,
        query: str,
        form_type: str = "10-K",
        hits: int = 5,
    ) -> list[dict]:
        params = {
            "q": query,
            "forms": form_type,
            "size": hits,
        }

        async with httpx.AsyncClient(timeout=20, headers=self.HEADERS) as c:
            r = await c.get(BASE, params=params)

        if r.status_code != 200:
            raise ProviderError("sec", r.text)

        data = r.json()
        hits_list = data.get("hits", {}).get("hits", [])
        return [h.get("_source", {}) for h in hits_list[:hits]]
    

    async def get_filing_document(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=30, headers=self.HEADERS) as c:
            r = await c.get(url)

        if r.status_code != 200:
            raise ProviderError("sec", f"doc fetch failed: {r.status_code}")

        return r.text