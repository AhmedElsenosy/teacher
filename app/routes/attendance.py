from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from app.models.student import StudentModel
from app.models.group import Group
from pydantic import BaseModel
from dateutil.parser import isoparse
import pytz

router = APIRouter(prefix="/attendance", tags=["Attendance"])

class AttendanceRequest(BaseModel):
    uid: int
    timestamp: str  # ISO format string, potentially with +03:00

@router.post("/")
async def auto_attendance(data: AttendanceRequest):
    try:
        # Parse timestamp (aware or naive)
        aware_timestamp = isoparse(data.timestamp)

        # Convert to naive datetime (removing timezone info)
        egypt_tz = pytz.timezone("Africa/Cairo")
        local_timestamp = aware_timestamp.astimezone(egypt_tz).astimezone(pytz.utc).replace(tzinfo=None)
        timestamp = local_timestamp
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid input format: {e}")

    student = await StudentModel.find_one(StudentModel.uid == data.uid)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    group = await Group.find(Group.students == student.id).first_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Build naive scheduled time based on Egypt time (08:00)
    today = timestamp.date()
    scheduled_start_time = datetime.combine(today, datetime.strptime("08:00", "%H:%M").time())

    allowed_start = scheduled_start_time - timedelta(hours=1)
    allowed_end = scheduled_start_time + timedelta(hours=1)

    is_on_time = allowed_start <= timestamp <= allowed_end

    if not hasattr(student, "attendance") or not isinstance(student.attendance, dict):
        student.attendance = {}

    day_index = len(student.attendance) + 1
    day_key = f"day{day_index}"

    student.attendance[day_key] = is_on_time
    await student.save()

    return {
        "message": "Attendance recorded",
        "uid": data.uid,
        "student": f"{student.first_name} {student.last_name}",
        "group": group.group_name,
        "day": day_key,
        "status": is_on_time
    }
