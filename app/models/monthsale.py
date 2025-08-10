from beanie import Document
from bson import ObjectId
from pydantic import Field
from datetime import datetime,date

class MonthlySale(Document):
    id: int
    student_id: ObjectId
    price: float
    default_price: float
    month: date
    created_at: datetime

    class Settings:
        name = "monthsales"

    class Config:
        arbitrary_types_allowed = True
