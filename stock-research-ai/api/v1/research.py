from fastapi import APIRouter,Depends

from api.dependencies import get_research_service
from schemas.research import ResearchRequest, ResearchResponse
from services.research_service import ResearchService

router = APIRouter(prefix="/research", tags=["research"])


@router.post("", response_model=ResearchResponse)
async def run_research(
    request: ResearchRequest,
    service: ResearchService = Depends(get_research_service),
) -> ResearchResponse:
    return await service.run_research(request)