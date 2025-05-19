"""
Timezone Normalizer

This module standardizes timezone operations across the application,
ensuring consistent timezone handling for dates and times.
"""

import re
from datetime import datetime, time, timedelta
import logging
import pytz

# Import structured logger
from utils.structured_logger import get_pipeline_logger

# Get logger
logger = get_pipeline_logger()

# Constants
DEFAULT_TIMEZONE = 'America/Chicago'  # CDT/CST timezone
UTC_TIMEZONE = 'UTC'

# Common time format strings
TIME_FORMAT_HH_MM = '%H:%M'
TIME_FORMAT_HH_MM_SS = '%H:%M:%S'
TIME_FORMAT_12H = '%I:%M %p'
TIME_FORMAT_ISO = '%Y-%m-%dT%H:%M:%S'

# Regular expression to identify next-day indicators
NEXT_DAY_PATTERN = re.compile(r'(\(\+1\)|\(Next Day\)|\+1d|\+1)', re.IGNORECASE)


def get_application_timezone():
    """
    Get the application timezone.
    
    Returns:
        pytz.timezone: Application timezone object
    """
    return pytz.timezone(DEFAULT_TIMEZONE)


def get_utc_timezone():
    """
    Get the UTC timezone.
    
    Returns:
        pytz.timezone: UTC timezone object
    """
    return pytz.timezone(UTC_TIMEZONE)


def localize_datetime(dt, tz_name=DEFAULT_TIMEZONE):
    """
    Localize a naive datetime to the specified timezone.
    
    Args:
        dt (datetime): Naive datetime object
        tz_name (str): Timezone name
        
    Returns:
        datetime: Localized datetime object
    """
    if dt is None:
        return None
        
    if dt.tzinfo is not None:
        return dt
        
    tz = pytz.timezone(tz_name)
    return tz.localize(dt)


def convert_to_utc(dt, source_tz_name=DEFAULT_TIMEZONE):
    """
    Convert a datetime from source timezone to UTC.
    
    Args:
        dt (datetime): Datetime object in source timezone
        source_tz_name (str): Source timezone name
        
    Returns:
        datetime: Datetime object in UTC timezone
    """
    if dt is None:
        return None
        
    if dt.tzinfo is None:
        dt = localize_datetime(dt, source_tz_name)
        
    return dt.astimezone(pytz.UTC)


def convert_from_utc(dt, target_tz_name=DEFAULT_TIMEZONE):
    """
    Convert a datetime from UTC to target timezone.
    
    Args:
        dt (datetime): Datetime object in UTC timezone
        target_tz_name (str): Target timezone name
        
    Returns:
        datetime: Datetime object in target timezone
    """
    if dt is None:
        return None
        
    if dt.tzinfo is None:
        dt = localize_datetime(dt, UTC_TIMEZONE)
        
    target_tz = pytz.timezone(target_tz_name)
    return dt.astimezone(target_tz)


def normalize_time_string(time_str, detect_next_day=True):
    """
    Normalize time string to HH:MM format.
    
    Args:
        time_str (str): Time string in various formats
        detect_next_day (bool): Whether to detect and handle next-day indicators
        
    Returns:
        tuple: (normalized time string, is_next_day flag)
    """
    if not time_str or time_str.strip() == '':
        return None, False
    
    # Convert to string explicitly for safety
    time_str = str(time_str).strip()
    
    # Check for next-day indicators
    is_next_day = False
    if detect_next_day:
        next_day_match = NEXT_DAY_PATTERN.search(time_str)
        if next_day_match:
            is_next_day = True
            # Remove the next-day indicator
            time_str = NEXT_DAY_PATTERN.sub('', time_str).strip()
    
    # Try various formats
    formats = [
        TIME_FORMAT_HH_MM,         # 13:45
        TIME_FORMAT_HH_MM_SS,      # 13:45:30
        TIME_FORMAT_12H,           # 1:45 PM
        '%I:%M:%S %p',   # 1:45:30 PM
        '%I:%M%p',       # 1:45PM
        '%I:%M:%S%p',    # 1:45:30PM
        '%I %p',         # 1 PM
        '%I%p'           # 1PM
    ]
    
    # Try each format
    for fmt in formats:
        try:
            # Parse time string
            dt = datetime.strptime(time_str, fmt)
            # Return normalized format with next-day flag
            return dt.strftime(TIME_FORMAT_HH_MM), is_next_day
        except ValueError:
            continue
    
    # If we got here, none of the formats matched
    logger.warning(f"Could not normalize time string: {time_str}")
    return None, False


def parse_time_with_next_day(time_str, base_date=None):
    """
    Parse time string with next-day handling.
    
    Args:
        time_str (str): Time string
        base_date (datetime): Base date to use, defaults to today
        
    Returns:
        datetime: Datetime object with correct date
    """
    if not time_str:
        return None
    
    # Use today if base_date not provided
    if base_date is None:
        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Normalize time string and get next-day flag
    normalized_time, is_next_day = normalize_time_string(time_str)
    
    if not normalized_time:
        return None
    
    # Parse the normalized time
    parsed_time = datetime.strptime(normalized_time, TIME_FORMAT_HH_MM).time()
    
    # Create datetime with the base date
    result_dt = datetime.combine(base_date.date(), parsed_time)
    
    # Adjust for next day
    if is_next_day:
        result_dt += timedelta(days=1)
    
    return result_dt


def format_datetime(dt, format_str=TIME_FORMAT_HH_MM, tz_name=DEFAULT_TIMEZONE):
    """
    Format datetime object to string.
    
    Args:
        dt (datetime): Datetime object
        format_str (str): Format string
        tz_name (str): Timezone name
        
    Returns:
        str: Formatted datetime string
    """
    if dt is None:
        return ''
    
    # Ensure timezone aware
    if dt.tzinfo is None:
        dt = localize_datetime(dt, tz_name)
    
    # Convert to target timezone
    dt = dt.astimezone(pytz.timezone(tz_name))
    
    # Format
    return dt.strftime(format_str)


def calculate_time_difference_minutes(time1, time2):
    """
    Calculate the difference between two time strings in minutes.
    
    Args:
        time1 (str): First time string
        time2 (str): Second time string
        
    Returns:
        int: Difference in minutes (positive if time2 > time1)
    """
    # Normalize time strings
    norm_time1, is_next_day1 = normalize_time_string(time1)
    norm_time2, is_next_day2 = normalize_time_string(time2)
    
    if not norm_time1 or not norm_time2:
        return None
    
    # Parse times
    dt1 = datetime.strptime(norm_time1, TIME_FORMAT_HH_MM)
    dt2 = datetime.strptime(norm_time2, TIME_FORMAT_HH_MM)
    
    # Adjust for next day
    if is_next_day1:
        dt1 += timedelta(days=1)
    if is_next_day2:
        dt2 += timedelta(days=1)
    
    # Calculate difference
    diff = dt2 - dt1
    return int(diff.total_seconds() / 60)