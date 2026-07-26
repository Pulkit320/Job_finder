import re
from datetime import datetime, timedelta
from dateutil import parser as dateutil_parser

def parse_relative_date(date_str: str) -> datetime:
    if not date_str:
        return datetime.now()
    
    text = date_str.strip().lower()
    now = datetime.now()

    if any(x in text for x in ["just posted", "today", "0d", "0 days ago", "few hours ago", "hours ago", "m ago", "minutes ago"]):
        return now

    if "yesterday" in text or "1d" in text or "1 day ago" in text:
        return now - timedelta(days=1)

    match = re.search(r"(\d+)\s*(d|day|days|h|hour|hours|w|week|weeks)\s*ago", text)
    if match:
        val = int(match.group(1))
        unit = match.group(2)
        if unit.startswith("d"):
            return now - timedelta(days=val)
        elif unit.startswith("h"):
            return now - timedelta(hours=val)
        elif unit.startswith("w"):
            return now - timedelta(weeks=val)

    # Short format e.g. "2d", "3d", "1w"
    match_short = re.search(r"^(\d+)\s*([dhw])$", text)
    if match_short:
        val = int(match_short.group(1))
        unit = match_short.group(2)
        if unit == "d":
            return now - timedelta(days=val)
        elif unit == "h":
            return now - timedelta(hours=val)
        elif unit == "w":
            return now - timedelta(weeks=val)

    try:
        dt = dateutil_parser.parse(date_str, fuzzy=True)
        return dt
    except Exception:
        return now

def format_date_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")

def is_within_days(date_str: str, max_days: int = 3) -> bool:
    try:
        parsed_dt = parse_relative_date(date_str)
        cutoff = datetime.now() - timedelta(days=max_days, hours=6)  # cushion
        return parsed_dt >= cutoff
    except Exception:
        return True
