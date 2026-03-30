import cv2
import numpy as np
import pytesseract
from PIL import Image
from config import TESSERACT_PATH

if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def is_hindi(text: str) -> bool:
    devanagari = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    latin      = sum(1 for c in text if c.isalpha() and c.isascii())
    return devanagari > latin * 0.4


def preprocess(pil_image, hindi: bool = False):
    cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    gray     = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

    h, w  = gray.shape
    scale = 2.5 if hindi else 2.0
    if w < 1800:
        gray = cv2.resize(gray, None, fx=scale, fy=scale,
                          interpolation=cv2.INTER_CUBIC)

    denoised = cv2.fastNlMeansDenoising(gray, h=8 if hindi else 10)

    thresh = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=15 if hindi else 25,
        C=8 if hindi else 10,
    )
    return thresh


def extract_text(processed_image, hindi: bool = False) -> str:
    lang   = "eng+hin" if hindi else "eng"
    config = r"--psm 6 --oem 3"
    return pytesseract.image_to_string(
        processed_image, lang=lang, config=config
    ).strip()


# FIX: detect language by running a FAST hindi OCR pass on a small
# crop of the image — much more reliable than checking garbled English output
def detect_language(pil_image) -> bool:
    """Returns True if image is predominantly Hindi/Devanagari."""
    # Crop center strip of the image (most content, skip header/footer)
    w, h   = pil_image.size
    crop   = pil_image.crop((0, int(h * 0.2), w, int(h * 0.6)))

    # Small quick preprocess
    cv_img   = cv2.cvtColor(np.array(crop), cv2.COLOR_RGB2BGR)
    gray     = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    gray     = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Quick OCR with Hindi
    quick = pytesseract.image_to_string(thresh, lang="eng+hin", config="--psm 6 --oem 3")
    return is_hindi(quick)
