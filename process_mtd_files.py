"""
Process MTD Files Module

This module provides specialized functionality for processing large Month-to-Date (MTD) files
in a memory-efficient manner by processing them in chunks and focusing only on records
for a specific target date.
"""

import os
import re
import csv
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.DEBUG)
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
    driver_data = process_driving_history_files(driving_history_paths, target_date, report_data)
    
    # Process activity detail files
    process_activity_detail_files(activity_detail_paths, target_date, driver_data, report_data)
    
    # Calculate metrics
    calculate_metrics(driver_data, report_data)
    
    logger.info(f"Completed processing MTD files for date: {report_date}")
    return report_data

def process_driving_history_files(
    file_paths: List[str],
    target_date: datetime.date,
    report_data: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """
    Process driving history files in chunks, filtering for the target date
    
    Args:
        file_paths: List of file paths to process
        target_date: Target date to filter records for
        report_data: Report data structure to update with statistics
        
    Returns:
        Dict mapping driver names to their data
    """
    logger.info(f"Processing {len(file_paths)} driving history files")
    
    driver_data = {}
    total_records = 0
    filtered_records = 0
    
    for file_path in file_paths:
        try:
            logger.info(f"Processing driving history file: {file_path}")
            
            # Process file in chunks
            chunk_size = 10000  # Adjust based on memory constraints
            
            try:
                # First pass: get total count and identify column names
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    # Read first line to identify columns
                    reader = csv.reader(f)
                    header = next(reader)
                    
                    # Identify key columns
                    driver_col = None
                    event_col = None
                    time_col = None
                    
                    for i, col in enumerate(header):
                        col_lower = col.lower()
                        if any(name in col_lower for name in ['driver name', 'driver', 'contact', 'person']):
                            driver_col = i
                        if any(name in col_lower for name in ['event', 'action', 'type']):
                            event_col = i
                        if any(name in col_lower for name in ['event date time', 'eventdatetimex', 'timestamp']):
                            time_col = i
                    
                    if driver_col is None or event_col is None or time_col is None:
                        logger.warning(f"Missing required columns in {file_path}")
                        continue
                        
                    # Count total rows (but don't load them into memory)
                    row_count = sum(1 for _ in reader) + 1  # +1 for header
                    total_records += row_count - 1  # Exclude header
                    logger.info(f"Total records in file: {row_count - 1}")
            
                # Second pass: process relevant rows only
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    next(reader)  # Skip header
                    
                    for row in reader:
                        if len(row) <= max(driver_col, event_col, time_col):
                            # Skip malformed rows
                            continue
                            
                        try:
                            # Parse timestamp
                            timestamp_str = row[time_col]
                            timestamp = parse_timestamp(timestamp_str)
                            
                            if timestamp and timestamp.date() == target_date:
                                # This record matches our target date
                                filtered_records += 1
                                
                                # Extract driver name
                                driver_name = row[driver_col].strip()
                                if not driver_name:
                                    continue
                                    
                                # Normalize driver name
                                normalized_name = normalize_name(driver_name)
                                
                                # Get or create driver record
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
                                        'events': []
                                    }
                                elif 'driving_history' not in driver_data[normalized_name]['data_sources']:
                                    driver_data[normalized_name]['data_sources'].append('driving_history')
                                
                                # Extract event type
                                event_type = row[event_col].strip().lower()
                                
                                # Record event
                                driver_data[normalized_name]['events'].append({
                                    'timestamp': timestamp,
                                    'event_type': event_type,
                                    'source': 'driving_history'
                                })
                                
                                # Update key times based on event type
                                if 'key on' in event_type or 'keyon' in event_type:
                                    # This is a key on event
                                    if (driver_data[normalized_name]['key_on_time'] is None or 
                                        timestamp < driver_data[normalized_name]['key_on_time']):
                                        driver_data[normalized_name]['key_on_time'] = timestamp
                                        
                                elif 'key off' in event_type or 'keyoff' in event_type:
                                    # This is a key off event
                                    if (driver_data[normalized_name]['key_off_time'] is None or 
                                        timestamp > driver_data[normalized_name]['key_off_time']):
                                        driver_data[normalized_name]['key_off_time'] = timestamp
                                        
                        except Exception as e:
                            logger.warning(f"Error processing row: {e}")
                            continue
            
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        except Exception as e:
            logger.error(f"Fatal error processing file {file_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    # Update statistics
    report_data['driving_history_stats']['total_records'] = total_records
    report_data['driving_history_stats']['filtered_records'] = filtered_records
    
    logger.info(f"Processed {filtered_records} relevant records out of {total_records} total")
    logger.info(f"Identified {len(driver_data)} unique drivers")
    
    return driver_data

def process_activity_detail_files(
    file_paths: List[str],
    target_date: datetime.date,
    driver_data: Dict[str, Dict[str, Any]],
    report_data: Dict[str, Any]
) -> None:
    """
    Process activity detail files in chunks, filtering for the target date
    
    Args:
        file_paths: List of file paths to process
        target_date: Target date to filter records for
        driver_data: Driver data to update with activity details
        report_data: Report data structure to update with statistics
    """
    logger.info(f"Processing {len(file_paths)} activity detail files")
    
    total_records = 0
    filtered_records = 0
    
    for file_path in file_paths:
        try:
            logger.info(f"Processing activity detail file: {file_path}")
            
            # Process file in chunks
            chunk_size = 10000  # Adjust based on memory constraints
            
            try:
                # First pass: get total count and identify column names
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    # Read first line to identify columns
                    reader = csv.reader(f)
                    header = next(reader)
                    
                    # Identify key columns
                    driver_col = None
                    asset_col = None
                    time_col = None
                    location_col = None
                    
                    for i, col in enumerate(header):
                        col_lower = col.lower()
                        if any(name in col_lower for name in ['driver name', 'driver', 'contact', 'person']):
                            driver_col = i
                        if any(name in col_lower for name in ['asset label', 'unit', 'assetlabel', 'unitid']):
                            asset_col = i
                        if any(name in col_lower for name in ['event date time', 'eventdatetimex', 'timestamp']):
                            time_col = i
                        if any(name in col_lower for name in ['location', 'address', 'loc']):
                            location_col = i
                    
                    if driver_col is None or asset_col is None or time_col is None:
                        logger.warning(f"Missing required columns in {file_path}")
                        continue
                        
                    # Count total rows (but don't load them into memory)
                    row_count = sum(1 for _ in reader) + 1  # +1 for header
                    total_records += row_count - 1  # Exclude header
                    logger.info(f"Total records in file: {row_count - 1}")
            
                # Second pass: process relevant rows only
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    next(reader)  # Skip header
                    
                    for row in reader:
                        if len(row) <= max(driver_col, asset_col, time_col):
                            # Skip malformed rows
                            continue
                            
                        try:
                            # Parse timestamp
                            timestamp_str = row[time_col]
                            timestamp = parse_timestamp(timestamp_str)
                            
                            if timestamp and timestamp.date() == target_date:
                                # This record matches our target date
                                filtered_records += 1
                                
                                # Extract driver name
                                driver_name = row[driver_col].strip()
                                if not driver_name:
                                    continue
                                    
                                # Normalize driver name
                                normalized_name = normalize_name(driver_name)
                                
                                # Get or create driver record
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
                                        'asset_ids': []
                                    }
                                elif 'activity_detail' not in driver_data[normalized_name]['data_sources']:
                                    driver_data[normalized_name]['data_sources'].append('activity_detail')
                                
                                # Extract asset ID
                                asset_id = row[asset_col].strip()
                                if asset_id and asset_id not in driver_data[normalized_name].get('asset_ids', []):
                                    if 'asset_ids' not in driver_data[normalized_name]:
                                        driver_data[normalized_name]['asset_ids'] = []
                                    driver_data[normalized_name]['asset_ids'].append(asset_id)
                                
                                # Extract location if available
                                location = None
                                if location_col is not None and location_col < len(row):
                                    location = row[location_col].strip()
                                
                                # Record event
                                event_data = {
                                    'timestamp': timestamp,
                                    'asset_id': asset_id,
                                    'source': 'activity_detail'
                                }
                                
                                if location:
                                    event_data['location'] = location
                                    
                                driver_data[normalized_name]['events'].append(event_data)
                                
                        except Exception as e:
                            logger.warning(f"Error processing row: {e}")
                            continue
            
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        except Exception as e:
            logger.error(f"Fatal error processing file {file_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    # Update statistics
    report_data['activity_detail_stats']['total_records'] = total_records
    report_data['activity_detail_stats']['filtered_records'] = filtered_records
    
    logger.info(f"Processed {filtered_records} relevant records out of {total_records} total")

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
            'status': status
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
        
    # Convert to lowercase and remove extra spaces
    normalized = name.lower().strip()
    
    # Remove special characters
    normalized = re.sub(r'[^a-z0-9]', '', normalized)
    
    return normalized

def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse a timestamp string into a datetime object
    
    Args:
        timestamp_str: Timestamp string to parse
        
    Returns:
        datetime: Parsed datetime or None if parsing failed
    """
    if not timestamp_str or pd.isna(timestamp_str):
        return None
    
    # Possible timestamp formats from various exports
    formats = [
        '%Y-%m-%d %H:%M:%S',  # 2025-05-15 08:30:00
        '%m/%d/%Y %H:%M:%S',  # 05/15/2025 08:30:00
        '%m/%d/%Y %I:%M:%S %p',  # 05/15/2025 08:30:00 AM
        '%Y-%m-%dT%H:%M:%S',  # 2025-05-15T08:30:00
        '%Y-%m-%dT%H:%M:%S.%f',  # 2025-05-15T08:30:00.000
        '%m/%d/%Y %I:%M %p',  # 05/15/2025 08:30 AM
        '%Y-%m-%d %I:%M %p',  # 2025-05-15 08:30 AM
    ]
    
    # Try each format
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    # If all formats fail, try pandas parsing as a last resort
    try:
        return pd.to_datetime(timestamp_str).to_pydatetime()
    except:
        logger.warning(f"Failed to parse timestamp: {timestamp_str}")
        return None

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
    
    # Look for patterns like "Job 1234" or "1234-56"
    job_patterns = [
        r'job\s+(\d{4})',  # Job 1234
        r'job\s+(\d{4}-\d{2})',  # Job 1234-56
        r'(\d{4}-\d{2})',  # 1234-56
        r'(\d{4})',  # 1234
    ]
    
    for pattern in job_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None