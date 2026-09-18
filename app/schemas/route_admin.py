from typing import List, Optional
from pydantic import BaseModel


class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class StopItem(BaseModel):
    id: int  # 1-indexed (1, 2, ..., N)
    name: str


class FareMatrixCell(BaseModel):
    cell_id: str  # e.g., "1_13"
    source_stop_id: int
    destination_stop_id: int
    source_name: str
    destination_name: str
    amount: Optional[float] = None
    distance_km: Optional[float] = None
    source_box: Optional[BoundingBox] = None
    destination_box: Optional[BoundingBox] = None
    fare_box: Optional[BoundingBox] = None
    is_mapped: bool = False


class RouteSummary(BaseModel):
    route_id: str
    route_name: str
    route_number: Optional[str] = None
    total_stops: int
    total_cells: int
    mapped_cells: int
    pdf_filename: str
    created_at: str


class RouteDetailResponse(BaseModel):
    route_id: str
    route_name: str
    route_number: Optional[str] = None
    rate_per_km: Optional[float] = None
    min_fare: Optional[float] = None
    pdf_filename: str
    total_stops: int
    total_cells: int
    mapped_cells: int
    created_at: str
    stops: List[StopItem]
    cells: List[FareMatrixCell]


class CellPatchRequest(BaseModel):
    amount: Optional[float] = None
    distance_km: Optional[float] = None
    source_box: Optional[BoundingBox] = None
    destination_box: Optional[BoundingBox] = None
    fare_box: Optional[BoundingBox] = None


class BatchMatrixUpdateRequest(BaseModel):
    cells: List[FareMatrixCell]
