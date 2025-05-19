"""
Attendance Data Pipeline

This module processes raw attendance data from various sources,
normalizes it, and prepares it for consumption by the UI and reporting tools.
"""

import os
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
import re
from pathlib import Path

# Import structured logger
from utils.structured_logger import get_pipeline_logger

# Get pipeline-specific logger
logger = get_pipeline_logger()

# Constants and configuration
DEFAULT_START_TIME = "07:00"
LATE_THRESHOLD_MINUTES = 15
TIMEZONE_UTC_OFFSET = -5  # CDT/CST timezone (UTC-5)

def find_latest_activity_file():
    """Find the latest activity detail file in the attached_assets directory"""
    activity_files = []
    
    # Check attached_assets directory for files
    assets_dir = Path("attached_assets")
    if not assets_dir.exists():
        logger.warning(f"Directory not found: {assets_dir}")
        return None
    
    # Look for ActivityDetail files
    for file in assets_dir.glob("ActivityDetail*.csv"):
        activity_files.append(str(file))
    
    if not activity_files:
        logger.warning("No ActivityDetail files found")
        return None
    
    # Return the latest file based on modification time
    latest_file = max(activity_files, key=os.path.getmtime)
    logger.info(f"Found latest activity file: {latest_file}")
    return latest_file


def find_latest_driving_history_file():
    """Find the latest driving history file in the attached_assets directory"""
    driving_files = []
    
    # Check attached_assets directory for files
    assets_dir = Path("attached_assets")
    if not assets_dir.exists():
        logger.warning(f"Directory not found: {assets_dir}")
        return None
    
    # Look for DrivingHistory files
    for file in assets_dir.glob("DrivingHistory*.csv"):
        driving_files.append(str(file))
    
    if not driving_files:
        logger.warning("No DrivingHistory files found")
        return None
    
    # Return the latest file based on modification time
    latest_file = max(driving_files, key=os.path.getmtime)
    logger.info(f"Found latest driving history file: {latest_file}")
    return latest_file


def find_latest_fleet_utilization_file():
    """Find the latest fleet utilization file in the attached_assets directory"""
    fleet_files = []
    
    # Check attached_assets directory for files
    assets_dir = Path("attached_assets")
    if not assets_dir.exists():
        logger.warning(f"Directory not found: {assets_dir}")
        return None
    
    # Look for FleetUtilization files
    for file in assets_dir.glob("FleetUtilization*.xlsx"):
        fleet_files.append(str(file))
    
    if not fleet_files:
        logger.warning("No FleetUtilization files found")
        return None
    
    # Return the latest file based on modification time
    latest_file = max(fleet_files, key=os.path.getmtime)
    logger.info(f"Found latest fleet utilization file: {latest_file}")
    return latest_file


def normalize_time(time_str):
    """
    Normalize time string to HH:MM format.
    
    Args:
        time_str (str): Time string in various formats
        
    Returns:
        str: Normalized time string in HH:MM format or None if invalid
    """
    if not time_str or pd.isna(time_str):
        return None
    
    # Convert to string explicitly for safety
    time_str = str(time_str).strip()
    
    # Try various formats
    formats = [
        '%H:%M',         # 13:45
        '%H:%M:%S',      # 13:45:30
        '%I:%M %p',      # 1:45 PM
        '%I:%M:%S %p',   # 1:45:30 PM
        '%I:%M%p',       # 1:45PM
        '%I:%M:%S%p',    # 1:45:30PM
        '%I %p',         # 1 PM
        '%I%p'           # 1PM
    ]
    
    # Try each format
    for fmt in formats:
        try:
            # Parse time string
            dt = datetime.strptime(time_str, fmt)
            # Return normalized format
            return dt.strftime('%H:%M')
        except ValueError:
            continue
    
    # If we got here, none of the formats matched
    logger.warning(f"Could not normalize time string: {time_str}")
    return None


