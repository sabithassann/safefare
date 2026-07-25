from fastapi import APIRouter
from app.schemas.fare import FareRequest, FareResponse
from app.services.fare_calculator import calculate_fare

router = APIRouter()

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
