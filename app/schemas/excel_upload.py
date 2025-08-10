from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class StudentCreationResult(BaseModel):
    row_number: int
    success: bool
    student_id: Optional[int] = None
    student_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ExcelUploadResponse(BaseModel):
    total_rows: int
    successful_creations: int
    failed_creations: int
    results: List[StudentCreationResult]
    summary: str

class ExcelValidationError(BaseModel):
    row_number: int
    column: str
    error: str
    value: Any