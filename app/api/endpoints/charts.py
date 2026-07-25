from fastapi import APIRouter

router = APIRouter()

@router.get("/{route_id}")
def get_chart(route_id: int):
    """
    Retrieve the official BTRC/government fare chart metadata for a specific route.
    """
    return {
        "route_id": route_id,
        "chart_image_url": f"https://example.com/charts/route_{route_id}.png",
        "description": "Official BRTA approved fare chart."
    }
