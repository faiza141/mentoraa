import re

# clean text
UNWANTED_PHRASES = [
    "Gautam Buddha University",
    "Greater Noida, U.P.",
    "Greater Noida",
    "Notice",
    "confidential",
    "draft",
]

def find_end_index(lines):
    total = len(lines)
    min_line = int(total * 0.30)

    for i, line in enumerate(lines):
        if i < min_line:
            continue

        stripped = line.strip()

        # Dr. / डा० signature marker
        if re.search(r"(\(Dr\.|\(डा०|\(डा0)", stripped, re.IGNORECASE):
            end_index = i
            for j in range(i - 1, max(i - 4, -1), -1):
                prev = lines[j].strip()
                if not prev:
                    continue
                if len(prev) < 10 and not prev[0].isdigit():
                    end_index = j
                break
            return end_index

        # Designation line without Dr. prefix
        if re.search(r"(Chairperson|नोडल\s+अधिकारी|In-Charge|Prof\.|Finance\s+Officer|Hostel\s+Warden|कुलसचिव|निदेशक)", stripped):
            for j in range(i - 1, max(i - 5, -1), -1):
                prev = lines[j].strip()
                if not prev:
                    continue
                if len(prev) < 50 and not re.search(r"(must|shall|are|were|will|है|हैं|करना|होगा|अनिवार्य)", prev):
                    return j
                else:
                    return i
                break

        # English distribution list
        if re.match(r"(?i)c[o0]py\s*t[o0]\s*[:\-]?", stripped):
            return i

        # Hindi distribution list — प्रतिलिपि
        if re.match(r"(प्रतिलिपि|प्रति\s*[:\-])", stripped):
            return i

        # Hindi bullet distribution list — ०.
        if re.match(r"^[०o0]\s*[\.\-]", stripped):
            return i

    return total


def clean_text(text):

    lines = text.splitlines()
    end_index = find_end_index(lines)
    lines = lines[:end_index]
    text = "\n".join(lines)
    
    for phrase in UNWANTED_PHRASES:
        text = re.sub(re.escape(phrase), "", text, flags=re.IGNORECASE)

    text = re.sub(r"[^\x20-\x7E\u0900-\u097F\n]", "", text) # Remove non-ASCII and non-Devanagari characters

    cleaned_lines = []
    for line in text.splitlines():
        if len(line.strip()) == 0:
            cleaned_lines.append(line)
            continue
        letter_ratio = sum(c.isalpha() for c in line) / len(line)
        if letter_ratio >= 0.4:
            cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

