"""
Time Utilities Module

This module contains utility functions for time-related operations,
particularly for parsing time strings and calculating time differences.
"""

import logging
from datetime import datetime, time, timedelta
import pytz

# Configure logging
logger = logging.getLogger(__name__)

# Time zone configurations
CENTRAL_TIMEZONE = pytz.timezone('America/Chicago')
UTC_TIMEZONE = pytz.timezone('UTC')

def parse_time_with_tz(time_str, tz=CENTRAL_TIMEZONE):
    """
    Parse a time string into a datetime object with timezone
    
    Args:
        time_str (str): Time string in format like "7:30 AM" or "15:45"
        tz (timezone): Timezone to use (default: Central Time)
        
    Returns:
        datetime: Datetime object with timezone, or None if parsing fails
    """
    if not time_str or not isinstance(time_str, str):
        return None
        
    time_str = time_str.strip()
    if not time_str:
        return None
        
    # Try different time formats
    formats = [
        '%I:%M %p',  # 7:30 AM
        '%H:%M',     # 15:45
        '%I:%M:%S %p',  # 7:30:00 AM
        '%H:%M:%S'   # 15:45:00
    ]
    
    # Get today's date in the target timezone
    today = datetime.now(tz).date()
    
    # Try to parse with each format
    for fmt in formats:
        try:
            # Parse the time string
            parsed_time = datetime.strptime(time_str, fmt).time()
            
            # Combine with today's date and add timezone
            dt = datetime.combine(today, parsed_time)
            localized_dt = tz.localize(dt)
            
            return localized_dt
            
        except ValueError:
            continue
    
    # Log if we couldn't parse the time
    logger.warning(f"Failed to parse time string: {time_str}")
    return None

def calculate_lateness(actual_time, expected_time, threshold_minutes=0):
    """
    Calculate minutes late, accounting for a threshold
    
    Args:
        actual_time (datetime): The actual start time
        expected_time (datetime): The expected start time
        threshold_minutes (int): Grace period in minutes
        
    Returns:
        int: Minutes late, or 0 if on time or within threshold
    """
    if not actual_time or not expected_time:
        return 0
        
    # Calculate the time difference in minutes
    time_diff = (actual_time - expected_time).total_seconds() / 60
    
    # Return minutes late if beyond threshold, otherwise 0
    return max(0, round(time_diff - threshold_minutes))

def format_time(dt, format_str='%I:%M %p'):
    """
    Format a datetime object as a time string
    
    Args:
        dt (datetime): Datetime object to format
        format_str (str): Format string
        
    Returns:
        str: Formatted time string, or empty string if dt is None
    """
    if not dt:
        return ''
        
    try:
        return dt.strftime(format_str)
    except:
        return ''

def format_duration(minutes):
    """
    Format minutes as hours and minutes
    
    Args:
        minutes (int): Duration in minutes
        
    Returns:
        str: Formatted duration string (e.g., "2h 15m")
    """
    if not minutes:
        return '0m'
        
    hours = minutes // 60
    mins = minutes % 60
    
    if hours > 0:
        return f"{hours}h {mins}m"
    else:
        return f"{mins}m"

def is_within_working_hours(dt, start_hour=6, end_hour=18):
    """
    Check if a datetime is within working hours
    
    Args:
        dt (datetime): Datetime to check
        start_hour (int): Start of working hours (default: 6 AM)
        end_hour (int): End of working hours (default: 6 PM)
        
    Returns:
        bool: True if within working hours, False otherwise
    """
    if not dt:
        return False
        
    hour = dt.hour
    return start_hour <= hour < end_hour