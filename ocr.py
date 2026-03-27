import easyocr
import numpy as np

# Initialize once at module level
ocr_engine = easyocr.Reader(
    ['en'],
    gpu=True  # Colab has free GPU — use it
)

def extract_text(processed_image):
    # EasyOCR expects numpy array
    if not isinstance(processed_image, np.ndarray):
        processed_image = np.array(processed_image)

    result = ocr_engine.readtext(
        processed_image,
        detail=0,          # return text only, no bounding boxes
        paragraph=True,    # merge nearby text into paragraphs
        confidence_threshold=0.6  # skip low confidence results
    )

    return "\n".join(result)