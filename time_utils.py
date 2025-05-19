"""
Time Utilities Module

This module contains utility functions for working with time values,
particularly for parsing and comparing times in attendance records.
"""

import re
import logging
import pytz
from datetime import datetime, timedelta, time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Time format constants
TIME_FORMATS = [
    '%I:%M %p',  # 12-hour with AM/PM (e.g., "07:00 AM")
    '%H:%M',     # 24-hour (e.g., "07:00")
    '%I:%M%p',   # 12-hour without space (e.g., "07:00AM")
    '%I:%M',     # 12-hour without AM/PM (assumes AM)
    '%H:%M:%S',  # 24-hour with seconds
]

# Time zone abbreviations (for stripping from input)
TIME_ZONE_ABBREVS = ['CT', 'ET', 'MT', 'PT', 'CST', 'EST', 'MST', 'PST']

# Time zone mapping to pytz timezones
TZ_MAPPING = {
    'CT': 'America/Chicago',
    'CST': 'America/Chicago',
    'ET': 'America/New_York',
    'EST': 'America/New_York',
    'MT': 'America/Denver',
    'MST': 'America/Denver',
    'PT': 'America/Los_Angeles',
    'PST': 'America/Los_Angeles',
}

# Default timezone (Central Time)
DEFAULT_TIMEZONE = 'America/Chicago'

# Next-day markers for overnight shifts
NEXT_DAY_MARKERS = [
    r'\(\+1\)',           # (+1)
    r'\(Next Day\)',      # (Next Day)
    r'\(next day\)',      # (next day)
    r'\+1d',              # +1d
    r'\+1',               # +1
    r'Next Day',          # Next Day without parentheses
    r'next day'           # next day without parentheses
]

def parse_time(time_str):
    """
    Parse a time string into a datetime.time object
    
    Handles various time formats and cleans the input string.
    
    Args:
        time_str (str): Time string to parse
        
    Returns:
        datetime.time: Parsed time object or None if parsing fails
    """
    if not time_str:
        return None
    
    # Clean the input string
    time_str = clean_time_string(time_str)
    
    # Try each format
    for fmt in TIME_FORMATS:
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt.time()
        except ValueError:
            continue
    
    # If all formats fail, log and return None
    logger.warning(f"Could not parse time: {time_str}")
    return None

def parse_time_with_day_marker(time_str):
    """
    Parse a time string and detect next-day markers
    
    Handles overnight shifts with indicators like (+1), (Next Day)
    
    Args:
        time_str (str): Time string to parse
        
    Returns:
        tuple: (datetime.time object, is_next_day boolean) or (None, False) if parsing fails
    """
    if not time_str:
        return None, False
    
    # Check for next-day markers
    is_next_day = False
    clean_time = time_str
    
    for marker in NEXT_DAY_MARKERS:
        if re.search(marker, clean_time, re.IGNORECASE):
            is_next_day = True
            clean_time = re.sub(marker, '', clean_time, flags=re.IGNORECASE)
    
    # Remove any parentheses or brackets left behind
    clean_time = re.sub(r'[\(\[\)\]]\s*$', '', clean_time).strip()
    
    # Clean and parse the time
    time_obj = parse_time(clean_time)
    
    return time_obj, is_next_day

def parse_time_with_tz(time_str, default_tz=DEFAULT_TIMEZONE):
    """
    Parse a time string with timezone awareness and next-day detection
    
    Handles various time formats, removes timezone abbreviations, 
    detects next-day markers, and applies timezone information.
    
    Args:
        time_str (str): Time string to parse
        default_tz (str): Default timezone to use if none detected in the string
        
    Returns:
        tuple: (datetime.time object, is_next_day boolean, timezone string)
    """
    if not time_str:
        return None, False, default_tz
    
    # Convert to string if needed
    time_str = str(time_str).strip()
    
    # Check for next-day markers
    is_next_day = False
    for marker in NEXT_DAY_MARKERS:
        if re.search(marker, time_str, re.IGNORECASE):
            is_next_day = True
            time_str = re.sub(marker, '', time_str, flags=re.IGNORECASE)
    
    # Detect timezone abbreviation
    detected_tz = default_tz
    for tz in TIME_ZONE_ABBREVS:
        if re.search(rf'\s*{tz}\s*$', time_str, re.IGNORECASE):
            # Map the abbreviation to a pytz timezone
            detected_tz = TZ_MAPPING.get(tz.upper(), default_tz)
            # Remove the timezone abbreviation
            time_str = re.sub(rf'\s*{tz}\s*$', '', time_str, flags=re.IGNORECASE)
            break
    
    # Clean the time string
    clean_time = clean_time_string(time_str)
    
    # Parse the time
    time_obj = parse_time(clean_time)
    
    return time_obj, is_next_day, detected_tz

