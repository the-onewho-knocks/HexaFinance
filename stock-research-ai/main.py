from fastapi import FastAPI

from api.v1.health import router as health_router
from core.config import settings
from core.logging import configure_logging

configure_logging(settings.debug)

app = FastAPI(
    title="Stock Research AI",
    version="0.1.0",
    debug=settings.debug,
)

app.include_router(health_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "stock-research-ai", "status": "ok"}