def parse_activity_detail(file_path):
    """
    Parse activity detail file to extract driver activity data.
    
    Args:
        file_path (str): Path to the ActivityDetail CSV file
        
    Returns:
        list: List of driver activity records
    """
    try:
        if not file_path or not os.path.exists(file_path):
            logger.error(f"Activity detail file not found: {file_path}")
            return []
        
        # Read the CSV file
        logger.info(f"Reading activity detail file: {file_path}")
        df = pd.read_csv(file_path)
        
        # Check if the file has required columns
        required_columns = ['Operator', 'Job Site', 'Time On Site']
        if not all(col in df.columns for col in required_columns):
            logger.error(f"Activity detail file missing required columns: {file_path}")
            return []
        
        # Convert to records
        records = []
        for _, row in df.iterrows():
            # Extract driver name and job site
            driver_name = row.get('Operator', '').strip()
            job_site = row.get('Job Site', '').strip()
            
            # Skip empty records
            if not driver_name or not job_site:
                continue
            
            # Parse time on site
            time_on_site = normalize_time(row.get('Time On Site'))
            
            # Create record
            record = {
                'driver_name': driver_name,
                'job_site': job_site,
                'actual_start': time_on_site,
                'data_source': 'activity_detail'
            }
            
            records.append(record)
        
        logger.info(f"Parsed {len(records)} records from activity detail file")
        return records
    except Exception as e:
        logger.error(f"Error parsing activity detail file: {e}", exc_info=True)
        return []


def parse_driving_history(file_path):
    """
    Parse driving history file to extract driver movement data.
    
    Args:
        file_path (str): Path to the DrivingHistory CSV file
        
    Returns:
        list: List of driver movement records
    """
    try:
        if not file_path or not os.path.exists(file_path):
            logger.error(f"Driving history file not found: {file_path}")
            return []
        
        # Read the CSV file
        logger.info(f"Reading driving history file: {file_path}")
        df = pd.read_csv(file_path)
        
        # Check if the file has required columns
        required_columns = ['Driver', 'Start Location', 'Start Time', 'End Time']
        if not all(col in df.columns for col in required_columns):
            logger.error(f"Driving history file missing required columns: {file_path}")
            return []
        
        # Convert to records
        records = []
        for _, row in df.iterrows():
            # Extract driver name and location
            driver_name = row.get('Driver', '').strip()
            start_location = row.get('Start Location', '').strip()
            
            # Skip empty records
            if not driver_name or not start_location:
                continue
            
            # Parse times
            start_time = normalize_time(row.get('Start Time'))
            end_time = normalize_time(row.get('End Time'))
            
            # Create record
            record = {
                'driver_name': driver_name,
                'job_site': start_location,
                'actual_start': start_time,
                'actual_end': end_time,
                'data_source': 'driving_history'
            }
            
            records.append(record)
        
        logger.info(f"Parsed {len(records)} records from driving history file")
        return records
    except Exception as e:
        logger.error(f"Error parsing driving history file: {e}", exc_info=True)
        return []


def parse_fleet_utilization(file_path):
    """
    Parse fleet utilization file to extract scheduled times.
    
    Args:
        file_path (str): Path to the FleetUtilization Excel file
        
    Returns:
        list: List of scheduled time records
    """
    try:
        if not file_path or not os.path.exists(file_path):
            logger.error(f"Fleet utilization file not found: {file_path}")
            return []
        
        # Read the Excel file
        logger.info(f"Reading fleet utilization file: {file_path}")
        df = pd.read_excel(file_path)
        
        # Check if the file has required columns
        required_columns = ['Asset', 'Operator', 'Scheduled Start', 'Scheduled End']
        if not all(col in df.columns for col in required_columns):
            logger.error(f"Fleet utilization file missing required columns: {file_path}")
            return []
        
        # Convert to records
        records = []
        for _, row in df.iterrows():
            # Extract driver name and asset
            driver_name = row.get('Operator', '').strip()
            asset = row.get('Asset', '').strip()
            
            # Skip empty records
            if not driver_name or not asset:
                continue
            
            # Parse times
            scheduled_start = normalize_time(row.get('Scheduled Start'))
            scheduled_end = normalize_time(row.get('Scheduled End'))
            
            # Create record
            record = {
                'driver_name': driver_name,
                'asset_id': asset,
                'scheduled_start': scheduled_start,
                'scheduled_end': scheduled_end,
                'data_source': 'fleet_utilization'
            }
            
            records.append(record)
        
        logger.info(f"Parsed {len(records)} records from fleet utilization file")
        return records
    except Exception as e:
        logger.error(f"Error parsing fleet utilization file: {e}", exc_info=True)
        return []


