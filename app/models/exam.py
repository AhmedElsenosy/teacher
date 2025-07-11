from beanie import Document
from datetime import date

class ExamModel(Document):
    exam_name: str
    exam_level: int
    exam_date: date
    exam_start_time: str  
    solution_photo: str | None = None
    final_degree: int

    class Settings:
        name = "exams"
