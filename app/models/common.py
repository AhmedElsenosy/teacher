# app/models/common.py
from bson import ObjectId
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

class ExamEntry(BaseModel):
    exam_id: PyObjectId
    exam_name: str
    student_degree: int
    degree_percentage: float
    delivery_time: datetime
    solution_photo: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
