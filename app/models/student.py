from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import date, datetime
from typing import Optional, List, Dict
from beanie import Document
from app.schemas.student import ExamEntry

class StudentModel(Document):  
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
    is_subscription: bool
    created_at: date
    exams: List[ExamEntry] = []
    fingerprint_template: Optional[str] = None
    uid: int
    attendance: Dict[str, bool] = Field(default_factory=dict)
    created_at: datetime

    class Settings:
        name = "students"  

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}