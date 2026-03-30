# translate.py
from deep_translator import GoogleTranslator

def translate_to_english(text: str) -> str:
    """Translate Hindi (or mixed) text to English. Returns original if already English."""
    if not text.strip():
        return text
    
    try:
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        return translated if translated else text
    except Exception as e:
        print(f"  ⚠ Translation failed: {e}")
        return text  # fail gracefully, return original