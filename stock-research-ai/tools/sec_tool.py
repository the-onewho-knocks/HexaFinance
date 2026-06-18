from loguru import logger

from core.exceptions import ProviderError
from providers.finance.sec_client import SECClient

class SECTool:
    def __init__(self)->None:
        self._client = SECClient()

    async def get_filings(
            self,
            symbol:str,
            form_type : str = "10-k",
            hits: int = 3,
    ) -> dict:
        try:
            filings = await self._client.search_fillings(
                query = symbol,
                form_type = form_type,
                hits = hits,
            )
            return{
                "filings" : filings,
                "total": len(filings),
                "source": "sec",
            }
        except ProviderError as exc:
            logger.warning(f"Filings fetch failed for {symbol}: {exc}")
            return {
                "filings": [],
                "total": 0,
                "source": "sec",
                "error": str(exc),
            }
        
    async def get_filings_document(self , url: str) -> dict:
        try:
            text = await self._client.get_filing_document(url)
            return {"text": text[:5000], "source": "sec"}
        except ProviderError as exc:
            logger.warning(f"Document fetch failed for {url}: {exc}")
            return {"text": "", "source": "sec", "error": str(exc)}