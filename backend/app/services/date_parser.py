import re
from datetime import datetime, timezone
from dateutil import parser as dateutil_parser

def parse_date(date_str: str) -> dict:
    """
    Parses a date string and normalizes it to UTC datetime.
    Returns a dict with 'original', 'parsed', 'ambiguous', 'confidence'.
    """
    if not date_str or not isinstance(date_str, str):
        return None
        
    date_str = date_str.strip()
    if not date_str:
        return None
        
    # Handle known explicit "N/A" or empty cases
    if date_str.upper() in ["N/A", "NONE", "TBD", "UNKNOWN"]:
        return None

    ambiguous = False
    confidence = 0.9
    parsed_dt = None

    try:
        # Check if it looks like just a year
        if re.match(r'^\d{4}$', date_str):
            parsed_dt = datetime(int(date_str), 1, 1, tzinfo=timezone.utc)
            ambiguous = True
            confidence = 0.5
        # Check if it looks like Month Year (e.g. "Oct 2023" or "10/2023")
        elif re.match(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}$', date_str, re.IGNORECASE) or re.match(r'^\d{1,2}/\d{4}$', date_str):
            parsed_dt = dateutil_parser.parse(date_str, fuzzy=True)
            if parsed_dt.tzinfo is None:
                parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
            ambiguous = True
            confidence = 0.7
        else:
            # Try standard parsing
            parsed_dt = dateutil_parser.parse(date_str, fuzzy=True)
            if parsed_dt.tzinfo is None:
                parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
            confidence = 0.95
    except Exception:
        # Failed to parse
        return None
        
    return {
        "original": date_str,
        "parsed": parsed_dt,
        "ambiguous": ambiguous,
        "confidence": confidence
    }
