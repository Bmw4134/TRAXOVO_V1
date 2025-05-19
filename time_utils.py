"""
Time Utilities Module

This module provides functions for working with time data,
particularly for parsing, formatting, and calculating time
differences in the context of driver reporting.
"""

import re
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pytz

# Configure logger
logger = logging.getLogger(__name__)

# Default timezone
DEFAULT_TZ = ZoneInfo("America/Chicago")  # Central Time

# Compatibility functions for older modules
def parse_time_with_tz(time_str, default_date=None):
    """Compatibility function for older code - redirects to parse_time_string"""
    return parse_time_string(time_str, default_date)

def calculate_lateness(start_time, expected_start=None, threshold_minutes=15):
    """Compatibility function for older code - calculates lateness in minutes"""
    if not start_time:
        return 0
        
    if not expected_start:
        # Get the date from start_time
        date = start_time.date()
        # Create expected start time at 7:00 AM
        expected_start = datetime.combine(date, datetime.min.time().replace(hour=7))
        # Add timezone info
        if expected_start.tzinfo is None:
            expected_start = expected_start.replace(tzinfo=DEFAULT_TZ)
    
    # If not late, return 0
    if start_time <= expected_start:
        return 0
        
    # Calculate lateness in minutes
    lateness_minutes = (start_time - expected_start).total_seconds() / 60
    
    # If within threshold, not considered late
    if lateness_minutes <= threshold_minutes:
        return 0
        
    return int(lateness_minutes)

def parse_time_string(time_str, default_date=None):
    """
    Parse a time string into a datetime object
    
    Handles various formats including:
    - "8:30 AM" or "8:30 AM CT" 
    - "08:30" or "08:30 CT"
    - ISO format "2023-05-15T08:30:00"
    - Excel/CSV export formats
    
    Args:
        time_str (str): Time string to parse
        default_date (datetime.date): Default date to use if not specified in time_str
        
    Returns:
        datetime: Parsed datetime object, or None if parsing fails
    """
    if not time_str or not isinstance(time_str, str):
        return None
    
    time_str = time_str.strip()
    
    # If empty after stripping
    if not time_str:
        return None
        
    # Get the default date to use
    if not default_date:
        default_date = datetime.now(DEFAULT_TZ).date()
    elif isinstance(default_date, datetime):
        default_date = default_date.date()
    
    # Check for timezone suffix and remove it temporarily
    timezone = DEFAULT_TZ
    tz_match = re.search(r'\s+(CT|ET|PT|MT|CST|EST|PST|MST)$', time_str)
    if tz_match:
        tz_code = tz_match.group(1)
        time_str = time_str[:tz_match.start()]
        
        # Map timezone abbreviations to pytz timezones
        tz_map = {
            'CT': 'America/Chicago',
            'ET': 'America/New_York',
            'PT': 'America/Los_Angeles',
            'MT': 'America/Denver',
            'CST': 'America/Chicago',
            'EST': 'America/New_York',
            'PST': 'America/Los_Angeles',
            'MST': 'America/Denver',
        }
        if tz_code in tz_map:
            timezone = ZoneInfo(tz_map[tz_code])
    
    try:
        # Try various formats
        formats = [
            # 12-hour formats with AM/PM
            "%I:%M %p",       # "8:30 AM"
            "%I:%M:%S %p",    # "8:30:00 AM"
            "%I:%M%p",        # "8:30AM"
            "%I:%M:%S%p",     # "8:30:00AM"
            
            # 24-hour formats
            "%H:%M",          # "08:30" or "8:30"
            "%H:%M:%S",       # "08:30:00" or "8:30:00"
            
            # Date and time formats
            "%Y-%m-%d %H:%M:%S",  # "2023-05-15 08:30:00"
            "%Y-%m-%d %H:%M",     # "2023-05-15 08:30"
            "%m/%d/%Y %H:%M:%S",  # "05/15/2023 08:30:00"
            "%m/%d/%Y %H:%M",     # "05/15/2023 08:30"
            "%m/%d/%y %H:%M:%S",  # "05/15/23 08:30:00"
            "%m/%d/%y %H:%M",     # "05/15/23 08:30"
        ]
        
        # Try to parse with each format
        parsed_dt = None
        
        for fmt in formats:
            try:
                if '%Y' in fmt or '%y' in fmt:
                    # Format has date, parse directly
                    parsed_dt = datetime.strptime(time_str, fmt)
                    # Add timezone info
                    parsed_dt = parsed_dt.replace(tzinfo=timezone)
                    return parsed_dt
                else:
                    # Format is time only, combine with default date
                    parsed_time = datetime.strptime(time_str, fmt).time()
                    parsed_dt = datetime.combine(default_date, parsed_time)
                    # Add timezone info
                    parsed_dt = parsed_dt.replace(tzinfo=timezone)
                    return parsed_dt
            except ValueError:
                continue
        
        # Try ISO format as last resort
        try:
            parsed_dt = datetime.fromisoformat(time_str)
            # Add timezone if not present
            if parsed_dt.tzinfo is None:
                parsed_dt = parsed_dt.replace(tzinfo=timezone)
            return parsed_dt
        except ValueError:
            pass
        
        # If all parsing attempts failed
        logger.warning(f"Failed to parse time string: {time_str}")
        return None
    
    except Exception as e:
        logger.error(f"Error parsing time string '{time_str}': {e}")
        return None

