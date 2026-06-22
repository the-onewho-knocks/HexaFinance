# LangGraph node names
NODE_NEWS       = "news_agent"
NODE_FINANCIAL  = "financial_agent"
NODE_MARKET     = "market_agent"
NODE_SEC        = "sec_agent"
NODE_MEMORY     = "memory_agent"
NODE_AGGREGATE  = "aggregation_agent"
NODE_QDRANT     = "qdrant_agent"
COLLECTION_SEC_FILINGS = "sec_filings"
COLLECTION_REPORTS = "reports"

TTL_MARKET_DATA = 60
TTL_NEWS = 300

# Pagination
DEFAULT_PAGE_SIZE = 20

# LLM
DEFAULT_LLM_PROVIDER = "gemini"   # "gemini" | "groq"
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
DEFAULT_GROQ_MODEL   = "llama-3.3-70b-versatile"
MAX_TOKENS           = 8192