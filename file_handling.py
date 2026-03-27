import os
from PIL import Image
from pdf2image import convert_from_path
from config import poppler_path, supported_formats

# load files
def load_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()

    if ext == '.pdf':
        images = convert_from_path(filepath, dpi=300, poppler_path=poppler_path)
        return images
    else:
        image = Image.open(filepath)
        return [image]
    
# crop header    
def crop_header(pil_image):
    width, height = pil_image.size
    top_crop = int(height * 0.20)
    return pil_image.crop((0, top_crop, width, height))