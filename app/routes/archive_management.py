from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.encoders import jsonable_encoder
from app.dependencies.auth import get_current_assistant
from app.database import student_collection
from bson import ObjectId
from datetime import datetime
from app.schemas.archived_student import ArchivedStudentOut, ArchiveRequest, PaginatedArchivedStudentsResponse
from typing import List, Any, Dict
from app.models.archived_student import ArchivedStudentModel

# Helper function to convert ObjectIds to strings recursively
def convert_objectids_to_strings(obj: Any) -> Any:
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectids_to_strings(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectids_to_strings(item) for item in obj]
    else:
        return obj

router = APIRouter(
    prefix="/archive",
    tags=["Archive Management"],
    dependencies=[Depends(get_current_assistant)]
)

# ✅ Helper to move student by _id
async def move_student_to_archive(student_id: str, archive_reason: str):
    if not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid student ObjectId")

    student = await student_collection.find_one({"_id": ObjectId(student_id)})

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student["archived"] = True
    student["archive_reason"] = archive_reason
    student["archived_at"] = datetime.utcnow()
    student["months_without_payment"] = 0

    archived_student = ArchivedStudentModel(**student)
    await archived_student.insert()

    await student_collection.delete_one({"_id": ObjectId(student_id)})

    return archived_student

@router.post("/{student_id}")
async def archive_student(student_id: str, request: ArchiveRequest):
    archived_student = await move_student_to_archive(student_id, request.archive_reason)
    return {
        "message": f"Student {student_id} archived successfully",
        "archived_student": jsonable_encoder(archived_student)
    }

@router.post("/{student_id}/restore")
async def restore_student(student_id: str):
    if not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId")

    from app.database import archived_student_collection
    archived_student = await archived_student_collection.find_one({"_id": ObjectId(student_id)})

    if not archived_student:
        raise HTTPException(status_code=404, detail="Archived student not found")

    archived_student["archived"] = False
    archived_student["archive_reason"] = None
    archived_student["archived_at"] = None

    await student_collection.insert_one(archived_student)
    await archived_student_collection.delete_one({"_id": ObjectId(student_id)})

    return {"message": f"Student {student_id} restored successfully"}

@router.get("/", response_model=PaginatedArchivedStudentsResponse)
async def get_all_archived_students(page: int = 1, limit: int = 25):
    from app.database import archived_student_collection
    try:
        # Get total count
        total = await archived_student_collection.count_documents({})
        
        # Calculate skip from page number
        skip = (page - 1) * limit
        
        # Get archived students with pagination
        archived = await archived_student_collection.find().skip(skip).limit(limit).to_list(length=None)

        # Convert all ObjectId fields to strings recursively
        archived = [convert_objectids_to_strings(student) for student in archived]
        
        # Calculate pagination metadata
        total_pages = (total + limit - 1) // limit  # Ceiling division
        has_next = page < total_pages
        has_prev = page > 1

        return PaginatedArchivedStudentsResponse(
            archived_students=archived,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{student_id}")
async def get_archived_student(student_id: str):
    from app.database import archived_student_collection

    try:
        student = await archived_student_collection.find_one({"_id": ObjectId(student_id)})
        if not student:
            raise HTTPException(status_code=404, detail="Archived student not found")

        # Convert ObjectId to string
        student["_id"] = str(student["_id"])

        return jsonable_encoder(student)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{student_id}")
async def permanently_delete_archived_student(student_id: str):
    from app.database import archived_student_collection
    if not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId")
    result = await archived_student_collection.delete_one({"_id": ObjectId(student_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Archived student not found")
    return {"message": f"Archived student {student_id} permanently deleted"}
