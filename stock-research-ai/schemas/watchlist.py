from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class WatchListAdd(BaseModel):
    user_id: str
    symbol: str
    notes: Optional[str] = None


class WatchListOut(BaseModel):
    id: str
    user_id: str
    symbol: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True