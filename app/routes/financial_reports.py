from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from bson import ObjectId

from app.dependencies.auth import get_current_assistant
from app.models.monthsale import MonthlySale
from app.models.student import StudentModel
from app.models.student_default_price import StudentDefaultPrice
from app.models.archived_student import ArchivedStudentModel
from app.database import student_collection, archived_student_collection

router = APIRouter(
    prefix="/financial-reports",
    tags=["Financial Reports"],
    dependencies=[Depends(get_current_assistant)]
)

def get_month_key(date):
    """Convert date to YYYY-MM format"""
    return date.strftime("%Y-%m")

async def get_student_expected_payments(student_id: int, months_to_calculate: List[str]) -> Dict:
    """Calculate expected payments for a student based on their default price"""
    # Get student's default price
    default_price_doc = await StudentDefaultPrice.find_one(StudentDefaultPrice.student_id == student_id)
    if not default_price_doc:
        # If no default price set, use a default of 200
        default_price = 200.0
    else:
        default_price = float(default_price_doc.default_price)
    
    return {
        "default_price": default_price,
        "expected_total": default_price * len(months_to_calculate)
    }

@router.get("/monthly-report")
async def get_monthly_subscription_report(
    month: str = Query(description="Month in YYYY-MM format (e.g., 2025-07)"),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    limit: int = Query(100, ge=1, le=100, description="Number of students per page (max 100)")
):
    """
    Get subscription report for a specific month showing:
    - Count of students who made subscription payment
    - Total amount collected from paying students
    - Count of students who didn't make subscription payment  
    - Total amount not collected from non-paying students
    """
    try:
        # Validate month format
        try:
            year, month_num = month.split('-')
            target_date = datetime(int(year), int(month_num), 1)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM (e.g., 2025-07)")
        
        # Get all subscription students (active only)
        all_students = await student_collection.find({"is_subscription": True}).to_list(length=None)
        
        if not all_students:
            return {
                "month": month,
                "paying_students": {
                    "count": 0,
                    "total_amount": 0.0,
                    "students": []
                },
                "non_paying_students": {
                    "count": 0,
                    "total_amount_not_paid": 0.0,
                    "students": []
                },
                "summary": {
                    "total_students": 0,
                    "total_collected": 0.0,
                    "total_outstanding": 0.0,
                    "collection_rate": 0.0
                }
            }
        
        # Get all monthly sales for the specified month
        monthly_sales = await MonthlySale.find(MonthlySale.month == target_date).to_list()
        
        # Create a dictionary of payments by student_id
        payments_by_student = {}
        for sale in monthly_sales:
            student_id = sale.student_id
            if student_id in payments_by_student:
                payments_by_student[student_id] += float(sale.price)
            else:
                payments_by_student[student_id] = float(sale.price)
        
        paying_students = []
        non_paying_students = []
        total_collected = 0.0
        total_outstanding = 0.0
        
        for student in all_students:
            student_object_id = student["_id"]
            student_id = student["student_id"]
            student_name = f"{student.get('first_name', '')} {student.get('last_name', '')}"
            
            # Get student's expected price for this month
            default_price_doc = await StudentDefaultPrice.find_one(StudentDefaultPrice.student_id == student_id)
            expected_price = float(default_price_doc.default_price) if default_price_doc else 200.0
            
            # Check if student paid for this month
            amount_paid = payments_by_student.get(student_object_id, 0.0)
            
            if amount_paid > 0:
                # Student made payment
                paying_students.append({
                    "student_id": student_id,
                    "student_name": student_name,
                    "amount_paid": amount_paid,
                    "expected_price": expected_price
                })
                total_collected += amount_paid
            else:
                # Student didn't make payment
                non_paying_students.append({
                    "student_id": student_id,
                    "student_name": student_name,
                    "expected_price": expected_price,
                    "amount_not_paid": expected_price
                })
                total_outstanding += expected_price
        
        # Calculate collection rate
        total_expected = total_collected + total_outstanding
        collection_rate = (total_collected / total_expected * 100) if total_expected > 0 else 0
        
        # Apply pagination
        skip = (page - 1) * limit
        
        # Paginate paying students
        paying_students_paginated = paying_students[skip:skip + limit]
        paying_students_remaining = len(paying_students) - skip - len(paying_students_paginated)
        
        # Paginate non-paying students  
        non_paying_students_paginated = non_paying_students[skip:skip + limit]
        non_paying_students_remaining = len(non_paying_students) - skip - len(non_paying_students_paginated)
        
        # Calculate total pages
        total_paying_pages = (len(paying_students) + limit - 1) // limit if paying_students else 0
        total_non_paying_pages = (len(non_paying_students) + limit - 1) // limit if non_paying_students else 0
        
        return {
            "month": month,
            "pagination": {
                "current_page": page,
                "limit_per_page": limit,
                "has_next_page": paying_students_remaining > 0 or non_paying_students_remaining > 0,
                "total_paying_pages": total_paying_pages,
                "total_non_paying_pages": total_non_paying_pages
            },
            "paying_students": {
                "count": len(paying_students),
                "total_amount": round(total_collected, 2),
                "students": paying_students_paginated,
                "showing": len(paying_students_paginated),
                "remaining": max(0, paying_students_remaining)
            },
            "non_paying_students": {
                "count": len(non_paying_students),
                "total_amount_not_paid": round(total_outstanding, 2),
                "students": non_paying_students_paginated,
                "showing": len(non_paying_students_paginated),
                "remaining": max(0, non_paying_students_remaining)
            },
            "summary": {
                "total_students": len(all_students),
                "total_collected": round(total_collected, 2),
                "total_outstanding": round(total_outstanding, 2),
                "total_expected": round(total_expected, 2),
                "collection_rate": round(collection_rate, 2)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating monthly report: {str(e)}")






