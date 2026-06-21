# import asyncio
# import httpx

# HEADERS = {
#     "User-Agent": "StockResearchAI/1.0 (test@example.com)",
#     "Accept-Encoding": "gzip, deflate",
# }

# BASE = "https://efts.sec.gov/LATEST/search-index"


# async def main():
#     async with httpx.AsyncClient(timeout=20, headers=HEADERS) as c:
#         # Test 1: ticker as full-text query (what your current code does)
#         r1 = await c.get(BASE, params={"q": "AAPL", "forms": "10-K", "size": 5})
#         print("=== q=AAPL (ticker as full text search) ===")
#         print("status:", r1.status_code)
#         print("total hits:", r1.json().get("hits", {}).get("total"))
#         print()

#         # Test 2: company name as full-text query
#         r2 = await c.get(BASE, params={"q": "Apple Inc", "forms": "10-K", "size": 5})
#         print("=== q='Apple Inc' (company name as full text search) ===")
#         print("status:", r2.status_code)
#         print("total hits:", r2.json().get("hits", {}).get("total"))
#         print()

#         # Test 3: correct way - look up CIK first, then filter by it
#         tickers_url = "https://www.sec.gov/files/company_tickers.json"
#         r3 = await c.get(tickers_url)
#         print("=== company_tickers.json lookup ===")
#         print("status:", r3.status_code)
#         if r3.status_code == 200:
#             data = r3.json()
#             match = next((d for d in data.values() if d["ticker"] == "AAPL"), None)
#             print("AAPL entry:", match)


# if __name__ == "__main__":
#     asyncio.run(main())

# import asyncio
# import json
# import httpx

# HEADERS = {
#     "User-Agent": "StockResearchAI/1.0 (test@example.com)",
#     "Accept-Encoding": "gzip, deflate",
# }
# BASE = "https://efts.sec.gov/LATEST/search-index"


# async def main():
#     async with httpx.AsyncClient(timeout=20, headers=HEADERS) as c:
#         r = await c.get(BASE, params={"ciks": "0000320193", "forms": "10-K", "size": 3})
#         data = r.json()
#         hits = data.get("hits", {}).get("hits", [])
#         print(f"got {len(hits)} hits\n")
#         if hits:
#             print(json.dumps(hits[0], indent=2))


# if __name__ == "__main__":
#     asyncio.run(main())

import asyncio
from providers.finance.sec_client import SECClient


async def main():
    client = SECClient()

    cik = await client.resolve_cik("AAPL")
    print(f"resolved CIK: {cik}\n")

    filings = await client.search_filings(cik=cik, form_type="10-K", hits=3)

    for f in filings:
        url = client.build_filing_url(f)
        title = client.build_title(f)
        print("title:", title)
        print("url:  ", url)
        print()


if __name__ == "__main__":
    asyncio.run(main())