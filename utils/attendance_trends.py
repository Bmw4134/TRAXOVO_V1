"""
Attendance Trends Module

This module extends the attendance processor to analyze trends across multiple days,
identifying patterns such as chronic lateness, repeated absences, or unstable shifts.
"""

import os
import sys
import csv
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict

# Add project root to path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import config
from utils.attendance_processor import read_daily_usage_file, process_attendance_data
from driver_utils import extract_driver_from_label, clean_asset_info, is_vehicle_id, normalize_driver_name

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for trend flags
CHRONIC_LATE_THRESHOLD = 3  # Number of late occurrences in observation period
REPEATED_ABSENCE_THRESHOLD = 2  # Number of absences in observation period
UNSTABLE_SHIFT_THRESHOLD = 180  # Minutes (3 hours) of variation in start/end times

def process_date_range(start_date=None, end_date=None, file_path=None):
    """
    Process attendance data for a range of dates
    
    Args:
        start_date (str or list, optional): Start date in YYYY-MM-DD format or a list of dates
        end_date (str, optional): End date in YYYY-MM-DD format (inclusive)
        file_path (str, optional): Path to the DailyUsage.csv file, if None will search in uploads folder
    
    Returns:
        dict: Dictionary with trend analysis and per-driver summaries
    """
    # Default to today if no start_date provided
    if start_date is None:
        start_date = datetime.now().strftime('%Y-%m-%d')
    # Initialize result structure
    result = {
        'date_range': {},
        'daily_summaries': {},
        'driver_trends': [],
        'trend_summary': {
            'chronic_late_count': 0,
            'repeated_absence_count': 0,
            'unstable_shift_count': 0,
            'total_drivers_analyzed': 0,
            'days_analyzed': 0
        }
    }
    
    # Handle different input formats
    dates_to_process = []
    if isinstance(start_date, list):
        # If a list of dates is provided
        dates_to_process = start_date
        result['date_range'] = {
            'start': min(dates_to_process),
            'end': max(dates_to_process)
        }
    else:
        # If a start and end date are provided
        if end_date:
            # Generate all dates in the range
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Include both start and end dates
            current_date = start
            while current_date <= end:
                dates_to_process.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
                
            result['date_range'] = {
                'start': start_date,
                'end': end_date
            }
        else:
            # If only one date is provided
            dates_to_process = [start_date]
            result['date_range'] = {
                'start': start_date,
                'end': start_date
            }
    
    # Process each date - create a nested defaultdict to properly initialize each driver
    all_driver_data = {}
    
    # Helper function to create a new driver entry
    def create_driver_entry():
        return {
            'name': '',
            'employee_id': '',  # Will be populated if available
            'dates': {},
            'late_count': 0,
            'early_end_count': 0,
            'absence_count': 0,
            'start_times': [],
            'end_times': [],
            'flags': []
        }
    
    result['trend_summary']['days_analyzed'] = len(dates_to_process)
    
    for date in dates_to_process:
        # Process attendance data for this date
        attendance_data = process_attendance_data(date, file_path)
        if not attendance_data:
            logger.warning(f"No attendance data available for {date}")
            continue
        
        # Store daily summary
        result['daily_summaries'][date] = {
            'late_count': len(attendance_data.get('late_drivers', [])),
            'early_end_count': len(attendance_data.get('early_end_drivers', [])),
            'not_on_job_count': len(attendance_data.get('not_on_job_drivers', [])),
            'total_drivers': attendance_data.get('summary', {}).get('total_drivers', 0)
        }
        
        # Process each driver
        unique_drivers_processed = set()
        
        # Process late drivers
        for driver in attendance_data.get('late_drivers', []):
            driver_name = driver.get('driver', '')
            if not driver_name:
                continue
                
            # Normalize the driver name to handle different formats
            normalized_name = normalize_driver_name(driver_name)
            
            # Initialize driver entry if not exists
            if normalized_name not in all_driver_data:
                all_driver_data[normalized_name] = create_driver_entry()
            
            # Add to driver data
            all_driver_data[normalized_name]['name'] = driver_name
            
            # Add date-specific data
            all_driver_data[normalized_name]['dates'][date] = {
                'late': True,
                'early_end': False,
                'not_on_job': False,
                'time_start': driver.get('time_start', ''),
                'time_stop': driver.get('time_stop', ''),
                'minutes_late': driver.get('minutes_late', 0)
            }
            
            # Increment late count
            all_driver_data[normalized_name]['late_count'] += 1
            
            # Add start time for variation analysis
            if driver.get('time_start'):
                all_driver_data[normalized_name]['start_times'].append(
                    (date, driver.get('time_start', ''))
                )
            
            # Add end time for variation analysis
            if driver.get('time_stop'):
                all_driver_data[normalized_name]['end_times'].append(
                    (date, driver.get('time_stop', ''))
                )
                
            unique_drivers_processed.add(normalized_name)
        
        # Process early end drivers
        for driver in attendance_data.get('early_end_drivers', []):
            driver_name = driver.get('driver', '')
            if not driver_name:
                continue
                
            # Normalize the driver name
            normalized_name = normalize_driver_name(driver_name)
            
            # Initialize driver entry if not exists
            if normalized_name not in all_driver_data:
                all_driver_data[normalized_name] = create_driver_entry()
            
            # Add to driver data
            all_driver_data[normalized_name]['name'] = driver_name
            
            # Check if we already processed this driver from late drivers
            if normalized_name in unique_drivers_processed:
                # Update existing date entry
                if date in all_driver_data[normalized_name]['dates']:
                    all_driver_data[normalized_name]['dates'][date]['early_end'] = True
                    all_driver_data[normalized_name]['dates'][date]['minutes_early'] = driver.get('minutes_early', 0)
                else:
                    # Create new date entry
                    all_driver_data[normalized_name]['dates'][date] = {
                        'late': False,
                        'early_end': True,
                        'not_on_job': False,
                        'time_start': driver.get('time_start', ''),
                        'time_stop': driver.get('time_stop', ''),
                        'minutes_early': driver.get('minutes_early', 0)
                    }
            else:
                # Create new date entry
                all_driver_data[normalized_name]['dates'][date] = {
                    'late': False,
                    'early_end': True,
                    'not_on_job': False,
                    'time_start': driver.get('time_start', ''),
                    'time_stop': driver.get('time_stop', ''),
                    'minutes_early': driver.get('minutes_early', 0)
                }
            
            # Increment early end count
            all_driver_data[normalized_name]['early_end_count'] += 1
            
            # Add start/end times if we haven't already from late drivers
            if normalized_name not in unique_drivers_processed:
                if driver.get('time_start'):
                    all_driver_data[normalized_name]['start_times'].append(
                        (date, driver.get('time_start', ''))
                    )
                
                if driver.get('time_stop'):
                    all_driver_data[normalized_name]['end_times'].append(
                        (date, driver.get('time_stop', ''))
                    )
                
                unique_drivers_processed.add(normalized_name)
        
        # Process not on job drivers
        for driver in attendance_data.get('not_on_job_drivers', []):
            driver_name = driver.get('driver', '')
            if not driver_name:
                continue
                
            # Normalize the driver name
            normalized_name = normalize_driver_name(driver_name)
            
            # Initialize driver entry if not exists
            if normalized_name not in all_driver_data:
                all_driver_data[normalized_name] = create_driver_entry()
            
            # Add to driver data
            all_driver_data[normalized_name]['name'] = driver_name
            
            # Add date-specific data
            all_driver_data[normalized_name]['dates'][date] = {
                'late': False,
                'early_end': False,
                'not_on_job': True
            }
            
            # Increment absence count
            all_driver_data[normalized_name]['absence_count'] += 1
            
            unique_drivers_processed.add(normalized_name)
    
    # Analyze trends for each driver
    for driver_id, driver_data in all_driver_data.items():
        # Skip drivers with no data
        if not driver_data['dates']:
            continue
        
        # Check for trend flags
        flags = []
        
        # Check for chronic lateness
        if driver_data['late_count'] >= CHRONIC_LATE_THRESHOLD:
            flags.append('CHRONIC_LATE')
            result['trend_summary']['chronic_late_count'] += 1
        
        # Check for repeated absences
        if driver_data['absence_count'] >= REPEATED_ABSENCE_THRESHOLD:
            flags.append('REPEATED_ABSENCE')
            result['trend_summary']['repeated_absence_count'] += 1
        
        # Check for unstable shifts
        if _has_unstable_shifts(driver_data['start_times'], driver_data['end_times']):
            flags.append('UNSTABLE_SHIFT')
            result['trend_summary']['unstable_shift_count'] += 1
        
        # Set flags
        driver_data['flags'] = flags
        
        # Add to driver trends
        result['driver_trends'].append({
            'employee_id': driver_data.get('employee_id', f"D{len(result['driver_trends']):03d}"),
            'name': driver_data['name'],
            'flags': flags,
            'days_analyzed': len(driver_data['dates']),
            'late_count': driver_data['late_count'],
            'early_end_count': driver_data['early_end_count'],
            'absence_count': driver_data['absence_count']
        })
    
    # Update total drivers analyzed
    result['trend_summary']['total_drivers_analyzed'] = len(result['driver_trends'])
    
    return result

