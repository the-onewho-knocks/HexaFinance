from langgraph.graph import END, StateGraph

from core.constants import (
    NODE_NEWS,
    NODE_FINANCIAL,
    NODE_MARKET,
    NODE_SEC,
    NODE_QDRANT,
    NODE_MEMORY,
    NODE_AGGREGATE,
)

from graph.edges import ALL_NODES
from graph.nodes import (
    aggregation_node,
    financial_node,
    market_node,
    memory_node,
    news_node,
    qdrant_node,
    sec_node,
)
from graph.state import ResearchState


def build_graph() -> StateGraph:
    workflow = StateGraph(ResearchState)

    workflow.add_node(NODE_NEWS, news_node)
    workflow.add_node(NODE_FINANCIAL, financial_node)
    workflow.add_node(NODE_MARKET, market_node)
    workflow.add_node(NODE_SEC, sec_node)
    workflow.add_node(NODE_QDRANT, qdrant_node)
    workflow.add_node(NODE_MEMORY, memory_node)
    workflow.add_node(NODE_AGGREGATE, aggregation_node)

    workflow.set_entry_point(NODE_NEWS)

    workflow.add_edge(NODE_NEWS, NODE_FINANCIAL)
    workflow.add_edge(NODE_FINANCIAL, NODE_MARKET)
    workflow.add_edge(NODE_MARKET, NODE_SEC)
    workflow.add_edge(NODE_SEC, NODE_QDRANT)
    workflow.add_edge(NODE_QDRANT, NODE_MEMORY)
    workflow.add_edge(NODE_MEMORY, NODE_AGGREGATE)
    workflow.add_edge(NODE_AGGREGATE, END)

    return workflow.compile()


_compiled = build_graph()


async def run_research_workflow(
    symbol: str,
    user_id: str | None = None,
    deep_analysis: bool = False,
) -> dict:
    initial_state: ResearchState = {
        "symbol": symbol.upper(),
        "user_id": user_id,
        "deep_analysis": deep_analysis,
    }

    result = await _compiled.ainvoke(initial_state)

    return result