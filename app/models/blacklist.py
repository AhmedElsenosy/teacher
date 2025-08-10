from beanie import Document
from pydantic import Field, ConfigDict
from datetime import datetime, date
from typing import Optional, Dict, List, Any
from bson import ObjectId

class BlacklistStudent(Document):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Original student data
    student_id: int = Field(...)
    first_name: str = Field(...)
    last_name: str = Field(...)
    email: Optional[str] = Field(default=None)
    phone_number: str = Field(...)
    guardian_number: str = Field(...)
    birth_date: Optional[date] = Field(default=None)
    national_id: Optional[str] = Field(default=None)
    gender: str = Field(...)
    level: int = Field(...)
    school_name: Optional[str] = Field(default=None)
    is_subscription: bool = Field(...)
    exams: List[Dict[str, Any]] = Field(default_factory=list)
    uid: int = Field(...)
    attendance: Dict[str, Any] = Field(default_factory=dict)
    subscription: Dict[str, Any] = Field(default_factory=dict)
    months_without_payment: int = Field(default=0)
    archived: bool = Field(default=False)
    
    # Blacklist specific fields
    blacklisted_at: datetime = Field(default_factory=datetime.utcnow)
    blacklist_reason: Optional[str] = Field(default=None)
    original_student_object_id: ObjectId = Field(...)  # Store the original ObjectId from students collection
    
    # Original creation date
    created_at: datetime = Field(...)
    
    class Settings:
        name = "blacklist"
