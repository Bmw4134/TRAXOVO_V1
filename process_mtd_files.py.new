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

def find_header_row(file_path: str) -> Tuple[Optional[List[str]], int, Dict[str, int]]:
    """
    Find the actual header row in a CSV file that might have metadata at the top
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Tuple of (header row, header row index, column mapping)
    """
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        
        # Try to find the actual header row by scanning for known header terms
        header = None
        header_row_idx = 0
        
        for row_idx, row in enumerate(reader):
            # Skip empty rows
            if not row or (len(row) == 1 and not row[0].strip()):
                continue
                
            # Look for keywords that indicate a header row
            row_text = ' '.join(row).lower()
            if 'contact' in row_text or 'eventdatetime' in row_text or 'msgtype' in row_text or 'reasonx' in row_text:
                header = row
                header_row_idx = row_idx
                break
        
        # If we can't find a header row, try heuristics like looking for the longest row
        if not header:
            # Reset file pointer and try different approach
            f.seek(0)
            reader = csv.reader(f)
            
            max_columns = 0
            for row_idx, row in enumerate(reader):
                if len(row) > max_columns:
                    max_columns = len(row)
                    header = row
                    header_row_idx = row_idx
            
            logger.info(f"Using longest row as header: {header}")
    
    # Map column indices
    column_map = {}
    
    if header:
        logger.info(f"Found header row ({header_row_idx}): {header}")
        for i, col in enumerate(header):
            col_lower = col.lower()
            
            # Map standard column names
            if col_lower == 'contact' or 'driver' in col_lower or col_lower == 'contactname':
                column_map['driver'] = i
                logger.info(f"Found driver column: {col} at position {i}")
                
            elif col_lower == 'msgtype' or col_lower == 'reasonx' or 'event' in col_lower:
                column_map['event'] = i
                logger.info(f"Found event column: {col} at position {i}")
                
            elif col_lower == 'eventdatetime' or col_lower == 'eventdatetimex' or 'timestamp' in col_lower:
                column_map['time'] = i
                logger.info(f"Found time column: {col} at position {i}")
                
            elif col_lower == 'assetlabel' or 'asset' in col_lower:
                column_map['asset'] = i
                logger.info(f"Found asset column: {col} at position {i}")
                
            elif col_lower == 'locationx' or 'location' in col_lower or 'address' in col_lower:
                column_map['location'] = i
                logger.info(f"Found location column: {col} at position {i}")
    
    return header, header_row_idx, column_map

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
            
            # Find header row and column mapping
            header, header_row_idx, column_map = find_header_row(file_path)
            
            if not header or not all(k in column_map for k in ['driver', 'event', 'time']):
                missing_cols = [k for k in ['driver', 'event', 'time'] if k not in column_map]
                logger.warning(f"Missing required columns in {file_path}: {', '.join(missing_cols)}")
                continue
            
            # Process the file row by row
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                
                # Skip to header row
                for _ in range(header_row_idx + 1):
                    next(reader, None)
                
                # Process data rows
                rows_processed = 0
                for row in reader:
                    rows_processed += 1
                    
                    # Skip rows that don't have enough columns
                    if len(row) <= max(column_map.values()):
                        continue
                    
                    # Extract time
                    try:
                        time_str = row[column_map['time']]
                        if not time_str:
                            continue
                            
                        timestamp = parse_timestamp(time_str)
                        if not timestamp:
                            continue
                            
                        if timestamp.date() != target_date:
                            continue
                            
                        filtered_records += 1
                        
                        # Extract driver name
                        driver_name = row[column_map['driver']].strip()
                        if not driver_name:
                            continue
                            
                        # Extract event type
                        event_type = row[column_map['event']].strip().lower()
                        
                        # Normalize name for consistent matching
                        normalized_name = normalize_name(driver_name)
                        
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
                                'asset_ids': []
                            }
                        elif 'driving_history' not in driver_data[normalized_name]['data_sources']:
                            driver_data[normalized_name]['data_sources'].append('driving_history')
                        
                        # Record event
                        driver_data[normalized_name]['events'].append({
                            'timestamp': timestamp,
                            'event_type': event_type,
                            'source': 'driving_history'
                        })
                        
                        # Update key times based on event
                        if 'key on' in event_type or 'keyon' in event_type:
                            if (driver_data[normalized_name]['key_on_time'] is None or 
                                timestamp < driver_data[normalized_name]['key_on_time']):
                                driver_data[normalized_name]['key_on_time'] = timestamp
                        
                        elif 'key off' in event_type or 'keyoff' in event_type:
                            if (driver_data[normalized_name]['key_off_time'] is None or 
                                timestamp > driver_data[normalized_name]['key_off_time']):
                                driver_data[normalized_name]['key_off_time'] = timestamp
                                
                    except Exception as e:
                        logger.warning(f"Error processing row: {e}")
                        continue
                
                total_records += rows_processed
                logger.info(f"Processed {rows_processed} rows")
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
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
            
            # Find header row and column mapping
            header, header_row_idx, column_map = find_header_row(file_path)
            
            if not header or not all(k in column_map for k in ['driver', 'time']):
                missing_cols = [k for k in ['driver', 'time'] if k not in column_map]
                logger.warning(f"Missing required columns in {file_path}: {', '.join(missing_cols)}")
                continue
            
            # Process the file row by row
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                
                # Skip to header row
                for _ in range(header_row_idx + 1):
                    next(reader, None)
                
                # Process data rows
                rows_processed = 0
                for row in reader:
                    rows_processed += 1
                    
                    # Skip rows that don't have enough columns
                    if len(row) <= max(column_map.values()):
                        continue
                    
                    # Extract time
                    try:
                        time_str = row[column_map['time']]
                        if not time_str:
                            continue
                            
                        timestamp = parse_timestamp(time_str)
                        if not timestamp:
                            continue
                            
                        if timestamp.date() != target_date:
                            continue
                            
                        filtered_records += 1
                        
                        # Extract driver name
                        driver_name = row[column_map['driver']].strip()
                        if not driver_name:
                            continue
                        
                        # Normalize name for consistent matching
                        normalized_name = normalize_name(driver_name)
                        
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
                                'asset_ids': []
                            }
                        elif 'activity_detail' not in driver_data[normalized_name]['data_sources']:
                            driver_data[normalized_name]['data_sources'].append('activity_detail')
                        
                        # Extract asset ID if available
                        if 'asset' in column_map:
                            asset_id = row[column_map['asset']].strip()
                            if asset_id and asset_id not in driver_data[normalized_name]['asset_ids']:
                                driver_data[normalized_name]['asset_ids'].append(asset_id)
                        
                        # Extract location if available
                        location = None
                        if 'location' in column_map:
                            location = row[column_map['location']].strip()
                        
                        # Extract event type if available
                        event_type = None
                        if 'event' in column_map:
                            event_type = row[column_map['event']].strip().lower()
                        
                        # Record event
                        event_data = {
                            'timestamp': timestamp,
                            'source': 'activity_detail'
                        }
                        
                        if location:
                            event_data['location'] = location
                            
                        if event_type:
                            event_data['event_type'] = event_type
                            
                            # Update key times based on event
                            if event_type and ('key on' in event_type or 'keyon' in event_type):
                                if (driver_data[normalized_name]['key_on_time'] is None or 
                                    timestamp < driver_data[normalized_name]['key_on_time']):
                                    driver_data[normalized_name]['key_on_time'] = timestamp
                            
                            elif event_type and ('key off' in event_type or 'keyoff' in event_type):
                                if (driver_data[normalized_name]['key_off_time'] is None or 
                                    timestamp > driver_data[normalized_name]['key_off_time']):
                                    driver_data[normalized_name]['key_off_time'] = timestamp
                        
                        driver_data[normalized_name]['events'].append(event_data)
                                
                    except Exception as e:
                        logger.warning(f"Error processing row: {e}")
                        continue
                
                total_records += rows_processed
                logger.info(f"Processed {rows_processed} rows")
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
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
    
    # Remove parentheses and numbers that might indicate IDs
    name = re.sub(r'\s*\(\d+\)', '', name)
    
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
    
    # Check for potential date/time indicators
    timestamp_str = timestamp_str.strip()
    
    # Possible timestamp formats from various exports
    formats = [
        '%Y-%m-%d %H:%M:%S',  # 2025-05-15 08:30:00
        '%m/%d/%Y %H:%M:%S',  # 05/15/2025 08:30:00
        '%m/%d/%Y %I:%M:%S %p',  # 05/15/2025 08:30:00 AM
        '%m/%d/%Y %I:%M:%S %p CT',  # 05/15/2025 08:30:00 AM CT
        '%Y-%m-%dT%H:%M:%S',  # 2025-05-15T08:30:00
        '%Y-%m-%dT%H:%M:%S.%f',  # 2025-05-15T08:30:00.000
        '%m/%d/%Y %I:%M %p',  # 05/15/2025 08:30 AM
        '%m/%d/%Y %I:%M %p CT',  # 05/15/2025 08:30 AM CT
        '%Y-%m-%d %I:%M %p',  # 2025-05-15 08:30 AM
    ]
    
    # Clean the timestamp string (remove timezone indicators)
    clean_timestamp = re.sub(r'\s+[A-Z]{2,3}$', '', timestamp_str)
    
    # Try each format
    for fmt in formats:
        try:
            return datetime.strptime(clean_timestamp, fmt)
        except ValueError:
            continue
    
    # If all formats fail, try pandas parsing as a last resort
    try:
        return pd.to_datetime(timestamp_str).to_pydatetime()
    except:
        logger.warning(f"Failed to parse timestamp: {timestamp_str}")
        return None