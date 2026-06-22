from typing import Any, TypedDict


class ResearchState(TypedDict, total=False):
    # Input
    symbol: str
    user_id: str | None
    deep_analysis: bool

    # Raw agent outputs
    news_data: dict[str, Any]
    financial_data: dict[str, Any]
    market_data: dict[str, Any]
    sec_data: dict[str, Any]
    memory_data: dict[str, Any]

    # Agent summaries
    news_summary: str
    financial_summary: str
    market_summary: str
    sec_summary: str
    sec_risk_factors: list[str]
    sec_red_flags: list[str]
    sec_opportunities: list[str]
    sec_growth_trends: list[str]
    sec_insider_trades: list[dict]
    sec_key_metrics: dict[str, Any]
    sec_material_events: list[str]
    sec_management_outlook: str
    memory_summary: str
    memory_provider: str | None
    memory_error: str | None

    qdrant_context: str
    qdrant_sources: list[dict]
    qdrant_error: str | None

    # Aggregation output
    executive_summary: str
    investment_thesis: str
    recommendation: str
    confidence_score: float
    strengths: list[str]
    risks: list[str]
    opportunities: list[str]
    red_flags: list[str]

    # Sources
    sources: list[dict[str, Any]]

    # Metadata
    errors: list[str]
    aggregated: dict[str, Any]