import os
import re
import json
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
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


def _get_bangla_font(size: int = 18):
    font_paths = [
        "C:/Windows/Fonts/NirmalaB.ttf",
        "C:/Windows/Fonts/Nirmala.ttf",
        "C:/Windows/Fonts/vrinda.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_dashed_line(draw: ImageDraw.ImageDraw, pt1: tuple, pt2: tuple, color="#2563eb", width=3, dash_len=10, space_len=6):
    x1, y1 = pt1
    x2, y2 = pt2
    dist = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
    if dist == 0:
        return
    dx = (x2 - x1) / dist
    dy = (y2 - y1) / dist
    
    curr = 0
    while curr < dist:
        start_x = x1 + dx * curr
        start_y = y1 + dy * curr
        end_curr = min(curr + dash_len, dist)
        end_x = x1 + dx * end_curr
        end_y = y1 + dy * end_curr
        draw.line([(start_x, start_y), (end_x, end_y)], fill=color, width=width)
        curr += dash_len + space_len


def render_cell_preview(route_id: str, cell_id: str, page_num: int = 0, zoom: float = 2.0) -> bytes:
    route = get_route(route_id)
    cell = next((c for c in route.cells if c.cell_id == cell_id), None)
    if not cell:
        raise HTTPException(status_code=404, detail=f"Cell '{cell_id}' not found.")

    img_bytes = get_route_page_image(route_id, page_num, zoom)
    img = Image.open(io.BytesIO(img_bytes))
    draw = ImageDraw.Draw(img)

    # 1. Calculate centers of boxes
    src_pt = None
    dest_pt = None
    fare_pt = None

    if cell.source_box:
        src_pt = (
            cell.source_box.x + cell.source_box.width // 2,
            cell.source_box.y + cell.source_box.height // 2
        )
    if cell.destination_box:
        dest_pt = (
            cell.destination_box.x + cell.destination_box.width // 2,
            cell.destination_box.y + cell.destination_box.height // 2
        )
    if cell.fare_box:
        fare_pt = (
            cell.fare_box.x + cell.fare_box.width // 2,
            cell.fare_box.y + cell.fare_box.height // 2
        )

    # 2. Draw Dashed Connecting Line (- - - -) ONLY between Source Stop and Destination Stop
    if src_pt and dest_pt:
        _draw_dashed_line(draw, src_pt, dest_pt, color="#2563eb", width=3, dash_len=10, space_len=6)
        draw.ellipse([src_pt[0]-4, src_pt[1]-4, src_pt[0]+4, src_pt[1]+4], fill="#2563eb")
        draw.ellipse([dest_pt[0]-4, dest_pt[1]-4, dest_pt[0]+4, dest_pt[1]+4], fill="#0284c7")

    # 3. Draw Bounding Boxes
    def draw_box(box: Optional[BoundingBox], outline="blue", width=3):
        if not box:
            return
        draw.rectangle(
            [box.x, box.y, box.x + box.width, box.y + box.height],
            outline=outline,
            width=width
        )

    draw_box(cell.source_box, outline="#2563eb", width=3)
    draw_box(cell.destination_box, outline="#0284c7", width=3)
    draw_box(cell.fare_box, outline="#ef4444", width=4)

    # 4. Draw Static Bangla Word + Dynamic Fare Badge: "এই গন্তব্যস্থলের ভাড়া: ৳ [fare]"
    if cell.fare_box:
        fare_val = cell.amount
        if fare_val is not None:
            fare_str = f"{int(fare_val)}" if float(fare_val).is_integer() else f"{fare_val:.2f}"
            badge_text = f"এই গন্তব্যস্থলের ভাড়া: ৳ {fare_str}"
        else:
            badge_text = "এই গন্তব্যস্থলের ভাড়া"

        font = _get_bangla_font(size=max(16, int(18 * (zoom / 2.0))))

        try:
            bbox = draw.textbbox((0, 0), badge_text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except Exception:
            text_w = len(badge_text) * 10
            text_h = 20

        pad_x = 10
        pad_y = 6
        badge_w = text_w + pad_x * 2
        badge_h = text_h + pad_y * 2

        # Position above or below fare box
        badge_x = cell.fare_box.x + (cell.fare_box.width - badge_w) // 2
        badge_x = max(10, min(badge_x, img.width - badge_w - 10))

        if cell.fare_box.y >= badge_h + 10:
            badge_y = cell.fare_box.y - badge_h - 8
        else:
            badge_y = cell.fare_box.y + cell.fare_box.height + 8

        # Draw badge background
        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
            radius=6,
            fill="#0f172a",
            outline="#ef4444",
            width=2
        )

        # Draw Bangla badge text
        draw.text(
            (badge_x + pad_x, badge_y + pad_y - 2),
            badge_text,
            font=font,
            fill="#ffffff"
        )

    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output.read()

