from pydantic import BaseModel
from typing import Dict

class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int

class ChartMapping(BaseModel):
    # A mapping of Stop Name -> BoundingBox
    stops: Dict[str, BoundingBox]
    
    # A mapping of "Source_Destination" -> BoundingBox (representing the fare cell)
    # E.g., "StopA_StopB": {"x": 100, "y": 200, "width": 50, "height": 20}
    fares: Dict[str, BoundingBox]
