from pydantic import BaseModel, Field
from enum import IntEnum
from datetime import date

class LevelChoices(IntEnum):
    level1 = 1
    level2 = 2
    level3 = 3

class ExamBase(BaseModel):
    exam_name: str
    exam_level: LevelChoices
    exam_date: date
    exam_start_time: str  
    final_degree: int
    solution_photo: str | None = None

class ExamCreate(ExamBase):
    pass

class ExamUpdate(BaseModel):
    exam_name: str | None = None
    exam_level: LevelChoices | None = None
    exam_date: date | None = None
    exam_start_time: str | None = None  
    final_degree: int | None = None
    solution_photo: str | None = None

class ExamOut(ExamBase):
    id: str
    student_count: int = 0
