import fitz  # PyMuPDF
import matplotlib.pyplot as plt
from PIL import Image
import io
import os

# Path to the PDF
PDF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "split", "chartfare.pdf")

def load_pdf_page_as_image(pdf_path, page_num=0):
    """
    Loads a specific page of a PDF and converts it to a PIL Image.
    """
    print(f"Loading PDF from: {pdf_path}")
    if not os.path.exists(pdf_path):
        print("Error: PDF file not found. Please ensure it is in the 'split' folder.")
        return None

    # Open the document
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    
    # Render page to an image (pixmap)
    # zoom factor 2.0 or 3.0 gives better resolution for picking coordinates
    zoom = 2.0 
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    # Convert pixmap to PIL Image
    img_data = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_data))
    return img, zoom

def onclick(event):
    """
    Callback function to capture mouse clicks on the plot.
    """
    if event.xdata is not None and event.ydata is not None:
        # Convert matplotlib coordinates (floats) to integers
        x = int(event.xdata)
        y = int(event.ydata)
        print(f"Clicked Coordinates -> X: {x}, Y: {y}")
    else:
        print("Clicked outside the image bounds.")

def main():
    # Load the image and zoom factor
    result = load_pdf_page_as_image(PDF_PATH)
    if not result:
        return
    
    img, zoom_factor = result
    
    print(f"Image loaded with zoom factor: {zoom_factor}x")
    print("Use the toolbar at the bottom to zoom/pan.")
    print("Click anywhere on the image to print the coordinates to this console.")
    print("Close the window to exit.")

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.canvas.manager.set_window_title('SafeFare Coordinate Picker')
    
    # Display the image
    ax.imshow(img)
    ax.axis('on')  # Show axes to help with coordinate estimation visually
    
    # Connect the click event
    cid = fig.canvas.mpl_connect('button_press_event', onclick)
    
    # Show the UI
    plt.show()

if __name__ == "__main__":
    main()
