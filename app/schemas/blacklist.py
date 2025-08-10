from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BlacklistStudentRequest(BaseModel):
    student_object_id: str  # The ObjectId from students collection
    blacklist_reason: Optional[str] = None

class BlacklistStudentResponse(BaseModel):
    id: str
    student_id: int
    first_name: str
    last_name: str
    email: Optional[str]
    phone_number: str
    blacklisted_at: datetime
    blacklist_reason: Optional[str]
    original_student_object_id: str

class RestoreStudentRequest(BaseModel):
    blacklist_id: str  # The ObjectId from blacklist collection

class PaginatedBlacklistStudentsResponse(BaseModel):
    blacklist_students: List[BlacklistStudentResponse]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
