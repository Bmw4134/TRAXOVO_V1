"""
Attendance Data Pipeline

This module handles the automated ingestion, processing, and storage of attendance data
from raw source files (DailyUsage.csv, Timecards, etc.) into structured daily attendance records.
"""

import csv
import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from utils.attendance_audit import log_file_processing, setup_audit_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define path constants
DATA_DIR = Path("data")
RAW_DATA_DIR = Path("attached_assets")
PROCESSED_DIR = DATA_DIR / "processed"
ATTENDANCE_DB = DATA_DIR / "attendance.db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

def setup_database():
    """Create attendance database and tables if they don't exist"""
    conn = sqlite3.connect(ATTENDANCE_DB)
    cursor = conn.cursor()
    
    # Create daily_attendance table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        driver_name TEXT,
        asset_id TEXT,
        scheduled_start TEXT,
        actual_start TEXT,
        scheduled_end TEXT,
        actual_end TEXT,
        location TEXT,
        is_late INTEGER,
        is_early_end INTEGER,
        late_minutes INTEGER,
        early_minutes INTEGER,
        job_site TEXT,
        company TEXT,
        status TEXT,
        UNIQUE(date, driver_name, asset_id)
    )
    ''')
    
    # Create attendance_trends table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_trends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_name TEXT,
        date_range_start TEXT,
        date_range_end TEXT,
        days_analyzed INTEGER,
        late_count INTEGER,
        absence_count INTEGER,
        early_end_count INTEGER,
        chronic_late INTEGER,
        repeated_absence INTEGER,
        unstable_shift INTEGER,
        UNIQUE(driver_name, date_range_start, date_range_end)
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Attendance database setup complete")

def find_source_files():
    """Find all relevant source files for attendance data processing"""
    source_files = {
        'daily_usage': [],
        'timecards': [],
        'tracking': [],
        'driving_history': [],
        'activity_detail': []
    }
    
    # Walk through raw data directory to find relevant files
    for file_path in RAW_DATA_DIR.glob('**/*'):
        if file_path.is_file():
            file_name = file_path.name.lower()
            
            # Categorize files based on name patterns
            if 'dailyusage' in file_name and file_name.endswith('.csv'):
                source_files['daily_usage'].append(file_path)
            elif 'timecard' in file_name and file_name.endswith(('.xlsx', '.csv')):
                source_files['timecards'].append(file_path)
            elif 'tracking' in file_name and file_name.endswith('.csv'):
                source_files['tracking'].append(file_path)
            elif 'drivinghistory' in file_name and file_name.endswith('.csv'):
                source_files['driving_history'].append(file_path)
            elif 'activitydetail' in file_name and file_name.endswith(('.csv', '.xlsx')):
                source_files['activity_detail'].append(file_path)
    
    # Sort files by modification time (newest first)
    for category in source_files:
        source_files[category].sort(key=lambda f: os.path.getmtime(f), reverse=True)
    
    return source_files

def extract_date_from_file(file_path):
    """
    Extract date information from filename or file content
    Returns date in YYYY-MM-DD format
    """
    file_name = file_path.name
    
    # Try to extract date from filename
    date_formats = [
        # Format: YYYY-MM-DD
        r'(\d{4}-\d{2}-\d{2})',
        # Format: MM.DD.YYYY
        r'(\d{2}\.\d{2}\.\d{4})',
        # Format: YYYY_MM_DD
        r'(\d{4}_\d{2}_\d{2})'
    ]
    
    import re
    for pattern in date_formats:
        match = re.search(pattern, file_name)
        if match:
            date_str = match.group(1)
            # Convert to standard format if needed
            if '-' not in date_str:
                if '.' in date_str:
                    month, day, year = date_str.split('.')
                    date_str = f"{year}-{month}-{day}"
                elif '_' in date_str:
                    year, month, day = date_str.split('_')
                    date_str = f"{year}-{month}-{day}"
            return date_str
    
    # If we can't extract from filename, try to get from file content
    if file_path.suffix.lower() == '.xlsx':
        try:
            df = pd.read_excel(file_path, nrows=5)
            # Look for date in headers or first few rows
            date_cols = [col for col in df.columns if 'date' in str(col).lower()]
            if date_cols:
                date_val = df[date_cols[0]].iloc[0]
                if isinstance(date_val, datetime):
                    return date_val.strftime('%Y-%m-%d')
        except Exception as e:
            logger.warning(f"Could not extract date from Excel file {file_path}: {e}")
    
    elif file_path.suffix.lower() == '.csv':
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                # Check first few rows for date
                for _ in range(5):
                    try:
                        row = next(reader)
                        for cell in row:
                            # Check if cell contains date-like string
                            if re.search(r'\d{1,4}[-/\.]\d{1,2}[-/\.]\d{2,4}', cell):
                                # Try to parse as date
                                try:
                                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%d/%m/%Y']:
                                        try:
                                            dt = datetime.strptime(cell, fmt)
                                            return dt.strftime('%Y-%m-%d')
                                        except ValueError:
                                            continue
                                except:
                                    pass
                    except StopIteration:
                        break
        except Exception as e:
            logger.warning(f"Could not extract date from CSV file {file_path}: {e}")
    
    # If we can't determine the date, fall back to file modification date
    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    return mod_time.strftime('%Y-%m-%d')

def process_daily_usage_file(file_path):
    """
    Process a DailyUsage.csv file and convert to structured attendance records
    Returns a list of attendance records
    """
    records = []
    date = extract_date_from_file(file_path)
    
    try:
        df = pd.read_csv(file_path)
        required_columns = ['Driver', 'Asset', 'TimeStart', 'TimeEnd', 'Location']
        
        # Check for required columns (case insensitive)
        actual_columns = set(df.columns)
        missing_columns = []
        column_mapping = {}
        
        for req_col in required_columns:
            found = False
            for actual_col in actual_columns:
                if req_col.lower() == actual_col.lower():
                    column_mapping[req_col] = actual_col
                    found = True
                    break
            if not found:
                missing_columns.append(req_col)
        
        if missing_columns:
            logger.warning(f"Missing required columns in {file_path}: {missing_columns}")
            return records
        
        # Process records
        for _, row in df.iterrows():
            try:
                driver_name = row[column_mapping['Driver']]
                asset_id = row[column_mapping['Asset']]
                time_start = row[column_mapping['TimeStart']]
                time_end = row[column_mapping['TimeEnd']]
                location = row[column_mapping['Location']]
                
                # Skip rows with missing critical data
                if pd.isna(driver_name) or pd.isna(asset_id) or pd.isna(time_start):
                    continue
                
                # Default scheduled times (can be refined based on company policies)
                scheduled_start = '07:00:00'
                scheduled_end = '16:00:00'
                
                # Determine if late or early end
                is_late = 0
                is_early_end = 0
                late_minutes = 0
                early_minutes = 0
                
                # Convert time strings to datetime for comparison
                if isinstance(time_start, str):
                    actual_start_time = datetime.strptime(time_start, '%H:%M:%S')
                    scheduled_start_time = datetime.strptime(scheduled_start, '%H:%M:%S')
                    
                    # Calculate lateness
                    if actual_start_time > scheduled_start_time:
                        is_late = 1
                        late_minutes = int((actual_start_time - scheduled_start_time).total_seconds() / 60)
                
                # Calculate early end if time_end exists
                if not pd.isna(time_end) and isinstance(time_end, str):
                    actual_end_time = datetime.strptime(time_end, '%H:%M:%S')
                    scheduled_end_time = datetime.strptime(scheduled_end, '%H:%M:%S')
                    
                    # Calculate early departure
                    if actual_end_time < scheduled_end_time:
                        is_early_end = 1
                        early_minutes = int((scheduled_end_time - actual_end_time).total_seconds() / 60)
                
                # Create attendance record
                record = {
                    'date': date,
                    'driver_name': driver_name,
                    'asset_id': asset_id,
                    'scheduled_start': scheduled_start,
                    'actual_start': time_start,
                    'scheduled_end': scheduled_end,
                    'actual_end': time_end if not pd.isna(time_end) else None,
                    'location': location,
                    'is_late': is_late,
                    'is_early_end': is_early_end,
                    'late_minutes': late_minutes,
                    'early_minutes': early_minutes,
                    'job_site': location,  # Use location as job site if not specified
                    'company': 'Unknown',  # Default company
                    'status': 'Active'
                }
                
                records.append(record)
                
            except Exception as e:
                logger.warning(f"Error processing row in {file_path}: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Failed to process DailyUsage file {file_path}: {e}")
    
    return records

def process_timecard_file(file_path):
    """
    Process a Timecard Excel file and convert to structured attendance records
    Returns a list of attendance records
    """
    records = []
    
    try:
        # Extract date range from filename
        file_name = file_path.name
        date_range = None
        import re
        
        # Look for date range pattern in filename (e.g., "2025-05-11 - 2025-05-17")
        match = re.search(r'(\d{4}-\d{2}-\d{2})\s*-\s*(\d{4}-\d{2}-\d{2})', file_name)
        if match:
            start_date = datetime.strptime(match.group(1), '%Y-%m-%d')
            end_date = datetime.strptime(match.group(2), '%Y-%m-%d')
            date_range = (start_date, end_date)
        
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Try to find key columns for timecard data
        name_col = None
        date_col = None
        time_in_col = None
        time_out_col = None
        location_col = None
        
        # Look for column names (case-insensitive)
        for col in df.columns:
            col_lower = str(col).lower()
            if 'name' in col_lower or 'employee' in col_lower:
                name_col = col
            elif 'date' in col_lower:
                date_col = col
            elif ('time' in col_lower and 'in' in col_lower) or 'start' in col_lower:
                time_in_col = col
            elif ('time' in col_lower and 'out' in col_lower) or 'end' in col_lower:
                time_out_col = col
            elif 'location' in col_lower or 'job' in col_lower or 'site' in col_lower:
                location_col = col
        
        # If we don't have the essential columns, try another approach
        if not (name_col and (date_col or date_range) and (time_in_col or time_out_col)):
            # Try to infer structure from typical timecard layout
            # This is a fallback for complex or unusual timecard formats
            logger.warning(f"Could not identify standard columns in {file_path}, using inference")
            
            # Approach 2: Use first row as header and try again
            df = pd.read_excel(file_path, header=0)
            
            for col in df.columns:
                col_lower = str(col).lower()
                if 'name' in col_lower or 'employee' in col_lower:
                    name_col = col
                elif 'date' in col_lower:
                    date_col = col
                elif ('time' in col_lower and 'in' in col_lower) or 'start' in col_lower:
                    time_in_col = col
                elif ('time' in col_lower and 'out' in col_lower) or 'end' in col_lower:
                    time_out_col = col
                elif 'location' in col_lower or 'job' in col_lower or 'site' in col_lower:
                    location_col = col
        
        # Process each row in the timecard
        for _, row in df.iterrows():
            try:
                # Skip rows with no name (likely header rows or blank rows)
                if name_col and (pd.isna(row[name_col]) or not row[name_col]):
                    continue
                
                # Extract driver name
                driver_name = row[name_col] if name_col else "Unknown"
                
                # Determine date
                if date_col and not pd.isna(row[date_col]):
                    if isinstance(row[date_col], datetime):
                        date = row[date_col].strftime('%Y-%m-%d')
                    elif isinstance(row[date_col], str):
                        try:
                            date = datetime.strptime(row[date_col], '%Y-%m-%d').strftime('%Y-%m-%d')
                        except ValueError:
                            try:
                                date = datetime.strptime(row[date_col], '%m/%d/%Y').strftime('%Y-%m-%d')
                            except ValueError:
                                # Extract date if it's in the format "MM/DD" with assumed year
                                if '/' in row[date_col] and len(row[date_col].split('/')) == 2:
                                    month, day = row[date_col].split('/')
                                    if date_range:  # Use year from date range
                                        year = date_range[0].year
                                        try:
                                            date = datetime(year, int(month), int(day)).strftime('%Y-%m-%d')
                                        except ValueError:
                                            continue
                                    else:
                                        continue
                                else:
                                    continue
                elif date_range:
                    # If we have a date range but no explicit date column,
                    # try to determine date from context or use the start date
                    date = date_range[0].strftime('%Y-%m-%d')
                else:
                    # Last resort: use file modification date
                    date = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d')
                
                # Extract time in/out
                time_in = row[time_in_col] if time_in_col and not pd.isna(row[time_in_col]) else None
                time_out = row[time_out_col] if time_out_col and not pd.isna(row[time_out_col]) else None
                
                # Format times for consistency
                if time_in:
                    if isinstance(time_in, datetime):
                        time_in = time_in.strftime('%H:%M:%S')
                    elif isinstance(time_in, str):
                        if ':' not in time_in:  # Handle numeric time format (e.g. 730 for 7:30)
                            if len(time_in) <= 4 and time_in.isdigit():
                                if len(time_in) <= 2:
                                    time_in = f"{time_in}:00:00"
                                else:
                                    hours = time_in[:-2] or '0'
                                    minutes = time_in[-2:]
                                    time_in = f"{hours}:{minutes}:00"
                
                if time_out:
                    if isinstance(time_out, datetime):
                        time_out = time_out.strftime('%H:%M:%S')
                    elif isinstance(time_out, str):
                        if ':' not in time_out:  # Handle numeric time format
                            if len(time_out) <= 4 and time_out.isdigit():
                                if len(time_out) <= 2:
                                    time_out = f"{time_out}:00:00"
                                else:
                                    hours = time_out[:-2] or '0'
                                    minutes = time_out[-2:]
                                    time_out = f"{hours}:{minutes}:00"
                
                # Skip rows with no time data
                if not time_in and not time_out:
                    continue
                
                # Get location/job site
                location = row[location_col] if location_col and not pd.isna(row[location_col]) else "Unknown"
                
                # Set default scheduled times
                scheduled_start = '07:00:00'
                scheduled_end = '16:00:00'
                
                # Calculate lateness and early departure
                is_late = 0
                is_early_end = 0
                late_minutes = 0
                early_minutes = 0
                
                if time_in:
                    try:
                        if ':' in time_in:
                            actual_start_time = datetime.strptime(time_in, '%H:%M:%S')
                            scheduled_start_time = datetime.strptime(scheduled_start, '%H:%M:%S')
                            
                            # Calculate lateness
                            if actual_start_time > scheduled_start_time:
                                is_late = 1
                                late_minutes = int((actual_start_time - scheduled_start_time).total_seconds() / 60)
                    except ValueError:
                        pass
                
                if time_out:
                    try:
                        if ':' in time_out:
                            actual_end_time = datetime.strptime(time_out, '%H:%M:%S')
                            scheduled_end_time = datetime.strptime(scheduled_end, '%H:%M:%S')
                            
                            # Calculate early departure
                            if actual_end_time < scheduled_end_time:
                                is_early_end = 1
                                early_minutes = int((scheduled_end_time - actual_end_time).total_seconds() / 60)
                    except ValueError:
                        pass
                
                # Create attendance record
                record = {
                    'date': date,
                    'driver_name': driver_name,
                    'asset_id': "Unknown",  # Timecards often don't include asset info
                    'scheduled_start': scheduled_start,
                    'actual_start': time_in,
                    'scheduled_end': scheduled_end,
                    'actual_end': time_out,
                    'location': location,
                    'is_late': is_late,
                    'is_early_end': is_early_end,
                    'late_minutes': late_minutes,
                    'early_minutes': early_minutes,
                    'job_site': location,
                    'company': 'Unknown',
                    'status': 'Active'
                }
                
                records.append(record)
                
            except Exception as e:
                logger.warning(f"Error processing row in {file_path}: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Failed to process Timecard file {file_path}: {e}")
    
    return records

def process_activity_detail_file(file_path):
    """
    Process an ActivityDetail file with attendance information
    Returns a list of attendance records
    """
    records = []
    
    try:
        # Determine if file is CSV or Excel
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Try to identify key columns
        driver_col = None
        asset_col = None
        date_col = None
        time_in_col = None
        time_out_col = None
        location_col = None
        
        # Look for column names (case-insensitive)
        for col in df.columns:
            col_lower = str(col).lower()
            if 'driver' in col_lower or 'employee' in col_lower or 'name' in col_lower:
                driver_col = col
            elif 'asset' in col_lower or 'vehicle' in col_lower or 'equipment' in col_lower:
                asset_col = col
            elif 'date' in col_lower:
                date_col = col
            elif ('time' in col_lower and 'in' in col_lower) or 'start' in col_lower:
                time_in_col = col
            elif ('time' in col_lower and 'out' in col_lower) or 'end' in col_lower or 'stop' in col_lower:
                time_out_col = col
            elif 'location' in col_lower or 'job' in col_lower or 'site' in col_lower:
                location_col = col
        
        # Process each row
        for _, row in df.iterrows():
            try:
                # Extract driver name
                driver_name = row[driver_col] if driver_col and not pd.isna(row[driver_col]) else "Unknown"
                
                # Skip rows with no driver name
                if driver_name == "Unknown":
                    continue
                
                # Extract asset ID
                asset_id = row[asset_col] if asset_col and not pd.isna(row[asset_col]) else "Unknown"
                
                # Determine date
                if date_col and not pd.isna(row[date_col]):
                    if isinstance(row[date_col], datetime):
                        date = row[date_col].strftime('%Y-%m-%d')
                    elif isinstance(row[date_col], str):
                        try:
                            date = datetime.strptime(row[date_col], '%Y-%m-%d').strftime('%Y-%m-%d')
                        except ValueError:
                            try:
                                date = datetime.strptime(row[date_col], '%m/%d/%Y').strftime('%Y-%m-%d')
                            except ValueError:
                                # Try to extract date from file name
                                date = extract_date_from_file(file_path)
                else:
                    # Use file date as fallback
                    date = extract_date_from_file(file_path)
                
                # Extract time in/out
                time_in = row[time_in_col] if time_in_col and not pd.isna(row[time_in_col]) else None
                time_out = row[time_out_col] if time_out_col and not pd.isna(row[time_out_col]) else None
                
                # Format times
                if time_in:
                    if isinstance(time_in, datetime):
                        time_in = time_in.strftime('%H:%M:%S')
                    elif isinstance(time_in, str) and ':' not in time_in:
                        # Handle numeric format
                        if len(time_in) <= 4 and time_in.isdigit():
                            hours = time_in[:-2] or '0'
                            minutes = time_in[-2:]
                            time_in = f"{hours}:{minutes}:00"
                
                if time_out:
                    if isinstance(time_out, datetime):
                        time_out = time_out.strftime('%H:%M:%S')
                    elif isinstance(time_out, str) and ':' not in time_out:
                        # Handle numeric format
                        if len(time_out) <= 4 and time_out.isdigit():
                            hours = time_out[:-2] or '0'
                            minutes = time_out[-2:]
                            time_out = f"{hours}:{minutes}:00"
                
                # Get location
                location = row[location_col] if location_col and not pd.isna(row[location_col]) else "Unknown"
                
                # Set scheduled times
                scheduled_start = '07:00:00'
                scheduled_end = '16:00:00'
                
                # Calculate lateness and early departure
                is_late = 0
                is_early_end = 0
                late_minutes = 0
                early_minutes = 0
                
                if time_in and ':' in time_in:
                    try:
                        actual_start_time = datetime.strptime(time_in, '%H:%M:%S')
                        scheduled_start_time = datetime.strptime(scheduled_start, '%H:%M:%S')
                        
                        # Calculate lateness
                        if actual_start_time > scheduled_start_time:
                            is_late = 1
                            late_minutes = int((actual_start_time - scheduled_start_time).total_seconds() / 60)
                    except ValueError:
                        pass
                
                if time_out and ':' in time_out:
                    try:
                        actual_end_time = datetime.strptime(time_out, '%H:%M:%S')
                        scheduled_end_time = datetime.strptime(scheduled_end, '%H:%M:%S')
                        
                        # Calculate early departure
                        if actual_end_time < scheduled_end_time:
                            is_early_end = 1
                            early_minutes = int((scheduled_end_time - actual_end_time).total_seconds() / 60)
                    except ValueError:
                        pass
                
                # Create attendance record
                record = {
                    'date': date,
                    'driver_name': driver_name,
                    'asset_id': asset_id,
                    'scheduled_start': scheduled_start,
                    'actual_start': time_in,
                    'scheduled_end': scheduled_end,
                    'actual_end': time_out,
                    'location': location,
                    'is_late': is_late,
                    'is_early_end': is_early_end,
                    'late_minutes': late_minutes,
                    'early_minutes': early_minutes,
                    'job_site': location,
                    'company': 'Unknown',
                    'status': 'Active'
                }
                
                records.append(record)
                
            except Exception as e:
                logger.warning(f"Error processing row in {file_path}: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Failed to process ActivityDetail file {file_path}: {e}")
    
    return records

def store_attendance_records(records):
    """Store attendance records in the database"""
    if not records:
        logger.info("No records to store")
        return 0
    
    conn = sqlite3.connect(ATTENDANCE_DB)
    cursor = conn.cursor()
    
    records_added = 0
    
    for record in records:
        try:
            # Insert or replace record
            cursor.execute('''
            INSERT OR REPLACE INTO daily_attendance
            (date, driver_name, asset_id, scheduled_start, actual_start, 
             scheduled_end, actual_end, location, is_late, is_early_end,
             late_minutes, early_minutes, job_site, company, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record['date'],
                record['driver_name'],
                record['asset_id'],
                record['scheduled_start'],
                record['actual_start'],
                record['scheduled_end'],
                record['actual_end'],
                record['location'],
                record['is_late'],
                record['is_early_end'],
                record['late_minutes'],
                record['early_minutes'],
                record['job_site'],
                record['company'],
                record['status']
            ))
            records_added += 1
        except Exception as e:
            logger.error(f"Error storing record: {e}")
    
    conn.commit()
    conn.close()
    
    return records_added

