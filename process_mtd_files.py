"""
Process MTD Files Module

This module provides specialized functionality for processing large Month-to-Date (MTD) files
in a memory-efficient manner by processing them in chunks and focusing only on records
for a specific target date.
"""

import os
import csv
import re
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_mtd_files(
    driving_history_paths: List[str],
    activity_detail_paths: List[str],
    report_date: str
) -> Dict[str, Any]:
    """
    Process MTD files for a specific date
    
    Args:
        driving_history_paths: List of paths to driving history files
        activity_detail_paths: List of paths to activity detail files
        report_date: Target date in YYYY-MM-DD format
        
    Returns:
        Dict containing the processed report data
    """
    logger.info(f"Processing MTD files for date: {report_date}")
    
    # Convert report_date to datetime
    target_date = datetime.strptime(report_date, '%Y-%m-%d').date()
    
    # Initialize report data structure
    report_data = {
        'date': report_date,
        'total_drivers': 0,
        'on_time_count': 0,
        'late_count': 0,
        'early_end_count': 0,
        'not_on_job_count': 0,
        'on_time_percent': 0,
        'late_percent': 0,
        'early_end_percent': 0,
        'not_on_job_percent': 0,
        'driving_history_stats': {
            'total_records': 0,
            'filtered_records': 0,
            'processed_files': driving_history_paths
        },
        'activity_detail_stats': {
            'total_records': 0,
            'filtered_records': 0,
            'processed_files': activity_detail_paths
        },
        'driver_metrics': {}
    }
    
    # Process driving history files
    driver_data = {}
    
    # Process driving history files
    if driving_history_paths:
        logger.info(f"Processing {len(driving_history_paths)} driving history files")
        for file_path in driving_history_paths:
            logger.info(f"Processing driving history file: {file_path}")
            process_driving_history_file(file_path, target_date, driver_data, report_data)
    
    # Process activity detail files
    if activity_detail_paths:
        logger.info(f"Processing {len(activity_detail_paths)} activity detail files")
        for file_path in activity_detail_paths:
            logger.info(f"Processing activity detail file: {file_path}")
            process_activity_detail_file(file_path, target_date, driver_data, report_data)
    
    # Calculate metrics
    calculate_metrics(driver_data, report_data)
    
    logger.info(f"Completed processing MTD files for date: {report_date}")
    return report_data

