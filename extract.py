import cv2
import numpy as np
import pytesseract
import pandas as pd
from PIL import Image

from img_preprocessor import preprocess
from ocr import extract_cell_text 

# constants
_SCALE           = 2.0
_OCR_CONFIG      = r"--psm 7 --oem 3"
_OCR_LANG        = "eng+hin"
_MIN_TABLE_AREA  = 0.01   
_MIN_TABLE_WIDTH = 0.20  
_MIN_TABLE_HEIGHT = 30   

# image preprocessing
def _upscale(image: np.ndarray) -> np.ndarray:
    return cv2.resize(image, None, fx=_SCALE, fy=_SCALE,  interpolation=cv2.INTER_CUBIC)
 
 
def _to_bgr(pil_image: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
 
 
def _to_gray(bgr: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
 
 
def _adaptive_thresh(gray: np.ndarray) -> np.ndarray:
    return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 15)


# detect tables 
def has_table(gray, w_img):
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 31, 15)
    h_len = max(40, w_img // 10)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_len, 1))
    horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    return cv2.countNonZero(horizontal_lines) > (w_img * 5)

# detect table lines
def _build_table_grid(thresh: np.ndarray, w_img: int, h_img: int) -> np.ndarray:
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(40, w_img // 10), 1))
    h_lines  = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel, iterations=2)
 
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(20, h_img // 20)))
    v_lines  = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel, iterations=2)
 
    grid = cv2.add(h_lines, v_lines)
    dilate_k = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    return cv2.dilate(grid, dilate_k, iterations=1)

# group cells into rows
def _group_cells_into_rows(
    cells: list[tuple[int, int, int, int]]
) -> list[list[tuple[int, int, int, int]]]:
    """Sort cells top-to-bottom, then bucket into rows by Y proximity."""
    cells.sort(key=lambda c: c[1])
    avg_h     = sum(c[3] for c in cells) / len(cells)
    tolerance = avg_h * 0.5
 
    rows: list[list] = [[cells[0]]]
    for cell in cells[1:]:
        if abs(cell[1] - rows[-1][0][1]) <= tolerance:
            rows[-1].append(cell)
        else:
            rows[-1].sort(key=lambda c: c[0])   # sort each row left-to-right
            rows.append([cell])
    rows[-1].sort(key=lambda c: c[0])
    return rows

# OCR each cell 
def _ocr_cell(cell_img_bgr: np.ndarray) -> str:
    if cell_img_bgr.size == 0:
        return ""
    cell_pil       = Image.fromarray(cv2.cvtColor(cell_img_bgr, cv2.COLOR_BGR2RGB))
    cell_processed = preprocess(cell_pil)
    return extract_cell_text(cell_processed)

# main function to detect and extract tables
def detect_and_extract_tables(pil_image):
    bgr  = _upscale(_to_bgr(pil_image))
    gray = _upscale(_to_gray(_to_bgr(pil_image)))   # independent upscale for gray
    h_img, w_img = gray.shape

    # Early exit if no table detected
    if not has_table(gray, w_img):
        return []

    thresh     = _adaptive_thresh(gray)
    grid       = _build_table_grid(thresh, w_img, h_img)
    table_mask = np.zeros_like(gray)

    # FIND TABLE BOUNDING BOXES
    contours, _ = cv2.findContours(grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    tables_text = []
    min_table_area = (w_img * h_img) * _MIN_TABLE_AREA

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        if w * h < min_table_area:
            continue
        if w < w_img * _MIN_TABLE_WIDTH or h < _MIN_TABLE_HEIGHT:
            continue

        # MASK THE TABLE AREA
        table_mask[y:y+h, x:x+w] = 255

        # EXTRACT CELLS
        table_region = grid[y:y+h, x:x+w]
        img_region = bgr[y:y+h, x:x+w]

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
        rows = _group_cells_into_rows(cells)
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

                row_data.append(_ocr_cell(cell_img))

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

    return tables_text, table_mask if tables_text else []