from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional, List
from app.schemas.student import StudentBase

class ArchivedStudentOut(StudentBase):
    id: str
    student_id: int
    is_subscription: bool
    uid: int
    archived_at: datetime
    archive_reason: Optional[str] = None
    months_without_payment: int = 0
    group: Optional[str] = None

class ArchiveRequest(BaseModel):
    archive_reason: Optional[str] = "Manually archived"

class PaginatedArchivedStudentsResponse(BaseModel):
    archived_students: List[dict]  # Using dict because we work with raw MongoDB documents
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
