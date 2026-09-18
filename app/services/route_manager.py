import os
import re
import json
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
import fitz  # PyMuPDF
from PIL import Image, ImageDraw
import io
from fastapi import HTTPException, UploadFile

from app.schemas.route_admin import (
    RouteDetailResponse,
    RouteSummary,
    StopItem,
    FareMatrixCell,
    BoundingBox,
    CellPatchRequest,
    BatchMatrixUpdateRequest
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
ROUTES_DIR = os.path.join(DATA_DIR, "routes")
CHARTS_DIR = os.path.join(DATA_DIR, "charts")
INDEX_FILE = os.path.join(ROUTES_DIR, "index.json")


def _init_storage():
    os.makedirs(ROUTES_DIR, exist_ok=True)
    os.makedirs(CHARTS_DIR, exist_ok=True)
    if not os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump({"routes": []}, f, indent=2, ensure_ascii=False)


def _load_index() -> Dict[str, Any]:
    _init_storage()
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_index(index_data: Dict[str, Any]):
    _init_storage()
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[\s\-_]+', '_', text)
    text = re.sub(r'[^\w_]', '', text)
    return text[:40] if text else "route"


def _get_route_file_path(route_id: str) -> str:
    return os.path.join(ROUTES_DIR, f"{route_id}.json")


def _get_pdf_file_path(route_id: str) -> str:
    return os.path.join(CHARTS_DIR, f"{route_id}.pdf")


def list_routes() -> List[RouteSummary]:
    index = _load_index()
    return [RouteSummary(**r) for r in index.get("routes", [])]


def get_route(route_id: str) -> RouteDetailResponse:
    file_path = _get_route_file_path(route_id)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Route '{route_id}' not found.")
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return RouteDetailResponse(**data)


def create_route_with_pdf(
    pdf_bytes: bytes,
    original_filename: str,
    route_name: str,
    route_number: Optional[str] = None,
    rate_per_km: Optional[float] = None,
    min_fare: Optional[float] = None,
    stops_raw: List[str] = []
) -> RouteDetailResponse:
    _init_storage()

    # Filter out empty stop names and strip whitespace
    stops_cleaned = [s.strip() for s in stops_raw if s and s.strip()]
    if len(stops_cleaned) < 2:
        raise HTTPException(status_code=400, detail="At least 2 stops are required to generate a fare matrix.")

    slug = _slugify(route_name)
    timestamp = int(time.time())
    route_id = f"{slug}_{timestamp}"

    # Save PDF
    pdf_path = _get_pdf_file_path(route_id)
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    # Generate stops
    stop_items: List[StopItem] = []
    for idx, name in enumerate(stops_cleaned, start=1):
        stop_items.append(StopItem(id=idx, name=name))

    # Generate N*(N-1)/2 matrix cells
    cells: List[FareMatrixCell] = []
    n = len(stop_items)
    for i in range(1, n):
        for j in range(i + 1, n + 1):
            cell_id = f"{i}_{j}"
            src_stop = stop_items[i - 1]
            dest_stop = stop_items[j - 1]
            cells.append(
                FareMatrixCell(
                    cell_id=cell_id,
                    source_stop_id=src_stop.id,
                    destination_stop_id=dest_stop.id,
                    source_name=src_stop.name,
                    destination_name=dest_stop.name,
                    amount=None,
                    distance_km=None,
                    source_box=None,
                    destination_box=None,
                    fare_box=None,
                    is_mapped=False
                )
            )

    created_at = datetime.now().isoformat()
    total_cells = len(cells)

    route_data = {
        "route_id": route_id,
        "route_name": route_name,
        "route_number": route_number,
        "rate_per_km": rate_per_km,
        "min_fare": min_fare,
        "pdf_filename": original_filename,
        "total_stops": len(stop_items),
        "total_cells": total_cells,
        "mapped_cells": 0,
        "created_at": created_at,
        "stops": [s.dict() for s in stop_items],
        "cells": [c.dict() for c in cells]
    }

    # Save route JSON
    route_path = _get_route_file_path(route_id)
    with open(route_path, "w", encoding="utf-8") as f:
        json.dump(route_data, f, indent=2, ensure_ascii=False)

    # Update index
    index = _load_index()
    index["routes"].insert(0, {
        "route_id": route_id,
        "route_name": route_name,
        "route_number": route_number,
        "total_stops": len(stop_items),
        "total_cells": total_cells,
        "mapped_cells": 0,
        "pdf_filename": original_filename,
        "created_at": created_at
    })
    _save_index(index)

    return RouteDetailResponse(**route_data)


def update_cell(route_id: str, cell_id: str, patch_data: CellPatchRequest) -> RouteDetailResponse:
    route = get_route(route_id)
    route_dict = route.dict()

    target_cell = None
    for cell in route_dict["cells"]:
        if cell["cell_id"] == cell_id:
            target_cell = cell
            break

    if not target_cell:
        raise HTTPException(status_code=404, detail=f"Cell '{cell_id}' not found in route '{route_id}'.")

    if patch_data.amount is not None:
        target_cell["amount"] = patch_data.amount
    if patch_data.distance_km is not None:
        target_cell["distance_km"] = patch_data.distance_km
    if patch_data.source_box is not None:
        target_cell["source_box"] = patch_data.source_box.dict()
    if patch_data.destination_box is not None:
        target_cell["destination_box"] = patch_data.destination_box.dict()
    if patch_data.fare_box is not None:
        target_cell["fare_box"] = patch_data.fare_box.dict()

    # Determine mapped status
    target_cell["is_mapped"] = (
        target_cell["amount"] is not None and 
        target_cell["fare_box"] is not None
    )

    # Recompute mapped count
    mapped_count = sum(1 for c in route_dict["cells"] if c.get("is_mapped"))
    route_dict["mapped_cells"] = mapped_count

    # Save route JSON
    route_path = _get_route_file_path(route_id)
    with open(route_path, "w", encoding="utf-8") as f:
        json.dump(route_dict, f, indent=2, ensure_ascii=False)

    # Update index
    index = _load_index()
    for r in index.get("routes", []):
        if r["route_id"] == route_id:
            r["mapped_cells"] = mapped_count
            break
    _save_index(index)

    return RouteDetailResponse(**route_dict)


def batch_update_matrix(route_id: str, batch_req: BatchMatrixUpdateRequest) -> RouteDetailResponse:
    route = get_route(route_id)
    route_dict = route.dict()

    incoming_map = {c.cell_id: c for c in batch_req.cells}

    for cell in route_dict["cells"]:
        cid = cell["cell_id"]
        if cid in incoming_map:
            updated = incoming_map[cid]
            cell["amount"] = updated.amount
            cell["distance_km"] = updated.distance_km
            cell["source_box"] = updated.source_box.dict() if updated.source_box else None
            cell["destination_box"] = updated.destination_box.dict() if updated.destination_box else None
            cell["fare_box"] = updated.fare_box.dict() if updated.fare_box else None
            cell["is_mapped"] = (cell["amount"] is not None and cell["fare_box"] is not None)

    mapped_count = sum(1 for c in route_dict["cells"] if c.get("is_mapped"))
    route_dict["mapped_cells"] = mapped_count

    route_path = _get_route_file_path(route_id)
    with open(route_path, "w", encoding="utf-8") as f:
        json.dump(route_dict, f, indent=2, ensure_ascii=False)

    index = _load_index()
    for r in index.get("routes", []):
        if r["route_id"] == route_id:
            r["mapped_cells"] = mapped_count
            break
    _save_index(index)

    return RouteDetailResponse(**route_dict)


def delete_route(route_id: str) -> bool:
    route_path = _get_route_file_path(route_id)
    pdf_path = _get_pdf_file_path(route_id)

    if os.path.exists(route_path):
        os.remove(route_path)
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    index = _load_index()
    index["routes"] = [r for r in index.get("routes", []) if r["route_id"] != route_id]
    _save_index(index)
    return True


def get_route_page_image(route_id: str, page_num: int = 0, zoom: float = 2.0) -> bytes:
    pdf_path = _get_pdf_file_path(route_id)
    # Check fallback in split/ if chart not in charts/
    if not os.path.exists(pdf_path):
        fallback_path = os.path.join(PROJECT_ROOT, "split", "chartfare.pdf")
        if os.path.exists(fallback_path):
            pdf_path = fallback_path
        else:
            raise HTTPException(status_code=404, detail=f"PDF for route '{route_id}' not found.")

    doc = fitz.open(pdf_path)
    if page_num >= len(doc):
        raise HTTPException(status_code=400, detail="Invalid page number.")

    page = doc.load_page(page_num)
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    return pix.tobytes("png")


def render_cell_preview(route_id: str, cell_id: str, page_num: int = 0, zoom: float = 2.0) -> bytes:
    route = get_route(route_id)
    cell = next((c for c in route.cells if c.cell_id == cell_id), None)
    if not cell:
        raise HTTPException(status_code=404, detail=f"Cell '{cell_id}' not found.")

    img_bytes = get_route_page_image(route_id, page_num, zoom)
    img = Image.open(io.BytesIO(img_bytes))
    draw = ImageDraw.Draw(img)

    def draw_box(box: Optional[BoundingBox], outline="blue", width=3):
        if not box:
            return
        draw.rectangle(
            [box.x, box.y, box.x + box.width, box.y + box.height],
            outline=outline,
            width=width
        )

    # Highlight source & destination in blue, fare cell in red
    draw_box(cell.source_box, outline="#2563eb", width=3)
    draw_box(cell.destination_box, outline="#2563eb", width=3)
    draw_box(cell.fare_box, outline="#ef4444", width=4)

    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output.read()
