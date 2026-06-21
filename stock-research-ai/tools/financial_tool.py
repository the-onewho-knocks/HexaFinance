from loguru import logger

from core.exceptions import ProviderError
from providers.finance.fmp_client import FMPClient


class FinancialTool:
    def __init__(self) -> None:
        self._client = FMPClient()

    async def get_financials(self, symbol: str) -> dict:
        try:
            income, balance, ratios = await self._fetch_all(symbol)
            return {
                "income_statement": income[:4] if income else [],
                "balance_sheet": balance[:4] if balance else [],
                "ratios": ratios[:1] if ratios else [],
                "source": "fmp",
            }

        except Exception as exc:
            logger.exception(f"Financial fetch failed for {symbol}")

            return {
                "income_statement": [],
                "balance_sheet": [],
                "ratios": [],
                "source": "fmp",
                "error": str(exc),
            }

    async def _fetch_all(self, symbol: str) -> tuple:
        income = await self._client.get_income_statement(symbol)
        balance = await self._client.get_balance_sheet(symbol)
        ratios = await self._client.get_ratios(symbol)
        return income, balance, ratios