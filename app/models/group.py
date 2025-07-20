from beanie import Document, PydanticObjectId
from pydantic import Field
from datetime import time
from enum import Enum
from typing import List, Any
from beanie import Document
from pydantic import BaseModel, Field
from bson import ObjectId
from pydantic_core import core_schema
from pydantic import GetCoreSchemaHandler



class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(cls._validate)

    @classmethod
    def _validate(cls, value, *args, **kwargs):
        if isinstance(value, ObjectId):
            return value
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")
        return ObjectId(value)

    @classmethod
    def __get_json_schema__(cls, core_schema, handler):
        return {"type": "string"}

class DayOfWeek(str, Enum):
    saturday = "Saturday"
    sunday = "Sunday"
    monday = "Monday"
    tuesday = "Tuesday"
    wednesday = "Wednesday"
    thursday = "Thursday"
    friday = "Friday"


class Group(Document):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    group_name: str
    start_time: str
    level: int = Field(..., ge=1, le=3)
    day1: DayOfWeek
    day2: DayOfWeek
    students: List[PyObjectId] = []

    class Settings:
        name = "groups"
