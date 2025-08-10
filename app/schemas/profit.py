from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from typing import Optional

class DailyProfitResponse(BaseModel):
    date: date
    total_monthsales: Decimal
    total_booksales: Decimal
    total_outgoings: Decimal
    profit: Decimal



class ProfitFilterRequest(BaseModel):
    day_date: Optional[date] = None
