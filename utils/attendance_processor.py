"""
Attendance Processor Module

This module handles processing of daily usage data to generate attendance reports.
It identifies late drivers, early end drivers, and other attendance issues.
"""

import os
import sys
import csv
import logging
from datetime import datetime, timedelta

# Add project root to path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import config
from driver_utils import extract_driver_from_label, clean_asset_info, is_vehicle_id
from time_utils import (
    parse_time, 
    parse_time_with_day_marker,
    calculate_time_difference, 
    calculate_lateness, 
    in_allowed_range
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_daily_usage_file(file_path, target_date=None):
    """
    Read and parse a DailyUsage.csv file to extract attendance data
    
    Args:
        file_path (str): Path to the DailyUsage.csv file
        target_date (str, optional): Target date in YYYY-MM-DD format. If provided,
                                    only records for this date will be processed.
                                    
    Returns:
        dict: Dictionary with parsed attendance data
    """
    try:
        # Initialize results
        results = {
            'date': target_date,
            'raw_data': [],
            'late_drivers': [],
            'early_end_drivers': [],
            'not_on_job_drivers': [],
            'exception_drivers': []
        }
        
        # Read the CSV file
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            # Skip header lines (varies in real files)
            for _ in range(7):  # Skip typical header rows
                next(csvfile, None)
            
            # Parse CSV
            reader = csv.DictReader(csvfile)
            for row in reader:
                if not row or 'Date' not in row:
                    continue
                
                # If target_date is provided, only process matching records
                if target_date and row['Date'] != target_date:
                    continue
                
                # Use the date from the data if target_date not specified
                if not target_date and not results['date']:
                    results['date'] = row['Date']
                
                # Add to raw data
                results['raw_data'].append(row)
        
        # Process the data to identify attendance issues
        processed_data = process_attendance_data_from_raw(results['raw_data'])
        
        # Update results with processed data
        results.update(processed_data)
        
        return results
        
    except Exception as e:
        logger.error(f"Error reading DailyUsage file: {e}")
        return {'error': str(e)}

def process_attendance_data(date=None):
    """
    Process attendance data for the specified date
    
    Args:
        date (str, optional): Date in YYYY-MM-DD format. If None, today's date will be used.
        
    Returns:
        dict: Dictionary with attendance data
    """
    # Use today's date if none provided
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # Find the appropriate DailyUsage.csv file
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    available_files = [f for f in os.listdir(uploads_dir) if f.endswith('.csv')]
    
    file_to_use = None
    for filename in available_files:
        if 'DailyUsage' in filename:
            file_to_use = os.path.join(uploads_dir, filename)
            break
    
    if not file_to_use:
        logger.error(f"No DailyUsage file found in {uploads_dir}")
        return None
    
    # Process the file
    return read_daily_usage_file(file_to_use, date)

def process_attendance_data_from_raw(raw_data):
    """
    Process raw attendance data to identify attendance issues
    
    Args:
        raw_data (list): List of dictionaries with raw attendance data
        
    Returns:
        dict: Dictionary with processed attendance data
    """
    # Initialize results
    results = {
        'late_drivers': [],
        'early_end_drivers': [],
        'not_on_job_drivers': [],
        'exception_drivers': [],
        'summary': {
            'total_drivers': 0,
            'total_issues': 0,
            'late_count': 0,
            'early_end_count': 0,
            'not_on_job_count': 0,
            'exception_count': 0
        }
    }
    
    # Set for tracking unique drivers
    unique_drivers = set()
    
    # Process each record
    for record in raw_data:
        # Skip records without an asset label
        if 'Asset' not in record or not record['Asset']:
            continue
        
        # Extract driver and asset info
        asset_label = record['Asset']
        driver_name = extract_driver_from_label(asset_label)
        asset_id = clean_asset_info(asset_label)
        
        # Skip if no driver name could be extracted
        if not driver_name:
            continue
        
        # Add to unique drivers set
        unique_drivers.add(driver_name)
        
        # Extract time data
        time_start = record.get('Time Start', '')
        time_stop = record.get('Time Stop', '')
        
        # Parse expected times
        expected_start = config.EXPECTED_START_TIME  # e.g., "07:00 AM"
        expected_end = config.EXPECTED_END_TIME      # e.g., "03:30 PM"
        
        # Define grace periods (in minutes)
        late_grace_period = config.LATE_GRACE_PERIOD  # e.g., 15
        early_end_grace_period = config.EARLY_END_GRACE_PERIOD  # e.g., 15
        
        # Create driver record
        driver_record = {
            'driver': driver_name,
            'asset': asset_id,
            'asset_label': asset_label,
            'company': record.get('Company', ''),
            'job_site': record.get('Job Site', ''),
            'time_start': time_start,
            'time_stop': time_stop
        }
        
        # Check for not on job (missing start or end time)
        if not time_start or not time_stop:
            results['not_on_job_drivers'].append(driver_record)
            continue
        
        # Check for late start - with next-day marker detection
        parsed_start, start_is_next_day = parse_time_with_day_marker(time_start)
        parsed_expected_start = parse_time(expected_start)
        
        if parsed_start and parsed_expected_start:
            # Use the improved lateness calculation that handles next-day markers
            is_late, minutes_late, lateness_text = calculate_lateness(
                parsed_start, parsed_expected_start, late_grace_period, start_is_next_day
            )
            
            if is_late:
                # Add late start info
                driver_record['minutes_late'] = minutes_late
                driver_record['lateness_text'] = lateness_text
                driver_record['start_is_overnight'] = start_is_next_day
                results['late_drivers'].append(driver_record)
        
        # Check for early end - with next-day marker detection
        parsed_end, end_is_next_day = parse_time_with_day_marker(time_stop)
        parsed_expected_end = parse_time(expected_end)
        
        if parsed_end and parsed_expected_end:
            # For early end, we're checking if they left before expected end time
            # For overnight shifts, we need special handling
            
            if end_is_next_day:
                # For overnight shifts with next-day markers, compare based on hours/minutes within a day
                # rather than absolute datetime difference
                expected_minutes = parsed_expected_end.hour * 60 + parsed_expected_end.minute
                actual_minutes = parsed_end.hour * 60 + parsed_end.minute
                
                # If the expected end time is PM (afternoon) and actual end time is AM (morning next day)
                # then this is not an early end, it's actually working longer
                if parsed_expected_end.hour >= 12 and parsed_end.hour < 12:
                    # They worked past midnight when they were expected to end in the afternoon
                    # This is not an early end
                    minutes_early = 0
                else:
                    # Normal comparison of minutes within the day
                    minutes_early = expected_minutes - actual_minutes
            else:
                # Standard calculation for same-day shifts
                # For early end, we need expected_end - actual_end
                minutes_early = calculate_time_difference(parsed_end, parsed_expected_end)
            
            # Only flag as early end if they actually left early
            if minutes_early > early_end_grace_period:
                # Format human-readable time text
                hours = minutes_early // 60
                remaining_minutes = minutes_early % 60
                
                if hours > 0:
                    early_text = f"{hours}h {remaining_minutes}m early"
                else:
                    early_text = f"{minutes_early} minutes early"
                
                # Add early end info
                driver_record['minutes_early'] = minutes_early
                driver_record['early_text'] = early_text
                driver_record['end_is_overnight'] = end_is_next_day
                results['early_end_drivers'].append(driver_record)
    
    # Update summary statistics
    results['summary']['total_drivers'] = len(unique_drivers)
    results['summary']['late_count'] = len(results['late_drivers'])
    results['summary']['early_end_count'] = len(results['early_end_drivers'])
    results['summary']['not_on_job_count'] = len(results['not_on_job_drivers'])
    results['summary']['exception_count'] = len(results['exception_drivers'])
    
    # Calculate total issues
    results['summary']['total_issues'] = (
        results['summary']['late_count'] +
        results['summary']['early_end_count'] +
        results['summary']['not_on_job_count'] +
        results['summary']['exception_count']
    )
    
    return results