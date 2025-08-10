from pydantic import BaseModel, Field
from datetime import time
from typing import Optional, List
from enum import Enum
from beanie import PydanticObjectId
from app.models.group import PyObjectId

class DayOfWeek(str, Enum):
    saturday = "Saturday"
    sunday = "Sunday"
    monday = "Monday"
    tuesday = "Tuesday"
    wednesday = "Wednesday"
    thursday = "Thursday"
    friday = "Friday"


class GroupCreate(BaseModel):
    group_name: str
    start_time: str
    level: int = Field(..., ge=1, le=3)
    days: List[DayOfWeek]


class GroupUpdate(BaseModel):
    group_name: Optional[str] = None
    start_time: Optional[str] = None
    level: Optional[int] = None
    days: Optional[List[DayOfWeek]] = None


class GroupOut(BaseModel):
    id: str
    group_name: str
    start_time: time
    level: int
    days: List[DayOfWeek]

class AddStudentToGroup(BaseModel):
    student_id: PyObjectId


class StudentInGroupOut(BaseModel):
    student_name: str
    level: int
    phone_number: str
    guardian_number: str
    is_subscription: bool
    group_name: str

class GroupWithStudentsOut(BaseModel):
    group_id: str
    group_name: str
    level: int
    students: List[StudentInGroupOut]