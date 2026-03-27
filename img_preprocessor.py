import cv2
import numpy as np
import pytesseract
from PIL import Image
from config import TESSERACT_PATH

# Set Tesseract path on Windows
if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ── Language detection ─────────────────────────────────────────
# Returns True if the text is dominantly Hindi/Devanagari.
# Called on a quick English-only OCR pass first (cheap),
# then we re-preprocess with Hindi settings if needed.
def is_hindi(text: str) -> bool:
    devanagari = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    latin      = sum(1 for c in text if c.isalpha() and c.isascii())
    return devanagari > latin * 0.4


# ── Preprocessing ──────────────────────────────────────────────
# hindi=False  →  English settings  (scale 2.0, blockSize 25, C 10)
# hindi=True   →  Hindi settings    (scale 2.5, blockSize 15, C  8)
#
# Devanagari strokes are thinner so a smaller blockSize preserves
# them better under adaptive thresholding, and a higher scale
# gives Tesseract more pixels per character.
#
# NO sharpening kernel — creates artefacts on clean scans.
# NO deskew           — GBU docs are straight; deskew was
#                       computing angles from noise and randomly
#                       rotating clean pages.
def preprocess(pil_image, hindi: bool = False):
    cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    gray     = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

    h, w  = gray.shape
    scale = 2.5 if hindi else 2.0
    if w < 1800:   # don't upscale 300-dpi PDFs that are already large
        gray = cv2.resize(gray, None, fx=scale, fy=scale,
                          interpolation=cv2.INTER_CUBIC)

    # h=8 preserves fine Devanagari strokes; h=10 is fine for English
    denoised = cv2.fastNlMeansDenoising(gray, h=8 if hindi else 10)

    thresh = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=15 if hindi else 25,
        C=8 if hindi else 10,
    )
    return thresh


# ── OCR ────────────────────────────────────────────────────────
def extract_text(processed_image, hindi: bool = False) -> str:
    lang   = "eng+hin" if hindi else "eng"
    config = r"--psm 6 --oem 3"
    return pytesseract.image_to_string(
        processed_image, lang=lang, config=config
    ).strip()