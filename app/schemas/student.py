from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional
from enum import Enum


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
    email: EmailStr
    phone_number: str
    guardian_number: str
    birth_date: date
    national_id: str
    gender: Gender
    level: Level
    school_name: str

class StudentCreate(StudentBase):
    pass


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
