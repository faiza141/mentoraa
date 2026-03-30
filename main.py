import os
import numpy as np
from PIL import Image

from config import INPUT_DIR, OUTPUT_DIR, supported_formats
from img_preprocessor import preprocess, extract_text
from clean_text import clean_text
from file_handling import load_file, crop_header
from extract import detect_and_extract_tables

# File processing 
def process_file(filepath):
    filename = os.path.basename(filepath)
    name_without_ext = os.path.splitext(filename)[0]
    print(f"\nProcessing: {filename}")

    pages = load_file(filepath)
    if not pages:
        return

    all_text = []

    for i, pil_image in enumerate(pages):
        print(f"  → Page {i + 1}/{len(pages)}")

        if i == 0:
            pil_image = crop_header(pil_image)

        tables = detect_and_extract_tables(pil_image)

        processed = preprocess(pil_image)
        text = extract_text(processed)
        text = clean_text(text)

        page_content = text
        if tables:
            page_content += "\n\n--- TABLES ---\n\n"
            page_content += "\n\n".join(tables)

        all_text.append(f"--- Page {i + 1} ---\n{page_content}")

    final_text = "\n\n".join(all_text)
    output_path = os.path.join(OUTPUT_DIR, f"{name_without_ext}.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_text)
    print(f"  ✓ Saved: {output_path}")

# main execution
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_files = [
        os.path.join(INPUT_DIR, f)
        for f in os.listdir(INPUT_DIR)
        if os.path.splitext(f)[1].lower() in supported_formats
    ]

    if not all_files:
        print("No supported files found in inputs folder.")
    else:
        print(f"Found {len(all_files)} file(s) to process.")
        for filepath in all_files:
            process_file(filepath)