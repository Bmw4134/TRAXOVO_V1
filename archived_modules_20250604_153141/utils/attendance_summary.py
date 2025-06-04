"""
TRAXORA | Attendance Summary Utilities

This module provides utilities for summarizing attendance data,
including classification of attendance records.
"""

import logging
from datetime import datetime, time
from typing import Dict, Any, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Define time thresholds for classification
START_TIME_THRESHOLD = time(7, 30)  # 7:30 AM
END_TIME_THRESHOLD = time(16, 30)   # 4:30 PM

def parse_time(time_str: str) -> Optional[time]:
    """
    Parse a time string in various formats
    
    Args:
        time_str (str): Time string to parse
        
    Returns:
        datetime.time: Parsed time or None if parsing failed
    """
    if not time_str:
        return None
        
    formats = [
        "%H:%M:%S",       # 13:45:30
        "%H:%M",          # 13:45
        "%I:%M:%S %p",    # 1:45:30 PM
        "%I:%M %p"        # 1:45 PM
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt.time()
        except ValueError:
            continue
    
    # Try special formats with AM/PM
    try:
        # Handle formats like "7:30AM" (no space)
        time_str = time_str.replace("AM", " AM").replace("PM", " PM")
        return parse_time(time_str)
    except Exception:
        pass
    
    logger.warning(f"Could not parse time: {time_str}")
    return None

def classify_day(record: Dict[str, Any]) -> str:
    """
    Classify a day based on attendance record
    
    Args:
        record (dict): Attendance record
        
    Returns:
        str: Classification ('On Time', 'Late', 'Early End', 'No Show', 'Unknown')
    """
    # Check for on job or driving status
    on_job = record.get('OnJob')
    activity = record.get('Activity')
    
    # Fields to check for specific records
    time_on_site = record.get('TimeOnSite', 0)
    start_time_str = record.get('StartTime')
    end_time_str = record.get('EndTime')
    
    # Parse times
    start_time = parse_time(start_time_str) if start_time_str else None
    end_time = parse_time(end_time_str) if end_time_str else None
    
    # If no data at all, mark as No Show
    if not on_job and not activity and not time_on_site and not start_time and not end_time:
        return "No Show"
    
    # Non-driving activities (we only care about drivers)
    if activity and "non-driving" in str(activity).lower():
        return "Non-Driving"
    
    # Explicitly not on job
    if on_job is not None and not on_job:
        return "No Show"
    
    # Check start time (late)
    if start_time and start_time > START_TIME_THRESHOLD:
        return "Late"
    
    # Check end time (early end)
    if end_time and end_time < END_TIME_THRESHOLD:
        return "Early End"
    
    # If we have valid start and end times, mark as On Time
    if start_time and end_time:
        return "On Time"
    
    # Default to Unknown if we don't have enough information
    return "Unknown"

def get_attendance_stats(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get overall attendance statistics
    
    Args:
        data (list): List of attendance records
        
    Returns:
        dict: Summary statistics
    """
    total_records = len(data)
    classifications = {
        "On Time": 0,
        "Late": 0,
        "Early End": 0,
        "No Show": 0,
        "Unknown": 0,
        "Non-Driving": 0
    }
    
    for record in data:
        classification = classify_day(record)
        classifications[classification] = classifications.get(classification, 0) + 1
    
    attendance_rate = (classifications["On Time"] / total_records) * 100 if total_records > 0 else 0
    
    return {
        "total_records": total_records,
        "on_time": classifications["On Time"],
        "late": classifications["Late"],
        "early_end": classifications["Early End"],
        "no_show": classifications["No Show"],
        "unknown": classifications["Unknown"],
        "non_driving": classifications.get("Non-Driving", 0),
        "attendance_rate": round(attendance_rate, 1)
    }