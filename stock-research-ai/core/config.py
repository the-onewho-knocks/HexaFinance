
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # LLMs
    gemini_api_key: str = Field("", env="GEMINI_API_KEY")
    groq_api_key: str = Field("", env="GROQ_API_KEY")

    # Finance providers
    finnhub_api_key: str = Field("", env="FINNHUB_API_KEY")
    fmp_api_key: str = Field("", env="FMP_API_KEY")
    polygon_api_key: str = Field("", env="POLYGON_API_KEY")
    sec_api_key: str = Field("", env="SEC_API_KEY")

    # Memory
    xtrace_api_key: str = Field("", env="XTRACE_API_KEY")
    xtrace_org_id: str = Field("", env="XTRACE_BASE_URL")

    # Vector DB
    qdrant_url: str = Field("http://localhost:6333", env="QDRANT_URL")
    qdrant_api_key: str = Field("", env="QDRANT_API_KEY")

    # PostgreSQL
    database_url: str = Field("", env="DATABASE_URL")
    #redis
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")


    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()