def generate_daily_report(date):
    """
    Generate a "DAILY LATE START-EARLY END & NOJ REPORT" style report for a specific date
    Returns report data structure
    """
    conn = sqlite3.connect(ATTENDANCE_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get attendance records for specified date
    cursor.execute('''
    SELECT * FROM daily_attendance WHERE date = ?
    ''', (date,))
    
    records = cursor.fetchall()
    conn.close()
    
    # Convert to dictionary format
    drivers = []
    late_count = 0
    early_count = 0
    
    for record in records:
        record_dict = dict(record)
        
        # Count stats
        if record_dict['is_late']:
            late_count += 1
        if record_dict['is_early_end']:
            early_count += 1
        
        # Format the record for the report
        driver_record = {
            'driver_name': record_dict['driver_name'],
            'asset_id': record_dict['asset_id'],
            'start_time': record_dict['actual_start'],
            'end_time': record_dict['actual_end'],
            'location': record_dict['location'],
            'is_late': record_dict['is_late'],
            'left_early': record_dict['is_early_end'],
            'late_minutes': record_dict['late_minutes'],
            'early_minutes': record_dict['early_minutes'],
            'expected_start': record_dict['scheduled_start'],
            'expected_end': record_dict['scheduled_end'],
            'job_site': record_dict['job_site'],
            'company': record_dict['company']
        }
        
        drivers.append(driver_record)
    
    # Construct report structure
    report = {
        'date': date,
        'formatted_date': datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y'),
        'drivers': drivers,
        'stats': {
            'total_count': len(drivers),
            'late_count': late_count,
            'early_count': early_count,
            # Add bracket counts for charts
            'late_brackets': [
                sum(1 for d in drivers if d['is_late'] and d['late_minutes'] <= 15),
                sum(1 for d in drivers if d['is_late'] and 15 < d['late_minutes'] <= 30),
                sum(1 for d in drivers if d['is_late'] and 30 < d['late_minutes'] <= 60),
                sum(1 for d in drivers if d['is_late'] and d['late_minutes'] > 60)
            ],
            'early_brackets': [
                sum(1 for d in drivers if d['left_early'] and d['early_minutes'] <= 15),
                sum(1 for d in drivers if d['left_early'] and 15 < d['early_minutes'] <= 30),
                sum(1 for d in drivers if d['left_early'] and 30 < d['early_minutes'] <= 60),
                sum(1 for d in drivers if d['left_early'] and d['early_minutes'] > 60)
            ]
        }
    }
    
    return report

def generate_attendance_trends(start_date, end_date):
    """
    Generate attendance trends for the specified date range
    Stores results in the attendance_trends table
    """
    conn = sqlite3.connect(ATTENDANCE_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all unique driver names in the date range
    cursor.execute('''
    SELECT DISTINCT driver_name FROM daily_attendance 
    WHERE date BETWEEN ? AND ?
    ''', (start_date, end_date))
    
    drivers = [row['driver_name'] for row in cursor.fetchall()]
    
    for driver_name in drivers:
        # Get attendance records for this driver in date range
        cursor.execute('''
        SELECT * FROM daily_attendance 
        WHERE driver_name = ? AND date BETWEEN ? AND ?
        ORDER BY date
        ''', (driver_name, start_date, end_date))
        
        records = cursor.fetchall()
        
        # Skip if not enough records
        if len(records) < 2:
            continue
        
        # Count late and early days
        late_count = sum(1 for r in records if r['is_late'])
        early_end_count = sum(1 for r in records if r['is_early_end'])
        
        # Determine absence count (we don't have direct absence data)
        # This would need to be refined based on how absences are tracked
        absence_count = 0
        
        # Calculate shift stability
        shift_start_times = []
        for record in records:
            if record['actual_start']:
                try:
                    start_time = datetime.strptime(record['actual_start'], '%H:%M:%S')
                    shift_start_times.append(start_time.hour * 60 + start_time.minute)
                except (ValueError, TypeError):
                    shift_start_times.append(None)
        
        # Filter out None values
        valid_start_times = [t for t in shift_start_times if t is not None]
        
        # Determine trend flags
        chronic_late = 1 if late_count >= 3 and len(records) >= 5 else 0
        repeated_absence = 1 if absence_count >= 2 else 0
        
        # Calculate shift stability (max variance > 3 hours)
        unstable_shift = 0
        if len(valid_start_times) >= 3:
            start_time_range = max(valid_start_times) - min(valid_start_times)
            unstable_shift = 1 if start_time_range >= 180 else 0  # 3 hours = 180 minutes
        
        # Store trend data
        cursor.execute('''
        INSERT OR REPLACE INTO attendance_trends
        (driver_name, date_range_start, date_range_end, days_analyzed,
         late_count, absence_count, early_end_count,
         chronic_late, repeated_absence, unstable_shift)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            driver_name,
            start_date,
            end_date,
            len(records),
            late_count,
            absence_count,
            early_end_count,
            chronic_late,
            repeated_absence,
            unstable_shift
        ))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Generated attendance trends for {len(drivers)} drivers ({start_date} to {end_date})")

def get_attendance_trends(end_date, days=5):
    """
    Get attendance trends data for the specified end date and number of days
    Returns the driver trends data structure
    """
    # Calculate start date
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    start_date_obj = end_date_obj - timedelta(days=days-1)
    start_date = start_date_obj.strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(ATTENDANCE_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get trend data
    cursor.execute('''
    SELECT * FROM attendance_trends 
    WHERE date_range_start = ? AND date_range_end = ?
    ''', (start_date, end_date))
    
    trend_records = cursor.fetchall()
    conn.close()
    
    # Convert to driver_trends structure
    driver_trends = {}
    chronic_late_count = 0
    repeated_absence_count = 0
    unstable_shift_count = 0
    
    for record in trend_records:
        flags = []
        
        if record['chronic_late']:
            flags.append('CHRONIC_LATE')
            chronic_late_count += 1
        
        if record['repeated_absence']:
            flags.append('REPEATED_ABSENCE')
            repeated_absence_count += 1
        
        if record['unstable_shift']:
            flags.append('UNSTABLE_SHIFT')
            unstable_shift_count += 1
        
        driver_trends[record['driver_name']] = {
            'flags': flags,
            'days_analyzed': record['days_analyzed'],
            'late_count': record['late_count'],
            'absence_count': record['absence_count'],
            'early_end_count': record['early_end_count']
        }
    
    # Create trend data structure
    trend_data = {
        'driver_trends': driver_trends,
        'summary': {
            'total_drivers': len(driver_trends),
            'chronic_late_count': chronic_late_count,
            'repeated_absence_count': repeated_absence_count,
            'unstable_shift_count': unstable_shift_count,
            'date_range': {
                'start': start_date,
                'end': end_date
            },
            'days_analyzed': days
        }
    }
    
    return trend_data

def run_attendance_pipeline():
    """
    Main function to run the complete attendance pipeline
    1. Finds all source files
    2. Processes each file type
    3. Stores attendance records in database
    4. Generates daily reports
    5. Generates attendance trends
    """
    # Ensure database setup
    setup_database()
    
    # Find source files
    source_files = find_source_files()
    
    # Track processed dates for trend generation
    processed_dates = set()
    
    # Process DailyUsage files
    for file_path in source_files['daily_usage']:
        logger.info(f"Processing DailyUsage file: {file_path}")
        records = process_daily_usage_file(file_path)
        if records:
            records_added = store_attendance_records(records)
            logger.info(f"Added {records_added} attendance records from {file_path}")
            
            # Add date to processed set
            for record in records:
                processed_dates.add(record['date'])
    
    # Process Timecard files
    for file_path in source_files['timecards']:
        logger.info(f"Processing Timecard file: {file_path}")
        records = process_timecard_file(file_path)
        if records:
            records_added = store_attendance_records(records)
            logger.info(f"Added {records_added} attendance records from {file_path}")
            
            # Add dates to processed set
            for record in records:
                processed_dates.add(record['date'])
    
    # Process ActivityDetail files
    for file_path in source_files['activity_detail']:
        logger.info(f"Processing ActivityDetail file: {file_path}")
        records = process_activity_detail_file(file_path)
        if records:
            records_added = store_attendance_records(records)
            logger.info(f"Added {records_added} attendance records from {file_path}")
            
            # Add dates to processed set
            for record in records:
                processed_dates.add(record['date'])
    
    # Generate trends for date ranges
    if processed_dates:
        # Sort dates
        sorted_dates = sorted(processed_dates)
        
        # Generate trends for each potential 5-day window
        for i in range(len(sorted_dates)):
            end_date = sorted_dates[i]
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Define window start (up to 5 days before)
            window_start_obj = end_date_obj - timedelta(days=4)
            window_start = window_start_obj.strftime('%Y-%m-%d')
            
            # Filter dates in window
            window_dates = [d for d in sorted_dates if window_start <= d <= end_date]
            
            # Only generate trends if we have enough days
            if len(window_dates) >= 2:
                logger.info(f"Generating attendance trends for {window_start} to {end_date}")
                generate_attendance_trends(window_start, end_date)
    
    logger.info("Attendance pipeline completed successfully")
    
    # Return processed dates
    return sorted(processed_dates) if processed_dates else []

if __name__ == "__main__":
    # Run the attendance pipeline
    processed_dates = run_attendance_pipeline()
    
    # Log results
    if processed_dates:
        logger.info(f"Processed attendance data for dates: {', '.join(processed_dates)}")
    else:
        logger.info("No attendance data processed")