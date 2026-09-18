import glob
import json
import os
from typing import Optional
from app.schemas.fare import FareResponse, ChartCoordinates
from fastapi import HTTPException

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
ROUTES_DIR = os.path.join(PROJECT_ROOT, "data", "routes")


def _normalize(text: str) -> str:
    return text.lower().replace("-", " ").replace("_", " ").strip()


def calculate_fare(source: str, destination: str, route_name: Optional[str] = None) -> FareResponse:
    """
    Search for mapped fare between source and destination across all stored route JSON files.
    """
    if not os.path.exists(ROUTES_DIR):
        raise HTTPException(status_code=404, detail="No route data found in data/routes/.")

    norm_src = _normalize(source)
    norm_dest = _normalize(destination)

    # Find all route JSON files (excluding index.json)
    route_files = [
        f for f in glob.glob(os.path.join(ROUTES_DIR, "*.json"))
        if not f.endswith("index.json")
    ]

    for file_path in route_files:
        with open(file_path, "r", encoding="utf-8") as f:
            route_data = json.load(f)

        # Optional route_name filter
        if route_name and _normalize(route_name) not in _normalize(route_data.get("route_name", "")):
            continue

        route_id = route_data.get("route_id")

        for cell in route_data.get("cells", []):
            c_src = _normalize(cell.get("source_name", ""))
            c_dest = _normalize(cell.get("destination_name", ""))

            # Direct or reverse match
            direct_match = (norm_src in c_src or c_src in norm_src) and (norm_dest in c_dest or c_dest in norm_dest)
            reverse_match = (norm_dest in c_src or c_src in norm_dest) and (norm_src in c_dest or c_dest in norm_src)

            if direct_match or reverse_match:
                amount = cell.get("amount")
                if amount is None:
                    continue  # Found pair but fare not entered yet

                fare_box = cell.get("fare_box")
                chart_coords = None
                if fare_box:
                    chart_coords = ChartCoordinates(
                        x_start=fare_box["x"],
                        y_start=fare_box["y"],
                        x_end=fare_box["x"] + fare_box["width"],
                        y_end=fare_box["y"] + fare_box["height"],
                        page=0
                    )

                return FareResponse(
                    source=cell["source_name"],
                    destination=cell["destination_name"],
                    calculated_fare=round(float(amount), 2),
                    distance_km=float(cell.get("distance_km") or 0.0),
                    chart_url=f"/api/v1/admin/routes/{route_id}/preview-cell/{cell['cell_id']}",
                    highlight_coordinates=chart_coords
                )

    raise HTTPException(
        status_code=404,
        detail=f"Fare not found or not mapped yet between '{source}' and '{destination}'."
    )


if __name__ == "__main__":
    import pprint
    print("Testing calculate_fare()...")
    try:
        # Example 1: Use names that might be in your route_mapping.json
        result = calculate_fare("mirpur", "gulshan")
        print("\nResult for mirpur -> gulshan:")
        pprint.pprint(result.dict())
    except Exception as e:
        print("\nError calculating fare for mirpur -> gulshan:", e)

    try:
        # Example 2: Fallback or error case
        result2 = calculate_fare("unknown_source", "unknown_dest")
        print("\nResult for unknown_source -> unknown_dest:")
        pprint.pprint(result2.dict())
    except Exception as e:
        print("\nError calculating fare for unknown_source -> unknown_dest:", e)
