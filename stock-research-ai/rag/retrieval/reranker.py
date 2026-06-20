
def rerank_by_symbol(results: list[dict], symbol: str) -> list[dict]:
    """Boost results that match the given symbol."""
    symbol_upper = symbol.upper()

    def sort_key(item: dict) -> float:
        base = item.get("score", 0.0)
        payload_symbol = (item.get("symbol") or "").upper()
        boost = 0.2 if payload_symbol == symbol_upper else 0.0
        return base + boost

    return sorted(results, key=sort_key, reverse=True)


def rerank_by_form_type(results: list[dict], preferred: str) -> list[dict]:
    """Boost results with the preferred form type."""
    def sort_key(item: dict) -> float:
        base = item.get("score", 0.0)
        form = (item.get("form_type") or "").upper()
        boost = 0.15 if form == preferred.upper() else 0.0
        return base + boost

    return sorted(results, key=sort_key, reverse=True)


def filter_by_threshold(
    results: list[dict],
    min_score: float = 0.5,
) -> list[dict]:
    return [r for r in results if (r.get("score") or 0.0) >= min_score]