import json
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response

from app.schemas.route_admin import (
    RouteSummary,
    RouteDetailResponse,
    CellPatchRequest,
    BatchMatrixUpdateRequest
)
from app.services import route_manager

router = APIRouter()


@router.post("/upload-and-init", response_model=RouteDetailResponse)
async def upload_pdf_and_init_route(
    pdf_file: UploadFile = File(...),
    route_name: str = Form(...),
    route_number: Optional[str] = Form(None),
    rate_per_km: Optional[float] = Form(None),
    min_fare: Optional[float] = Form(None),
    stops: str = Form(...)  # Accepts JSON string `["Stop1", "Stop2"]` or comma/newline-separated list
):
    """
    Step 1: Upload a fare chart PDF and input ordered stops list.
    Automatically generates all N*(N-1)/2 matrix cells ready for coordinate mapping.
    """
    if not pdf_file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    pdf_bytes = await pdf_file.read()

    # Parse stops input
    parsed_stops = []
    try:
        data = json.loads(stops)
        if isinstance(data, list):
            parsed_stops = [str(s).strip() for s in data if str(s).strip()]
    except Exception:
        # Fallback: newline or comma separated
        raw_lines = stops.replace(",", "\n").split("\n")
        parsed_stops = [s.strip() for s in raw_lines if s.strip()]

    if len(parsed_stops) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 stop names are required to generate a fare matrix."
        )

    return route_manager.create_route_with_pdf(
        pdf_bytes=pdf_bytes,
        original_filename=pdf_file.filename,
        route_name=route_name,
        route_number=route_number,
        rate_per_km=rate_per_km,
        min_fare=min_fare,
        stops_raw=parsed_stops
    )


@router.get("", response_model=List[RouteSummary])
def list_all_routes():
    """
    List all created routes with their mapping statistics.
    """
    return route_manager.list_routes()


@router.get("/{route_id}", response_model=RouteDetailResponse)
def get_route_details(route_id: str):
    """
    Retrieve full route details and all matrix cells.
    """
    return route_manager.get_route(route_id)


@router.get("/{route_id}/page-image")
def get_chart_image(route_id: str, page_num: int = 0, zoom: float = 2.0):
    """
    Returns high-resolution rendered PNG image of the PDF chart for canvas coordinate picker.
    """
    img_bytes = route_manager.get_route_page_image(route_id, page_num=page_num, zoom=zoom)
    return Response(content=img_bytes, media_type="image/png")


@router.patch("/{route_id}/cells/{cell_id}", response_model=RouteDetailResponse)
def update_matrix_cell(route_id: str, cell_id: str, req: CellPatchRequest):
    """
    Live auto-save single cell coordinates (source_box, destination_box, fare_box), amount, and distance.
    """
    return route_manager.update_cell(route_id, cell_id, req)


@router.put("/{route_id}/matrix", response_model=RouteDetailResponse)
def batch_update_cells(route_id: str, req: BatchMatrixUpdateRequest):
    """
    Batch update multiple or all matrix cells in one request.
    """
    return route_manager.batch_update_matrix(route_id, req)


@router.get("/{route_id}/preview-cell/{cell_id}")
def preview_cell_highlight(route_id: str, cell_id: str, page_num: int = 0, zoom: float = 2.0):
    """
    Returns chart image highlighting the selected cell (source/destination in blue, fare cell in red).
    """
    img_bytes = route_manager.render_cell_preview(route_id, cell_id, page_num=page_num, zoom=zoom)
    return Response(content=img_bytes, media_type="image/png")


@router.delete("/{route_id}")
def delete_route_item(route_id: str):
    """
    Delete route and its stored JSON/PDF data.
    """
    route_manager.delete_route(route_id)
    return {"message": f"Route '{route_id}' successfully deleted."}
