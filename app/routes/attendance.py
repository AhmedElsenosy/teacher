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
    assistant_approved: bool = False  # Optional parameter to bypass group schedule validation

@router.post("/")
async def auto_attendance(data: AttendanceRequest):
    try:
        # Parse timestamp (aware or naive)
        aware_timestamp = isoparse(data.timestamp)
        egypt_tz = pytz.timezone("Africa/Cairo")
        # Ensure timestamp is in Egypt time
        local_timestamp = aware_timestamp.astimezone(egypt_tz)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid input format: {e}")

    # 1. Check if student exists
    student = await StudentModel.find_one(StudentModel.uid == data.uid)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 2. Check if student belongs to a group
    group = await Group.find(Group.students == student.id).first_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Student is not assigned to any group")

    # 3. Check if student's level matches group's level
    if student.level != group.level:
        raise HTTPException(
            status_code=400, 
            detail=f"Student level ({student.level}) does not match group level ({group.level})"
        )

    # Skip validations 4 and 5 if assistant approved
    if not data.assistant_approved:
        # 4. Check if current day is in group's allowed days
        current_day = local_timestamp.strftime("%A")  # Gets day name like "Monday", "Tuesday", etc.
        allowed_days = [day.value for day in group.days]  # Convert enum to string values
        if current_day not in allowed_days:
            raise HTTPException(
                status_code=400,
                detail=f"Attendance not allowed on {current_day}. Group schedule: {', '.join(allowed_days)}"
            )

        # 5. Check if attendance time is within allowed window
        try:
            group_start_time_str = group.start_time
            group_start_time = datetime.strptime(group_start_time_str, "%H:%M").time()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Invalid group start_time format: {e}")

        today = local_timestamp.date()
        scheduled_start_time = egypt_tz.localize(datetime.combine(today, group_start_time))
        allowed_start = scheduled_start_time - timedelta(hours=1)
        allowed_end = scheduled_start_time + timedelta(hours=1)

        is_on_time = allowed_start <= local_timestamp <= allowed_end
        if not is_on_time:
            raise HTTPException(
                status_code=400,
                detail=f"Attendance time ({local_timestamp.strftime('%H:%M')}) is outside allowed window ({allowed_start.strftime('%H:%M')} - {allowed_end.strftime('%H:%M')})"
            )

    # All validations passed - record attendance
    if not hasattr(student, "attendance") or not isinstance(student.attendance, dict):
        student.attendance = {}

    day_index = len(student.attendance) + 1
    day_key = f"day{day_index}"

    student.attendance[day_key] = True  # Always True if all validations pass
    await student.save()

    message = "Attendance recorded successfully"
    if data.assistant_approved:
        message += " (Assistant Approved - bypassed schedule validation)"
    
    return {
        "success": True,
        "message": message,
        "uid": data.uid,
        "student": f"{student.first_name} {student.last_name}",
        "group": group.group_name,
        "day": day_key,
        "status": True,
        "timestamp": local_timestamp.isoformat(),
        "assistant_approved": data.assistant_approved
    }
