from beanie import Document
from datetime import date
from typing import List, Optional
from pydantic import BaseModel

class ExamModelVariant(BaseModel):
    model_number: int  # 1, 2, or 3
    model_name: str   # "Model A", "Model B", "Model C"
    solution_photo: Optional[str] = None  # Path to this model's answer key

class ExamModel(Document):
    exam_name: str
    exam_level: int
    exam_date: date
    exam_start_time: str  
    solution_photo: str | None = None  # Legacy field for backward compatibility
    final_degree: int
    models: List[ExamModelVariant] = []  # New field for 3 exam models

    class Settings:
        name = "exams"
