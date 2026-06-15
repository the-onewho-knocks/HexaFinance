from datetime import datetime
from uuid import uuid4

from schemas.watchlist import WatchListAdd, WatchListOut


class WatchlistService:
    def __init__(self):
        self._items: dict[str, WatchListOut] = {}

    async def add_symbol(self, item: WatchListAdd) -> WatchListOut:
        watchlist_item = WatchListOut(
            id=str(uuid4()),
            user_id=item.user_id,
            symbol=item.symbol.upper(),
            notes=item.notes,
            created_at=datetime.utcnow(),
        )
        self._items[watchlist_item.id] = watchlist_item
        return watchlist_item

    async def list_symbols(self, user_id: str) -> list[WatchListOut]:
        return [
            item
            for item in self._items.values()
            if item.user_id == user_id
        ]