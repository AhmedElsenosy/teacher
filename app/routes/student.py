from fastapi import APIRouter, HTTPException, status, Depends
from app.database import db
from app.schemas.student import StudentCreate, StudentOut, StudentUpdate, StudentBase
from app.models.student import StudentModel
from app.dependencies.auth import get_current_assistant
from bson import ObjectId
from datetime import datetime, date
from typing import List
from app.utils.fingerprint import enroll_fingerprint
import subprocess
from app.utils.id_generator import get_next_sequence
from app.models.counter import Counter
from app.models.group import Group

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
    counter = await Counter.find_one(Counter.name == "student_id")
    if not counter:
        counter = Counter(name="student_id", sequence_value=10000)
        await counter.insert()
    counter.sequence_value += 1
    await counter.save()
    return counter.sequence_value

@router.get("/next-ids")
async def get_next_ids():
    next_id = await get_next_student_id()
    return {"student_id": next_id, "uid": next_id}


@router.post("/", response_model=StudentOut)
async def create_student(student: StudentCreate):
    student_data = student.dict()

    # Auto-increment IDs
    student_data["student_id"] = await get_next_sequence("student_id")
    student_data["uid"] = await get_next_sequence("uid")

    # Convert birth_date to datetime
    if isinstance(student_data["birth_date"], date):
        student_data["birth_date"] = datetime.combine(student_data["birth_date"], datetime.min.time())

    # Convert enums
    student_data["gender"] = getattr(student_data["gender"], "value", student_data["gender"])
    student_data["level"] = getattr(student_data["level"], "value", student_data["level"])

    # Extra metadata
    student_data["created_at"] = datetime.utcnow()
    student_data["updated_at"] = None
    student_data["exams"] = []

    # Insert into DB
    result = await students_collection.insert_one(student_data)
    student_data["id"] = str(result.inserted_id)

    return StudentOut(**student_data)



@router.get("/", response_model=List[StudentOut])
async def get_all_students():
    students = await students_collection.find().to_list(length=None)
    for student in students:
        student["id"] = str(student["_id"])
        del student["_id"]
        student.setdefault("is_subscription", False)
        student.setdefault("uid", 0)

        # Find group(s) for this student
        group = await Group.find(Group.students == ObjectId(student["id"])).first_or_none()
        student["group"] = group.group_name if group else None

    return [StudentOut(**student) for student in students]


@router.get("/{student_id}", response_model=StudentOut)
async def get_student_by_id(student_id: int):
    student = await students_collection.find_one({"student_id": student_id})
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    student["id"] = str(student["_id"])
    del student["_id"]
    student.setdefault("is_subscription", False)
    student.setdefault("uid", 0)

    # Find group(s) for this student
    group = await Group.find(Group.students == ObjectId(student["id"])).first_or_none()
    student["group"] = group.group_name if group else None

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



