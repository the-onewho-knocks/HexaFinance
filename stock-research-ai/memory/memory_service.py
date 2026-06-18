from memory.schemas import(
    BaseMemoryProvider,
    MemorySearchResult,
    MemoryStoreResult,
)
from memory.xtrace_client import XTraceMemoryProvider


class MemoryService:
    def __init__(self , provider : BaseMemoryProvider | None = None)->None:
        self.provider =  provider or  XTraceMemoryProvider() 

    async def get_research_context(
            self,
            symbol:str,
            user_id: str | None = None,
            query: str | None = None,
            limit: int = 5,
    )-> MemorySearchResult:
        return await self.provider.search(
            query=query or f"Research context for {symbol}",
            user_id=user_id,
            symbol=symbol,
            limit=limit,
        )
        
    async def store_research_summary(
        self,
        *,
        symbol: str,
        user_id: str | None = None,
        recommendation: str = "",
        confidence_score: float = 0.0,
        executive_summary: str = "",
        key_risks: list[str] | None = None,
        key_strengths: list[str] | None = None,
    ) -> MemoryStoreResult:
        risks = ", ".join(key_risks or [])
        strengths = ", ".join(key_strengths or [])

        text = (
            f"Research summary for {symbol}:\n"
            f"Recommendation: {recommendation}\n"
            f"Confidence: {confidence_score}\n"
            f"Summary: {executive_summary}\n"
            f"Strengths: {strengths}\n"
            f"Risks: {risks}"
        )

        return await self.provider.store(
            text=text,
            user_id=user_id,
            symbol=symbol,
            metadata={
                "recommendation": recommendation,
                "confidence_score": confidence_score,
            },
        )