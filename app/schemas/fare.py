from pydantic import BaseModel
from typing import Optional, List

class FareRequest(BaseModel):
    source: str
    destination: str
    route_name: Optional[str] = None

class ChartCoordinates(BaseModel):
    x_start: int
    y_start: int
    x_end: int
    y_end: int
    page: int

class FareResponse(BaseModel):
    source: str
    destination: str
    calculated_fare: float
    distance_km: float
    chart_url: Optional[str] = None
    highlight_coordinates: Optional[ChartCoordinates] = None

class AIRequest(BaseModel):
    question: str
    context_route: Optional[str] = None

class AIResponse(BaseModel):
    answer: str
