from core.config import settings
from providers.llm.gateway import LLMGateway
from schemas.llm import LLMRequest


class AggregationAgent:
    def __init__(self):
        has_gemini = bool(settings.gemini_api_key)
        has_groq = bool(settings.groq_api_key)
        self._llm_available = has_groq or has_gemini
        if self._llm_available:
            provider = "groq" if has_groq else "gemini"
            self._llm = LLMGateway(provider=provider)

    async def run(self, agent_outputs: dict) -> dict:
        news = agent_outputs.get("news", {})
        financial = agent_outputs.get("financial", {})
        market = agent_outputs.get("market", {})
        sec = agent_outputs.get("sec", {})
        memory = agent_outputs.get("memory", {})
        qdrant = agent_outputs.get("qdrant", "")

        if self._llm_available:
            return await self._llm_aggregate(
                news, financial, market, sec, memory, qdrant,
            )

        return self._deterministic_aggregate(
            news, financial, market, sec, memory, qdrant,
        )

    async def _llm_aggregate(
        self, news: dict, financial: dict,
        market: dict, sec: dict, memory: dict,
        qdrant_context: str = "",
    ) -> dict:
        prompt = (
            "Financial analyst task. Synthesize the 6 sources below into one detailed "
            "recommendation. Weigh all sources together. Treat News/Market as sentiment "
            "signals, Financial/SEC as factual. Flag contradictions. If a source is N/A, "
            "note it as a gap and lower confidence_score.\n\n"
            f"News: {news.get('news_summary', 'N/A')}\n"
            f"Financial: {financial.get('financial_summary', 'N/A')}\n"
            f"Market: {market.get('market_summary', 'N/A')}\n"
            f"SEC: {sec.get('sec_summary', 'N/A')}\n"
            f"Memory: {memory.get('memory_summary', 'N/A')}\n"
            f"Qdrant (semantic SEC filing chunks): {qdrant_context}\n\n"
            "For strengths/risks/opportunities/red_flags, give 3-5 specific, substantive "
            "points each (not generic filler) — cite which source(s) support each point. "
            "executive_summary should be a thorough paragraph (5-8 sentences), not a "
            "one-liner.\n\n"
            "Return ONLY this JSON (no markdown, no preamble), empty arrays if nothing notable:\n"
            '{"recommendation":"BUY|SELL|HOLD","confidence_score":0.0-1.0,'
            '"executive_summary":"detailed paragraph","strengths":[],"risks":[],'
            '"opportunities":[],"red_flags":[],"data_gaps":[]}'
        )

        req = LLMRequest(prompt=prompt, max_tokens=2048, temperature=0.3)
        resp = await self._llm.complete(req)
        return self._parse_llm_response(
            resp.text, news, financial, market, sec, memory,
        )

    def _parse_llm_response(
        self, text: str, news: dict, financial: dict,
        market: dict, sec: dict, memory: dict,
    ) -> dict:
        import json
        try:
            data = json.loads(text)
            return {
                "executive_summary": data.get("executive_summary", ""),
                "investment_thesis": data.get("investment_thesis", ""),
                "recommendation": data.get("recommendation", "HOLD"),
                "confidence_score": float(data.get("confidence_score", 0.5)),
                "strengths": data.get("strengths", []),
                "risks": data.get("risks", []),
                "opportunities": data.get("opportunities", []),
                "red_flags": data.get("red_flags", []),
                "memory_summary": memory.get("memory_summary", ""),
                "news_summary": news.get("news_summary", ""),
                "financial_summary": financial.get("financial_summary", ""),
                "market_summary": market.get("market_summary", ""),
                "sec_summary": sec.get("sec_summary", ""),
                "sec_risk_factors": sec.get("risk_factors", []),
                "sec_red_flags": sec.get("red_flags", []),
                "sec_opportunities": sec.get("opportunities", []),
                "sec_insider_trades": sec.get("insider_trading", []),
                "sec_management_outlook": sec.get("management_outlook", ""),
                "source": "llm",
                "error": None,
            }
        except (json.JSONDecodeError, ValueError):
            return self._deterministic_aggregate(
                news, financial, market, sec, memory,
            )

    def _deterministic_aggregate(
        self, news: dict, financial: dict,
        market: dict, sec: dict, memory: dict,
        qdrant_context: str = "",
    ) -> dict:
        news_text = news.get("news_summary", "")
        fin_text = financial.get("financial_summary", "")
        mkt_text = market.get("market_summary", "")
        sec_text = sec.get("sec_summary", "")
        mem_text = memory.get("memory_summary", "")

        strengths: list[str] = []
        risks: list[str] = []

        fin_metrics = financial.get("key_metrics", {})

        if fin_metrics.get("pe_ratio") and fin_metrics["pe_ratio"] < 25:
            strengths.append("Reasonable valuation (P/E ratio)")
        if fin_metrics.get("debt_to_equity") and fin_metrics["debt_to_equity"] < 1.5:
            strengths.append("Healthy debt-to-equity ratio")
        if fin_metrics.get("revenue") and fin_metrics["revenue"] > 0:
            strengths.append("Positive revenue reported")

        fin_risks = financial.get("risks", [])
        risks.extend(fin_risks)

        sec_risks = sec.get("risk_factors", [])
        risks.extend(sec_risks)

        sec_red_flags = sec.get("red_flags", [])
        sec_opportunities = sec.get("opportunities", [])
        sec_insider_trades = sec.get("insider_trading", [])
        sec_management_outlook = sec.get("management_outlook", "")
        sec_key_metrics = sec.get("key_metrics", {})

        red_flags = list(sec_red_flags)
        opportunities = list(sec_opportunities)

        confidence = 0.5

        # Confidence boost from positive management outlook
        if sec_management_outlook:
            positive_words = ["growth", "increase", "strong",
                              "positive", "improvement", "record"]
            if any(w in sec_management_outlook.lower() for w in positive_words):
                confidence = min(confidence + 0.05, 1.0)

        # Insider selling penalty
        sell_count = sum(
            1 for t in sec_insider_trades
            if "sell" in str(t.get("document", "")).lower()
        )
        if sell_count >= 3:
            red_flags.append(f"Multiple insider sales detected ({sell_count})")
            confidence = max(confidence - 0.1, 0)

        sentiment = news.get("sentiment", "neutral")
        recommendation = "HOLD"

        if sentiment == "positive" and len(strengths) >= 2:
            recommendation = "BUY"
            confidence = 0.65
        elif sentiment == "negative" or len(risks) >= 2:
            recommendation = "SELL"
            confidence = 0.55

        summary_parts = [
            f"News: {news_text[:100]}" if news_text else "",
            f"Financial: {fin_text[:100]}" if fin_text else "",
            f"Market: {mkt_text[:100]}" if mkt_text else "",
            f"SEC: {sec_text[:100]}" if sec_text else "",
            f"Qdrant: {qdrant_context[:100]}" if qdrant_context and "No relevant" not in qdrant_context else "",
        ]
        executive_summary = ". ".join(p for p in summary_parts if p)
        if not executive_summary:
            executive_summary = "Analysis completed with available data."

        return {
            "executive_summary": executive_summary,
            "investment_thesis": f"Analysis based on {len(strengths)} strengths and {len(risks)} risk factors.",
            "recommendation": recommendation,
            "confidence_score": confidence,
            "strengths": strengths,
            "risks": risks,
            "red_flags": red_flags,
            "opportunities": opportunities,
            "memory_summary": mem_text,
            "news_summary": news_text,
            "financial_summary": fin_text,
            "market_summary": mkt_text,
            "sec_summary": sec_text,
            "source": "deterministic",
            "error": None,
        }


