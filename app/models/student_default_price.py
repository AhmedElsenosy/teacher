from beanie import Document
from pydantic import Field
from decimal import Decimal


class StudentDefaultPrice(Document):
    student_id: int
    default_price: Decimal = Field(default=200)

    class Settings:
        name = "student_default_prices"