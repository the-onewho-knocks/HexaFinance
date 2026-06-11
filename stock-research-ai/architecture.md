stock-research-ai/

├── app/
│
├── api/
│   ├── v1/
│   │   ├── research.py
│   │   ├── watchlist.py
│   │   ├── reports.py
│   │   └── health.py
│   │
│   └── dependencies.py
│
├── core/
│   ├── config.py
│   ├── constants.py
│   ├── logging.py
│   └── exceptions.py
│
├── graph/
│   ├── workflow.py
│   ├── state.py
│   ├── nodes.py
│   └── edges.py
│
├── agents/
│   ├── news_agent.py
│   ├── financial_agent.py
│   ├── market_agent.py
│   ├── sec_agent.py
│   ├── memory_agent.py
│   └── aggregation_agent.py
│
├── providers/
│   ├── llm/
│   │   ├── gemini_provider.py
│   │   ├── groq_provider.py
│   │   └── gateway.py
│   │
│   ├── finance/
│   │   ├── finnhub_client.py
│   │   ├── polygon_client.py
│   │   ├── fmp_client.py
│   │   └── sec_client.py
│   │
│   └── embeddings/
│       └── embedding_provider.py
│
├── rag/
│   ├── ingestion/
│   │   ├── pdf_loader.py
│   │   ├── chunker.py
│   │   └── embedding_pipeline.py
│   │
│   ├── retrieval/
│   │   ├── retriever.py
│   │   ├── reranker.py
│   │   └── search.py
│   │
│   └── index_manager.py
│
├── memory/
│   ├── xtrace_client.py
│   ├── memory_service.py
│   └── schemas.py
│
├── services/
│   ├── research_service.py
│   ├── report_service.py
│   ├── watchlist_service.py
│   └── sec_ingestion_service.py
│
├── tools/
│   ├── news_tool.py
│   ├── financial_tool.py
│   ├── market_tool.py
│   └── sec_tool.py
│
├── vectorstore/
│   ├── qdrant_client.py
│   └── collections.py
│
├── database/
│   ├── postgres.py
│   ├── models/
│   │   ├── report.py
│   │   ├── watchlist.py
│   │   └── user.py
│   │
│   └── repositories/
│       ├── report_repository.py
│       ├── watchlist_repository.py
│       └── user_repository.py
│
├── schemas/
│   ├── research.py
│   ├── report.py
│   ├── watchlist.py
│   └── llm.py
│
├── prompts/
│   ├── investment_report.py
│   ├── recommendation.py
│   └── executive_summary.py
│
├── tests/
│   ├── agents/
│   ├── services/
│   └── api/
│
├── main.py
│
├── requirements.txt
│
├── .env
│
└── docker-compose.yml