def format_time(dt, format_str="%I:%M %p"):
    """
    Format a datetime object as a time string
    
    Args:
        dt (datetime): Datetime object to format
        format_str (str): Format string to use
        
    Returns:
        str: Formatted time string, or empty string if dt is None
    """
    if not dt:
        return ""
    
    try:
        # Ensure datetime has timezone info
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=DEFAULT_TZ)
        
        # Format the time
        return dt.strftime(format_str)
    except Exception as e:
        logger.error(f"Error formatting time '{dt}': {e}")
        return ""

def calculate_time_difference(start_time, end_time, unit='minutes'):
    """
    Calculate the difference between two times
    
    Args:
        start_time (datetime): Start time
        end_time (datetime): End time
        unit (str): Unit for the result ('minutes', 'hours', or 'seconds')
        
    Returns:
        int or float: Time difference in the specified unit, or None if calculation fails
    """
    if not start_time or not end_time:
        return None
    
    try:
        # Ensure both times have timezone info
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=DEFAULT_TZ)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=DEFAULT_TZ)
        
        # Calculate difference
        delta = end_time - start_time
        
        # Convert to specified unit
        if unit == 'seconds':
            return delta.total_seconds()
        elif unit == 'minutes':
            return delta.total_seconds() / 60
        elif unit == 'hours':
            return delta.total_seconds() / 3600
        else:
            logger.warning(f"Unsupported time difference unit: {unit}")
            return delta.total_seconds() / 60  # Default to minutes
    except Exception as e:
        logger.error(f"Error calculating time difference: {e}")
        return None

def is_late_start(start_time, expected_start=None, threshold_minutes=0):
    """
    Check if a start time is considered late
    
    Args:
        start_time (datetime): Actual start time
        expected_start (datetime): Expected start time, defaults to 7:00 AM
        threshold_minutes (int): Minutes of grace period
        
    Returns:
        bool: True if start_time is later than expected_start + threshold_minutes
    """
    if not start_time:
        return False
    
    try:
        # Default expected start time is 7:00 AM if not specified
        if not expected_start:
            # Get the date from start_time
            date = start_time.date()
            # Create expected start time at 7:00 AM
            expected_start = datetime.combine(date, datetime.min.time().replace(hour=7))
            # Add timezone info
            if expected_start.tzinfo is None:
                expected_start = expected_start.replace(tzinfo=DEFAULT_TZ)
        
        # Add grace period
        expected_with_threshold = expected_start + timedelta(minutes=threshold_minutes)
        
        # Compare times
        return start_time > expected_with_threshold
    except Exception as e:
        logger.error(f"Error checking for late start: {e}")
        return False

def is_early_end(end_time, expected_end=None, threshold_minutes=0):
    """
    Check if an end time is considered early
    
    Args:
        end_time (datetime): Actual end time
        expected_end (datetime): Expected end time, defaults to 3:30 PM
        threshold_minutes (int): Minutes of grace period
        
    Returns:
        bool: True if end_time is earlier than expected_end - threshold_minutes
    """
    if not end_time:
        return False
    
    try:
        # Default expected end time is 3:30 PM if not specified
        if not expected_end:
            # Get the date from end_time
            date = end_time.date()
            # Create expected end time at 3:30 PM
            expected_end = datetime.combine(date, datetime.min.time().replace(hour=15, minute=30))
            # Add timezone info
            if expected_end.tzinfo is None:
                expected_end = expected_end.replace(tzinfo=DEFAULT_TZ)
        
        # Subtract grace period
        expected_with_threshold = expected_end - timedelta(minutes=threshold_minutes)
        
        # Compare times
        return end_time < expected_with_threshold
    except Exception as e:
        logger.error(f"Error checking for early end: {e}")
        return False

def get_date_range(reference_date, range_days, include_today=True):
    """
    Get a date range ending on reference_date
    
    Args:
        reference_date (datetime.date or str): End date for the range
        range_days (int): Number of days in the range
        include_today (bool): Whether to include reference_date in the range
        
    Returns:
        tuple: (start_date, end_date) as datetime.date objects
    """
    try:
        # Parse reference date if it's a string
        if isinstance(reference_date, str):
            reference_date = datetime.strptime(reference_date, "%Y-%m-%d").date()
        elif isinstance(reference_date, datetime):
            reference_date = reference_date.date()
        
        # Calculate end date
        end_date = reference_date
        
        # Calculate start date
        if include_today:
            start_date = end_date - timedelta(days=range_days - 1)
        else:
            start_date = end_date - timedelta(days=range_days)
        
        return (start_date, end_date)
    except Exception as e:
        logger.error(f"Error calculating date range: {e}")
        # Fall back to current date and past week
        today = datetime.now(DEFAULT_TZ).date()
        return (today - timedelta(days=7), today)