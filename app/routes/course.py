from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Form
from app.schemas.course import CourseCreate, CourseOut, CourseUpdate
from app.dependencies.auth import get_current_assistant
from app.database import db
from bson import ObjectId
from datetime import datetime
import os
import shutil

router = APIRouter(prefix="/courses", tags=["Courses"])
courses_collection = db["courses"]

UPLOAD_DIR = "upload/photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=CourseOut)
async def create_course(
    course_name: str = Form(...),
    course_level: int = Form(...),
    course_start_date: str = Form(...),
    course_end_date: str = Form(...),
    photo: UploadFile = File(...),
    assistant=Depends(get_current_assistant)
):
    # Save the uploaded photo
    photo_path = os.path.join(UPLOAD_DIR, photo.filename)
    with open(photo_path, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)

    course_data = {
        "course_name": course_name,
        "course_level": course_level,
        "course_start_date": course_start_date,
        "course_end_date": course_end_date,
        "photo_path": photo_path,
        "created_at": datetime.utcnow()
    }

    result = await courses_collection.insert_one(course_data)
    course_data["id"] = str(result.inserted_id)
    return CourseOut(**course_data)

@router.get("/", response_model=list[CourseOut])
async def get_all_courses(assistant=Depends(get_current_assistant)):
    courses = await courses_collection.find().to_list(length=None)
    for course in courses:
        course["id"] = str(course["_id"])
        del course["_id"]
    return [CourseOut(**c) for c in courses]

@router.get("/{course_id}", response_model=CourseOut)
async def get_course_by_id(course_id: str, assistant=Depends(get_current_assistant)):
    course = await courses_collection.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course["id"] = str(course["_id"])
    del course["_id"]
    return CourseOut(**course)

@router.put("/{course_id}", response_model=dict)
async def update_course(
    course_id: str,
    course_name: str = Form(None),
    course_level: int = Form(None),
    course_start_date: str = Form(None),
    course_end_date: str = Form(None),
    photo: UploadFile = File(None),
    assistant=Depends(get_current_assistant)
):
    update_data = {}
    if course_name is not None:
        update_data["course_name"] = course_name
    if course_level is not None:
        update_data["course_level"] = course_level
    if course_start_date is not None:
        update_data["course_start_date"] = course_start_date
    if course_end_date is not None:
        update_data["course_end_date"] = course_end_date
    if photo is not None:
        photo_path = os.path.join(UPLOAD_DIR, photo.filename)
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        update_data["photo_path"] = photo_path

    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided for update")

    result = await courses_collection.update_one({"_id": ObjectId(course_id)}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Course not found or nothing changed")
    return {"message": "Course updated successfully"}

@router.delete("/{course_id}")
async def delete_course(course_id: str, assistant=Depends(get_current_assistant)):
    result = await courses_collection.delete_one({"_id": ObjectId(course_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course deleted successfully"}
