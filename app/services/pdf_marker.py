import fitz  # PyMuPDF
from PIL import Image, ImageDraw
import io
import os
import json
from app.schemas.chart_poc import ChartMapping

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PDF_PATH = os.path.join(BASE_DIR, "split", "chartfare.pdf")
JSON_PATH = os.path.join(BASE_DIR, "data", "chart_coordinates.json")

def load_coordinates() -> ChartMapping:
    """
    Loads and validates the hardcoded coordinates from JSON.
    """
    with open(JSON_PATH, 'r') as f:
        data = json.load(f)
    return ChartMapping(**data)

def generate_marked_chart(source: str, destination: str) -> io.BytesIO:
    """
    Loads the PDF, converts the first page to an image, draws rectangles 
    around the source, destination, and fare cell based on coordinates, 
    and returns the image bytes.
    """
    if not os.path.exists(PDF_PATH):
        raise FileNotFoundError(f"PDF not found at {PDF_PATH}")
        
    mapping = load_coordinates()
    
    # 1. Convert PDF to Image
    doc = fitz.open(PDF_PATH)
    page = doc.load_page(0) # First page only for POC
    
    # Use the exact same zoom factor as the coordinate picker tool (2.0)
    # so the coordinates match perfectly.
    zoom = 2.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    img_data = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_data))
    
    # 2. Draw Rectangles
    draw = ImageDraw.Draw(img)
    
    # Helper to draw a red rectangle with outline thickness
    def draw_box(box_data, outline_color="red", width=3):
        if not box_data: return
        x, y, w, h = box_data.x, box_data.y, box_data.width, box_data.height
        draw.rectangle([x, y, x + w, y + h], outline=outline_color, width=width)
        
    # Get the bounding boxes from our mapping schema
    source_box = mapping.stops.get(source)
    dest_box = mapping.stops.get(destination)
    
    # Assumes key format like "StopA_StopB" or "StopB_StopA"
    fare_key_1 = f"{source}_{destination}"
    fare_key_2 = f"{destination}_{source}"
    fare_box = mapping.fares.get(fare_key_1) or mapping.fares.get(fare_key_2)
    
    # Draw them
    draw_box(source_box, outline_color="blue")
    draw_box(dest_box, outline_color="blue")
    draw_box(fare_box, outline_color="red", width=5)
    
    # 3. Save to a byte buffer to return via API
    output_buffer = io.BytesIO()
    img.save(output_buffer, format="JPEG")
    output_buffer.seek(0)
    
    return output_buffer