def clean_time_string(time_str):
    """
    Clean a time string for parsing
    
    Removes timezone abbreviations, extra spaces, and normalizes AM/PM.
    
    Args:
        time_str (str): Time string to clean
        
    Returns:
        str: Cleaned time string
    """
    if not time_str:
        return time_str
    
    # Convert to string if needed
    time_str = str(time_str).strip()
    
    # Remove timezone abbreviations
    for tz in TIME_ZONE_ABBREVS:
        time_str = re.sub(rf'\s*{tz}\s*$', '', time_str, flags=re.IGNORECASE)
    
    # Normalize AM/PM format
    time_str = re.sub(r'([0-9])([AP]\.?M\.?)', r'\1 \2', time_str, flags=re.IGNORECASE)
    time_str = re.sub(r'([AP])\.?M\.?', lambda m: m.group(0).upper(), time_str, flags=re.IGNORECASE)
    time_str = re.sub(r'AM', 'AM', time_str, flags=re.IGNORECASE)
    time_str = re.sub(r'PM', 'PM', time_str, flags=re.IGNORECASE)
    
    # Remove extra spaces
    time_str = re.sub(r'\s+', ' ', time_str).strip()
    
    return time_str

def calculate_time_difference(time1, time2, time2_is_next_day=False):
    """
    Calculate the difference in minutes between two time objects
    
    For attendance calculations, if time2 is earlier than time1, it's
    considered to be on the same day (not the next day) unless explicitly
    marked as next day.
    
    Args:
        time1 (datetime.time): First time
        time2 (datetime.time): Second time
        time2_is_next_day (bool): Whether time2 is explicitly marked as being on the next day
        
    Returns:
        int: Difference in minutes (positive if time2 > time1, negative if time1 > time2)
    """
    if not time1 or not time2:
        return 0
    
    # Convert to datetime objects with a base date
    base_date = datetime.now().date()
    dt1 = datetime.combine(base_date, time1)
    
    # If time2 is explicitly marked as next day, add a day to its base date
    if time2_is_next_day:
        dt2 = datetime.combine(base_date + timedelta(days=1), time2)
    else:
        dt2 = datetime.combine(base_date, time2)
        
        # Auto-detect overnight shifts not explicitly marked
        diff = (dt2 - dt1).total_seconds() / 60
        
        # Handle crossing midnight (assume same day for attendance)
        if diff < -720:  # More than 12 hours negative = crossing midnight forward
            dt2 = datetime.combine(base_date + timedelta(days=1), time2)
        elif diff > 720:  # More than 12 hours positive = crossing midnight backward
            dt1 = datetime.combine(base_date + timedelta(days=1), time1)
    
    # Calculate final difference in minutes
    diff = (dt2 - dt1).total_seconds() / 60
    return round(diff)

def in_allowed_range(actual_time, expected_time, grace_period_minutes):
    """
    Check if an actual time is within the allowed range of an expected time
    
    Args:
        actual_time (datetime.time): Actual time to check
        expected_time (datetime.time): Expected time
        grace_period_minutes (int): Grace period in minutes
        
    Returns:
        bool: True if within range, False otherwise
    """
    if not actual_time or not expected_time:
        return False
    
    diff = calculate_time_difference(expected_time, actual_time)
    return abs(diff) <= grace_period_minutes

def format_time(time_obj, use_12h=True):
    """
    Format a time object as a string
    
    Args:
        time_obj (datetime.time): Time object to format
        use_12h (bool): Whether to use 12-hour format with AM/PM
        
    Returns:
        str: Formatted time string
    """
    if not time_obj:
        return ""
    
    if use_12h:
        return time_obj.strftime("%I:%M %p")
    else:
        return time_obj.strftime("%H:%M")

def format_duration(minutes):
    """
    Format a duration in minutes as a human-readable string
    
    Args:
        minutes (int): Duration in minutes
        
    Returns:
        str: Formatted duration string (e.g., "2h 30m")
    """
    if not minutes:
        return "0m"
    
    hours, mins = divmod(abs(minutes), 60)
    
    if hours > 0:
        return f"{hours}h {mins}m"
    else:
        return f"{mins}m"

def calculate_lateness(actual_time, expected_time, threshold_minutes, actual_is_next_day=False):
    """
    Calculate lateness in minutes based on actual and expected times
    
    Args:
        actual_time (datetime.time): Actual time recorded
        expected_time (datetime.time): Expected time (scheduled time)
        threshold_minutes (int): Threshold in minutes for what counts as "late"
        actual_is_next_day (bool): Whether the actual time is on the next day
        
    Returns:
        tuple: (is_late (bool), minutes_late (int), formatted_lateness (str))
    """
    if not actual_time or not expected_time:
        return True, 0, "Missing time data"
    
    # Calculate minutes difference, accounting for next-day markers
    minutes_diff = calculate_time_difference(expected_time, actual_time, actual_is_next_day)
    
    # If arrival is after expected time (positive diff) by more than threshold, it's late
    is_late = minutes_diff > threshold_minutes
    
    # Format the lateness as a string
    if is_late:
        formatted_lateness = format_duration(minutes_diff)
    else:
        formatted_lateness = "On time"
    
    return is_late, minutes_diff if is_late else 0, formatted_lateness

def get_business_days_in_month(year, month):
    """
    Get the number of business days (Mon-Fri) in a month
    
    Args:
        year (int): Year
        month (int): Month (1-12)
        
    Returns:
        int: Number of business days
    """
    # Get the first day of the month
    first_day = datetime(year, month, 1)
    
    # Get the last day of the month
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    
    # Count business days
    business_days = 0
    current_day = first_day
    while current_day <= last_day:
        if current_day.weekday() < 5:  # Monday-Friday
            business_days += 1
        current_day += timedelta(days=1)
    
    return business_days