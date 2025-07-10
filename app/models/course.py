from datetime import date
from pydantic import BaseModel
from enum import Enum

class CourseLevelEnum(int, Enum):
    level1 = 1
    level2 = 2
    level3 = 3

class CourseModel(BaseModel):
    course_name: str
    course_level: CourseLevelEnum
    course_start_date: date
    course_end_date: date
    photo_path: str
