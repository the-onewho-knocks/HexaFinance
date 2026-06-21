import json
import re

from loguru import logger

from core.config import settings
from providers.llm.gateway import LLMGateway
from schemas.llm import LLMRequest
from tools.sec_tool import SECTool


class SECAgent:
    def __init__(self) -> None:
        self._tool = SECTool()
        has_gemini = bool(settings.gemini_api_key)
        has_groq = bool(settings.groq_api_key)
        self._llm_available = has_gemini or has_groq
        if self._llm_available:
            provider = "groq" if has_groq else "gemini"
            self._llm = LLMGateway(provider=provider)

    async def run(self, symbol: str) -> dict:
        filings_result = await self._tool.get_all_filings(symbol)

        # If CIK lookup failed, fall back to metadata-only search
        if not filings_result.get("cik"):
            return await self._metadata_fallback(symbol)

        html = filings_result.get("latest_10k_html", "")
        insider_trades = filings_result.get("insider_trades", [])

        risk_factors = self._tool.extract_risk_factors(html)
        mda_text = self._tool.extract_mda(html)
        key_metrics = self._tool.extract_key_metrics_from_10k(html)
        material_events = self._tool.extract_material_events(html)

        if self._llm_available:
            insights = await self._llm_insights(
                symbol, risk_factors, mda_text,
                insider_trades, material_events, key_metrics,
            )
        else:
            insights = self._deterministic_insights(
                risk_factors, mda_text,
                insider_trades, material_events, key_metrics,
            )

        sec_summary = self._build_summary(
            symbol, filings_result, risk_factors,
            insights, insider_trades,
        )

        sources = self._build_sources(filings_result)

        return {
            "sec_summary": sec_summary,
            "risk_factors": insights.get("risk_factors", risk_factors),
            "management_outlook": insights.get("management_outlook", ""),
            "growth_trends": insights.get("growth_trends", []),
            "material_events": insights.get(
                "material_events", material_events
            ),
            "insider_trading": insights.get(
                "insider_trading", insider_trades
            ),
            "key_metrics": insights.get("key_metrics", key_metrics),
            "red_flags": insights.get("red_flags", []),
            "opportunities": insights.get("opportunities", []),
            "source": "sec",
            "sources": sources,
            "error": filings_result.get("error"),
        }

    async def _llm_insights(
        self,
        symbol: str,
        risk_factors: list[str],
        mda_text: str,
        insider_trades: list[dict],
        material_events: list[str],
        key_metrics: dict,
    ) -> dict:
        prompt = (
            f"Analyze SEC filings for {symbol} and return structured JSON with:\n"
            f"- risk_factors: list of top risks from the filing\n"
            f"- management_outlook: brief outlook from MD&A\n"
            f"- growth_trends: list of positive trends\n"
            f"- material_events: list of significant events\n"
            f"- red_flags: list of warning signs\n"
            f"- opportunities: list of opportunities\n"
            f"- key_metrics: dict of financial metrics\n\n"
            f"Risk factors: {risk_factors}\n\n"
            f"MD&A: {mda_text[:1500]}\n\n"
            f"Insider trades: {insider_trades}\n\n"
            f"Events: {material_events}\n\n"
            f"Metrics: {key_metrics}\n\n"
            "Respond in JSON format only."
        )

        try:
            req = LLMRequest(
                prompt=prompt, max_tokens=1024, temperature=0.3
            )
            resp = await self._llm.complete(req)
            return self._parse_llm_json(resp.text, risk_factors, mda_text, insider_trades, material_events, key_metrics)
        
        except Exception as exc:
            logger.warning(f"LLM SEC insights failed: {exc}")
            return self._deterministic_insights(
                risk_factors, mda_text,
                insider_trades, material_events, key_metrics,
            )

    def _deterministic_insights(
        self,
        risk_factors: list[str],
        mda_text: str,
        insider_trades: list[dict],
        material_events: list[str],
        key_metrics: dict,
    ) -> dict:
        red_flags = []
        opportunities = []
        growth_trends = []

        # Red flags from risk factors
        high_risk_keywords = ["material adverse", "significant loss",
                              "going concern", "substantial doubt"]
        for rf in risk_factors:
            if any(kw in rf.lower() for kw in high_risk_keywords):
                red_flags.append(rf)

        # Opportunities from MD&A
        opp_keywords = ["growth", "opportunity", "expansion",
                        "new market", "investment"]
        if mda_text:
            sentences = re.split(r"[.!?]\s+", mda_text)
            for s in sentences:
                if any(kw in s.lower() for kw in opp_keywords):
                    opportunities.append(s.strip()[:200])
            growth_sentences = [s for s in sentences
                                if "growth" in s.lower() or "increase" in s.lower()]
            growth_trends = growth_sentences[:3]

        # Red flags from insider trading
        insider_sell_count = 0
        for trade in insider_trades:
            doc = trade.get("document", "").lower()
            if "sell" in doc:
                insider_sell_count += 1
        if insider_sell_count >= 3:
            red_flags.append(
                f"High insider selling activity detected "
                f"({insider_sell_count} sell transactions)"
            )

        return {
            "risk_factors": risk_factors,
            "management_outlook": mda_text[:500] if mda_text else "",
            "growth_trends": growth_trends,
            "material_events": material_events,
            "insider_trading": insider_trades,
            "key_metrics": key_metrics,
            "red_flags": red_flags,
            "opportunities": opportunities,
        }

    async def _metadata_fallback(self, symbol: str) -> dict:
        raw = await self._tool.get_filings(symbol, form_type="10-K", hits=3)
        filings = raw.get("filings", [])

        if not filings:
            return {
                "sec_summary": f"No SEC filings found for {symbol}",
                "risk_factors": [],
                "management_outlook": "",
                "growth_trends": [],
                "material_events": [],
                "insider_trading": [],
                "key_metrics": {},
                "red_flags": [],
                "opportunities": [],
                "source": "sec",
                "sources": [],
                "error": raw.get("error"),
            }

        sources = []
        for f in filings[:3]:
            raw_title = (
                f.get("displayNames")
                or f.get("display_name")
                or f.get("summary")
                or ""
            )
            title = (
                "; ".join(raw_title)
                if isinstance(raw_title, list)
                else str(raw_title)
            )
            sources.append({
                "type": "sec",
                "title": title,
                "url": None,
            })

        return {
            "sec_summary": (
                f"Found {len(filings)} SEC filings for {symbol}. "
                f"Content analysis unavailable (CIK lookup failed)."
            ),
            "risk_factors": [],
            "management_outlook": "",
            "growth_trends": [],
            "material_events": [],
            "insider_trading": [],
            "key_metrics": {},
            "red_flags": [],
            "opportunities": [],
            "source": "sec",
            "sources": sources,
            "error": raw.get("error"),
        }

    def _build_summary(
        self,
        symbol: str,
        filings_result: dict,
        risk_factors: list[str],
        insights: dict,
        insider_trades: list[dict],
    ) -> str:
        filings_by_type = filings_result.get("filings_by_type", {})
        counts = {k: len(v) for k, v in filings_by_type.items()}
        parts = [f"SEC analysis for {symbol}:"]

        if counts.get("10-K"):
            parts.append(f"Annual report (10-K): {counts['10-K']} filing(s)")
        if counts.get("10-Q"):
            parts.append(f"Quarterly reports (10-Q): {counts['10-Q']} filing(s)")
        if counts.get("8-K"):
            parts.append(f"Current reports (8-K): {counts['8-K']} filing(s)")

        if risk_factors:
            parts.append(
                f"Risk factors identified: {len(risk_factors)} key risks"
            )
        if insights.get("opportunities"):
            parts.append(
                f"Opportunities identified: {len(insights['opportunities'])}"
            )
        if insights.get("red_flags"):
            parts.append(
                f"Red flags: {len(insights['red_flags'])} warning signs"
            )
        if insider_trades:
            part = f"Insider trading activity detected: {len(insider_trades)} Form 4 filings"
            parts.append(part)

        return ". ".join(parts)

    def _build_sources(self, filings_result: dict) -> list[dict]:
        sources = []
        for ftype, filings in filings_result.get("filings_by_type", {}).items():
            for f in filings[:3]:
                title = f"{ftype} — filed {f.get('filing_date', '')}"
                doc = f.get("primary_document", "")
                url = (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{filings_result.get('cik')}/"
                    f"{f.get('accession_number', '').replace('-', '')}/{doc}"
                    if filings_result.get("cik") and doc else None
                )
                sources.append({"type": "sec", "title": title, "url": url})
        return sources
    
    def _parse_llm_json(self, text: str, risk_factors, mda_text, insider_trades, material_events, key_metrics) -> dict:
        import re
        # Strip markdown code fences
        cleaned = re.sub(r"```(?:json)?\s*", "", text).strip()
        # Try to find JSON object
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        # Fallback
        return self._deterministic_insights(risk_factors, mda_text, insider_trades, material_events, key_metrics)

