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
    
    try:
        # Check attached_assets directory for files
        assets_dir = Path("attached_assets")
        if not assets_dir.exists():
            logger.warning(f"Directory not found: {assets_dir}")
            return None
        
        # Look for ActivityDetail files with fault tolerance
        for file in assets_dir.glob("ActivityDetail*.csv"):
            # Validate file exists and is readable
            if os.path.isfile(file) and os.access(file, os.R_OK):
                activity_files.append(str(file))
            else:
                logger.warning(f"File exists but not readable: {file}")
        
        if not activity_files:
            logger.warning("No ActivityDetail files found")
            return None
        
        # Return the latest file based on modification time
        latest_file = max(activity_files, key=os.path.getmtime)
        logger.info(f"Found latest activity file: {latest_file}")
        return latest_file
        
    except Exception as e:
        logger.error(f"Error finding latest activity file: {str(e)}")
        # Return fallback file path if it exists
        fallback_file = "attached_assets/ActivityDetail.csv"
        if os.path.exists(fallback_file):
            logger.info(f"Using fallback activity file: {fallback_file}")
            return fallback_file
        return None


def find_latest_driving_history_file():
    """Find the latest driving history file in the attached_assets directory"""
    driving_files = []
    
    try:
        # Check attached_assets directory for files
        assets_dir = Path("attached_assets")
        if not assets_dir.exists():
            logger.warning(f"Directory not found: {assets_dir}")
            return None
        
        # Look for DrivingHistory files with fault tolerance
        for file in assets_dir.glob("DrivingHistory*.csv"):
            # Validate file exists and is readable
            if os.path.isfile(file) and os.access(file, os.R_OK):
                driving_files.append(str(file))
            else:
                logger.warning(f"File exists but not readable: {file}")
        
        if not driving_files:
            logger.warning("No DrivingHistory files found")
            return None
        
        # Return the latest file based on modification time
        latest_file = max(driving_files, key=os.path.getmtime)
        logger.info(f"Found latest driving history file: {latest_file}")
        return latest_file
        
    except Exception as e:
        logger.error(f"Error finding latest driving history file: {str(e)}")
        # Return fallback file path if it exists
        fallback_file = "attached_assets/DrivingHistory.csv"
        if os.path.exists(fallback_file):
            logger.info(f"Using fallback driving history file: {fallback_file}")
            return fallback_file
        return None


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


