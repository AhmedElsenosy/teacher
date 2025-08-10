from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from datetime import datetime
from bson import ObjectId
from beanie.operators import In

from app.models.monthsale import MonthlySale
from app.models.counter import get_next_id
from app.schemas.monthsale import MonthlySaleCreate, MonthlySaleResponse, MonthQuery, MonthSaleDetailResponse, PaginatedMonthSalesResponse
from app.dependencies.auth import get_current_assistant
from app.models.student import StudentModel

router = APIRouter(prefix="/finance/monthsales", tags=["Finance"])


@router.post("/", response_model=MonthlySaleResponse)
async def create_month_sale(data: MonthlySaleCreate, assistant=Depends(get_current_assistant)):
    sale = MonthlySale(
        id=await get_next_id("monthsales"),
        student_id=ObjectId(data.student_id),
        price=data.price,
        default_price=data.default_price,
        month=data.month,
        created_at=datetime.utcnow()
    )
    await sale.insert()

    # ----------------------------
    # Update Student subscription
    # ----------------------------
    student = await StudentModel.get(sale.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Initialize subscription and monthsales dicts if they don't exist
    if not student.subscription:
        student.subscription = {}

    student.subscription.setdefault("monthsales", {})

    # Format month key as "YYYY-MM"
    try:
        month_key = sale.month.strftime("%Y-%m")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid month format")

    # Update the monthsales entry
    student.subscription["monthsales"][month_key] = float(sale.price)
    
    # Set is_subscription to True when a monthly sale is made
    student.is_subscription = True

    # Save the updated student
    await student.save()

    return MonthlySaleResponse(
        id=sale.id,
        student_id=str(sale.student_id),
        price=sale.price,
        default_price=sale.default_price,
        month=str(sale.month),
        created_at=sale.created_at,
    )


@router.delete("/{monthsale_id}")
async def delete_month_sale(monthsale_id: int, assistant=Depends(get_current_assistant)):
    sale = await MonthlySale.find_one(MonthlySale.id == monthsale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Month sale not found")
    await sale.delete()
    return {"detail": f"Month sale with id {monthsale_id} deleted successfully"}


@router.post("/by-month")
async def get_month_sales_by_month(data: MonthQuery, assistant=Depends(get_current_assistant)):
    try:
        start_date = datetime.strptime(data.month, "%Y-%m")
        end_date = (
            datetime(start_date.year + 1, 1, 1)
            if start_date.month == 12
            else datetime(start_date.year, start_date.month + 1, 1)
        )

        sales = await MonthlySale.find({
            "created_at": {
                "$gte": start_date,
                "$lt": end_date
            }
        }).to_list()

        return [
            {
                "id": sale.id,
                "student_id": str(sale.student_id),
                "price": float(sale.price),
                "default_price": float(sale.default_price),
                "month": str(sale.month),
                "created_at": sale.created_at.isoformat()
            }
            for sale in sales
        ]

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")


@router.get("/student/{student_id}")
async def get_monthsales_by_student(student_id: str, assistant=Depends(get_current_assistant)):
    try:
        student_obj_id = ObjectId(student_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid student ID")

    sales = await MonthlySale.find(MonthlySale.student_id == student_obj_id).to_list()

    total_price = sum(sale.price for sale in sales)

    monthly_sales = [
        {
            "id": sale.id,
            "student_id": str(sale.student_id),
            "price": sale.price,
            "default_price": sale.default_price,
            "month": str(sale.month),
            "created_at": sale.created_at,
        }
        for sale in sales
    ]

    return {
        "student_total_price": total_price,
        "monthly_sales": monthly_sales
    }

@router.get("/all", response_model=PaginatedMonthSalesResponse)
async def get_all_monthsales(page: int = 1, limit: int = 10, assistant=Depends(get_current_assistant)):
    # Get total count
    total = await MonthlySale.count()
    
    # Calculate skip from page number
    skip = (page - 1) * limit
    
    # Get monthsales with pagination
    monthsales = await MonthlySale.find_all().skip(skip).limit(limit).to_list()

    student_ids = list({sale.student_id for sale in monthsales})
    students = await StudentModel.find(In(StudentModel.id, student_ids)).to_list()
    
    student_map = {
        student.id: f"{student.first_name} {student.last_name}" for student in students
    }

    response = []
    for sale in monthsales:
        student_name = student_map.get(sale.student_id, "Unknown")
        sale_month = sale.created_at.strftime("%Y-%m")  # Extract the month

        response.append(MonthSaleDetailResponse(
            student_name=student_name,
            price=float(sale.price),
            created_at=sale.created_at,
            month=sale_month
        ))
    
    # Calculate pagination metadata
    total_pages = (total + limit - 1) // limit  # Ceiling division
    has_next = page < total_pages
    has_prev = page > 1

    return PaginatedMonthSalesResponse(
        month_sales=response,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )
