"""
Attendance Processor Module

This module processes attendance data from Daily Usage CSV and Excel files,
extracts structured information about driver attendance, and identifies issues
such as late starts, early ends, and drivers not on job.
"""

import os
import re
import logging
import pandas as pd
from datetime import datetime, time

from time_utils import parse_time_string, is_late_start, is_early_end
from driver_utils import extract_driver_from_label, clean_asset_info
from config import (
    SKIPROWS_DAILY_USAGE, 
    DRIVER_EXPECTED_START_TIME, 
    DRIVER_EXPECTED_END_TIME,
    DRIVER_LATE_THRESHOLD_MINUTES,
    DRIVER_EARLY_END_THRESHOLD_MINUTES,
    UPLOADS_FOLDER
)

# Configure logger
logger = logging.getLogger(__name__)

def find_latest_daily_file(file_pattern='DailyUsage', extension='.csv'):
    """
    Find the most recent Daily Usage file in the uploads folder
    
    Args:
        file_pattern (str): Pattern to match in filenames
        extension (str): File extension to look for
        
    Returns:
        str: Path to the latest file, or None if not found
    """
    try:
        files = [f for f in os.listdir(UPLOADS_FOLDER) 
                if file_pattern in f and f.endswith(extension)]
        
        if not files:
            logger.warning(f"No {file_pattern} files found in {UPLOADS_FOLDER}")
            return None
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(UPLOADS_FOLDER, x)), 
                  reverse=True)
        
        return os.path.join(UPLOADS_FOLDER, files[0])
    except Exception as e:
        logger.error(f"Error finding latest file: {e}")
        return None

def extract_employee_id(driver_name):
    """
    Extract employee ID from driver name if present
    Pattern: Name may contain ID in format "NAME (ID123)" or "NAME - ID123"
    
    Args:
        driver_name (str): Driver name possibly containing ID
        
    Returns:
        tuple: (clean_name, employee_id) where employee_id may be None
    """
    if not driver_name or not isinstance(driver_name, str):
        return "", None
    
    # Clean up
    driver_name = driver_name.strip()
    
    # Check for ID in parentheses: "NAME (ID123)"
    paren_match = re.search(r'(.*?)\s*\(([A-Z0-9]+)\)\s*$', driver_name)
    if paren_match:
        return paren_match.group(1).strip(), paren_match.group(2)
    
    # Check for ID after dash: "NAME - ID123"
    dash_match = re.search(r'(.*?)\s*-\s*([A-Z0-9]+)\s*$', driver_name)
    if dash_match:
        return dash_match.group(1).strip(), dash_match.group(2)
    
    # Check for standard employee ID format at the end: "NAME EMP123"
    id_match = re.search(r'(.*?)\s+((?:EMP|ID|E)[0-9]{3,6})\s*$', driver_name, re.IGNORECASE)
    if id_match:
        return id_match.group(1).strip(), id_match.group(2)
    
    # No employee ID found
    return driver_name, None

def read_daily_usage_file(file_path=None, date=None):
    """
    Read and parse a Daily Usage CSV file
    
    Args:
        file_path (str): Path to CSV file, or None to find latest
        date (str): Date to filter records by (YYYY-MM-DD format)
        
    Returns:
        dict: Processed data with driver attendance details
    """
    # Find latest file if not specified
    if not file_path:
        file_path = find_latest_daily_file()
        if not file_path:
            logger.error("No Daily Usage file found")
            return {'error': 'No Daily Usage file found'}
    
    try:
        # Read CSV with custom handling for odd format
        # Skip initial rows as specified in config
        df = pd.read_csv(file_path, skiprows=SKIPROWS_DAILY_USAGE)
        
        # Clean up column names (they may have whitespace or unusual characters)
        df.columns = [c.strip() for c in df.columns]
        
        # Standardize expected column names
        column_mapping = {
            'Asset': 'asset_label',
            'Asset Label': 'asset_label',
            'Date': 'date',
            'Time Start': 'start_time',
            'Start Time': 'start_time',
            'Time Stop': 'end_time',
            'End Time': 'end_time',
            'Stop Time': 'end_time',
            'Company': 'company',
            'Job Site': 'job_site',
            'Location': 'location'
        }
        
        # Rename columns based on mapping
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df.rename(columns={old_name: new_name}, inplace=True)
        
        # Check that required columns exist
        required_columns = ['asset_label', 'date', 'start_time', 'end_time']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns in CSV: {missing_columns}")
            return {'error': f"File is missing required columns: {', '.join(missing_columns)}"}
        
        # Filter by date if specified
        if date:
            try:
                target_date = datetime.strptime(date, '%Y-%m-%d').date()
                
                # Convert date column to datetime if it's not already
                if not pd.api.types.is_datetime64_dtype(df['date']):
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                
                # Filter to records from the target date
                df = df[df['date'].dt.date == target_date]
                
                if df.empty:
                    logger.warning(f"No records found for date {date}")
                    return {'date': date, 'drivers': [], 'summary': {'total_drivers': 0}}
            except Exception as e:
                logger.error(f"Error filtering by date: {e}")
        
        # Process the data
        processed_data = process_attendance_data(df)
        return processed_data
        
    except Exception as e:
        logger.error(f"Error reading Daily Usage file: {e}")
        return {'error': f"Failed to process file: {str(e)}"}

