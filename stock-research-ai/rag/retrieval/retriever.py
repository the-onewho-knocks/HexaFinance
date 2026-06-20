from rag.retrieval.search import search_similar


async def retrieve_context(
    query: str,
    *,
    symbol: str | None = None,
    limit: int = 5,
) -> str:
    results = await search_similar(
        query=query,
        symbol=symbol,
        limit=limit,
    )

    if not results:
        return "No relevant context found."

    context_parts = []
    for r in results:
        score = r.get("score", 0)
        if score < 0.5:
            continue
        text = r.get("text", "")
        if text:
            context_parts.append(f"[Relevance: {score:.2f}] {text}")

    if not context_parts:
        return "No relevant context found."

    return "\n\n".join(context_parts[:3])


async def retrieve_sources(
    query: str,
    *,
    symbol: str | None = None,
    limit: int = 5,
) -> list[dict]:
    return await search_similar(
        query=query,
        symbol=symbol,
        limit=limit,
    )