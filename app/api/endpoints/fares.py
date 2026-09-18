from typing import List, Optional
from fastapi import APIRouter, Query
from app.schemas.fare import FareRequest, FareResponse
from app.services.fare_calculator import calculate_fare, get_stop_suggestions

router = APIRouter()

@router.get("/stops", response_model=List[str])
def get_stops(q: Optional[str] = Query(None, description="Search query for autocomplete")):
    """
    Get stop name suggestions for autocomplete search.
    """
    return get_stop_suggestions(query=q)

@router.post("/search", response_model=FareResponse)
def search_fare(request: FareRequest):
    """
    Calculate and return the exact bus fare between two locations.
    Also returns the official government chart URL and highlight coordinates.
    """
    return calculate_fare(
        source=request.source, 
        destination=request.destination, 
        route_name=request.route_name
    )

