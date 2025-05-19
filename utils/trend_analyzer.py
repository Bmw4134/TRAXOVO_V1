"""
Attendance Trend Analyzer

This module provides functions for analyzing attendance trends over time,
identifying patterns such as chronic lateness, repeated absences, and shift instability.
"""

import logging
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

# Constants
CHRONIC_LATE_THRESHOLD = 3  # Number of late days to consider chronic (in a week)
REPEATED_ABSENCE_THRESHOLD = 2  # Number of absent days to consider repeated (in a week)
UNSTABLE_SHIFT_THRESHOLD = 180  # Minutes variance to consider a shift unstable (3 hours)


def detect_attendance_trends(daily_data_list):
    """
    Detect trends across multiple days of attendance data.
    
    Args:
        daily_data_list (list): List of daily attendance data dictionaries
        
    Returns:
        dict: Trends analysis with patterns and statistics
    """
    if not daily_data_list:
        return {}
    
    # Initialize trend data structure
    trends = {
        'late_trend': [],  # Daily late percentage 
        'early_end_trend': [],  # Daily early end percentage
        'not_on_job_trend': [],  # Daily not on job percentage
        'dates': [],  # List of dates in the trend
        'average_late_minutes': 0,  # Average minutes late across the period
        'average_early_minutes': 0,  # Average minutes early across the period
        'total_drivers': 0,  # Total unique drivers in the period
    }
    
    # Driver tracking
    all_drivers = set()
    all_late_minutes = []
    all_early_minutes = []
    
    # Process each day's data
    for daily_data in daily_data_list:
        # Skip empty or invalid data
        if not daily_data or 'date' not in daily_data:
            continue
        
        # Track date for the trend
        trends['dates'].append(daily_data.get('date', ''))
        
        # Calculate percentages for trends
        total_drivers = daily_data.get('total_drivers', 0)
        if total_drivers > 0:
            late_percent = round(100 * daily_data.get('late_count', 0) / total_drivers, 1)
            early_percent = round(100 * daily_data.get('early_count', 0) / total_drivers, 1)
            missing_percent = round(100 * daily_data.get('missing_count', 0) / total_drivers, 1)
        else:
            late_percent = 0
            early_percent = 0
            missing_percent = 0
        
        # Add to trend lists
        trends['late_trend'].append(late_percent)
        trends['early_end_trend'].append(early_percent)
        trends['not_on_job_trend'].append(missing_percent)
        
        # Track drivers
        for records in [
            daily_data.get('late_start_records', []),
            daily_data.get('early_end_records', []),
            daily_data.get('not_on_job_records', [])
        ]:
            for record in records:
                driver_name = record.get('driver_name')
                if driver_name:
                    all_drivers.add(driver_name)
                
                # Track minutes for averages
                if 'late_minutes' in record and record['late_minutes']:
                    all_late_minutes.append(record['late_minutes'])
                if 'early_minutes' in record and record['early_minutes']:
                    all_early_minutes.append(record['early_minutes'])
    
    # Calculate averages
    if all_late_minutes:
        trends['average_late_minutes'] = round(sum(all_late_minutes) / len(all_late_minutes), 1)
    if all_early_minutes:
        trends['average_early_minutes'] = round(sum(all_early_minutes) / len(all_early_minutes), 1)
    
    # Total drivers in the period
    trends['total_drivers'] = len(all_drivers)
    
    return trends


def identify_chronic_issues(daily_data_list):
    """
    Identify drivers with chronic attendance issues.
    
    Args:
        daily_data_list (list): List of daily attendance data dictionaries
        
    Returns:
        tuple: Lists of drivers with chronic lates, repeated absences, and unstable shifts
    """
    if not daily_data_list:
        return [], [], []
    
    # Track driver attendance issues
    driver_late_days = defaultdict(list)  # Maps driver to list of dates they were late
    driver_absence_days = defaultdict(list)  # Maps driver to list of dates they were absent
    driver_shift_times = defaultdict(list)  # Maps driver to list of shift start times for stability analysis
    
    # Process each day's data
    for daily_data in daily_data_list:
        date = daily_data.get('date', '')
        if not date:
            continue
        
        # Process late drivers
        for record in daily_data.get('late_start_records', []):
            driver_name = record.get('driver_name')
            if driver_name:
                driver_late_days[driver_name].append(date)
                
                # Track shift start times for stability analysis
                start_time = record.get('actual_start')
                if start_time:
                    # Convert to minutes since midnight if string format
                    if isinstance(start_time, str):
                        try:
                            hour, minute = map(int, start_time.split(':'))
                            minutes = hour * 60 + minute
                            driver_shift_times[driver_name].append(minutes)
                        except (ValueError, IndexError):
                            pass
        
        # Process absent drivers
        for record in daily_data.get('not_on_job_records', []):
            driver_name = record.get('driver_name')
            if driver_name:
                driver_absence_days[driver_name].append(date)
    
    # Identify chronic late drivers (3+ lates in the period)
    chronic_lates = [
        {
            'name': driver,
            'count': len(dates),
            'dates': dates
        }
        for driver, dates in driver_late_days.items()
        if len(dates) >= CHRONIC_LATE_THRESHOLD
    ]
    chronic_lates.sort(key=lambda x: x['count'], reverse=True)
    
    # Identify drivers with repeated absences (2+ absences in the period)
    repeated_absences = [
        {
            'name': driver,
            'count': len(dates),
            'dates': dates
        }
        for driver, dates in driver_absence_days.items()
        if len(dates) >= REPEATED_ABSENCE_THRESHOLD
    ]
    repeated_absences.sort(key=lambda x: x['count'], reverse=True)
    
    # Identify drivers with unstable shifts (large variance in start times)
    unstable_shifts = []
    for driver, times in driver_shift_times.items():
        if len(times) >= 3:  # Need at least 3 data points to assess stability
            # Calculate the range of shift start times
            time_range = max(times) - min(times)
            if time_range >= UNSTABLE_SHIFT_THRESHOLD:
                unstable_shifts.append({
                    'name': driver,
                    'variance_minutes': time_range,
                    'earliest': min(times),
                    'latest': max(times),
                    'count': len(times)
                })
    unstable_shifts.sort(key=lambda x: x['variance_minutes'], reverse=True)
    
    return chronic_lates, repeated_absences, unstable_shifts


def get_trending_drivers(daily_data_list, days=5, threshold=2):
    """
    Identify drivers with trending issues (recent attendance problems).
    
    Args:
        daily_data_list (list): List of daily attendance data dictionaries
        days (int): Number of recent days to analyze
        threshold (int): Minimum number of issues to be considered trending
        
    Returns:
        list: Drivers with trending attendance issues
    """
    if not daily_data_list or len(daily_data_list) < days:
        return []
    
    # Only analyze the most recent days
    recent_data = daily_data_list[-days:]
    
    # Track driver issues in recent days
    driver_issues = defaultdict(int)
    
    # Process each day's data
    for daily_data in recent_data:
        # Count issues by driver
        for records_type in ['late_start_records', 'early_end_records', 'not_on_job_records']:
            for record in daily_data.get(records_type, []):
                driver_name = record.get('driver_name')
                if driver_name:
                    driver_issues[driver_name] += 1
    
    # Identify trending drivers
    trending_drivers = [
        {
            'name': driver,
            'issue_count': count
        }
        for driver, count in driver_issues.items()
        if count >= threshold
    ]
    trending_drivers.sort(key=lambda x: x['issue_count'], reverse=True)
    
    return trending_drivers