def process_driving_history_file(file_path, target_date, driver_data, report_data):
    """Process a single driving history file"""
    try:
        # Skip metadata and load the CSV using pandas
        df = load_csv_with_header_detection(file_path)
        if df is None or df.empty:
            logger.warning(f"Failed to load driving history file: {file_path}")
            return
        
        logger.info(f"DataFrame columns: {df.columns.tolist()}")
        
        # Identify required columns
        driver_col = find_column(df, ['contact', 'driver', 'person'])
        event_type_col = find_column(df, ['msgtype', 'event type', 'type'])
        time_col = find_column(df, ['eventdatetime', 'event time', 'time'])
        location_col = find_column(df, ['location', 'address'])
        
        if not all([driver_col, event_type_col, time_col]):
            missing = []
            if not driver_col: missing.append("driver")
            if not event_type_col: missing.append("event type")
            if not time_col: missing.append("time")
            logger.warning(f"Missing required columns in {file_path}: {', '.join(missing)}")
            return
        
        logger.info(f"Found driver column: {driver_col}")
        logger.info(f"Found event type column: {event_type_col}")
        logger.info(f"Found time column: {time_col}")
        if location_col:
            logger.info(f"Found location column: {location_col}")
        
        # Parse timestamps
        df['parsed_time'] = pd.to_datetime(df[time_col], errors='coerce')
        valid_times = df['parsed_time'].notna()
        
        logger.info(f"Total rows: {len(df)}")
        logger.info(f"Rows with valid timestamps: {valid_times.sum()}")
        
        # Filter for target date
        df['date'] = df['parsed_time'].dt.date
        date_filter = df['date'] == target_date
        filtered_df = df[date_filter & valid_times]
        
        logger.info(f"Rows matching target date {target_date}: {len(filtered_df)}")
        
        # Process matching rows
        records_processed = 0
        
        for _, row in filtered_df.iterrows():
            records_processed += 1
            
            # Extract driver name
            driver_name = str(row[driver_col]).strip()
            if not driver_name or pd.isna(driver_name):
                continue
                
            # Normalize driver name
            normalized_name = normalize_name(driver_name)
            
            # Extract timestamp and event type
            timestamp = row['parsed_time']
            event_type = str(row[event_type_col]).strip().lower() if not pd.isna(row[event_type_col]) else ""
            
            # Extract location if available
            location = str(row[location_col]).strip() if location_col and not pd.isna(row[location_col]) else None
            
            # Create or update driver record
            if normalized_name not in driver_data:
                driver_data[normalized_name] = {
                    'name': driver_name,
                    'normalized_name': normalized_name,
                    'key_on_time': None,
                    'key_off_time': None,
                    'minutes_late': 0,
                    'minutes_early_end': 0,
                    'status': 'unknown',
                    'data_sources': ['driving_history'],
                    'events': [],
                    'job_number': None,
                    'location': None
                }
            elif 'driving_history' not in driver_data[normalized_name]['data_sources']:
                driver_data[normalized_name]['data_sources'].append('driving_history')
            
            # Record event
            event_data = {
                'timestamp': timestamp,
                'event_type': event_type,
                'source': 'driving_history'
            }
            
            if location:
                event_data['location'] = location
                
                # Try to extract job number from location
                job_number = extract_job_number(location)
                if job_number and not driver_data[normalized_name]['job_number']:
                    driver_data[normalized_name]['job_number'] = job_number
            
            driver_data[normalized_name]['events'].append(event_data)
            
            # Update key times based on event
            if 'key on' in event_type:
                if (driver_data[normalized_name]['key_on_time'] is None or 
                    timestamp < driver_data[normalized_name]['key_on_time']):
                    driver_data[normalized_name]['key_on_time'] = timestamp
            
            elif 'key off' in event_type:
                if (driver_data[normalized_name]['key_off_time'] is None or 
                    timestamp > driver_data[normalized_name]['key_off_time']):
                    driver_data[normalized_name]['key_off_time'] = timestamp
        
        # Update report stats
        report_data['driving_history_stats']['total_records'] += len(df)
        report_data['driving_history_stats']['filtered_records'] += records_processed
        
        logger.info(f"Processed {records_processed} driving history records for target date")
        
    except Exception as e:
        logger.error(f"Error processing driving history file {file_path}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def process_activity_detail_file(file_path, target_date, driver_data, report_data):
    """Process a single activity detail file"""
    try:
        # Skip metadata and load the CSV using pandas
        df = load_csv_with_header_detection(file_path)
        if df is None or df.empty:
            logger.warning(f"Failed to load activity detail file: {file_path}")
            return
        
        logger.info(f"DataFrame columns: {df.columns.tolist()}")
        
        # Identify required columns
        driver_col = find_column(df, ['contact', 'driver', 'person'])
        event_type_col = find_column(df, ['reasonx', 'event type', 'type'])
        time_col = find_column(df, ['eventdatetimex', 'event time', 'time'])
        location_col = find_column(df, ['locationx', 'location', 'address'])
        asset_col = find_column(df, ['assetlabel', 'asset', 'equipment'])
        
        if not all([driver_col, time_col]):
            missing = []
            if not driver_col: missing.append("driver")
            if not time_col: missing.append("time")
            logger.warning(f"Missing required columns in {file_path}: {', '.join(missing)}")
            return
        
        logger.info(f"Found driver column: {driver_col}")
        if event_type_col:
            logger.info(f"Found event type column: {event_type_col}")
        logger.info(f"Found time column: {time_col}")
        if location_col:
            logger.info(f"Found location column: {location_col}")
        if asset_col:
            logger.info(f"Found asset column: {asset_col}")
        
        # Parse timestamps
        df['parsed_time'] = pd.to_datetime(df[time_col], errors='coerce')
        valid_times = df['parsed_time'].notna()
        
        logger.info(f"Total rows: {len(df)}")
        logger.info(f"Rows with valid timestamps: {valid_times.sum()}")
        
        # Filter for target date
        df['date'] = df['parsed_time'].dt.date
        date_filter = df['date'] == target_date
        filtered_df = df[date_filter & valid_times]
        
        logger.info(f"Rows matching target date {target_date}: {len(filtered_df)}")
        
        # Process matching rows
        records_processed = 0
        
        for _, row in filtered_df.iterrows():
            records_processed += 1
            
            # Extract driver name
            driver_name = str(row[driver_col]).strip()
            if not driver_name or pd.isna(driver_name):
                continue
                
            # Normalize driver name
            normalized_name = normalize_name(driver_name)
            
            # Extract timestamp
            timestamp = row['parsed_time']
            
            # Extract event type if available
            event_type = ""
            if event_type_col and not pd.isna(row[event_type_col]):
                event_type = str(row[event_type_col]).strip().lower()
            
            # Extract location if available
            location = None
            if location_col and not pd.isna(row[location_col]):
                location = str(row[location_col]).strip()
            
            # Extract asset if available
            asset = None
            if asset_col and not pd.isna(row[asset_col]):
                asset = str(row[asset_col]).strip()
            
            # Create or update driver record
            if normalized_name not in driver_data:
                driver_data[normalized_name] = {
                    'name': driver_name,
                    'normalized_name': normalized_name,
                    'key_on_time': None,
                    'key_off_time': None,
                    'minutes_late': 0,
                    'minutes_early_end': 0,
                    'status': 'unknown',
                    'data_sources': ['activity_detail'],
                    'events': [],
                    'job_number': None,
                    'location': None,
                    'asset': asset
                }
            elif 'activity_detail' not in driver_data[normalized_name]['data_sources']:
                driver_data[normalized_name]['data_sources'].append('activity_detail')
                
            if asset and not driver_data[normalized_name].get('asset'):
                driver_data[normalized_name]['asset'] = asset
            
            # Record event
            event_data = {
                'timestamp': timestamp,
                'source': 'activity_detail'
            }
            
            if event_type:
                event_data['event_type'] = event_type
            
            if location:
                event_data['location'] = location
                
                # Try to extract job number from location
                job_number = extract_job_number(location)
                if job_number and not driver_data[normalized_name]['job_number']:
                    driver_data[normalized_name]['job_number'] = job_number
                    
                # Set location in driver record
                if not driver_data[normalized_name]['location']:
                    driver_data[normalized_name]['location'] = location
            
            driver_data[normalized_name]['events'].append(event_data)
            
            # Update key times based on event
            if event_type and ('key on' in event_type or event_type == 'key on'):
                if (driver_data[normalized_name]['key_on_time'] is None or 
                    timestamp < driver_data[normalized_name]['key_on_time']):
                    driver_data[normalized_name]['key_on_time'] = timestamp
            
            elif event_type and ('key off' in event_type or event_type == 'key off'):
                if (driver_data[normalized_name]['key_off_time'] is None or 
                    timestamp > driver_data[normalized_name]['key_off_time']):
                    driver_data[normalized_name]['key_off_time'] = timestamp
        
        # Update report stats
        report_data['activity_detail_stats']['total_records'] += len(df)
        report_data['activity_detail_stats']['filtered_records'] += records_processed
        
        logger.info(f"Processed {records_processed} activity detail records for target date")
        
    except Exception as e:
        logger.error(f"Error processing activity detail file {file_path}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def load_csv_with_header_detection(file_path):
    """Load a CSV file with header detection for MTD files"""
    try:
        # First, scan the file to find the header row
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        
        # Look for the row that's most likely to be the header
        header_row_idx = -1
        header_indicators = ['contact', 'driver', 'event', 'date', 'time', 'location', 'asset']
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            # Check if this line has multiple header indicators
            matches = sum(1 for indicator in header_indicators if indicator in line_lower)
            if matches >= 2:
                header_row_idx = i
                logger.info(f"Found header row at line {i+1}: {line.strip()}")
                break
        
        if header_row_idx == -1:
            logger.warning(f"Could not find header row in {file_path}")
            return None
        
        # Log the header row
        header_line = lines[header_row_idx].strip()
        logger.info(f"Using header: {header_line}")
        
        # Now read the CSV with pandas, skipping to the header row
        df = pd.read_csv(file_path, skiprows=header_row_idx, encoding='utf-8-sig')
        
        logger.info(f"Loaded dataframe with {len(df)} rows and columns: {df.columns.tolist()}")
        
        # Show first few rows for debugging
        logger.info(f"First row sample: {df.iloc[0].to_dict() if not df.empty else 'Empty dataframe'}")
        
        return df
    
    except Exception as e:
        logger.error(f"Error loading CSV with header detection for {file_path}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def find_column(df, keywords):
    """Find a column in the dataframe based on keywords"""
    for col in df.columns:
        col_str = str(col).lower()
        for keyword in keywords:
            if keyword in col_str:
                return col
    
    # If no match by name, try to look at the data to identify columns
    if 'contact' in keywords or 'driver' in keywords:
        # Driver columns typically have text that looks like names
        for col in df.columns:
            if df[col].dtype == 'object':
                sample = df[col].dropna().astype(str).iloc[:5].tolist()
                if any(' ' in s for s in sample):  # Names typically have spaces
                    return col
    
    # If no match found, take a direct approach based on expected column names
    common_mappings = {
        'contact': ['Contact', 'Driver', 'DriverName', 'Operator'],
        'eventdatetime': ['EventDateTime', 'DateTime', 'Time', 'Timestamp'],
        'eventdatetimex': ['EventDateTimex', 'DateTimex', 'Timex'],
        'msgtype': ['MsgType', 'EventType', 'Type', 'Action'],
        'reasonx': ['Reasonx', 'ReasonCode', 'ActionType'],
        'location': ['Location', 'Address', 'Place', 'Site'],
        'locationx': ['Locationx', 'AddressX', 'PlaceX', 'SiteX'],
        'assetlabel': ['AssetLabel', 'Asset', 'Equipment', 'Vehicle']
    }
    
    for keyword in keywords:
        if keyword in common_mappings:
            for possible_name in common_mappings[keyword]:
                if possible_name in df.columns:
                    return possible_name
    
    # No matching column found
    return None

def calculate_metrics(
    driver_data: Dict[str, Dict[str, Any]],
    report_data: Dict[str, Any]
) -> None:
    """
    Calculate metrics for the report
    
    Args:
        driver_data: Driver data to analyze
        report_data: Report data structure to update with metrics
    """
    logger.info("Calculating metrics for report")
    
    # Define standard work hours (7am to 5pm)
    standard_start_hour = 7
    standard_end_hour = 17
    
    # Set timing thresholds
    late_threshold_minutes = 15  # More than 15 minutes late
    early_end_threshold_minutes = 30  # Left more than 30 minutes early
    
    # Track counts
    total_drivers = len(driver_data)
    on_time_count = 0
    late_count = 0
    early_end_count = 0
    not_on_job_count = 0
    
    # Process each driver
    for driver_key, driver in driver_data.items():
        key_on_time = driver.get('key_on_time')
        key_off_time = driver.get('key_off_time')
        
        # Default values
        minutes_late = 0
        minutes_early_end = 0
        status = 'unknown'
        
        if key_on_time is None and key_off_time is None:
            # No key on/off records found
            status = 'not_on_job'
            not_on_job_count += 1
        else:
            # Calculate start time metrics
            if key_on_time:
                standard_start_time = datetime.combine(key_on_time.date(), 
                                                      datetime.min.time().replace(hour=standard_start_hour))
                
                if key_on_time > standard_start_time:
                    # Driver started late
                    time_diff = key_on_time - standard_start_time
                    minutes_late = time_diff.total_seconds() / 60
                    
                    if minutes_late > late_threshold_minutes:
                        status = 'late'
                        late_count += 1
                    else:
                        status = 'on_time'
                        on_time_count += 1
                else:
                    status = 'on_time'
                    on_time_count += 1
            
            # Calculate end time metrics
            if key_off_time:
                standard_end_time = datetime.combine(key_off_time.date(), 
                                                    datetime.min.time().replace(hour=standard_end_hour))
                
                if key_off_time < standard_end_time:
                    # Driver ended early
                    time_diff = standard_end_time - key_off_time
                    minutes_early_end = time_diff.total_seconds() / 60
                    
                    if minutes_early_end > early_end_threshold_minutes and status != 'late':
                        status = 'early_end'
                        # Adjust counts if we're changing the status
                        if minutes_late > late_threshold_minutes:
                            late_count -= 1
                        else:
                            on_time_count -= 1
                        early_end_count += 1
        
        # Update driver metrics
        driver['minutes_late'] = int(minutes_late)
        driver['minutes_early_end'] = int(minutes_early_end)
        driver['status'] = status
        
        # Add to report data
        report_data['driver_metrics'][driver['name']] = {
            'minutes_late': int(minutes_late),
            'minutes_early_end': int(minutes_early_end),
            'status': status,
            'key_on_time': key_on_time.strftime('%I:%M %p') if key_on_time else None,
            'key_off_time': key_off_time.strftime('%I:%M %p') if key_off_time else None,
            'job_number': driver.get('job_number'),
            'location': driver.get('location'),
            'asset': driver.get('asset')
        }
    
    # Update report summary
    report_data['total_drivers'] = total_drivers
    report_data['on_time_count'] = on_time_count
    report_data['late_count'] = late_count
    report_data['early_end_count'] = early_end_count
    report_data['not_on_job_count'] = not_on_job_count
    
    # Calculate percentages
    if total_drivers > 0:
        report_data['on_time_percent'] = round((on_time_count / total_drivers) * 100)
        report_data['late_percent'] = round((late_count / total_drivers) * 100)
        report_data['early_end_percent'] = round((early_end_count / total_drivers) * 100)
        report_data['not_on_job_percent'] = round((not_on_job_count / total_drivers) * 100)
    
    logger.info(f"Metrics calculation complete: {on_time_count} on time, {late_count} late, "
               f"{early_end_count} early end, {not_on_job_count} not on job")

def normalize_name(name: str) -> str:
    """
    Normalize a name for consistent matching
    
    Args:
        name: Name to normalize
        
    Returns:
        str: Normalized name
    """
    if not name:
        return ""
    
    # Remove parentheses and numbers that might indicate IDs
    name = re.sub(r'\s*\(\d+\)', '', name)
    
    # Convert to lowercase and remove extra spaces
    normalized = name.lower().strip()
    
    # Remove special characters
    normalized = re.sub(r'[^a-z0-9]', '', normalized)
    
    return normalized

def extract_job_number(text: str) -> Optional[str]:
    """
    Extract a job number from text
    
    Args:
        text: Text to extract job number from
        
    Returns:
        str: Extracted job number or None if not found
    """
    if not text:
        return None
    
    # Common patterns for job numbers
    patterns = [
        r'job\s*#?\s*(\d{4}-\d{3})',  # Job #2023-001
        r'job\s*#?\s*(\d{8})',         # Job #20230001
        r'job\s*#?\s*(\d{4})',         # Job #2023
        r'(\d{4}-\d{3})',              # 2023-001
        r'job site\s*#?\s*(\d+)',      # Job site #1234
        r'site\s*#?\s*(\d+)'           # Site #1234
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None