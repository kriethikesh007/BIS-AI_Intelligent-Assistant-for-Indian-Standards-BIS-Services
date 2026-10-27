import re
import string

def clean_text(text: str) -> str:
    """Basic text normalization, lowercasing, punctuation stripping, and whitespace collapse."""
    if not text:
        return ""
    text = text.lower().strip()
    # Normalize unicode spaces and hyphens
    text = re.sub(r'[\r\n\t]+', ' ', text)
    # Remove excessive punctuation but retain hyphens/digits for standard references like IS 14543
    text = re.sub(r'[^\w\s\-\:]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_standard_code(text: str) -> str | None:
    """Extract standard patterns like IS 14543, आईएस 4151, ஐஎஸ் 4151, IS10500, IS 15820:2009."""
    if not text:
        return None
    match = re.search(r'\b(?:(?:IS|आईएस|ஐஎஸ்)\s*[:\-\s]?\s*(\d{2,6}(?:\s*:\s*\d{4})?))\b', text, re.IGNORECASE)
    if match:
        digit_part = match.group(1).strip()
        return f"IS {digit_part}"
    match_digits = re.search(r'\b(?:standard|मानक|தரநிலை)\s*[:\-\s]?\s*(\d{3,5})\b', text, re.IGNORECASE)
    if match_digits:
        return f"IS {match_digits.group(1).strip()}"
    return None

