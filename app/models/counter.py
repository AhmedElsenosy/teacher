from beanie import Document
from pydantic import Field

class Counter(Document):
    name: str = Field(...)
    sequence_value: int = Field(...)

    class Settings:
        name = "counters"