# from core.config import settings
# from providers.llm.gateway import LLMGateway
# from schemas.llm import LLMRequest

# class AggregationAgent:
#     def __init__(self):
#         has_gemini = bool(settings.gemini_api_key)
#         has_groq = bool(settings.groq_api_key)
#         self._llm_available = has_groq or has_gemini
#         if self._llm_available:
#             provider = "groq" if has_groq else "gemini"
#             self._llm = LLMGateway(provider=provider)


#     """
#     we declared some functions below the run function that are 
#     _llm_aggregate() and _dterministic_aggregate() andd we use this fuction 
#     in the run() function to perform the operations
#     """

#     async def run(self , agent_outputs : dict)->dict:
#         news = agent_outputs.get("news", {})
#         financial = agent_outputs.get("financial", {})
#         market = agent_outputs.get("market", {})
#         sec = agent_outputs.get("sec", {})
#         memory = agent_outputs.get("memory", {})

#         if self._llm_available:
#             return await self._llm_aggregate(
#                 news , financial , market , sec , memory
#             )
        
#         return self._deterministic_aggregate(           
#              news, financial, market, sec, memory
#         )
    
#     async def _llm_aggregate(
#             self , news:dict , financial:dict ,
#             market: dict , sec:dict , memory: dict,
#                              )->dict:
#         # prompt = (
#         #     f"Analyze this stock research data and provide a recommendation.\n\n"
#         #     f"News: {news.get('news_summary', 'N/A')}\n"
#         #     f"Financial: {financial.get('financial_summary', 'N/A')}\n"
#         #     f"Market: {market.get('market_summary', 'N/A')}\n"
#         #     f"SEC: {sec.get('sec_summary', 'N/A')}\n"
#         #     f"Memory: {memory.get('memory_summary', 'N/A')}\n\n"
#         #     "Provide: recommendation (BUY/SELL/HOLD), confidence_score (0-1), "
#         #     "executive_summary, strengths, risks, opportunities, red_flags. "
#         #     "Respond in JSON format."
#         # )

