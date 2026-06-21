import re
from collections import defaultdict

from loguru import logger

from providers.finance.sec_client import SECClient


class SECTool:
    def __init__(self) -> None:
        self._client = SECClient()

    async def get_filings(
        self,
        symbol: str,
        form_type: str = "10-K",
        hits: int = 3,
    ) -> dict:
        try:
            filings = await self._client.search_filings(
                query=symbol,
                form_type=form_type,
                hits=hits,
            )
            return {
                "filings": filings,
                "total": len(filings),
                "source": "sec",
                "form_type": form_type,
                "error": None,
            }
        except Exception as exc:
            logger.warning(f"SEC filings fetch failed for {symbol}: {exc}")
            return {
                "filings": [],
                "total": 0,
                "source": "sec",
                "form_type": form_type,
                "error": str(exc),
            }

    async def get_all_filings(self, symbol: str) -> dict:
        result: dict = {
            "symbol": symbol,
            "cik": None,
            "filings_by_type": defaultdict(list),
            "latest_10k_html": "",
            "insider_trades": [],
            "error": None,
        }

        cik = await self._client.cik_from_ticker(symbol)
        if not cik:
            logger.warning(f"CIK lookup failed for {symbol}, falling back to search")
            return self._fallback(symbol, "CIK lookup failed")

        result["cik"] = cik

        try:
            submissions = await self._client.get_submissions(cik)
        except Exception as exc:
            logger.warning(f"Submissions fetch failed for {symbol}: {exc}")
            return self._fallback(symbol, str(exc))

        recent = submissions.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accession = recent.get("accessionNumber", [])
        primary_doc = recent.get("primaryDocument", [])
        filing_date = recent.get("filingDate", [])

        for i in range(len(forms)):
            ftype = forms[i]
            if ftype in ("10-K", "10-Q", "8-K", "4"):
                result["filings_by_type"][ftype].append({
                    "form": ftype,
                    "accession_number": accession[i] if i < len(accession) else "",
                    "primary_document": primary_doc[i] if i < len(primary_doc) else "",
                    "filing_date": filing_date[i] if i < len(filing_date) else "",
                })

        # Fetch latest 10-K HTML
        latest_10k = None
        for f in result["filings_by_type"].get("10-K", []):
            latest_10k = f
            break

        if latest_10k:
            try:
                acc = latest_10k["accession_number"].replace("-", "")
                doc = latest_10k["primary_document"]
                html = await self._client.get_filing_html(cik, acc, doc)
                result["latest_10k_html"] = html
            except Exception as exc:
                logger.warning(f"10-K HTML fetch failed for {symbol}: {exc}")

        # Parse insider trades from Form 4
        result["insider_trades"] = self._parse_insider_trades(
            result["filings_by_type"].get("4", [])
        )

        return result

    def extract_risk_factors(self, html: str) -> list[str]:
        if not html:
            return []
        risks = []
        patterns = [
            r"Item\s*1A\.?\s*[Rr]isk\s*[Ff]actors?\s*(.*?)(?=Item\s*1B\b|Item\s*2\b)",
            r"Item\s*1A\.?\s*[Rr]isk\s*[Ff]actors?\s*(.*?)(?=Item\s*1B\b|Item\s*2\b|<\/div>)",
        ]
        for pat in patterns:
            m = re.search(pat, html, re.DOTALL | re.IGNORECASE)
            if m:
                text = self._clean_html(m.group(1))
                risks = self._split_bullets(text)[:10]
                break

        # Fallback: keyword-based extraction
        if not risks:
            risk_keywords = ["risk", "uncertainty", "adversely", "could materially"]
            sentences = re.split(r"[.!?]\s+", self._clean_html(html))
            for s in sentences[:50]:
                if any(kw in s.lower() for kw in risk_keywords):
                    risks.append(s.strip()[:200])

        return risks[:10]

    def extract_mda(self, html: str) -> str:
        if not html:
            return ""
        pat = (
            r"Item\s*7\.?\s*[Mm]anagement['']?s?\s*[Dd]iscussion\s*"
            r"(.*?)(?=Item\s*7A\b|Item\s*8\b|Item\s*9\b|<\/div>)"
        )
        m = re.search(pat, html, re.DOTALL | re.IGNORECASE)
        if m:
            return self._clean_html(m.group(1))[:3000]
        return ""

    def extract_key_metrics_from_10k(self, html: str) -> dict:
        if not html:
            return {}
        text = self._clean_html(html)
        metrics = {}
        patterns = {
            "total_revenue": r"(?:total\s+)?revenues?\s*(?:of|:)?\s*\$?([0-9,]+(?:\.[0-9]+)?)\s*(?:million|billion|M|B)",
            "net_income": r"net\s+income\s*(?:of|:)?\s*\$?([0-9,]+(?:\.[0-9]+)?)\s*(?:million|billion|M|B)",
            "r_and_d": r"(?:research\s+(?:and|&)\s+development|R&D)\s*(?:expense|costs)?\s*(?:of|:)?\s*\$?([0-9,]+(?:\.[0-9]+)?)\s*(?:million|billion|M|B)",
        }
        for key, pat in patterns.items():
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                raw = m.group(1).replace(",", "")
                try:
                    metrics[key] = float(raw)
                except ValueError:
                    pass
        return metrics

    def _parse_insider_trades(self, form4_list: list[dict]) -> list[dict]:
        trades = []
        for f in form4_list[:10]:
            doc = f.get("primary_document", "")
            # Basic metadata from submissions API
            trades.append({
                "type": "Form 4",
                "filing_date": f.get("filing_date", ""),
                "document": doc,
            })
        return trades

    def extract_material_events(self, html: str) -> list[str]:
        if not html:
            return []
        events_pat = r"Item\s*8\.?\s*01\s*(.*?)(?=Item\s*9\.?\s*01|\Z)"
        m = re.search(events_pat, html, re.DOTALL | re.IGNORECASE)
        if m:
            text = self._clean_html(m.group(1))
            return self._split_bullets(text)[:5]
        return []

    def _fallback(self, symbol: str, error: str) -> dict:
        return {
            "symbol": symbol,
            "cik": None,
            "filings_by_type": {},
            "latest_10k_html": "",
            "insider_trades": [],
            "error": error,
        }

    @staticmethod
    def _clean_html(html: str) -> str:
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"&[a-z]+;", " ", text)
        return text.strip()

    @staticmethod
    def _split_bullets(text: str) -> list[str]:
        items = re.split(r"(?:^|\n)\s*(?:•|[-*]|\d+\.)\s*", text)
        return [i.strip() for i in items if len(i.strip()) > 20]

    async def get_filing_document(self, url: str) -> dict:
        try:
            text = await self._client.get_filing_document(url)
            return {"text": text[:5000], "source": "sec", "error": None}
        except Exception as exc:
            logger.warning(f"SEC document fetch failed for {url}: {exc}")
            return {"text": "", "source": "sec", "error": str(exc)}

