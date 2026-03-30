import cv2
import numpy as np
import pytesseract
import pandas as pd
from PIL import Image
from img_preprocessor import preprocess


def has_table(gray, w_img):
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 31, 15)
    h_len = max(40, w_img // 10)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_len, 1))
    horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    return cv2.countNonZero(horizontal_lines) > (w_img * 5)


def detect_and_extract_tables(pil_image):
    img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    scale = 2.0
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    h_img, w_img = gray.shape

    # Early exit if no table detected
    if not has_table(gray, w_img):
        return []

    # DETECT TABLE LINES
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 31, 15)

    h_len = max(40, w_img // 10)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_len, 1))
    horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)

    v_len = max(20, h_img // 20)
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_len))
    vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)

    table_grid = cv2.add(horizontal_lines, vertical_lines)

    dilate_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    table_grid = cv2.dilate(table_grid, dilate_kernel, iterations=1)

    # FIND TABLE BOUNDING BOXES
    contours, _ = cv2.findContours(table_grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    tables_text = []
    min_table_area = (w_img * h_img) * 0.01

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        if w * h < min_table_area:
            continue
        if w < w_img * 0.2 or h < 30:
            continue

        # EXTRACT CELLS
        table_region = table_grid[y:y+h, x:x+w]
        img_region = img[y:y+h, x:x+w]

        cell_contours, _ = cv2.findContours(
            table_region, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )

        min_cell_w = max(20, int(w * 0.02))
        min_cell_h = 15

        cells = []
        for cc in cell_contours:
            cx, cy, cw, ch = cv2.boundingRect(cc)
            if (cw >= min_cell_w and
                ch >= min_cell_h and
                cw < w * 0.95 and
                ch < h * 0.95):
                cells.append((cx, cy, cw, ch))

        if len(cells) < 2:
            continue

        # GROUP CELLS INTO ROWS
        cells.sort(key=lambda c: c[1])

        avg_cell_h = sum(c[3] for c in cells) / len(cells)
        row_tolerance = avg_cell_h * 0.5

        rows = []
        current_row = [cells[0]]

        for cell in cells[1:]:
            if abs(cell[1] - current_row[0][1]) <= row_tolerance:
                current_row.append(cell)
            else:
                rows.append(sorted(current_row, key=lambda c: c[0]))
                current_row = [cell]
        rows.append(sorted(current_row, key=lambda c: c[0]))

        if len(rows) < 2:
            continue

        # OCR EACH CELL
        table_data = []
        for row in rows:
            row_data = []
            for (cx, cy, cw, ch) in row:
                pad = 4
                cell_img = img_region[
                    max(0, cy + pad): min(img_region.shape[0], cy + ch - pad),
                    max(0, cx + pad): min(img_region.shape[1], cx + cw - pad)
                ]

                if cell_img.size == 0:
                    row_data.append("")
                    continue

                cell_pil = Image.fromarray(cv2.cvtColor(cell_img, cv2.COLOR_BGR2RGB))
                cell_processed = preprocess(cell_pil)
                config = r"--psm 7 --oem 3"
                cell_text = pytesseract.image_to_string(
                    cell_processed, lang="eng+hin", config=config
                ).strip()
                row_data.append(cell_text)

            if any(cell.strip() for cell in row_data):
                table_data.append(row_data)

        if not table_data:
            continue

        # FORMAT WITH PANDAS
        max_cols = max(len(row) for row in table_data)
        for row in table_data:
            while len(row) < max_cols:
                row.append("")

        df = pd.DataFrame(table_data)
        tables_text.append(df.to_string(index=False, header=False))

    return tables_text