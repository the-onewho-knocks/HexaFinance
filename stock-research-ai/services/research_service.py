from schemas.research import ResearchRequest, ResearchResponse


class ResearchService:
    async def run_research(self, request: ResearchRequest) -> ResearchResponse:
        symbol = request.symbol.upper()

        return ResearchResponse(
            symbol=symbol,
            company_name=symbol,
            executive_summary="Research workflow is not fully implemented yet.",
            recommendation="HOLD",
            confidence_score=0.0,
            news_summary="News analysis is pending implementation.",
            financial_summary="Financial analysis is pending implementation.",
            market_summary="Market analysis is pending implementation.",
            sec_summary="SEC filing analysis is pending implementation.",
            report_id=None,
        )