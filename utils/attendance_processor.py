"""
Attendance Data Processor

This module processes driver attendance data from various input files
and formats it for use in the daily driver report.
"""

import os
import csv
import pandas as pd
from datetime import datetime, timedelta
import logging

# Configure logging
logger = logging.getLogger(__name__)

def parse_time(time_str, default=None):
    """Parse time string in various formats and return a datetime object"""
    if not time_str or time_str == 'N/A':
        return default
        
    try:
        # Handle format like "06:15 AM CT"
        if 'CT' in time_str:
            time_str = time_str.replace(' CT', '')
        
        # Parse time in 12-hour format
        return datetime.strptime(time_str, '%I:%M %p')
    except Exception as e:
        logger.error(f"Error parsing time '{time_str}': {e}")
        return default

def calculate_minutes_late(scheduled_time, actual_time, threshold_minutes=5):
    """
    Calculate minutes late between scheduled and actual times
    Only counts as late if more than threshold_minutes (default 5) late
    """
    if not scheduled_time or not actual_time:
        return 0
        
    # Calculate time difference in minutes
    diff_minutes = (actual_time - scheduled_time).seconds // 60
    
    # Only consider late if more than threshold minutes
    return max(0, diff_minutes - threshold_minutes) if diff_minutes > threshold_minutes else 0

def calculate_minutes_early(scheduled_time, actual_time, threshold_minutes=5):
    """
    Calculate minutes early for departure between scheduled and actual times
    Only counts as early if more than threshold_minutes (default 5) early
    """
    if not scheduled_time or not actual_time:
        return 0
        
    # Calculate time difference in minutes
    diff_minutes = (scheduled_time - actual_time).seconds // 60
    
    # Only consider early if more than threshold minutes
    return max(0, diff_minutes - threshold_minutes) if diff_minutes > threshold_minutes else 0

