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
async def get_all_exams(assistant=Depends(get_current_assistant)):
    exams = await ExamModel.find_all().to_list()
    return [ExamOut(**exam.dict(exclude={"id", "_id"}), id=str(exam.id)) for exam in exams]


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
async def get_students_for_exam(exam_id: str, assistant=Depends(get_current_assistant)):
    students = await StudentDocument.find({"exams.exam_id": exam_id}).to_list()
    
    results = []
    for student in students:
        for entry in student.exams:
            if entry.exam_id == exam_id:
                results.append({
                    "student_id": str(student.id),
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "student_degree": entry.degree,  # ✅ Correct field
                    "degree_percentage": entry.percentage,
                    "delivery_time": entry.delivery_time,
                    "solution_photo": entry.solution_photo,
                })
                break  # Assuming only one record per student per exam
    return {"students": results}


