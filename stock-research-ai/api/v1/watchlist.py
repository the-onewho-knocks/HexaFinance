from fastapi import APIRouter, Depends

from api.dependencies import get_watchlist_service
from schemas.watchlist import WatchListAdd, WatchListOut
from services.watchlist_service import WatchlistService

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.post("", response_model=WatchListOut)
async def add_to_watchlist(
    item: WatchListAdd,
    service: WatchlistService = Depends(get_watchlist_service),
) -> WatchListOut:
    return await service.add_symbol(item)


@router.get("/{user_id}", response_model=list[WatchListOut])
async def list_watchlist(
    user_id: str,
    service: WatchlistService = Depends(get_watchlist_service),
) -> list[WatchListOut]:
    return await service.list_symbols(user_id)