# from tools.sec_tool import SECTool


# class SECAgent:
#     def __init__(self):
#         self._tool = SECTool()

#     async def run(self, symbol: str):
#         raw = await self._tool.get_filings(symbol, form_type="10-K", hits=3)
#         filings = raw.get("filings", [])

#         if not filings:
#             return {
#                 "sec_summary": f"No SEC filings found for {symbol}",
#                 "sources": [],
#                 "risk_factors": [],
#                 "filing_highlights": "",
#                 "source": "sec",
#                 "error": raw.get("error"),
#             }

#         latest = filings[0]
#         # real filings have no "description"/"summary" text field in search
#         # results (those are only present for some form types) — fall back
#         # to a constructed description from what's actually returned
#         highlights = (
#             latest.get("description")
#             or latest.get("summary")
#             or f"{latest.get('form', '')} filed {latest.get('file_date', '')} "
#                f"for period ending {latest.get('period_ending', '')}"
#         )
#         highlights_text = str(highlights)[:1500]

#         sources = [
#             {
#                 "type": "sec",
#                 "title": f.get("title", ""),
#                 "url": f.get("url"),
#             }
#             for f in filings[:3]
#         ]

#         risk_factors = []
#         if "risk" in highlights_text.lower():
#             risk_factors.append("Risk factor identified in latest filing")

#         summary = (
#             f"Found {len(filings)} SEC filings for {symbol}. "
#             f"Latest: {highlights_text[:200]}..."
#         )

#         return {
#             "sec_summary": summary,
#             "sources": sources,
#             "risk_factors": risk_factors,
#             "filing_highlights": highlights_text,
#             "source": "sec",
#             "error": None,
#         }