def process_daily_usage_data(file_path, date_str=None):
    """
    Process daily usage data from CSV file
    
    Args:
        file_path (str): Path to the daily usage CSV file
        date_str (str): Date string in YYYY-MM-DD format, defaults to today
        
    Returns:
        dict: Processed daily report data
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None
        
    # Default to today if no date provided
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Convert date string to datetime object
    try:
        report_date = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = report_date.strftime('%A, %B %d, %Y')
    except Exception as e:
        logger.error(f"Error parsing date '{date_str}': {e}")
        report_date = datetime.now()
        formatted_date = report_date.strftime('%A, %B %d, %Y')
    
    # Standard start/end times
    standard_start_time = parse_time('07:00 AM')
    standard_end_time = parse_time('05:00 PM')
    
    # Initialize report data
    report = {
        'date': date_str,
        'formatted_date': formatted_date,
        'divisions': set(),
        'summary': {
            'total_drivers': 0,            # Total unique drivers
            'on_time_drivers': 0,          # Drivers who arrived on time
            'total_issues': 0,             # Total of all issue categories combined
            'late_drivers': 0,             # Drivers who were late
            'early_end_drivers': 0,        # Drivers who left early
            'not_on_job_drivers': 0,       # Drivers not on job
            'exception_drivers': 0         # Drivers with exceptions/missing data
        },
        'late_drivers': [],
        'early_end_drivers': [],
        'not_on_job_drivers': [],
        'exceptions': []
    }
    
    try:
        # Read CSV file using pandas to handle complex format with header rows
        # Skip the header section (first 6 rows) and use row 7 as header
        df = pd.read_csv(file_path, skiprows=6, low_memory=False)
        
        # Normalize column names (remove spaces, lowercase)
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
        
        # Track unique drivers to avoid duplicates
        unique_drivers = set()
        
        # Process each row as a driver entry
        for _, row in df.iterrows():
            try:
                # Extract driver info and times
                asset_label = str(row.get('assetlabel', 'Unknown')).split(' - ')
                employee_id = asset_label[0].strip() if len(asset_label) > 0 else 'Unknown'
                driver_name = asset_label[1].strip() if len(asset_label) > 1 else 'Unknown'
                
                # Skip if we've already processed this driver
                driver_key = f"{employee_id}_{driver_name}"
                if driver_key in unique_drivers:
                    continue
                
                unique_drivers.add(driver_key)
                
                # Get vehicle info - parse from asset label if available
                vehicle_info = ""
                if len(asset_label) > 2:
                    vehicle_info = asset_label[2].strip()
                else:
                    vehicle_info = str(row.get('assettype', '')).strip()
                
                # Get division/region from CompanyName or other field
                division = str(row.get('companyname1', 'Unknown')).strip()
                report['divisions'].add(division)
                
                # Get job site from Location
                location = str(row.get('location', 'Unknown')).strip()
                job_site = location
                if ',' in location:
                    # Extract city and state from location
                    job_site = location.split(',')[0].strip()
                
                # Get start/end times and parse them
                started = str(row.get('started', 'N/A')).strip()
                stopped = str(row.get('stopped', 'N/A')).strip()
                
                # Use start time from data file or default to standard
                actual_start_time = None
                if started and started != 'N/A':
                    actual_start_time = parse_time(started)
                
                # Use end time from data file or default to standard
                actual_end_time = None  
                if stopped and stopped != 'N/A':
                    actual_end_time = parse_time(stopped)
                
                # Count as a driver
                report['summary']['total_drivers'] += 1
                
                # Check for morning attendance
                if actual_start_time:
                    report['summary']['total_morning_drivers'] += 1
                    
                    # Calculate lateness
                    minutes_late = 0
                    if standard_start_time:
                        # Only compare if we have both times
                        minutes_late = calculate_minutes_late(standard_start_time, actual_start_time) if actual_start_time > standard_start_time else 0
                    
                    # Check if late
                    if minutes_late > 0:
                        report['summary']['late_drivers'] += 1
                        report['late_drivers'].append({
                            'id': len(report['late_drivers']) + 1,
                            'employee_id': employee_id,
                            'name': driver_name,
                            'division': division,
                            'region': division,
                            'job_site': job_site,
                            'expected_start': standard_start_time.strftime('%I:%M %p') if standard_start_time else "07:00 AM",
                            'actual_start': actual_start_time.strftime('%I:%M %p') if actual_start_time else "N/A",
                            'scheduled_start': standard_start_time.strftime('%I:%M %p') if standard_start_time else "07:00 AM",
                            'minutes_late': minutes_late,
                            'vehicle': vehicle_info
                        })
                    else:
                        report['summary']['on_time_drivers'] += 1
                
                # Check for early departure
                if actual_end_time and standard_end_time:
                    minutes_early = calculate_minutes_early(standard_end_time, actual_end_time) if actual_end_time < standard_end_time else 0
                    
                    if minutes_early > 0:
                        report['summary']['early_end_drivers'] += 1
                        report['early_end_drivers'].append({
                            'id': len(report['early_end_drivers']) + 1,
                            'employee_id': employee_id,
                            'name': driver_name,
                            'division': division,
                            'region': division,
                            'job_site': job_site,
                            'expected_end': standard_end_time.strftime('%I:%M %p') if standard_end_time else "05:00 PM",
                            'actual_end': actual_end_time.strftime('%I:%M %p') if actual_end_time else "N/A",
                            'minutes_early': minutes_early,
                            'vehicle': vehicle_info
                        })
                
                # Check for missing data (exceptions)
                if not actual_start_time or not actual_end_time:
                    report['summary']['exception_drivers'] += 1
                    report['exceptions'].append({
                        'id': len(report['exceptions']) + 1,
                        'employee_id': employee_id,
                        'name': driver_name,
                        'division': division,
                        'region': division,
                        'job_site': job_site,
                        'expected_time': standard_start_time.strftime('%I:%M %p') if standard_start_time else "07:00 AM",
                        'actual_time': 'No Data',
                        'exception_type': 'Missing GPS Data',
                        'vehicle': vehicle_info
                    })
                
            except Exception as e:
                logger.error(f"Error processing row: {e}")
                continue
        
        # Convert divisions to list for serialization
        report['divisions'] = list(report['divisions'])
        
        # Add some default empty list if needed by the template
        if 'not_on_job_drivers' not in report or not report['not_on_job_drivers']:
            report['not_on_job_drivers'] = []
            
        return report
        
    except Exception as e:
        logger.error(f"Error processing daily usage data: {e}")
        return None

def process_attendance_file(file_path):
    """
    Process attendance file based on its type
    
    Args:
        file_path (str): Path to the attendance file
        
    Returns:
        dict: Processed attendance data
    """
    # Determine file type based on extension
    _, ext = os.path.splitext(file_path)
    
    if ext.lower() == '.csv':
        if 'dailyusage' in file_path.lower():
            return process_daily_usage_data(file_path)
        # Add other CSV file processors as needed
    
    elif ext.lower() in ['.xlsx', '.xls']:
        # Process Excel files
        return None
    
    # Default fallback
    logger.error(f"Unsupported file type: {ext}")
    return None