#         # req = LLMRequest(promt = prompt , max_tokens=1024 , temperature=0.3)

#         prompt = (
#             "Financial analyst task. Synthesize the 5 sources below into one detailed "
#             "recommendation. Weigh all sources together. Treat News/Market as sentiment "
#             "signals, Financial/SEC as factual. Flag contradictions. If a source is N/A, "
#             "note it as a gap and lower confidence_score.\n\n"
#             f"News: {news.get('news_summary', 'N/A')}\n"
#             f"Financial: {financial.get('financial_summary', 'N/A')}\n"
#             f"Market: {market.get('market_summary', 'N/A')}\n"
#             f"SEC: {sec.get('sec_summary', 'N/A')}\n"
#             f"Memory: {memory.get('memory_summary', 'N/A')}\n\n"
#             "For strengths/risks/opportunities/red_flags, give 3-5 specific, substantive "
#             "points each (not generic filler) — cite which source(s) support each point. "
#             "executive_summary should be a thorough paragraph (5-8 sentences), not a "
#             "one-liner.\n\n"
#             "Return ONLY this JSON (no markdown, no preamble), empty arrays if nothing notable:\n"
#             '{"recommendation":"BUY|SELL|HOLD","confidence_score":0.0-1.0,'
#             '"executive_summary":"detailed paragraph","strengths":[],"risks":[],'
#             '"opportunities":[],"red_flags":[],"data_gaps":[]}'
#         )

#         req = LLMRequest(prompt=prompt, max_tokens=2048, temperature=0.3)
#         resp = await self._llm.complete(req)
#         return self._parse_llm_response(
#             resp.text,
#             news,
#             financial,
#             market,
#             sec,
#             memory,
#         )

#         # return self._parse_llm.complete(req)
    
#     def _parse_llm_response(
#         self, text: str, news: dict, financial: dict,
#         market: dict, sec: dict, memory: dict,
#     ) -> dict:
#         import json
#         try:
#             data = json.loads(text)
#             return {
#                 "executive_summary": data.get("executive_summary", ""),
#                 "investment_thesis": data.get("investment_thesis", ""),
#                 "recommendation": data.get("recommendation", "HOLD"),
#                 "confidence_score": float(data.get("confidence_score", 0.5)),
#                 "strengths": data.get("strengths", []),
#                 "risks": data.get("risks", []),
#                 "opportunities": data.get("opportunities", []),
#                 "red_flags": data.get("red_flags", []),
#                 "memory_summary": memory.get("memory_summary", ""),
#                 "news_summary": news.get("news_summary", ""),
#                 "financial_summary": financial.get("financial_summary", ""),
#                 "market_summary": market.get("market_summary", ""),
#                                 "sec_summary": sec.get("sec_summary", ""),
#                 "sec_risk_factors": sec.get("risk_factors", []),
#                 "sec_red_flags": sec.get("red_flags", []),
#                 "sec_opportunities": sec.get("opportunities", []),
#                 "sec_insider_trades": sec.get("insider_trading", []),
#                 "sec_management_outlook": sec.get("management_outlook", ""),
#                 "source": "llm",
#                 "error": None,
#             }
#         except (json.JSONDecodeError, ValueError):
#             return self._deterministic_aggregate(news, financial, market, sec, memory)


