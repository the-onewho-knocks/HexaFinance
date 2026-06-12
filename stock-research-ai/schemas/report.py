from pydantic import BaseModel,Field
from datetime import datetime
from typing import Optional

class ReportCreate(BaseModel):
    user_id:str
    symbol:str = Field(min_length=1, max_length=10)
    content:str
    recommendation:str
    confidence_score:float = Field(ge=0, le=1)

class ReportOut(BaseModel):
    id:str
    user_id:str
    symbol:str
    content:str
    recommendation:str
    confidence_score:float
    created_at:datetime

    class Config:
        from_attributes=True