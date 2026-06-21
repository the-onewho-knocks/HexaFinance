import json

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings
from core.exceptions import ProviderError

BASE = "https://efts.sec.gov/LATEST/search-index"
CIK_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
IX_VIEWER = "https://www.sec.gov/ix?doc=/Archives/edgar/data/{cik}/{accession}/{primary_doc}"
ARCHIVES = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_doc}"

_CIK_CACHE: dict[str, str] = {}


class SECClient:
    HEADERS = {
        "User-Agent": "StockResearchAI/1.0 (drj2905@gmail.com)",
        "Accept-Encoding": "gzip, deflate",
    }

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=8))
    async def search_filings(
        self,
        query: str,
        form_type: str = "10-K",
        hits: int = 5,
    ) -> list[dict]:
        params = {"q": query, "forms": form_type, "size": hits}

        async with httpx.AsyncClient(timeout=20, headers=self.HEADERS) as c:
            r = await c.get(BASE, params=params)

        if r.status_code != 200:
            raise ProviderError("sec", f"status {r.status_code}: {r.text[:200]}")

        content_type = r.headers.get("content-type", "")
        if "json" not in content_type:
            raise ProviderError("sec", f"Expected JSON, got {content_type}: {r.text[:200]}")

        try:
            data = r.json()
        except json.JSONDecodeError:
            raise ProviderError("sec", f"Non-JSON response: {r.text[:200]}")

        hits_list = data.get("hits", {}).get("hits", [])
        return [h.get("_source", {}) for h in hits_list[:hits]]

    async def cik_from_ticker(self, symbol: str) -> str | None:
        symbol = symbol.upper()
        if symbol in _CIK_CACHE:
            return _CIK_CACHE[symbol]

        try:
            async with httpx.AsyncClient(timeout=15, headers=self.HEADERS , follow_redirects=True) as c:
                r = await c.get(CIK_URL)

            if r.status_code != 200:
                logger.warning(f"CIK lookup failed: {r.status_code}")
                return None

            data = r.json()
            for item in data.values():
                ticker = item.get("ticker", "").upper()
                if ticker == symbol:
                    cik_str = str(item["cik_str"]).zfill(10)
                    _CIK_CACHE[symbol] = cik_str
                    return cik_str

            logger.warning(f"No CIK found for symbol '{symbol}'")
            return None
        except Exception as exc:
            logger.warning(f"CIK lookup exception for {symbol}: {exc}")
            return None
        
        
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=8))
    async def get_submissions(self, cik: str) -> dict:
        url = SUBMISSIONS_URL.format(cik=cik)
        async with httpx.AsyncClient(timeout=20, headers=self.HEADERS , follow_redirects = True) as c:
            r = await c.get(url)

        if r.status_code != 200:
            raise ProviderError("sec", f"submissions failed: {r.status_code}")

        return r.json()
    
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=8))
    async def get_filing_html(self, cik: str, accession: str, primary_doc: str) -> str:
        url = ARCHIVES.format(cik=cik, accession=accession, primary_doc=primary_doc)
        async with httpx.AsyncClient(timeout=30, headers=self.HEADERS , follow_redirects=True) as c:
            r = await c.get(url)

        if r.status_code != 200:
            raise ProviderError("sec", f"document fetch failed: {r.status_code}")

        return r.text

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=8))
    async def get_filing_document(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=30, headers=self.HEADERS) as c:
            r = await c.get(url)

        if r.status_code != 200:
            raise ProviderError("sec", f"doc fetch failed: {r.status_code}")

        return r.text

# import json

# import httpx
# from tenacity import retry, stop_after_attempt, wait_exponential

# from core.exceptions import ProviderError

# SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
# TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
# ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"


# class SECClient:
#     HEADERS = {
#         "User-Agent": "StockResearchAI/1.0 (contact@example.com)",
#         "Accept-Encoding": "gzip, deflate",
#     }

#     _cik_cache: dict[str, str] | None = None

#     @retry(
#         stop=stop_after_attempt(5),
#         wait=wait_exponential(min=1, max=8),
#     )
#     async def resolve_cik(self, symbol: str) -> str | None:
#         """Map ticker -> 10-digit zero-padded CIK. Cached after first call."""
#         if self._cik_cache is None:
#             async with httpx.AsyncClient(timeout=20, headers=self.HEADERS) as c:
#                 r = await c.get(TICKERS_URL)

