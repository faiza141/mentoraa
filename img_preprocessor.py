import cv2
import numpy as np
import pytesseract
from PIL import Image 
from config import TESSERACT_PATH

if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# constants
_SCALE         = 2.0
_SHARPEN_KERNEL = np.array([[0, -1, 0],
                             [-1, 5, -1],
                             [0, -1, 0]])

# grayscaling
def _to_gray(pil_image: Image.Image) -> np.ndarray:
    bgr  = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

# deskew the image
def _deskew(gray: np.ndarray) -> np.ndarray:
    coords = np.column_stack(np.where(gray > 0))
    if len(coords) == 0:
        return gray
 
    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle
 
    h, w   = gray.shape[:2]
    matrix = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(gray, matrix, (w, h),  flags=cv2.INTER_CUBIC,  borderMode=cv2.BORDER_REPLICATE)

# preprocessing
def preprocess(pil_image: Image.Image) -> np.ndarray:

    gray = _to_gray(pil_image)
    gray = cv2.resize(gray, None, fx=_SCALE, fy=_SCALE,  interpolation=cv2.INTER_CUBIC)
    gray = cv2.filter2D(gray, -1, _SHARPEN_KERNEL)
    gray = cv2.fastNlMeansDenoising(gray, h=20)
    gray = _deskew(gray)

    return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize=31, C=15)


# text extraction - OCR
def extract_text(processed_image):
    text = pytesseract.image_to_string(processed_image, lang="eng+hin", config= r"--psm 6 --oem 3")
    return text.strip()
