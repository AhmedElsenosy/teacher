from fastapi import APIRouter, HTTPException, status, Depends
from app.database import db
from app.schemas.student import StudentCreate, StudentOut, StudentUpdate
from app.models.student import StudentModel
from app.dependencies.auth import get_current_assistant
from bson import ObjectId
from datetime import datetime, date
from typing import List

# ✅ Apply authentication to all routes in this router
router = APIRouter(
    prefix="/students",
    tags=["Students"],
    dependencies=[Depends(get_current_assistant)]
)

students_collection = db["students"]
counters_collection = db["counters"]

# Utility to generate the next student_id
async def get_next_student_id():
    counter = await counters_collection.find_one_and_update(
        {"_id": "student_id"},
        {"$inc": {"value": 1}},
        return_document=True
    )
    if not counter:
        raise HTTPException(status_code=500, detail="Counter document not found.")
    return counter["value"]


@router.post("/", response_model=StudentOut)
async def create_student(student: StudentCreate):
    student_id = await get_next_student_id()
    student_data = student.dict()

    # Convert birth_date (date) → datetime
    birth_date = student_data["birth_date"]
    if isinstance(birth_date, date):
        student_data["birth_date"] = datetime.combine(birth_date, datetime.min.time())

    # Convert Enums to raw values
    if hasattr(student_data["gender"], "value"):
        student_data["gender"] = student_data["gender"].value
    if hasattr(student_data["level"], "value"):
        student_data["level"] = student_data["level"].value

    student_data.update({
        "student_id": student_id,
        "created_at": datetime.utcnow()
    })

    result = await students_collection.insert_one(student_data)
    student_data["id"] = str(result.inserted_id)
    return StudentOut(**student_data)


@router.get("/", response_model=List[StudentOut])
async def get_all_students():
    students = await students_collection.find().to_list(length=None)
    for student in students:
        student["id"] = str(student["_id"])
        del student["_id"]
    return [StudentOut(**student) for student in students]


@router.get("/{student_id}", response_model=StudentOut)
async def get_student_by_id(student_id: int):
    student = await students_collection.find_one({"student_id": student_id})
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    student["id"] = str(student["_id"])
    del student["_id"]
    return StudentOut(**student)


@router.put("/{student_id}", response_model=dict)
async def update_student(student_id: int, student_update: StudentUpdate):
    update_data = {k: v for k, v in student_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided for update")

    result = await students_collection.update_one({"student_id": student_id}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Student not found or nothing changed")

    return {"message": "Student updated successfully"}


@router.delete("/{student_id}")
async def delete_student(student_id: int):
    result = await students_collection.delete_one({"student_id": student_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student deleted successfully"}
