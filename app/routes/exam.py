from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from datetime import date, datetime
from typing import List
from pathlib import Path
from bson import ObjectId
import shutil
import os

from app.dependencies.auth import get_current_assistant
from app.models.exam import ExamModel
from app.models.student import StudentModel
from app.models.common import PyObjectId  
from app.schemas.student import ExamEntryCreate
from app.schemas.exam import ExamCreate, ExamUpdate, ExamOut
from app.models.student_document import StudentDocument, ExamEntry
from app.database import db

students_collection = db["students"]
exams_collection = db["exams"]



router = APIRouter(prefix="/exams", tags=["Exams"])

UPLOAD_DIR = "upload/solutions"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=ExamOut)
async def create_exam(
    exam_name: str = Form(...),
    exam_level: int = Form(...),
    exam_date: date = Form(...),
    exam_start_time: str = Form(...),
    final_degree: int = Form(...),
    solution_photo: UploadFile = File(None),
    assistant=Depends(get_current_assistant)
):
    photo_path = None
    if solution_photo:
        photo_path = f"{UPLOAD_DIR}/{solution_photo.filename}"
        with open(photo_path, "wb") as f:
            shutil.copyfileobj(solution_photo.file, f)

    exam_data = ExamCreate(
        exam_name=exam_name,
        exam_level=exam_level,
        exam_date=exam_date,
        exam_start_time=exam_start_time,
        final_degree=final_degree,
        solution_photo=photo_path
    )

    exam = ExamModel(**exam_data.dict())
    await exam.insert()
    exam_data = exam.dict(by_alias=True)
    exam_data["id"] = str(exam_data.pop("_id"))
    return ExamOut(**exam_data)



@router.get("/", response_model=List[ExamOut])
async def get_all_exams():
    exams = await exams_collection.find().to_list(length=None)
    students = await students_collection.find().to_list(length=None)
    exam_list = []
    for exam in exams:
        exam_id = str(exam["_id"])
        # Count students who have this exam in their exams list
        count = sum(
            any(str(entry.get("exam_id", "")) == exam_id for entry in student.get("exams", []))
            for student in students
        )
        exam["id"] = exam_id
        exam["student_count"] = count
        exam_list.append(ExamOut(**exam))
    return exam_list


@router.put("/{exam_id}", response_model=ExamOut)
async def update_exam(
    exam_id: str,
    exam_name: str = Form(None),
    exam_level: int = Form(None),
    exam_date: date = Form(None),
    exam_start_time: str = Form(None),
    final_degree: int = Form(None),
    solution_photo: UploadFile = File(None),
    assistant=Depends(get_current_assistant)
):
    exam = await ExamModel.get(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    update_data = {
        "exam_name": exam_name,
        "exam_level": exam_level,
        "exam_date": exam_date,
        "exam_start_time": exam_start_time,
        "final_degree": final_degree
    }

    
    update_data = {k: v for k, v in update_data.items() if v is not None}

    
    if solution_photo:
        photo_path = f"{UPLOAD_DIR}/{solution_photo.filename}"
        with open(photo_path, "wb") as f:
            shutil.copyfileobj(solution_photo.file, f)
        update_data["solution_photo"] = photo_path

    for key, value in update_data.items():
        setattr(exam, key, value)

    await exam.save()
    return ExamOut(**exam.dict(exclude={"id", "_id"}), id=str(exam.id))


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam(exam_id: str, assistant=Depends(get_current_assistant)):
    exam = await ExamModel.get(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    await exam.delete()



STUDENT_SOLUTION_DIR = "upload/student_solutions"

@router.post("/{exam_id}/students")
async def add_student_to_exam(
    exam_id: str,
    student_id: str = Form(...),
    student_degree: int = Form(...),
    degree_percentage: float = Form(...),
    delivery_time: datetime = Form(...),
    solution_photo: UploadFile = File(None),
    assistant=Depends(get_current_assistant)
):
    student = await StudentDocument.get(ObjectId(student_id))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    exam = await ExamModel.get(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    solution_path = None
    if solution_photo:
        filename = Path(solution_photo.filename).name
        os.makedirs(STUDENT_SOLUTION_DIR, exist_ok=True)
        solution_path = f"{STUDENT_SOLUTION_DIR}/{filename}"
        with open(solution_path, "wb") as f:
            shutil.copyfileobj(solution_photo.file, f)

    new_entry = ExamEntry(
        exam_id=str(exam.id),
        degree=student_degree,
        percentage=degree_percentage,
        delivery_time=delivery_time,
        solution_photo=solution_path
    )

    student.exams.append(new_entry)
    await student.save()

    return {"msg": "Student exam record added successfully"}



@router.get("/{exam_id}/students")
async def get_students_for_exam(exam_id: str):
    # Fetch exam
    exam = await exams_collection.find_one({"_id": ObjectId(exam_id)})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Extract exam info
    exam_details = {
        "exam_id": str(exam["_id"]),
        "exam_name": exam["exam_name"],
        "exam_level": exam["exam_level"],
        "exam_date": exam["exam_date"],
        "exam_start_time": exam["exam_start_time"],
        "final_degree": exam["final_degree"],
        "solution_photo": exam.get("solution_photo")
    }

    # Search students who participated
    students = await students_collection.find().to_list(length=None)
    entered_students = []
    for student in students:
        for entry in student.get("exams", []):
            if str(entry.get("exam_id", "")) == exam_id:
                entered_students.append({
                    "student_id": student["student_id"],
                    "first_name": student["first_name"],
                    "last_name": student["last_name"],
                    "phone_number": student["phone_number"],
                    "guardian_number": student["guardian_number"],
                    "degree": entry.get("degree"),
                    "percentage": entry.get("percentage"),
                    "delivery_time": entry.get("delivery_time")
                })

    return {
        "exam": exam_details,
        "student_count": len(entered_students),
        "students": entered_students
    }