#     def _deterministic_aggregate(
#         self, news: dict, financial: dict,
#         market: dict, sec: dict, memory: dict,
#     ) -> dict:
#         news_text = news.get("news_summary", "")
#         fin_text = financial.get("financial_summary", "")
#         mkt_text = market.get("market_summary", "")
#         sec_text = sec.get("sec_summary", "")
#         mem_text = memory.get("memory_summary", "")

#         strengths: list[str] = []
#         risks: list[str] = []

#         fin_metrics = financial.get("key_metrics", {})

#         if fin_metrics.get("pe_ratio") and fin_metrics["pe_ratio"] < 25:
#             strengths.append("Reasonable valuation (P/E ratio)")
#         if fin_metrics.get("debt_to_equity") and fin_metrics["debt_to_equity"] < 1.5:
#             strengths.append("Healthy debt-to-equity ratio")
#         if fin_metrics.get("revenue") and fin_metrics["revenue"] > 0:
#             strengths.append("Positive revenue reported")

#         fin_risks = financial.get("risks", [])
#         risks.extend(fin_risks)

#         sec_risks = sec.get("risk_factors", [])
#         risks.extend(sec_risks)
#                 # === New SEC insight integration ===
#         sec_red_flags = sec.get("red_flags", [])
#         sec_opportunities = sec.get("opportunities", [])
#         sec_insider_trades = sec.get("insider_trading", [])
#         sec_management_outlook = sec.get("management_outlook", "")
#         sec_key_metrics = sec.get("key_metrics", {})

#         red_flags = list(sec_red_flags)
#         opportunities = list(sec_opportunities)

#         # Confidence boost from positive management outlook
#         if sec_management_outlook:
#             positive_words = ["growth", "increase", "strong",
#                               "positive", "improvement", "record"]
#             if any(w in sec_management_outlook.lower() for w in positive_words):
#                 confidence = min(confidence + 0.05, 1.0)

#         # Insider selling penalty
#         sell_count = sum(
#             1 for t in sec_insider_trades
#             if "sell" in str(t.get("document", "")).lower()
#         )
#         if sell_count >= 3:
#             red_flags.append(f"Multiple insider sales detected ({sell_count})")
#             confidence = max(confidence - 0.1, 0)
       
#         sentiment = news.get("sentiment", "neutral")
#         recommendation = "HOLD"
#         confidence = 0.5

#         if sentiment == "positive" and len(strengths) >= 2:
#             recommendation = "BUY"
#             confidence = 0.65
#         elif sentiment == "negative" or len(risks) >= 2:
#             recommendation = "SELL"
#             confidence = 0.55

#         summary_parts = [
#             f"News: {news_text[:100]}" if news_text else "",
#             f"Financial: {fin_text[:100]}" if fin_text else "",
#             f"Market: {mkt_text[:100]}" if mkt_text else "",
#             f"SEC: {sec_text[:100]}" if sec_text else "",
#         ]
#         executive_summary = ". ".join(p for p in summary_parts if p)
#         if not executive_summary:
#             executive_summary = "Analysis completed with available data."

#         return {
#             "executive_summary": executive_summary,
#             "investment_thesis": f"Analysis based on {len(strengths)} strengths and {len(risks)} risk factors.",
#             "recommendation": recommendation,
#             "confidence_score": confidence,
#             "strengths": strengths,
#             "risks": risks,
#             "red_flags": red_flags,
#             "opportunities": opportunities,
#             "memory_summary": mem_text,
#             "news_summary": news_text,
#             "financial_summary": fin_text,
#             "market_summary": mkt_text,
#             "sec_summary": sec_text,
#             "source": "deterministic",
#             "error": None,
#         }
