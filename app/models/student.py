from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import date

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

class StudentModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    student_id: int
    first_name: str
    last_name: str
    email: str
    phone_number: str
    guardian_number: str
    birth_date: date
    national_id: str
    gender: str
    level: int
    school_name: str
    is_subscription: bool
    created_at: date

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}