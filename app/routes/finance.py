from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime, date
from decimal import Decimal
from collections import defaultdict
from pytz import timezone
from app.models.monthsale import MonthlySale
from app.models.booksale import BookSale
from app.models.outgoing import Outgoing
from app.schemas.profit import DailyProfitResponse, ProfitFilterRequest
from app.dependencies.auth import get_current_assistant

router = APIRouter(prefix="/finance", tags=["Finance"])
egypt_tz = timezone("Africa/Cairo")

@router.post("/profits", response_model=list[DailyProfitResponse])
async def get_daily_profits(
    filter_request: ProfitFilterRequest,
    assistant=Depends(get_current_assistant)
):
    profits_by_day = defaultdict(lambda: {
        "monthsales": Decimal("0.0"),
        "booksales": Decimal("0.0"),
        "outgoings": Decimal("0.0")
    })

    # Fetch all records
    monthsales = await MonthlySale.find_all().to_list()
    booksales = await BookSale.find_all().to_list()
    outgoings = await Outgoing.find_all().to_list()

    # Group and sum by Egypt day
    for sale in monthsales:
        local_day = sale.created_at.astimezone(egypt_tz).date()
        profits_by_day[local_day]["monthsales"] += Decimal(str(sale.price))

    for sale in booksales:
        local_day = sale.created_at.astimezone(egypt_tz).date()
        profits_by_day[local_day]["booksales"] += Decimal(str(sale.price))

    for out in outgoings:
        local_day = out.created_at.astimezone(egypt_tz).date()
        profits_by_day[local_day]["outgoings"] += Decimal(str(out.price))

    # Filter by date if provided
    result = []
    for day, values in sorted(profits_by_day.items()):
        if filter_request.day_date and day != filter_request.day_date:
            continue

        profit = (values["monthsales"] + values["booksales"]) - values["outgoings"]
        result.append(DailyProfitResponse(
            date=day,
            total_monthsales=values["monthsales"],
            total_booksales=values["booksales"],
            total_outgoings=values["outgoings"],
            profit=profit
        ))

    return result


@router.get("/booksales/last-default-price/{student_id}")
async def get_last_default_price(student_id: str, assistant=Depends(get_current_assistant)):
    if not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid student ID")

    # Fetch the latest book sale for the student by created_at descending
    last_sale = await BookSale.find(
        BookSale.student_id == ObjectId(student_id)
    ).sort("-created_at").first_or_none()

    if not last_sale:
        raise HTTPException(status_code=404, detail="No book sales found for this student")

    return {
        "student_id": student_id,
        "last_default_price": last_sale.default_price
    }

@router.get("/monthsales/last-default-price/{student_id}")
async def get_last_month_default_price(student_id: str, assistant=Depends(get_current_assistant)):
    if not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid student ID")

    last_month_sale = await MonthlySale.find(
        MonthlySale.student_id == ObjectId(student_id)
    ).sort("-created_at").first_or_none()

    if not last_month_sale:
        raise HTTPException(status_code=404, detail="No monthly sales found for this student")

    return {
        "student_id": student_id,
        "last_default_price": last_month_sale.default_price
    }


@router.get("/monthly-summary")
async def get_monthly_summary(assistant=Depends(get_current_assistant)):
    monthsales = await MonthlySale.find_all().to_list()
    booksales = await BookSale.find_all().to_list()

    report = defaultdict(lambda: {
        "student_ids": set(),
        "total_monthsales_price": 0,
        "total_booksales_price": 0,
        "books_sold_count": 0,
    })

    # Process monthsales
    for sale in monthsales:
        # Ensure month is in "YYYY-MM" format
        if isinstance(sale.month, str):
            month = sale.month
        elif isinstance(sale.month, datetime):
            month = sale.month.strftime("%Y-%m")
        else:
            # If it's a date or invalid, convert it
            try:
                month = sale.month.strftime("%Y-%m")
            except Exception:
                raise ValueError(f"Invalid month value: {sale.month}")

        report[month]["student_ids"].add(str(sale.student_id))
        report[month]["total_monthsales_price"] += float(sale.price)

    # Process booksales
    for sale in booksales:
        month = sale.created_at.strftime("%Y-%m")
        report[month]["total_booksales_price"] += float(sale.price)
        report[month]["books_sold_count"] += 1

    # Build response
    final_report = []
    for month, data in sorted(report.items()):
        final_report.append({
            "month": month,
            "student_count": len(data["student_ids"]),
            "total_monthsales_price": round(data["total_monthsales_price"], 2),
            "total_booksales_price": round(data["total_booksales_price"], 2),
            "books_sold_count": data["books_sold_count"]
        })

    return final_report