# from loguru import logger

# from providers.finance.sec_client import SECClient


# class SECTool:
#     def __init__(self) -> None:
#         self._client = SECClient()

#     async def get_filings(
#         self,
#         symbol: str,
#         form_type: str = "10-K",
#         hits: int = 3,
#     ) -> dict:
#         try:
#             cik = await self._client.resolve_cik(symbol)

#             if cik:
#                 filings = await self._client.search_filings(
#                     cik=cik,
#                     form_type=form_type,
#                     hits=hits,
#                 )
#             else:
#                 logger.warning(
#                     f"No CIK found for {symbol}, falling back to text search"
#                 )
#                 filings = await self._client.search_filings(
#                     query=symbol,
#                     form_type=form_type,
#                     hits=hits,
#                 )

#             # attach resolved url + title to each filing for downstream use
#             for f in filings:
#                 f["url"] = self._client.build_filing_url(f)
#                 f["title"] = self._client.build_title(f)

#             return {
#                 "filings": filings,
#                 "total": len(filings),
#                 "source": "sec",
#                 "error": None,
#             }

#         except Exception as exc:
#             logger.warning(
#                 f"SEC filings fetch failed for {symbol}: {exc}"
#             )

#             return {
#                 "filings": [],
#                 "total": 0,
#                 "source": "sec",
#                 "error": str(exc),
#             }

#     async def get_filing_document(self, url: str) -> dict:
#         try:
#             text = await self._client.get_filing_document(url)

#             return {
#                 "text": text[:5000],
#                 "source": "sec",
#                 "error": None,
#             }

#         except Exception as exc:
#             logger.warning(
#                 f"SEC document fetch failed for {url}: {exc}"
#             )

#             return {
#                 "text": "",
#                 "source": "sec",
#                 "error": str(exc),
#             }