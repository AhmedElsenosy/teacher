from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

class MonthlySaleCreate(BaseModel):
    student_id: str
    price: float
    default_price: float
    month: date

class MonthlySaleResponse(BaseModel):
    id: int
    student_id: str
    price: float
    default_price: float
    month: str
    created_at: datetime

class MonthQuery(BaseModel):
    month: str

class MonthSaleDetailResponse(BaseModel):
    student_name: str
    price: float
    created_at: datetime
    month: str

class PaginatedMonthSalesResponse(BaseModel):
    month_sales: List[MonthSaleDetailResponse]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
