import os
import platform

# path definitions
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR  = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

IS_WINDOWS = platform.system() == "Windows"
 
POPPLER_PATH   = r"C:\poppler-25.12.0\Library\bin" if IS_WINDOWS else None
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe" if IS_WINDOWS else None


# supported formats
supported_formats = {'.pdf', '.jpg', '.jpeg', '.png'}