def process_attendance_data(df):
    """
    Process attendance data from DataFrame into structured format with issues highlighted
    
    Args:
        df (DataFrame): Pandas DataFrame with attendance data
        
    Returns:
        dict: Processed attendance data with identified issues
    """
    # Extract date from the first row or use current date
    try:
        if 'date' in df.columns and not df.empty:
            # Convert to datetime if not already
            if not pd.api.types.is_datetime64_dtype(df['date']):
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            
            report_date = df['date'].iloc[0].strftime('%Y-%m-%d')
        else:
            report_date = datetime.now().strftime('%Y-%m-%d')
    except:
        report_date = datetime.now().strftime('%Y-%m-%d')
    
    # Prepare containers for different categories of issues
    late_drivers = []
    early_end_drivers = []
    not_on_job_drivers = []
    exception_drivers = []
    
    # Process each row
    for _, row in df.iterrows():
        try:
            # Extract driver name and asset ID from label
            asset_label = row.get('asset_label', '')
            driver_name = extract_driver_from_label(asset_label)
            asset_id = clean_asset_info(asset_label)
            
            # Extract employee ID if present in the driver name
            driver_name, employee_id = extract_employee_id(driver_name)
            
            # Parse start and end times with the report date as default
            date_obj = datetime.strptime(report_date, '%Y-%m-%d').date()
            start_time = parse_time_string(row.get('start_time', ''), date_obj)
            end_time = parse_time_string(row.get('end_time', ''), date_obj)
            
            # Skip records with missing essential data
            if not driver_name or not start_time:
                continue
            
            # Create basic driver data structure
            driver_data = {
                'driver_name': driver_name,
                'asset_id': asset_id,
                'start_time': start_time.strftime('%I:%M %p') if start_time else None,
                'end_time': end_time.strftime('%I:%M %p') if end_time else None,
                'job_site': row.get('job_site', row.get('location', 'Unknown')),
                'company': row.get('company', 'Unknown')
            }
            
            # Add employee ID if available
            if employee_id:
                driver_data['employee_id'] = employee_id
            else:
                # Generate a consistent ID based on driver name if no ID exists
                # This ensures we can track the same driver across categories
                driver_data['employee_id'] = f"GEN-{abs(hash(driver_name)) % 100000}"
            
            # Check for issues:
            
            # 1. Late start
            if start_time and is_late_start(start_time, 
                                           threshold_minutes=DRIVER_LATE_THRESHOLD_MINUTES):
                # Calculate minutes late
                expected_start = datetime.combine(date_obj, DRIVER_EXPECTED_START_TIME)
                expected_start = expected_start.replace(tzinfo=start_time.tzinfo)
                minutes_late = (start_time - expected_start).total_seconds() / 60
                
                driver_data['minutes_late'] = int(minutes_late)
                late_drivers.append(driver_data.copy())
            
            # 2. Early end
            if end_time and is_early_end(end_time, 
                                        threshold_minutes=DRIVER_EARLY_END_THRESHOLD_MINUTES):
                # Calculate minutes early
                expected_end = datetime.combine(date_obj, DRIVER_EXPECTED_END_TIME)
                expected_end = expected_end.replace(tzinfo=end_time.tzinfo)
                minutes_early = (expected_end - end_time).total_seconds() / 60
                
                driver_data['minutes_early'] = int(minutes_early)
                early_end_drivers.append(driver_data.copy())
            
            # 3. Not on job (missing either start or end time)
            if (not start_time and end_time) or (start_time and not end_time):
                driver_data['issue'] = 'missing_time_record'
                not_on_job_drivers.append(driver_data.copy())
            
            # 4. Other exceptions (e.g., both start and end missing but driver assigned)
            elif not start_time and not end_time:
                driver_data['issue'] = 'no_time_records'
                exception_drivers.append(driver_data.copy())
            
            # 5. Unusual work hours (less than 4 hours or more than 12)
            elif start_time and end_time:
                hours_worked = (end_time - start_time).total_seconds() / 3600
                if hours_worked < 4:
                    driver_data['issue'] = 'short_day'
                    driver_data['hours_worked'] = round(hours_worked, 1)
                    exception_drivers.append(driver_data.copy())
                elif hours_worked > 12:
                    driver_data['issue'] = 'long_day'
                    driver_data['hours_worked'] = round(hours_worked, 1)
                    exception_drivers.append(driver_data.copy())
            
        except Exception as e:
            logger.error(f"Error processing row: {e}")
            continue
    
    # Calculate summary statistics
    # Count unique drivers by employee_id
    all_employee_ids = set()
    for driver_list in [late_drivers, early_end_drivers, not_on_job_drivers, exception_drivers]:
        for driver in driver_list:
            all_employee_ids.add(driver.get('employee_id'))
    
    total_issues = len(late_drivers) + len(early_end_drivers) + len(not_on_job_drivers) + len(exception_drivers)
    
    summary = {
        'total_drivers': len(all_employee_ids),
        'total_issues': total_issues,
        'late_count': len(late_drivers),
        'early_end_count': len(early_end_drivers),
        'not_on_job_count': len(not_on_job_drivers),
        'exception_count': len(exception_drivers)
    }
    
    # Prepare result
    result = {
        'date': report_date,
        'late_drivers': late_drivers,
        'early_end_drivers': early_end_drivers,
        'not_on_job_drivers': not_on_job_drivers,
        'exception_drivers': exception_drivers,
        'summary': summary
    }
    
    return result

def get_attendance_data(date=None):
    """
    Get attendance data for a specific date
    
    Args:
        date (str): Date in YYYY-MM-DD format, or None for latest available
        
    Returns:
        dict: Processed attendance data with issues identified
    """
    # Find file for the specific date
    if date:
        # Try to find a file matching the date pattern
        file_pattern = f"DailyUsage_{date.replace('-', '')}"
        file_path = find_latest_daily_file(file_pattern)
        
        if not file_path:
            # If no specific file found, use latest and filter by date
            file_path = find_latest_daily_file()
    else:
        # Just use latest available file
        file_path = find_latest_daily_file()
    
    # Process the file
    return read_daily_usage_file(file_path, date)