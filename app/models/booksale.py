from beanie import Document
from bson import ObjectId, Decimal128
from decimal import Decimal
from datetime import datetime
from pydantic import Field, field_validator


class BookSale(Document):
    id: int = Field(alias="_id")
    student_id: ObjectId
    name: str
    price: Decimal
    default_price: Decimal
    created_at: datetime

    class Settings:
        name = "booksales"

    model_config = {
        "arbitrary_types_allowed": True
    }

    @field_validator("price", "default_price", mode="before")
    @classmethod
    def convert_decimal128(cls, value):
        if isinstance(value, Decimal128):
            return value.to_decimal()
        return value