def _has_unstable_shifts(start_times, end_times):
    """
    Check if a driver has unstable shift times
    
    Args:
        start_times (list): List of (date, time) tuples for start times
        end_times (list): List of (date, time) tuples for end times
    
    Returns:
        bool: True if shifts are unstable, False otherwise
    """
    from time_utils import parse_time
    
    # If less than 2 shifts recorded, can't determine stability
    if len(start_times) < 2:
        return False
    
    # Convert times to minutes since midnight for comparison
    start_minutes = []
    for _, time_str in start_times:
        time_obj = parse_time(time_str)
        if time_obj:
            minutes = time_obj.hour * 60 + time_obj.minute
            start_minutes.append(minutes)
    
    # Calculate max difference in start times
    if start_minutes:
        start_diff = max(start_minutes) - min(start_minutes)
        if start_diff > UNSTABLE_SHIFT_THRESHOLD:
            return True
    
    # Repeat for end times
    end_minutes = []
    for _, time_str in end_times:
        time_obj = parse_time(time_str)
        if time_obj:
            minutes = time_obj.hour * 60 + time_obj.minute
            end_minutes.append(minutes)
    
    # Calculate max difference in end times
    if end_minutes:
        end_diff = max(end_minutes) - min(end_minutes)
        if end_diff > UNSTABLE_SHIFT_THRESHOLD:
            return True
    
    return False

def generate_trend_report(start_date, end_date=None, file_path=None, output_file=None):
    """
    Generate a trend report for the specified date range
    
    Args:
        start_date (str or list): Start date in YYYY-MM-DD format or a list of dates
        end_date (str, optional): End date in YYYY-MM-DD format (inclusive)
        file_path (str, optional): Path to the DailyUsage.csv file
        output_file (str, optional): Path to output JSON file
    
    Returns:
        dict: Dictionary with trend analysis
    """
    # Process the date range
    trend_data = process_date_range(start_date, end_date, file_path)
    
    # Write to output file if specified
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(trend_data, f, indent=2)
        logger.info(f"Trend report written to {output_file}")
    
    return trend_data