import easyocr
import numpy as np
import pytesseract

from config import TESSERACT_PATH
from PIL import Image 

# Initialize once at module level
ocr_engine = easyocr.Reader(['en'], gpu=True)
if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

_devnagri_range = range(0x0900, 0x0980)

# If hindi -> use tesseract, else use easyocr 
def _is_hindi(text :str) -> bool:
    return any(char in _devnagri_range for char in text)

def extract_cell_text(processed_image):
    # EasyOCR expects numpy array
    if not isinstance(processed_image, np.ndarray):
        processed_image = np.array(processed_image)

    text = pytesseract.image_to_string(
        processed_image, lang="eng+hin", config=r"--psm 7 --oem 3"
    ).strip()

    if _is_hindi(text):
        return text
    
    result = ocr_engine.readtext(
        processed_image,
        detail=0,          
        paragraph=False,    
        confidence_threshold=0.6  
    )

    return " ".join(result)