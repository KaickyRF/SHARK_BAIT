from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class DealResponse(BaseModel):
    dealID: str
    updated_at: datetime
    title: str
    shop: str
    price_now: float
    normal_price: float
    metacritic: Optional[float] = None
    steam_rate: Optional[str] = None
    steam_rate_percent: Optional[float] = None
    critic_steam: float
    sort_rate_price: float
    thumb: Optional[str] = None

    class Config:
        from_atributes: True