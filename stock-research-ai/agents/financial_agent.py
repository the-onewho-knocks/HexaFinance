from tools.financial_tool import FinancialTool


class FinancialAgent:
    def __init__(self) -> None:
        self._tool = FinancialTool()

    async def run(self, symbol: str) -> dict:
        raw = await self._tool.get_financials(symbol)

        income = raw.get("income_statement", [])
        balance = raw.get("balance_sheet", [])
        ratios = raw.get("ratios", [])

        if not income and not balance:
            return {
                "financial_summary": f"Financial data unavailable for {symbol}.",
                "key_metrics": {},
                "risks": [],
                "error": raw.get("error"),
            }

        latest_income = income[0] if income else {}
        latest_balance = balance[0] if balance else {}
        latest_ratios = ratios[0] if ratios else {}

        revenue = latest_income.get("revenue", 0)
        net_income = latest_income.get("netIncome", 0)
        total_assets = latest_balance.get("totalAssets", 0)
        total_liabilities = latest_balance.get("totalLiabilities", 0)
        pe_ratio = (
            latest_ratios.get("priceEarningsRatio")
            or latest_ratios.get("priceToEarningsRatio")
            or latest_ratios.get("peRatio")
            or 0
        )
        debt_equity = (
            latest_ratios.get("debtEquityRatio")
            or latest_ratios.get("debtToEquityRatio")
            or latest_ratios.get("debtEquity")
            or 0
        )
        key_metrics = {
            "revenue": revenue,
            "net_income": net_income,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "pe_ratio": pe_ratio,
            "debt_to_equity": debt_equity,
        }

        risks = []
        if debt_equity and debt_equity > 2:
            risks.append("High debt-to-equity ratio")
        if net_income and revenue and net_income / revenue < 0.05:
            risks.append("Low profit margin")

        summary = (
            f"Revenue: {revenue}, Net Income: {net_income}, "
            f"P/E: {pe_ratio}, D/E: {debt_equity}"
        )

        return {
            "financial_summary": summary,
            "key_metrics": key_metrics,
            "risks": risks,
            "source": "fmp",
            "error": None,
        }