from beanie import Document
from datetime import datetime
from pydantic import Field

class Outgoing(Document):
    id: int
    product_name: str
    price: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "outgoings"
