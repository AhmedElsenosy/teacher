from pydantic import BaseModel, Field
from enum import Enum
from datetime import date

class CourseLevelEnum(int, Enum):
    level1 = 1
    level2 = 2
    level3 = 3

class CourseCreate(BaseModel):
    course_name: str
    course_level: CourseLevelEnum
    course_start_date: date
    course_end_date: date

class CourseOut(CourseCreate):
    id: str
    photo_path: str

class CourseUpdate(BaseModel):
    course_name: str | None = None
    course_level: CourseLevelEnum | None = None
    course_start_date: date | None = None
    course_end_date: date | None = None
