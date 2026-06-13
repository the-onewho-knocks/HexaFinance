import httpx
from core.config import settings
from core.exceptions import ProviderError

BASE = "https://efts.sec.gov/LATEST/search-index"
EDGAR_BASE = "https://data.sec.gov"


class SECClient:
    """Thin wrapper around SEC EDGAR full-text search."""

    HEADERS = {"User-Agent": "StockResearchAI contact@example.com"}

    async def search_filings(self, query: str, form_type: str = "10-K", hits: int = 5) -> list[dict]:
        url = "https://efts.sec.gov/LATEST/search-index"
        params = {
            "q": query,
            "dateRange": "custom",
            "forms": form_type,
            "hits.hits.total.value": hits,
        }
        # Use EDGAR full-text search
        search_url = "https://efts.sec.gov/LATEST/search-index?q=%22{q}%22&forms={form}&hits.hits._source.period_of_report=*"
        edgar_url = f"https://efts.sec.gov/LATEST/search-index?q={query}&forms={form_type}"
        async with httpx.AsyncClient(timeout=20, headers=self.HEADERS) as c:
            r = await c.get(edgar_url)
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