def merge_attendance_records(activity_records, driving_records, schedule_records):
    """
    Merge attendance records from different sources.
    
    Args:
        activity_records (list): Records from activity detail file
        driving_records (list): Records from driving history file
        schedule_records (list): Records from fleet utilization file
        
    Returns:
        list: Merged attendance records
    """
    # Create a dictionary to store merged records by driver name
    merged_records = {}
    
    # Process schedule records first (they contain the expected times)
    for record in schedule_records:
        driver_name = record.get('driver_name')
        if not driver_name:
            continue
        
        merged_records[driver_name] = {
            'driver_name': driver_name,
            'asset_id': record.get('asset_id'),
            'scheduled_start': record.get('scheduled_start'),
            'scheduled_end': record.get('scheduled_end'),
            'data_sources': ['fleet_utilization']
        }
    
    # Process activity records (they contain actual start times)
    for record in activity_records:
        driver_name = record.get('driver_name')
        if not driver_name:
            continue
        
        if driver_name in merged_records:
            # Update existing record
            merged_records[driver_name]['actual_start'] = record.get('actual_start')
            merged_records[driver_name]['job_site'] = record.get('job_site')
            if 'activity_detail' not in merged_records[driver_name].get('data_sources', []):
                merged_records[driver_name]['data_sources'].append('activity_detail')
        else:
            # Create new record
            merged_records[driver_name] = {
                'driver_name': driver_name,
                'job_site': record.get('job_site'),
                'actual_start': record.get('actual_start'),
                'data_sources': ['activity_detail']
            }
    
    # Process driving records (they contain both start and end times)
    for record in driving_records:
        driver_name = record.get('driver_name')
        if not driver_name:
            continue
        
        if driver_name in merged_records:
            # Update existing record
            if not merged_records[driver_name].get('actual_start'):
                merged_records[driver_name]['actual_start'] = record.get('actual_start')
            if not merged_records[driver_name].get('actual_end'):
                merged_records[driver_name]['actual_end'] = record.get('actual_end')
            if not merged_records[driver_name].get('job_site'):
                merged_records[driver_name]['job_site'] = record.get('job_site')
            if 'driving_history' not in merged_records[driver_name].get('data_sources', []):
                merged_records[driver_name]['data_sources'].append('driving_history')
        else:
            # Create new record
            merged_records[driver_name] = {
                'driver_name': driver_name,
                'job_site': record.get('job_site'),
                'actual_start': record.get('actual_start'),
                'actual_end': record.get('actual_end'),
                'data_sources': ['driving_history']
            }
    
    # Calculate lateness and early departure
    for driver_name, record in merged_records.items():
        # Default scheduled start if not available
        if not record.get('scheduled_start'):
            record['scheduled_start'] = DEFAULT_START_TIME
        
        # Calculate lateness
        if record.get('scheduled_start') and record.get('actual_start'):
            # Convert to datetime objects
            try:
                scheduled = datetime.strptime(record['scheduled_start'], '%H:%M')
                actual = datetime.strptime(record['actual_start'], '%H:%M')
                
                # Calculate minutes late
                delta = actual - scheduled
                minutes_late = delta.total_seconds() / 60
                
                # Only positive values (late arrivals)
                if minutes_late > 0:
                    record['late_minutes'] = round(minutes_late)
            except (ValueError, TypeError):
                logger.warning(f"Could not calculate lateness for driver {driver_name}")
        
        # Calculate early departure
        if record.get('scheduled_end') and record.get('actual_end'):
            # Convert to datetime objects
            try:
                scheduled = datetime.strptime(record['scheduled_end'], '%H:%M')
                actual = datetime.strptime(record['actual_end'], '%H:%M')
                
                # Calculate minutes early
                delta = scheduled - actual
                minutes_early = delta.total_seconds() / 60
                
                # Only positive values (early departures)
                if minutes_early > 0:
                    record['early_minutes'] = round(minutes_early)
            except (ValueError, TypeError):
                logger.warning(f"Could not calculate early departure for driver {driver_name}")
    
    # Convert to list
    merged_list = list(merged_records.values())
    logger.info(f"Merged {len(merged_list)} attendance records")
    
    return merged_list


def process_attendance_data(date_str=None):
    """
    Process attendance data for a specific date.
    
    Args:
        date_str (str): Date string in format YYYY-MM-DD, defaults to today
        
    Returns:
        list: Processed attendance records
    """
    logger.info(f"Processing attendance data for date: {date_str or 'today'}")
    
    # Find the latest input files
    activity_file = find_latest_activity_file()
    driving_file = find_latest_driving_history_file()
    fleet_file = find_latest_fleet_utilization_file()
    
    # Parse the input files
    activity_records = parse_activity_detail(activity_file)
    driving_records = parse_driving_history(driving_file)
    schedule_records = parse_fleet_utilization(fleet_file)
    
    # Merge the records
    merged_records = merge_attendance_records(activity_records, driving_records, schedule_records)
    
    # Log processing summary
    logger.info(f"Processed attendance data: {len(merged_records)} total records")
    
    return merged_records