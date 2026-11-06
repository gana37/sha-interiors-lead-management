"""
estimate_parser.py - Automatic Estimate Date & Time Extraction and Validation
SHA Interface Interiors Lead Management System

Specifications:
- Format: 10-digit HHMMDDMMYY
  - HH: Hour (00–23, 24-hour format)
  - MM: Minute (00–59)
  - DD: Day (01–31)
  - MM: Month (01–12)
  - YY: 2-digit Year (26 -> 2026; explicit rule: 2000 + YY)
- Prefix: Optional prefix such as 'EST-' (case-insensitive) stripped prior to parsing
- Calendar Date: Full validation including leap years (e.g., Feb 29 on leap years)
- Output ISO 8601: 'YYYY-MM-DD HH:MM:SS'
- User-friendly display: '31 Oct 2026 | 11:19 PM' and '31 October 2026, 11:19 PM'
"""

import re
import datetime
from typing import Optional, Tuple, Dict, Any, Union


def strip_estimate_prefix(reference: Optional[str]) -> Optional[str]:
    """Strips optional prefix like 'EST-', 'EST_', 'EST ' from reference."""
    if not reference or not isinstance(reference, str):
        return None
    cleaned = reference.strip()
    # Strip optional case-insensitive EST prefix followed by optional separator
    stripped = re.sub(r"^EST[\-_:\s]*", "", cleaned, flags=re.IGNORECASE)
    return stripped.strip()


def parse_estimate_reference(
    reference: Optional[str]
) -> Tuple[Optional[datetime.datetime], Optional[str], Optional[str]]:
    """
    Parses a 10-digit estimate reference (HHMMDDMMYY) with optional 'EST-' prefix.
    
    Returns:
        (datetime_obj, iso_string, warning_message)
        If reference is missing or invalid:
            Returns (None, None, warning_message)
            Never silently assigns the current date/time.
    """
    if reference is None:
        return None, None, "Missing estimate reference number."

    ref_str = str(reference).strip()
    if not ref_str or ref_str.lower() in ("nan", "none", "null", "—", "-"):
        return None, None, "Estimate reference number is empty."

    digits = strip_estimate_prefix(ref_str)
    if not digits:
        return None, None, f"Reference '{ref_str}' has no digit payload."

    if not re.fullmatch(r"\d{10}", digits):
        return None, None, (
            f"Invalid reference format '{ref_str}': Expected exactly 10 digits "
            f"HHMMDDMMYY, got {len(digits)} characters ('{digits}')."
        )

    hour_str = digits[0:2]
    min_str = digits[2:4]
    day_str = digits[4:6]
    mon_str = digits[6:8]
    yr_str = digits[8:10]

    try:
        hour = int(hour_str)
        minute = int(min_str)
        day = int(day_str)
        month = int(mon_str)
        year_short = int(yr_str)
    except ValueError as e:
        return None, None, f"Non-numeric characters in reference digits: {e}"

    # Validation Rule 1: Hour between 00 and 23
    if not (0 <= hour <= 23):
        return None, None, f"Invalid hour '{hour_str}': Hour must be between 00 and 23."

    # Validation Rule 2: Minutes between 00 and 59
    if not (0 <= minute <= 59):
        return None, None, f"Invalid minute '{min_str}': Minute must be between 00 and 59."

    # Validation Rule 3: Month between 01 and 12
    if not (1 <= month <= 12):
        return None, None, f"Invalid month '{mon_str}': Month must be between 01 and 12."

    # Explicit 2-digit year rule: 26 -> 2026 (2000 + YY)
    year = 2000 + year_short

    # Validation Rule 4: Valid calendar date with leap year support
    try:
        dt = datetime.datetime(year, month, day, hour, minute, 0)
    except ValueError as e:
        return None, None, f"Invalid calendar date '{day_str}/{mon_str}/{year}': {e}."

    iso_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt, iso_str, None


def validate_estimate_reference(reference: Optional[str]) -> Dict[str, Any]:
    """Provides a detailed diagnostic dictionary for a reference number."""
    dt, iso_str, warning = parse_estimate_reference(reference)
    return {
        "original_reference": reference,
        "is_valid": dt is not None,
        "datetime_obj": dt,
        "estimate_generated_at": iso_str,
        "display_friendly": format_estimate_display(dt) if dt else "—",
        "display_long": format_estimate_display_long(dt) if dt else "—",
        "warning": warning
    }


def format_estimate_display(dt_or_str: Union[datetime.datetime, str, None]) -> str:
    """
    User-friendly display format: '31 Oct 2026 | 11:19 PM' or '2 Nov 2026 | 7:07 PM'.
    """
    if dt_or_str is None:
        return "—"

    if isinstance(dt_or_str, str):
        cleaned = dt_or_str.strip()
        if not cleaned or cleaned in ("—", "-", "N/A", "None", "nan"):
            return "—"
        try:
            # Parse standard ISO 8601 string
            cleaned_iso = cleaned.replace("T", " ")[:19]
            dt = datetime.datetime.strptime(cleaned_iso, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return cleaned
    elif isinstance(dt_or_str, datetime.datetime):
        dt = dt_or_str
    else:
        return "—"

    # User-friendly 12-hour time format with AM/PM (e.g. 11:19 PM, 7:07 PM)
    time_part = dt.strftime("%I:%M %p").lstrip("0")
    if not time_part or time_part.startswith(":"):
        time_part = "12" + time_part

    # Display e.g. '31 Oct 2026 | 11:19 PM' or '2 Nov 2026 | 7:07 PM'
    return f"{dt.day} {dt.strftime('%b %Y')} | {time_part}"


def format_estimate_display_long(dt_or_str: Union[datetime.datetime, str, None]) -> str:
    """
    Full textual representation: '31 October 2026, 11:19 PM' or '2 November 2026, 7:07 PM'.
    """
    if dt_or_str is None:
        return "—"

    if isinstance(dt_or_str, str):
        cleaned = dt_or_str.strip()
        if not cleaned or cleaned in ("—", "-", "N/A", "None", "nan"):
            return "—"
        try:
            cleaned_iso = cleaned.replace("T", " ")[:19]
            dt = datetime.datetime.strptime(cleaned_iso, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return cleaned
    elif isinstance(dt_or_str, datetime.datetime):
        dt = dt_or_str
    else:
        return "—"

    time_part = dt.strftime("%I:%M %p").lstrip("0")
    if not time_part or time_part.startswith(":"):
        time_part = "12" + time_part

    return f"{dt.day} {dt.strftime('%B %Y')}, {time_part}"
