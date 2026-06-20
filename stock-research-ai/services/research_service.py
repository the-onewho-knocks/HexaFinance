import json
from datetime import datetime, timezone
from uuid import uuid4

from loguru import logger

from database.postgres import get_connection
from graph.workflow import run_research_workflow
from memory.memory_service import MemoryService
from schemas.research import ResearchRequest, ResearchResponse


class ResearchService:
    def __init__(self) -> None:
        self._memory = MemoryService()

    async def run_research(self, request: ResearchRequest) -> ResearchResponse:
        request_id = str(uuid4())
        symbol = request.symbol.upper()

        logger.info(f"Research started: {request_id} for {symbol}")

        try:
            result = await run_research_workflow(
                symbol=symbol,
                user_id=request.user_id,
                deep_analysis=request.deep_analysis,
            )
        except Exception as exc:
            logger.error(f"Workflow failed for {symbol}: {exc}")
            return self._error_response(symbol, request_id, str(exc))

        aggregated = result.get("aggregated", {})

        response = ResearchResponse(
            request_id=request_id,
            symbol=symbol,
            company_name=(
                result.get("market_data", {})
                .get("key_metrics", {})
                .get("company_name", symbol)
            ),
            executive_summary=aggregated.get("executive_summary", ""),
            investment_thesis=aggregated.get("investment_thesis", ""),
            recommendation=aggregated.get("recommendation", "HOLD"),
            confidence_score=aggregated.get("confidence_score", 0.0),
            news_summary=aggregated.get("news_summary", ""),
            financial_summary=aggregated.get("financial_summary", ""),
            market_summary=aggregated.get("market_summary", ""),
            sec_summary=aggregated.get("sec_summary", ""),
            memory_summary=aggregated.get("memory_summary", ""),
            key_metrics=(
                result.get("financial_data", {})
                .get("key_metrics", {})
            ),
            strengths=aggregated.get("strengths", []),
            risks=aggregated.get("risks", []),
            opportunities=aggregated.get("opportunities", []),
            red_flags=aggregated.get("red_flags", []),
            sources=result.get("sources", []),
            agent_outputs={
                "news": result.get("news_data", {}),
                "financial": result.get("financial_data", {}),
                "market": result.get("market_data", {}),
                "sec": result.get("sec_data", {}),
                "memory": result.get("memory_data", {}),
            },
            errors=result.get("errors", []),
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        await self._persist(request_id, request, response)
        await self._store_if_enabled(symbol, request.user_id, aggregated)

        return response

    async def _persist(
        self,
        request_id: str,
        request: ResearchRequest,
        response: ResearchResponse,
    ) -> None:
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO research_runs (
                        id, symbol, user_id, input_payload,
                        final_response, agent_outputs, status, created_at, completed_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        request_id,
                        request.symbol.upper(),
                        request.user_id,
                        json.dumps(request.model_dump()),
                        response.model_dump_json(),
                        json.dumps(response.agent_outputs),
                        "completed",
                        datetime.now(timezone.utc),
                        datetime.now(timezone.utc),
                    ),
                )
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.warning(f"Failed to persist research run: {exc}")

    async def _store_if_enabled(
        self,
        symbol: str,
        user_id: str | None,
        aggregated: dict,
    ) -> None:
        try:
            await self._memory.store_research_summary(
                symbol=symbol,
                user_id=user_id,
                recommendation=aggregated.get("recommendation", "HOLD"),
                confidence_score=aggregated.get("confidence_score", 0.0),
                executive_summary=aggregated.get("executive_summary", ""),
                key_risks=aggregated.get("risks", []),
                key_strengths=aggregated.get("strengths", []),
            )
        except Exception as exc:
            logger.warning(f"Failed to store memory summary: {exc}")

    def _error_response(
        self, symbol: str, request_id: str, error: str,
    ) -> ResearchResponse:
        return ResearchResponse(
            request_id=request_id,
            symbol=symbol,
            company_name=symbol,
            executive_summary="Research workflow encountered an error.",
            investment_thesis="",
            recommendation="HOLD",
            confidence_score=0.0,
            news_summary="",
            financial_summary="",
            market_summary="",
            sec_summary="",
            memory_summary="",
            key_metrics={},
            strengths=[],
            risks=[],
            opportunities=[],
            red_flags=[],
            sources=[],
            agent_outputs={},
            errors=[error],
            created_at=datetime.now(timezone.utc).isoformat(),
        )