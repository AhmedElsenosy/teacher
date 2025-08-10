from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from bson import ObjectId
from typing import Dict, Any
from pydantic import BaseModel

from app.database import db
from app.models.exam import ExamModel
from app.models.student_document import StudentDocument, ExamEntry
from app.dependencies.auth import get_current_assistant

router = APIRouter(prefix="/internal", tags=["Internal API"])

students_collection = db["students"]
exams_collection = db["exams"]

class ExamResultData(BaseModel):
    student_id: str
    degree: float = None
    percentage: float = None
    delivery_time: str
    solution_photo: str
    correction_details: Dict[str, Any] = None

class ExamResultUpdate(BaseModel):
    student_id: str
    degree: float
    percentage: float
    correction_details: Dict[str, Any] = None

@router.get("/exams/{exam_id}")
async def get_exam_for_correction(exam_id: str):
    """
    Get exam details for correction processing.
    This endpoint is used by the fingerprint backend to get exam information.
    """
    try:
        exam_obj_id = ObjectId(exam_id)
        exam = await exams_collection.find_one({"_id": exam_obj_id})
        
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")
        
        # Extract models information
        models = exam.get("models", [])
        models_data = []
        for model in models:
            models_data.append({
                "model_number": model.get("model_number"),
                "model_name": model.get("model_name"),
                "solution_photo": model.get("solution_photo")
            })
        
        return {
            "exam_id": str(exam["_id"]),
            "exam_name": exam["exam_name"],
            "exam_level": exam["exam_level"],
            "exam_date": exam["exam_date"],
            "exam_start_time": exam["exam_start_time"],
            "final_degree": exam["final_degree"],
            "solution_photo": exam.get("solution_photo"),  # Legacy field
            "models": models_data  # New 3-model data
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid exam ID format: {str(e)}")


@router.get("/students/by-student-id/{student_numeric_id}")
async def get_student_by_numeric_id(student_numeric_id: int):
    """
    Get student details by their numeric student_id field.
    Used by fingerprint backend to convert numeric ID to ObjectId.
    """
    try:
        student = await students_collection.find_one({"student_id": student_numeric_id})
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        return {
            "_id": str(student["_id"]),
            "student_id": student["student_id"],
            "first_name": student.get("first_name"),
            "last_name": student.get("last_name"),
            "email": student.get("email"),
            "phone_number": student.get("phone_number")
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error looking up student: {str(e)}")


@router.get("/exams/{exam_id}/students/{student_id}")
async def get_student_exam_submission(exam_id: str, student_id: str):
    """
    Get student's exam submission details.
    Used by fingerprint backend for manual correction.
    """
    try:
        student_obj_id = ObjectId(student_id)
        student = await students_collection.find_one({"_id": student_obj_id})
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Find the exam entry
        for entry in student.get("exams", []):
            if str(entry.get("exam_id")) == exam_id:
                return {
                    "student_id": str(student["_id"]),
                    "exam_id": entry.get("exam_id"),
                    "degree": entry.get("degree"),
                    "percentage": entry.get("percentage"),
                    "delivery_time": entry.get("delivery_time"),
                    "solution_photo": entry.get("solution_photo")
                }
        
        raise HTTPException(status_code=404, detail="Student exam submission not found")
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid ID format: {str(e)}")


@router.post("/exams/{exam_id}/results")
async def save_exam_results(exam_id: str, result_data: ExamResultData):
    """
    Save exam correction results from fingerprint backend.
    This creates a new exam entry for the student.
    """
    try:
        student_obj_id = ObjectId(result_data.student_id)
        exam_obj_id = ObjectId(exam_id)
        
        # Verify student and exam exist
        student = await students_collection.find_one({"_id": student_obj_id})
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        exam = await exams_collection.find_one({"_id": exam_obj_id})
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")
        
        # Check if student already has this exam
        for entry in student.get("exams", []):
            if str(entry.get("exam_id")) == exam_id:
                raise HTTPException(status_code=400, detail="Student has already submitted this exam")
        
        # Create new exam entry
        new_entry = ExamEntry(
            exam_id=exam_id,
            degree=result_data.degree,
            percentage=result_data.percentage,
            delivery_time=datetime.fromisoformat(result_data.delivery_time.replace('Z', '+00:00')),
            solution_photo=result_data.solution_photo
        )
        
        # Add to student's exams
        await students_collection.update_one(
            {"_id": student_obj_id},
            {"$push": {"exams": new_entry.dict()}}
        )
        
        return {
            "message": "Exam results saved successfully",
            "student_id": result_data.student_id,
            "exam_id": exam_id,
            "degree": result_data.degree,
            "percentage": result_data.percentage
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving results: {str(e)}")


@router.put("/exams/{exam_id}/students/{student_id}/results")
async def update_exam_results(exam_id: str, student_id: str, result_data: ExamResultUpdate):
    """
    Update existing exam results for a student.
    Used for manual correction updates.
    """
    try:
        student_obj_id = ObjectId(student_id)
        
        student = await students_collection.find_one({"_id": student_obj_id})
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Find and update the exam entry
        exam_entry_index = None
        for i, entry in enumerate(student.get("exams", [])):
            if str(entry.get("exam_id")) == exam_id:
                exam_entry_index = i
                break
        
        if exam_entry_index is None:
            raise HTTPException(status_code=404, detail="Student exam submission not found")
        
        # Update the exam entry
        await students_collection.update_one(
            {"_id": student_obj_id},
            {
                "$set": {
                    f"exams.{exam_entry_index}.degree": result_data.degree,
                    f"exams.{exam_entry_index}.percentage": result_data.percentage
                }
            }
        )
        
        return {
            "message": "Exam results updated successfully",
            "student_id": student_id,
            "exam_id": exam_id,
            "degree": result_data.degree,
            "percentage": result_data.percentage
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating results: {str(e)}")