# Import timezone normalizer
from utils.timezone_normalizer import normalize_time_string

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
    
    # Use timezone normalizer to standardize time handling
    normalized_time, is_next_day = normalize_time_string(time_str)
    
    # Add next-day indicator if detected
    if normalized_time and is_next_day:
        normalized_time += " (+1)"
        logger.info(f"Detected next-day time: {time_str} -> {normalized_time}")
    
    return normalized_time


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
        
        # First, find the actual header row
        with open(file_path, 'r') as f:
            header_row = None
            for i, line in enumerate(f):
                if 'AssetLabel' in line or 'EventDateTime' in line:
                    header_row = i
                    break
        
        if header_row is None:
            logger.error(f"Could not find header row in activity detail file: {file_path}")
            return []
        
        # Read the CSV file with the correct header row
        logger.info(f"Reading activity detail file: {file_path}")
        df = pd.read_csv(file_path, skiprows=header_row)
        
        # Log the columns we found
        logger.info(f"Found columns in activity detail file: {', '.join(df.columns)}")
        
        # Convert to records
        records = []
        current_asset = None
        current_driver = None
        
        for _, row in df.iterrows():
            # Get asset label which contains driver info
            asset_label = row.get('AssetLabel', '')
            if pd.notna(asset_label) and asset_label:
                current_asset = asset_label
                # Try to extract driver name from asset label
                if ' - ' in asset_label and '+' in asset_label:
                    parts = asset_label.split(' - ', 1)
                    if len(parts) > 1:
                        driver_part = parts[1].split('+')[0].strip()
                        # Assume the first two words are the driver's first and last name
                        name_parts = driver_part.split()
                        if len(name_parts) >= 2:
                            current_driver = f"{name_parts[0]} {name_parts[1]}"
            
            # Skip rows without event data
            event_time = row.get('EventDateTimex', '')
            if not pd.notna(event_time) or not event_time:
                continue
                
            # Get event reason and location
            reason = row.get('Reasonx', '')
            location = row.get('Locationx', '')
            
            # Skip if no location or reason
            if not pd.notna(location) or not location or not pd.notna(reason) or not reason:
                continue
                
            # Only process relevant events
            if not (pd.notna(reason) and reason in ['Key On', 'Key Off', 'Heartbeat', 'Idle Ended', 'Idling']):
                continue
                
            # Skip rows without a driver
            if not current_driver:
                continue
            
            # Create record
            record = {
                'driver_name': current_driver,
                'asset_id': current_asset,
                'job_site': location,
                'actual_start': normalize_time(event_time) if reason in ['Key On', 'Heartbeat'] else None,
                'actual_end': normalize_time(event_time) if reason == 'Key Off' else None,
                'data_source': 'activity_detail'
            }
            
            # Only add records with at least one time value
            if record['actual_start'] or record['actual_end']:
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
        
        # Read the CSV file with custom format handling
        logger.info(f"Reading driving history file: {file_path}")
        
        # First, try to determine the actual header row
        with open(file_path, 'r') as f:
            header_row = None
            for i, line in enumerate(f):
                if 'Textbox53' in line or 'Contact' in line or 'EventDateTime' in line:
                    header_row = i
                    break
        
        if header_row is None:
            logger.error(f"Could not find header row in driving history file: {file_path}")
            return []
        
        # Now read the file with the correct header row
        df = pd.read_csv(file_path, skiprows=header_row)
        
        # Log the columns we found
        logger.info(f"Found columns in driving history file: {', '.join(df.columns)}")
        
        # Process the data
        records = []
        current_vehicle = None
        current_driver = None
        
        for _, row in df.iterrows():
            # Check if this is a vehicle/driver header row
            if pd.notna(row.get('Textbox53')) and isinstance(row.get('Textbox53'), str) and '+' in row.get('Textbox53'):
                current_vehicle = row.get('Textbox53', '').strip()
                # Try to extract driver name from vehicle
                if ' - ' in current_vehicle:
                    driver_part = current_vehicle.split(' - ', 1)[1]
                    if ' ' in driver_part:
                        # Assumes format like "#210073 - BIKHYAT ADHIKARI TOYOTA 4 RUNNER 2022 Personal Vehicle +"
                        name_parts = driver_part.split(' ')
                        if len(name_parts) >= 2:
                            current_driver = f"{name_parts[0]} {name_parts[1]}"
                continue
            
            # Get contact info which contains driver name
            contact = row.get('Contact', '')
            if pd.notna(contact) and contact:
                # Extract driver name from contact format "Ammar Elhamad (210003)"
                if '(' in contact:
                    current_driver = contact.split('(')[0].strip()
            
            # Skip rows without event data
            event_time = row.get('EventDateTime', '')
            if not pd.notna(event_time) or not event_time:
                continue
                
            msg_type = row.get('MsgType', '')
            location = row.get('Location', '')
            
            # Only process key events
            if not (pd.notna(msg_type) and msg_type in ['Key On', 'Key Off', 'Arrived', 'Departed']):
                continue
                
            # Skip rows without driver or location
            if not current_driver or not location:
                continue
            
            # Create a record based on event type
            if msg_type == 'Key On' or msg_type == 'Arrived':
                record = {
                    'driver_name': current_driver,
                    'asset_id': current_vehicle if current_vehicle else '',
                    'job_site': location,
                    'actual_start': normalize_time(event_time),
                    'data_source': 'driving_history'
                }
                records.append(record)
                
            elif msg_type == 'Key Off' or msg_type == 'Departed':
                record = {
                    'driver_name': current_driver,
                    'asset_id': current_vehicle if current_vehicle else '',
                    'job_site': location,
                    'actual_end': normalize_time(event_time),
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
    
    # Import timezone calculation utility
    from utils.timezone_normalizer import calculate_time_difference_minutes
    
    # Calculate lateness and early departure
    for driver_name, record in merged_records.items():
        # Default scheduled start if not available
        if not record.get('scheduled_start'):
            record['scheduled_start'] = DEFAULT_START_TIME
        
        # Calculate lateness
        if record.get('scheduled_start') and record.get('actual_start'):
            try:
                # Use the timezone utility to calculate the difference
                minutes_late = calculate_time_difference_minutes(
                    record['scheduled_start'], 
                    record['actual_start']
                )
                
                # Only positive values (late arrivals)
                if minutes_late and minutes_late > 0:
                    record['late_minutes'] = minutes_late
                    logger.info(f"Driver {driver_name} is {minutes_late} minutes late: "
                               f"scheduled {record['scheduled_start']}, actual {record['actual_start']}")
            except Exception as e:
                logger.warning(f"Could not calculate lateness for driver {driver_name}: {e}")
        
        # Calculate early departure
        if record.get('scheduled_end') and record.get('actual_end'):
            try:
                # Use the timezone utility to calculate the difference
                minutes_early = calculate_time_difference_minutes(
                    record['actual_end'], 
                    record['scheduled_end']
                )
                
                # Only positive values (early departures)
                if minutes_early and minutes_early > 0:
                    record['early_minutes'] = minutes_early
                    logger.info(f"Driver {driver_name} left {minutes_early} minutes early: "
                               f"scheduled {record['scheduled_end']}, actual {record['actual_end']}")
            except Exception as e:
                logger.warning(f"Could not calculate early departure for driver {driver_name}: {e}")
    
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