from fastapi import APIRouter, HTTPException, Response
import fitz # PyMuPDF
import os

router = APIRouter()

@router.get("/highlighted")
def get_highlighted_chart(x: int, y: int, w: int, h: int, page_num: int = 0):
    """
    Returns the fare chart image with a red highlight box at the specified coordinates.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    pdf_path = os.path.join(project_root, "split", "chartfare.pdf")
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Chart PDF not found")
        
    doc = fitz.open(pdf_path)
    if page_num >= len(doc):
        raise HTTPException(status_code=400, detail="Invalid page number")
        
    page = doc.load_page(page_num)
    
    # Draw a semi-transparent red rectangle
    rect = fitz.Rect(x, y, x + w, y + h)
    
    annot = page.add_rect_annot(rect)
    annot.set_colors(stroke=(1, 0, 0), fill=(1, 0, 0)) # Red
    annot.set_opacity(0.3) # Semi-transparent
    annot.update()
    
    # Render to image (using zoom = 2.0 as done in the picker for clarity)
    zoom = 2.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    # Return as PNG response
    img_bytes = pix.tobytes("png")
    
    return Response(content=img_bytes, media_type="image/png")

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

