import re

_UNWANTED_PATTERNS = [
    r"[,;\s]*Gautam\s+Buddha?\s+University[,;\s]*",
    r"[,;\s]*Gautam\s+Budh?\s+Nagar[,;\s]*",
    r"[,;\s]*Greater\s+Noida[,;\s]*(?:,?\s*U\.?P\.?)?",
    r"[,;\s]*U\.?P\.?\s*(?=[,;\s]|$)",
    r"\bNotice\b",
    r"\bconfidential\b",
    r"\bdraft\b",
    r"\bExamination\s+Section\b",
    r"GBU[^\n]*Dated[^\n]*",
    r"जी\.बी\.यू\.[^\n]*दिनांक[^\n]*",
    r"Ph:[^\n]*Email:[^\n]*",
    r"Website:[^\n]*",
]

_SALUTATION_RE = re.compile(
    r"^(सेवा\s*में|सेवा\s*मेँ|महोदय/महोदया|महोदय|महोदया"
    r"|Dear\s+Sir|Dear\s+Madam|To\s*,?"
    r"|BAST|आपको\s+अवगत\s+कराना\s+है\s+कि"
    r")[,\.।\s]*$",
    re.IGNORECASE,
)

_OCR_NOISE_RE = re.compile(
    r"[^\x20-\x7E\u0900-\u097F\n]"
    r"|(?<!\w)[|\\@#^~`](?!\w)"
    r"|&\d+"
    r"|(?<!\w)[-:]+(?!\w)",
    re.UNICODE,
)


def find_end_index(lines):
    total    = len(lines)
    # FIX: lowered from 0.30 to 0.15 so signature is caught even after crop
    min_line = int(total * 0.15)
    for i, line in enumerate(lines):
        if i < min_line:
            continue
        stripped = line.strip()

        if re.search(r"(\(Dr\.|\(डा०|\(डा0|\(मनमोहन|\(श्री)", stripped, re.IGNORECASE):
            end_index = i
            for j in range(i - 1, max(i - 4, -1), -1):
                prev = lines[j].strip()
                if not prev:
                    continue
                if len(prev) < 10 and not prev[0].isdigit():
                    end_index = j
                break
            return end_index

        if re.search(
            r"(Chairperson|नोडल\s+अधिकारी|In-Charge|Prof\.|Finance\s+Officer"
            r"|Hostel\s+Warden|कुलसचिव|निदेशक|प्रभारी|छात्र\s+कल्याण)",
            stripped,
        ):
            for j in range(i - 1, max(i - 5, -1), -1):
                prev = lines[j].strip()
                if not prev:
                    continue
                if len(prev) < 50 and not re.search(
                    r"(must|shall|are|were|will|है|हैं|करना|होगा|अनिवार्य)", prev
                ):
                    return j
                else:
                    return i
            break

        if re.match(r"(?i)c[o0]py\s*t[o0]\s*[:\-]?", stripped):
            return i
        if re.match(r"(प्रतिलिपि|प्रतिलिपि\s*[:\-]|छाॉतलिलिपि)", stripped):
            return i
        if re.match(r"^[०o0]\s*[\.\-]", stripped):
            return i
    return total


def find_start_index(lines):
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if _SALUTATION_RE.match(stripped):
            continue
        if len(stripped) < 5:
            continue
        if re.search(r"(दिनांक|Dated|Ph:|Fax:|Email:|Website:|विश्वविद्यालय$|नगर$)", stripped):
            continue
        if len(stripped) > 0:
            letter_ratio = sum(c.isalpha() for c in stripped) / len(stripped)
            if letter_ratio < 0.4 and i < len(lines) * 0.3:
                continue
        return i
    return 0


def clean_text(text):
    lines       = text.splitlines()
    end_index   = find_end_index(lines)
    lines       = lines[:end_index]
    start_index = find_start_index(lines)
    lines       = lines[start_index:]
    text        = "\n".join(lines)

    for pattern in _UNWANTED_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    text = _OCR_NOISE_RE.sub("", text)
    text = re.sub(r"\n[-]\s+", " ", text)

    lines = []
    for line in text.splitlines():
        line = re.sub(r"[ \t]{2,}", " ", line)
        lines.append(line)
    text = "\n".join(lines)

    cleaned_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append(line)
            continue
        if len(stripped) < 3:
            continue
        letter_ratio = sum(c.isalpha() for c in line) / len(line)
        if letter_ratio >= 0.4:
            cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)

    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = []
    for line in text.splitlines():
        line = re.sub(r"^[\s,;।]+", "", line)
        line = re.sub(r"[\s,;]+$",  "", line)
        lines.append(line)
    text = "\n".join(lines)

    return text.strip()
