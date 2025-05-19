"""
Attendance Trend Analyzer

This module analyzes attendance data across multiple days to identify patterns 
such as chronic lateness, repeated absences, and unstable shift times.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple, Union, Optional, Any, Set

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.attendance_processor import process_attendance_data
from driver_utils import normalize_driver_name

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Trend detection thresholds
CHRONIC_LATE_THRESHOLD = 3      # Number of late days to flag as chronic
REPEATED_ABSENCE_THRESHOLD = 2  # Number of absent days to flag as repeated
UNSTABLE_SHIFT_THRESHOLD = 180  # Minutes (3 hours) of shift time variation 

class DriverTrendData:
    """Class to store attendance trend data for a driver"""
    
    def __init__(self, name: str):
        self.name = name
        self.dates = {}  # type: Dict[str, Dict[str, bool]]
        self.late_days = 0
        self.early_end_days = 0
        self.absent_days = 0
        self.start_times = []  # type: List[Tuple[str, str]]
        self.end_times = []    # type: List[Tuple[str, str]]
        self.flags = []        # type: List[str]

def analyze_trends(date_range=None, specific_dates=None):
    """
    Analyze attendance trends across multiple days.
    
    Args:
        date_range (tuple): (start_date, end_date) in YYYY-MM-DD format
        specific_dates (list): List of specific dates to analyze in YYYY-MM-DD format
        
    Returns:
        dict: Trend analysis results
    """
    # Initialize result structure
    results = {
        'date_range': {},
        'daily_summaries': {},
        'driver_trends': [],
        'trend_summary': {
            'total_drivers_analyzed': 0,
            'chronic_late_count': 0,
            'repeated_absence_count': 0,
            'unstable_shift_count': 0,
            'days_analyzed': 0
        }
    }
    
    # Determine which dates to process
    dates_to_process = []
    if specific_dates:
        dates_to_process = specific_dates
        results['date_range'] = {
            'start': min(specific_dates),
            'end': max(specific_dates)
        }
    elif date_range:
        start_date, end_date = date_range
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current_date <= end:
            dates_to_process.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
            
        results['date_range'] = {
            'start': start_date,
            'end': end_date
        }
    else:
        # Default to last 5 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=4)
        
        for i in range(5):
            date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            dates_to_process.append(date)
            
        results['date_range'] = {
            'start': dates_to_process[0],
            'end': dates_to_process[-1]
        }
    
    results['trend_summary']['days_analyzed'] = len(dates_to_process)
    
    # Dictionary to track driver data across all dates
    driver_data = {}  # type: Dict[str, DriverTrendData]
    
    # Process each date
    for date in dates_to_process:
        attendance_data = process_attendance_data(date)
        if not attendance_data:
            logger.warning(f"No attendance data for {date}")
            continue
            
        # Store daily summary
        results['daily_summaries'][date] = {
            'late_count': len(attendance_data.get('late_drivers', [])),
            'early_end_count': len(attendance_data.get('early_end_drivers', [])),
            'not_on_job_count': len(attendance_data.get('not_on_job_drivers', []))
        }
        
        # Process late drivers
        for driver in attendance_data.get('late_drivers', []):
            name = driver.get('driver', '')
            if not name:
                continue
                
            normalized_name = normalize_driver_name(name)
            
            # Initialize driver data if needed
            if normalized_name not in driver_data:
                driver_data[normalized_name] = DriverTrendData(name)
                
            # Update driver data
            driver_data[normalized_name].late_days += 1
            
            # Store start/end times for shift stability analysis
            if 'time_start' in driver and driver['time_start']:
                driver_data[normalized_name].start_times.append(
                    (date, driver['time_start'])
                )
            if 'time_stop' in driver and driver['time_stop']:
                driver_data[normalized_name].end_times.append(
                    (date, driver['time_stop'])
                )
                
            # Store date-specific data
            driver_data[normalized_name].dates[date] = {
                'late': True,
                'early_end': False,
                'absent': False
            }
                
        # Process early end drivers
        for driver in attendance_data.get('early_end_drivers', []):
            name = driver.get('driver', '')
            if not name:
                continue
                
            normalized_name = normalize_driver_name(name)
            
            # Initialize driver data if needed
            if normalized_name not in driver_data:
                driver_data[normalized_name] = DriverTrendData(name)
                
            # Update driver data
            driver_data[normalized_name].early_end_days += 1
            
            # Add start/end times if not already added
            date_start_times = {d[0] for d in driver_data[normalized_name].start_times}
            date_end_times = {d[0] for d in driver_data[normalized_name].end_times}
            
            if 'time_start' in driver and driver['time_start'] and date not in date_start_times:
                driver_data[normalized_name].start_times.append(
                    (date, driver['time_start'])
                )
            if 'time_stop' in driver and driver['time_stop'] and date not in date_end_times:
                driver_data[normalized_name].end_times.append(
                    (date, driver['time_stop'])
                )
            
            # Update or create date entry
            if date in driver_data[normalized_name].dates:
                driver_data[normalized_name].dates[date]['early_end'] = True
            else:
                driver_data[normalized_name].dates[date] = {
                    'late': False,
                    'early_end': True,
                    'absent': False
                }
                
        # Process not on job drivers
        for driver in attendance_data.get('not_on_job_drivers', []):
            name = driver.get('driver', '')
            if not name:
                continue
                
            normalized_name = normalize_driver_name(name)
            
            # Initialize driver data if needed
            if normalized_name not in driver_data:
                driver_data[normalized_name] = DriverTrendData(name)
                
            # Update driver data
            driver_data[normalized_name].absent_days += 1
            
            # Store date-specific data
            driver_data[normalized_name].dates[date] = {
                'late': False,
                'early_end': False,
                'absent': True
            }
    
    # Analyze trends for each driver
    for normalized_name, data in driver_data.items():
        flags = []
        
        # Check for chronic lateness
        if data.late_days >= CHRONIC_LATE_THRESHOLD:
            flags.append('CHRONIC_LATE')
            results['trend_summary']['chronic_late_count'] += 1
            
        # Check for repeated absences
        if data.absent_days >= REPEATED_ABSENCE_THRESHOLD:
            flags.append('REPEATED_ABSENCE')
            results['trend_summary']['repeated_absence_count'] += 1
            
        # Check for unstable shifts
        if has_unstable_shifts(data.start_times, data.end_times):
            flags.append('UNSTABLE_SHIFT')
            results['trend_summary']['unstable_shift_count'] += 1
            
        # Only add drivers with flags to the results
        if flags:
            data.flags = flags
            results['driver_trends'].append({
                'employee_id': f"D{len(results['driver_trends']):03d}",
                'name': data.name,
                'flags': flags,
                'days_analyzed': len(data.dates),
                'late_count': data.late_days,
                'early_end_count': data.early_end_days,
                'absence_count': data.absent_days
            })
    
    results['trend_summary']['total_drivers_analyzed'] = len(driver_data)
    return results

def has_unstable_shifts(start_times, end_times):
    """
    Determine if a driver has unstable shift times.
    
    Args:
        start_times: List of (date, time_str) tuples
        end_times: List of (date, time_str) tuples
        
    Returns:
        bool: True if shifts are unstable, False otherwise
    """
    from time_utils import parse_time
    
    # Need at least 2 shifts to detect instability
    if len(start_times) < 2:
        return False
        
    # Check start time variation
    start_minutes = []
    for _, time_str in start_times:
        time_obj = parse_time(time_str)
        if time_obj:
            minutes = time_obj.hour * 60 + time_obj.minute
            start_minutes.append(minutes)
            
    if len(start_minutes) >= 2:
        variation = max(start_minutes) - min(start_minutes)
        if variation > UNSTABLE_SHIFT_THRESHOLD:
            return True
            
    # Check end time variation
    end_minutes = []
    for _, time_str in end_times:
        time_obj = parse_time(time_str)
        if time_obj:
            minutes = time_obj.hour * 60 + time_obj.minute
            end_minutes.append(minutes)
            
    if len(end_minutes) >= 2:
        variation = max(end_minutes) - min(end_minutes)
        if variation > UNSTABLE_SHIFT_THRESHOLD:
            return True
            
    return False

def generate_trend_report(output_path, date_range=None, specific_dates=None):
    """
    Generate and save a trend report.
    
    Args:
        output_path: Path to save the report
        date_range: Tuple of (start_date, end_date)
        specific_dates: List of specific dates to analyze
        
    Returns:
        dict: Trend analysis results
    """
    results = analyze_trends(date_range, specific_dates)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
        
    logger.info(f"Trend report saved to {output_path}")
    return results