#             if r.status_code != 200:
#                 raise ProviderError(
#                     "sec", f"ticker lookup failed: status {r.status_code}"
#                 )

#             try:
#                 data = r.json()
#             except json.JSONDecodeError:
#                 raise ProviderError("sec", "ticker lookup returned non-JSON")

#             self.__class__._cik_cache = {
#                 entry["ticker"].upper(): str(entry["cik_str"]).zfill(10)
#                 for entry in data.values()
#             }

#         return self._cik_cache.get(symbol.upper())

#     @retry(
#         stop=stop_after_attempt(5),
#         wait=wait_exponential(min=1, max=8),
#     )
#     async def search_filings(
#         self,
#         cik: str | None = None,
#         query: str | None = None,
#         form_type: str = "10-K",
#         hits: int = 5,
#     ) -> list[dict]:
#         """
#         Search EDGAR full-text search index.

#         Prefer `cik` for precise, noise-free results scoped to one company.
#         Falls back to free-text `query` only if no CIK is available
#         (e.g. symbol not found in the ticker file).
#         """
#         if not cik and not query:
#             raise ProviderError("sec", "search_filings requires cik or query")

#         params: dict[str, str | int] = {
#             "forms": form_type,
#             "size": hits,
#         }
#         if cik:
#             params["ciks"] = cik
#         if query:
#             params["q"] = query

#         async with httpx.AsyncClient(timeout=20, headers=self.HEADERS) as c:
#             r = await c.get(SEARCH_URL, params=params)

#         if r.status_code != 200:
#             raise ProviderError("sec", f"status {r.status_code}: {r.text[:200]}")

#         content_type = r.headers.get("content-type", "")
#         if "json" not in content_type:
#             raise ProviderError(
#                 "sec",
#                 f"Expected JSON, got {content_type}: {r.text[:200]}",
#             )

#         try:
#             data = r.json()
#         except json.JSONDecodeError:
#             raise ProviderError(
#                 "sec",
#                 f"Non-JSON response: {r.text[:200]}",
#             )

#         hits_list = data.get("hits", {}).get("hits", [])
#         results = []
#         for h in hits_list[:hits]:
#             source = dict(h.get("_source", {}))  # copy, don't mutate original
#             source["_es_id"] = h.get("_id", "")
#             results.append(source)
#         return results

#     def build_filing_url(self, source: dict) -> str | None:
#         """
#         Construct the filing document URL from a search hit's _source.

#         Real EDGAR full-text-search fields (confirmed from live response):
#           - source["adsh"]          -> "0000320193-25-000079"
#           - source["ciks"]          -> ["0000320193"]  (list)
#           - source["_es_id"]        -> "0000320193-25-000079:aapl-20250927.htm"
#                                         (adsh:filename, injected by search_filings above)
#         """
#         adsh = source.get("adsh", "")
#         ciks = source.get("ciks") or []
#         cik = ciks[0] if ciks else None

#         if not adsh or not cik:
#             return None

#         accession_nodash = adsh.replace("-", "")
#         cik_nodash = cik.lstrip("0") or "0"  # archive paths use CIK without leading zeros

#         es_id = source.get("_es_id", "")
#         filename = es_id.split(":", 1)[1] if ":" in es_id else ""

#         if filename:
#             return f"{ARCHIVES_BASE}/{cik_nodash}/{accession_nodash}/{filename}"
#         return f"{ARCHIVES_BASE}/{cik_nodash}/{accession_nodash}/"

#     def build_title(self, source: dict) -> str:
#         """
#         Real field is 'display_names' (snake_case, list), e.g.:
#           ["Apple Inc.  (AAPL)  (CIK 0000320193)"]
#         """
#         names = source.get("display_names")
#         if isinstance(names, list) and names:
#             return "; ".join(names)
#         if isinstance(names, str):
#             return names
#         return source.get("form", "") or ""

#     @retry(
#         stop=stop_after_attempt(5),
#         wait=wait_exponential(min=1, max=8),
#     )
#     async def get_filing_document(self, url: str) -> str:
#         async with httpx.AsyncClient(timeout=30, headers=self.HEADERS) as c:
#             r = await c.get(url)

#         if r.status_code != 200:
#             raise ProviderError("sec", f"doc fetch failed: {r.status_code}")

#         return r.text

