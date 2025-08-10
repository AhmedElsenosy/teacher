from beanie import Document
from datetime import date, datetime
from bson import ObjectId
from pydantic import Field
from typing import Optional, List
from pydantic import Field, BaseModel




class ExamEntry(BaseModel):
    exam_id: str
    degree: Optional[float] = None
    percentage: Optional[float] = None
    delivery_time: datetime
    solution_photo: Optional[str] = None


class StudentDocument(Document):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    student_id: int
    first_name: str
    last_name: str
    email: str
    phone_number: str
    guardian_number: str
    birth_date: date
    national_id: str
    gender: str
    level: int
    school_name: str
    is_subscription: Optional[bool] = Field(default=False)
    created_at: datetime
    exams: List[ExamEntry] = Field(default_factory=list)

    class Settings:
        name = "students"

    model_config = {
        "arbitrary_types_allowed": True
    }