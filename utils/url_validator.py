import urllib.parse
import re
import logging

logger = logging.getLogger("bis_ai.utils.url_validator")

DEFAULT_BIS_PORTAL = "https://www.services.bis.gov.in"

def is_valid_url(url: str) -> bool:
    """
    Validates whether a URL has a valid HTTP/HTTPS scheme, valid host/domain, and parseable structure.
    """
    if not url or not isinstance(url, str):
        return False
    trimmed = url.strip()
    if not trimmed:
        return False
    try:
        parsed = urllib.parse.urlsplit(trimmed)
        if parsed.scheme not in ("http", "https"):
            return False
        if not parsed.netloc:
            return False
        # Domain must have at least one valid character or dot
        if not re.match(r"^[a-zA-Z0-9.-]+(?::[0-9]+)?$", parsed.netloc):
            return False
        return True
    except Exception:
        return False

def sanitize_and_validate_url(raw_url: str, fallback_url: str = DEFAULT_BIS_PORTAL) -> str:
    """
    Sanitizes and validates an HTTP/HTTPS URL:
    - Trims leading/trailing whitespace
    - Validates scheme is HTTP or HTTPS and hostname exists
    - Preserves existing legitimate percent-encoding (%20, %2F, etc.)
    - Safely converts unencoded raw spaces to %20 without deleting them
    - Preserves query parameters and fragments
    - Rejects invalid/malformed/unsafe protocols, falling back to fallback_url
    """
    if not raw_url or not isinstance(raw_url, str):
        return fallback_url
    
    trimmed = raw_url.strip()
    if not trimmed:
        return fallback_url

    # Strip HTML encoded spaces (&#x20; or &#32;) that may have been stored or passed
    trimmed = re.sub(r'&#x20;|&#32;|&nbsp;', ' ', trimmed).strip()

    # Check for unencoded spaces: encode raw spaces in path to %20 without breaking existing percent-encoding
    if " " in trimmed:
        trimmed = trimmed.replace(" ", "%20")

    try:
        parsed = urllib.parse.urlsplit(trimmed)
        if parsed.scheme.lower() not in ("http", "https"):
            logger.warning(f"Rejected non-HTTP URL scheme in '{raw_url}', using fallback.")
            return fallback_url
        if not parsed.netloc:
            logger.warning(f"Missing netloc in URL '{raw_url}', using fallback.")
            return fallback_url
        
        # Verify host structure
        if not re.match(r"^[a-zA-Z0-9.-]+(?::[0-9]+)?$", parsed.netloc):
            logger.warning(f"Invalid netloc '{parsed.netloc}' in URL '{raw_url}', using fallback.")
            return fallback_url

        # Reconstruct clean URL maintaining percent-encodings
        clean_url = urllib.parse.urlunsplit((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path,
            parsed.query,
            parsed.fragment
        ))
        return clean_url
    except Exception as e:
        logger.warning(f"Error parsing URL '{raw_url}': {e}, using fallback.")
        return fallback_url
