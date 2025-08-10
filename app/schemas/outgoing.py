from pydantic import BaseModel
from datetime import datetime
from typing import List

class OutgoingCreate(BaseModel):
    product_name: str
    price: float

class OutgoingResponse(BaseModel):
    id: int
    product_name: str
    price: float
    created_at: datetime

    class Config:
        orm_mode = True

class PaginatedOutgoingsResponse(BaseModel):
    outgoings: List[OutgoingResponse]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
