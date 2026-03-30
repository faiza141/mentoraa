import os
from PIL import Image

from config import INPUT_DIR, OUTPUT_DIR, supported_formats
from img_preprocessor import preprocess, extract_text, detect_language
from clean_text import clean_text
from file_handling import load_file, crop_header
from extract import detect_and_extract_tables
from translate import translate_to_english


def process_file(filepath):
    filename         = os.path.basename(filepath)
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

        # Detect language once using smart crop (reliable on Hindi docs)
        hindi = detect_language(pil_image)
        print(f"     Language: {'Hindi' if hindi else 'English'}")

        processed = preprocess(pil_image, hindi=hindi)
        raw_text  = extract_text(processed, hindi=hindi)
        text      = clean_text(raw_text)

        if hindi:
            print(f"     Translating to English...")
            text = translate_to_english(text)

        page_content = text
        if tables:
            page_content += "\n\n--- TABLES ---\n\n"
            page_content += "\n\n".join(tables)

        all_text.append(f"--- Page {i + 1} ---\n{page_content}")

    final_text  = "\n\n".join(all_text)
    output_path = os.path.join(OUTPUT_DIR, f"{name_without_ext}.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_text)
    print(f"  ✓ Saved: {output_path}")


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_files = [
        os.path.join(INPUT_DIR, f)
        for f in sorted(os.listdir(INPUT_DIR))
        if os.path.splitext(f)[1].lower() in supported_formats
    ]

    if not all_files:
        print("No supported files found in inputs folder.")
    else:
        print(f"Found {len(all_files)} file(s) to process.")
        for filepath in all_files:
            process_file(filepath)
