from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional, List
from enum import Enum
from app.models.common import PyObjectId, ExamEntry



# Choices for gender and level
class Gender(str, Enum):
    male = "male"
    female = "female"

class Level(int, Enum):
    level1 = 1
    level2 = 2
    level3 = 3

class StudentBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone_number: str
    guardian_number: str
    birth_date: Optional[date] = None
    national_id: Optional[str] = None
    gender: Gender
    level: Level
    school_name: Optional[str] = None

class StudentCreate(StudentBase):
    uid: Optional[int] = None
    student_id: Optional[int] = None
    is_subscription: bool


class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    guardian_number: Optional[str] = None
    birth_date: Optional[date] = None
    national_id: Optional[str] = None
    gender: Optional[str] = None
    level: Optional[int] = None
    school_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_subscription: Optional[bool] = None

class StudentOut(StudentBase):
    id: str
    student_id: int
    is_subscription: bool
    uid: int
    group: Optional[str] = None


class ExamEntryCreate(BaseModel):
    student_degree: int
    degree_percentage: float
    delivery_time: datetime
    solution_photo: Optional[str] = None

class PaginatedStudentsResponse(BaseModel):
    students: List[StudentOut]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool

