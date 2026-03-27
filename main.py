import os
from PIL import Image
from config import input_dir, output_dir, supported_formats
from img_preprocessor import preprocess, extract_text, is_hindi
from clean_text import clean_text
from file_handling import load_file, crop_header
from extract import detect_and_extract_tables


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

        # Quick English pass first to detect language cheaply
        quick      = preprocess(pil_image, hindi=False)
        quick_text = extract_text(quick, hindi=False)
        hindi      = is_hindi(quick_text)

        if hindi:
            print(f"     Hindi detected — re-processing with Hindi settings")
            processed = preprocess(pil_image, hindi=True)
            raw_text  = extract_text(processed, hindi=True)
        else:
            processed = quick
            raw_text  = quick_text

        text = clean_text(raw_text)

        page_content = text
        if tables:
            page_content += "\n\n--- TABLES ---\n\n"
            page_content += "\n\n".join(tables)

        all_text.append(f"--- Page {i + 1} ---\n{page_content}")

    final_text = "\n\n".join(all_text)
    output_path = os.path.join(output_dir, f"{name_without_ext}.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_text)
    print(f"  ✓ Saved: {output_path}")


if __name__ == "__main__":
    os.makedirs(output_dir, exist_ok=True)

    all_files = [
        os.path.join(input_dir, f)
        for f in sorted(os.listdir(input_dir))
        if os.path.splitext(f)[1].lower() in supported_formats
    ]

    if not all_files:
        print("No supported files found in inputs folder.")
    else:
        print(f"Found {len(all_files)} file(s) to process.")
        for filepath in all_files:
            process_file(filepath)