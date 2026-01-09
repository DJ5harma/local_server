"""
Date and time utilities for Indian Standard Time (IST - UTC+5:30).

All datetime operations in the local_server should use IST timezone
to ensure consistency with Indian time format.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

# Indian Standard Time (IST) is UTC+5:30
IST_OFFSET = timedelta(hours=5, minutes=30)
IST_TIMEZONE = timezone(IST_OFFSET, name="IST")


def now_ist() -> datetime:
    """
    Get current datetime in Indian Standard Time (IST).
    
    Returns:
        datetime object with IST timezone
    """
    return datetime.now(IST_TIMEZONE)


def now_ist_iso() -> str:
    """
    Get current datetime in IST as ISO 8601 formatted string.
    
    Returns:
        ISO 8601 formatted string with IST timezone offset (+05:30)
        Example: "2024-01-15T14:30:00+05:30"
    """
    return now_ist().isoformat()


def now_ist_iso_utc() -> str:
    """
    Get current datetime in IST, converted to UTC, as ISO 8601 formatted string.
    
    This is useful for sending to backend which may expect UTC timestamps.
    The timestamp represents the same moment in time but in UTC.
    
    Returns:
        ISO 8601 formatted string in UTC with Z suffix
        Example: "2024-01-15T09:00:00Z" (if IST is 14:30, UTC is 09:00)
    """
    ist_now = now_ist()
    utc_now = ist_now.astimezone(timezone.utc)
    return utc_now.isoformat().replace("+00:00", "Z")


def parse_iso_to_ist(iso_string: str) -> datetime:
    """
    Parse an ISO 8601 timestamp string and convert to IST.
    
    Args:
        iso_string: ISO 8601 formatted timestamp string
        
    Returns:
        datetime object in IST timezone
    """
    # Handle Z suffix (UTC)
    if iso_string.endswith('Z'):
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return dt.astimezone(IST_TIMEZONE)
    
    # Handle timezone offset
    dt = datetime.fromisoformat(iso_string)
    if dt.tzinfo is None:
        # If no timezone info, assume it's already IST
        return dt.replace(tzinfo=IST_TIMEZONE)
    
    # Convert to IST
    return dt.astimezone(IST_TIMEZONE)


def format_date_ist(dt: Optional[datetime] = None) -> str:
    """
    Format datetime as YYYY-MM-DD string in IST.
    
    Args:
        dt: datetime object (default: current IST time)
        
    Returns:
        Date string in YYYY-MM-DD format
    """
    if dt is None:
        dt = now_ist()
    elif dt.tzinfo is None:
        # Assume it's IST if no timezone info
        dt = dt.replace(tzinfo=IST_TIMEZONE)
    elif dt.tzinfo != IST_TIMEZONE:
        # Convert to IST
        dt = dt.astimezone(IST_TIMEZONE)
    
    return dt.strftime("%Y-%m-%d")


def add_minutes_ist(dt: datetime, minutes: float) -> datetime:
    """
    Add minutes to a datetime and return in IST.
    
    Args:
        dt: datetime object (will be converted to IST if needed)
        minutes: Number of minutes to add
        
    Returns:
        datetime object in IST timezone
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=IST_TIMEZONE)
    elif dt.tzinfo != IST_TIMEZONE:
        dt = dt.astimezone(IST_TIMEZONE)
    
    return dt + timedelta(minutes=minutes)
