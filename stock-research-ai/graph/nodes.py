from loguru import logger

from agents.news_agent import NewsAgent
from agents.financial_agent import FinancialAgent
from agents.market_agent import MarketAgent
from agents.sec_agent import SECAgent
from agents.memory_agent import MemoryAgent
from agents.aggregation_agent import AggregationAgent
from core.constants import COLLECTION_SEC_FILINGS
from graph.state import ResearchState
from rag.index_manager import index_text
from rag.retrieval.retriever import retrieve_context, retrieve_sources

_news = NewsAgent()
_financial = FinancialAgent()
_market = MarketAgent()
_sec = SECAgent()
_memory = MemoryAgent()
_aggregation = AggregationAgent()


async def news_node(state: ResearchState) -> dict:
    symbol = state["symbol"]
    output = await _news.run(symbol)
    return {
        "news_data": output,
        "news_summary": output.get("news_summary", ""),
    }


async def financial_node(state: ResearchState) -> dict:
    symbol = state["symbol"]
    output = await _financial.run(symbol)
    return {
        "financial_data": output,
        "financial_summary": output.get("financial_summary", ""),
    }


async def market_node(state: ResearchState) -> dict:
    symbol = state["symbol"]
    output = await _market.run(symbol)
    return {
        "market_data": output,
        "market_summary": output.get("market_summary", ""),
    }


async def sec_node(state: ResearchState) -> dict:
    symbol = state["symbol"]
    output = await _sec.run(symbol)
    return {
        "sec_data": output,
        "sec_summary": output.get("sec_summary", ""),
        "sec_risk_factors": output.get("risk_factors", []),
        "sec_red_flags": output.get("red_flags", []),
        "sec_opportunities": output.get("opportunities", []),
        "sec_growth_trends": output.get("growth_trends", []),
        "sec_insider_trades": output.get("insider_trading", []),
        "sec_key_metrics": output.get("key_metrics", {}),
        "sec_material_events": output.get("material_events", []),
        "sec_management_outlook": output.get("management_outlook", ""),
    }


async def qdrant_node(state: ResearchState) -> dict:
    symbol = state["symbol"]
    sec_data = state.get("sec_data", {})

    risk_factors = sec_data.get("risk_factors", [])
    mda_text = sec_data.get("management_outlook", "")

    text_to_index = ""
    if risk_factors:
        text_to_index += "Risk Factors:\n" + "\n".join(risk_factors) + "\n\n"
    if mda_text:
        text_to_index += "Management Outlook:\n" + mda_text

    result = {
        "qdrant_context": "",
        "qdrant_sources": [],
        "qdrant_error": None,
    }

    if not text_to_index.strip():
        result["qdrant_error"] = "No SEC text available to index"
        return result

    try:
        await index_text(
            text_to_index,
            symbol=symbol,
            form_type="10-K",
            collection_name=COLLECTION_SEC_FILINGS,
        )
    except Exception as exc:
        logger.warning(f"Qdrant indexing failed for {symbol}: {exc}")

    try:
        context = await retrieve_context(
            f"SEC risk factors and management outlook for {symbol}",
            symbol=symbol,
            limit=5,
        )
        sources = await retrieve_sources(
            f"SEC risk factors and management outlook for {symbol}",
            symbol=symbol,
            limit=5,
        )
        result["qdrant_context"] = context
        result["qdrant_sources"] = sources
    except Exception as exc:
        logger.warning(f"Qdrant search failed for {symbol}: {exc}")
        result["qdrant_error"] = str(exc)

    return result


async def memory_node(state: ResearchState) -> dict:
    symbol = state["symbol"]
    user_id = state.get("user_id")
    output = await _memory.run(symbol, user_id)
    return {
        "memory_data": output,
        "memory_summary": output.get("memory_summary", ""),
        "memory_provider": output.get("provider"),
        "memory_error": output.get("error"),
    }


async def aggregation_node(state: ResearchState) -> dict:
    agent_outputs = {
        "news": state.get("news_data", {}),
        "financial": state.get("financial_data", {}),
        "market": state.get("market_data", {}),
        "sec": state.get("sec_data", {}),
        "memory": state.get("memory_data", {}),
        "qdrant": state.get("qdrant_context", ""),
    }

    output = await _aggregation.run(agent_outputs)

    sources: list[dict] = []
    for key in ("news", "sec"):
        agent_out = agent_outputs.get(key, {})
        srcs = agent_out.get("sources", [])
        if isinstance(srcs, list):
            sources.extend(srcs)

    return {
        "aggregated": output,
        "executive_summary": output.get("executive_summary", ""),
        "investment_thesis": output.get("investment_thesis", ""),
        "recommendation": output.get("recommendation", "HOLD"),
        "confidence_score": output.get("confidence_score", 0.0),
        "strengths": output.get("strengths", []),
        "risks": output.get("risks", []),
        "opportunities": output.get("opportunities", []),
        "red_flags": output.get("red_flags", []),
        "sources": sources,
    }