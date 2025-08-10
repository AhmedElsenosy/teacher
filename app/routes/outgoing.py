from fastapi import APIRouter
from datetime import datetime
from app.models.outgoing import Outgoing
from app.schemas.outgoing import OutgoingCreate, OutgoingResponse, PaginatedOutgoingsResponse
from app.models.counter import get_next_id
from fastapi import HTTPException, Depends
from app.dependencies.auth import get_current_assistant


router = APIRouter(prefix="/finance/outgoings", tags=["Outgoings"])

@router.post("/", response_model=OutgoingResponse)
async def create_outgoing(data: OutgoingCreate, assistant=Depends(get_current_assistant)):
    outgoing = Outgoing(
        id=await get_next_id("outgoings"),
        product_name=data.product_name,
        price=data.price,
        created_at=datetime.utcnow()
    )
    await outgoing.insert()
    return outgoing

@router.get("/", response_model=PaginatedOutgoingsResponse)
async def get_all_outgoings(page: int = 1, limit: int = 30, assistant=Depends(get_current_assistant)):
    # Get total count
    total = await Outgoing.count()
    
    # Calculate skip from page number
    skip = (page - 1) * limit
    
    # Get outgoings with pagination
    outgoings_data = await Outgoing.find_all().skip(skip).limit(limit).to_list()
    
    # Convert model objects to OutgoingResponse objects
    outgoings = [
        OutgoingResponse(
            id=outgoing.id,
            product_name=outgoing.product_name,
            price=outgoing.price,
            created_at=outgoing.created_at
        )
        for outgoing in outgoings_data
    ]
    
    # Calculate pagination metadata
    total_pages = (total + limit - 1) // limit  # Ceiling division
    has_next = page < total_pages
    has_prev = page > 1
    
    return PaginatedOutgoingsResponse(
        outgoings=outgoings,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )


@router.delete("/{id}")
async def delete_outgoing(id: int, assistant=Depends(get_current_assistant)):
    outgoing = await Outgoing.find_one(Outgoing.id == id)
    if not outgoing:
        raise HTTPException(status_code=404, detail="Outgoing not found")
    await outgoing.delete()
    return {"message": "Outgoing deleted successfully"}
