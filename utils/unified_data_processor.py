"""
Unified Data Processor

This module handles direct parsing of raw source files including DrivingHistory, ActivityDetail, 
and Start Time & Job sheets to generate accurate driver status reports.
"""

import os
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import traceback
import json

# Set up logging
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('logs/unified_data_processor.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

# Constants for status determination
LATE_THRESHOLD_MINUTES = 15
EARLY_END_THRESHOLD_MINUTES = 30

def find_source_files(date_str=None):
    """
    Find all relevant source files for processing
    
    Args:
        date_str (str): Optional date filter in YYYY-MM-DD format
        
    Returns:
        dict: Dictionary of source files by category
    """
    source_files = {
        'driving_history': [],
        'activity_detail': [],
        'assets_time_on_site': [],
        'start_time_job': []
    }
    
    # Search directories
    search_dirs = ['data', 'attached_assets']
    
    for directory in search_dirs:
        if not os.path.exists(directory):
            continue
            
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            
            if not os.path.isfile(file_path):
                continue
                
            file_lower = file.lower()
            
            # Categorize file based on name pattern
            if 'driving' in file_lower and ('history' in file_lower or 'gps' in file_lower):
                source_files['driving_history'].append(file_path)
                
            elif 'activity' in file_lower and 'detail' in file_lower:
                source_files['activity_detail'].append(file_path)
                
            elif ('assets' in file_lower and 'time' in file_lower and 'site' in file_lower) or \
                 ('fleet' in file_lower and 'utilization' in file_lower):
                source_files['assets_time_on_site'].append(file_path)
                
            elif ('start' in file_lower and ('time' in file_lower or 'job' in file_lower)) or \
                 ('schedule' in file_lower) or \
                 ('baseline' in file_lower):
                source_files['start_time_job'].append(file_path)
    
    # If date filter provided, try to filter files containing that date
    if date_str:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        date_patterns = [
            date_str,
            date_obj.strftime('%m-%d-%Y'),
            date_obj.strftime('%m/%d/%Y'),
            date_obj.strftime('%Y%m%d')
        ]
        
        for category in source_files:
            date_filtered_files = []
            for file_path in source_files[category]:
                # Check if file contains date in name
                if any(pattern in file_path for pattern in date_patterns):
                    date_filtered_files.append(file_path)
            
            # If we found date-specific files, replace the list
            if date_filtered_files:
                source_files[category] = date_filtered_files
    
    return source_files

def read_file_with_multiple_encodings(file_path):
    """
    Attempt to read a file with multiple encodings
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        pandas.DataFrame or None: Dataframe if successful, None if all attempts fail
    """
    # Determine file type
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension in ['.xlsx', '.xls']:
        try:
            return pd.read_excel(file_path)
        except Exception as e:
            logger.error(f"Error reading Excel file {file_path}: {e}")
            return None
    
    # Try different encodings for CSV files
    encodings = ['utf-8', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except Exception as e:
            logger.warning(f"Failed to read with {encoding} encoding: {e}")
    
    logger.error(f"Could not read file with any encoding: {file_path}")
    return None

def process_driving_history(file_path, date_str):
    """
    Process driving history data to extract key on/off events
    
    Args:
        file_path (str): Path to driving history file
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        dict: Processed driving data by driver or asset ID
    """
    logger.info(f"Processing driving history file: {file_path}")
    
    # Read file
    df = read_file_with_multiple_encodings(file_path)
    
    if df is None:
        return {}
    
    # Standardize column names
    df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
    
    # Look for essential columns
    expected_columns = [
        # Different possible column names for driver
        ['driver', 'driver_name', 'drivername', 'operator', 'operator_name'],
        # Different possible column names for asset
        ['asset', 'asset_id', 'assetid', 'vehicle', 'vehicle_id', 'equipment'],
        # Different possible column names for timestamp
        ['timestamp', 'time', 'date_time', 'datetime', 'event_time', 'time_stamp'],
        # Different possible column names for event type
        ['event', 'event_type', 'eventtype', 'action', 'status']
    ]
    
    # Find actual column names in the file
    column_mapping = {}
    for category, possible_names in enumerate(expected_columns):
        found = False
        for name in possible_names:
            if name in df.columns:
                if category == 0:
                    column_mapping['driver'] = name
                elif category == 1:
                    column_mapping['asset'] = name
                elif category == 2:
                    column_mapping['timestamp'] = name
                elif category == 3:
                    column_mapping['event'] = name
                found = True
                break
        
        if not found:
            # If we couldn't find a critical column, try to identify it by position or type
            if category == 0:  # Driver
                for col in df.columns:
                    if 'name' in col or df[col].astype(str).str.contains('driver', case=False).any():
                        column_mapping['driver'] = col
                        break
            elif category == 1:  # Asset
                for col in df.columns:
                    if df[col].astype(str).str.contains('-', case=False).any() and df[col].astype(str).str.len().mean() < 10:
                        column_mapping['asset'] = col
                        break
            elif category == 2:  # Timestamp
                for col in df.columns:
                    if pd.api.types.is_datetime64_any_dtype(df[col]) or (
                        isinstance(df[col].iloc[0], str) and 
                        (':' in df[col].iloc[0] or '/' in df[col].iloc[0])
                    ):
                        column_mapping['timestamp'] = col
                        break
    
    # If we couldn't map all necessary columns, log and return
    if not all(key in column_mapping for key in ['driver', 'asset', 'timestamp']):
        missing = [key for key in ['driver', 'asset', 'timestamp'] if key not in column_mapping]
        logger.error(f"Could not identify essential columns in {file_path}: {missing}")
        return {}
    
    # Now that we have identified columns, process the data
    driver_data = {}
    
    # Convert timestamp to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(df[column_mapping['timestamp']]):
        # Try multiple formats
        timestamp_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y %I:%M:%S %p',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %I:%M:%S %p'
        ]
        
        converted = False
        for fmt in timestamp_formats:
            try:
                df[column_mapping['timestamp']] = pd.to_datetime(df[column_mapping['timestamp']], format=fmt)
                converted = True
                break
            except:
                continue
        
        if not converted:
            try:
                df[column_mapping['timestamp']] = pd.to_datetime(df[column_mapping['timestamp']])
            except Exception as e:
                logger.error(f"Could not convert timestamp column: {e}")
                return {}
    
    # Filter by date if specified
    if date_str:
        date_obj = pd.to_datetime(date_str)
        date_min = date_obj.normalize()  # Start of day
        date_max = date_min + timedelta(days=1)  # Start of next day
        
        # Filter dataframe to the specific date
        df = df[(df[column_mapping['timestamp']] >= date_min) & 
                (df[column_mapping['timestamp']] < date_max)]
        
        if len(df) == 0:
            logger.warning(f"No records found for {date_str} in {file_path}")
            return {}
    
    # Check if we have event type column
    has_event_column = 'event' in column_mapping
    
    # Group by driver or asset and extract first/last activity
    groupby_column = column_mapping['driver'] if 'driver' in column_mapping else column_mapping['asset']
    
    for name, group in df.groupby(groupby_column):
        # Skip empty names
        if pd.isna(name) or str(name).strip() == '':
            continue
            
        # Sort by timestamp
        group = group.sort_values(column_mapping['timestamp'])
        
        # Get asset ID if we're grouping by driver
        asset_id = group[column_mapping['asset']].iloc[0] if 'asset' in column_mapping else 'Unknown'
        
        # Determine key on/off events if we have that column
        first_activity = group[column_mapping['timestamp']].min()
        last_activity = group[column_mapping['timestamp']].max()
        
        key_on_time = first_activity
        key_off_time = last_activity
        
        if has_event_column:
            # Look for key on/off events
            key_on_events = group[
                group[column_mapping['event']].str.lower().str.contains('key on|keyon|start|ignition on', na=False)
            ]
            
            key_off_events = group[
                group[column_mapping['event']].str.lower().str.contains('key off|keyoff|stop|ignition off', na=False)
            ]
            
            if len(key_on_events) > 0:
                key_on_time = key_on_events[column_mapping['timestamp']].min()
            
            if len(key_off_events) > 0:
                key_off_time = key_off_events[column_mapping['timestamp']].max()
        
        # Extract location data if available
        location = "Unknown"
        location_columns = ['address', 'location', 'site', 'job_site', 'city', 'state']
        
        for loc_col in location_columns:
            if loc_col in df.columns and not group[loc_col].isna().all():
                location = group[loc_col].iloc[0]
                break
        
        # Store processed data
        driver_name = name if groupby_column == column_mapping['driver'] else "Unknown"
        driver_key = str(name).strip()
        
        if driver_key not in driver_data:
            driver_data[driver_key] = {
                'driver_name': driver_name,
                'asset_id': asset_id,
                'first_activity': first_activity,
                'last_activity': last_activity,
                'key_on_time': key_on_time,
                'key_off_time': key_off_time,
                'location': location,
                'activity_count': len(group)
            }
    
    logger.info(f"Found {len(driver_data)} driver records for {date_str}")
    return driver_data

def process_activity_detail(file_path, date_str):
    """
    Process activity detail data to extract additional driver activity information
    
    Args:
        file_path (str): Path to activity detail file
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        dict: Processed activity data by driver or asset ID
    """
    logger.info(f"Processing activity detail file: {file_path}")
    
    # Read file
    df = read_file_with_multiple_encodings(file_path)
    
    if df is None:
        return {}
    
    # Standardize column names
    df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
    
    # Look for essential columns
    expected_columns = [
        # Different possible column names for driver
        ['driver', 'driver_name', 'drivername', 'operator', 'operator_name'],
        # Different possible column names for asset
        ['asset', 'asset_id', 'assetid', 'vehicle', 'vehicle_id', 'equipment'],
        # Different possible column names for start time
        ['start_time', 'starttime', 'time_start', 'begin_time', 'from'],
        # Different possible column names for end time
        ['end_time', 'endtime', 'time_end', 'stop_time', 'to']
    ]
    
    # Find actual column names in the file
    column_mapping = {}
    for category, possible_names in enumerate(expected_columns):
        found = False
        for name in possible_names:
            if name in df.columns:
                if category == 0:
                    column_mapping['driver'] = name
                elif category == 1:
                    column_mapping['asset'] = name
                elif category == 2:
                    column_mapping['start_time'] = name
                elif category == 3:
                    column_mapping['end_time'] = name
                found = True
                break
        
        if not found:
            # Try to infer column based on content
            if category == 0:  # Driver
                for col in df.columns:
                    if 'name' in col or df[col].astype(str).str.contains('driver', case=False).any():
                        column_mapping['driver'] = col
                        break
            elif category == 1:  # Asset
                for col in df.columns:
                    if df[col].astype(str).str.contains('-', case=False).any() and df[col].astype(str).str.len().mean() < 10:
                        column_mapping['asset'] = col
                        break
    
    # If we couldn't map all necessary columns, log and return
    required_columns = ['driver', 'asset', 'start_time']
    if not all(key in column_mapping for key in required_columns):
        missing = [key for key in required_columns if key not in column_mapping]
        logger.error(f"Could not identify essential columns in {file_path}: {missing}")
        return {}
    
    # Convert time columns to datetime if needed
    for time_col in ['start_time', 'end_time']:
        if time_col in column_mapping and not pd.api.types.is_datetime64_any_dtype(df[column_mapping[time_col]]):
            try:
                df[column_mapping[time_col]] = pd.to_datetime(df[column_mapping[time_col]])
            except:
                # Try multiple formats
                timestamp_formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%m/%d/%Y %H:%M:%S',
                    '%m/%d/%Y %I:%M:%S %p',
                    '%Y-%m-%dT%H:%M:%S',
                    '%I:%M:%S %p'
                ]
                
                for fmt in timestamp_formats:
                    try:
                        df[column_mapping[time_col]] = pd.to_datetime(df[column_mapping[time_col]], format=fmt)
                        break
                    except:
                        continue
    
    # Filter by date if specified
    if date_str:
        date_obj = pd.to_datetime(date_str)
        
        # Try to filter by start time if it's a datetime
        if pd.api.types.is_datetime64_any_dtype(df[column_mapping['start_time']]):
            date_min = date_obj.normalize()  # Start of day
            date_max = date_min + timedelta(days=1)  # Start of next day
            
            df = df[(df[column_mapping['start_time']] >= date_min) & 
                    (df[column_mapping['start_time']] < date_max)]
        
        if len(df) == 0:
            logger.warning(f"No records found for {date_str} in {file_path}")
            return {}
    
    # Process activity data
    activity_data = {}
    
    # Group by driver or asset
    groupby_column = column_mapping['driver'] if 'driver' in column_mapping else column_mapping['asset']
    
    for name, group in df.groupby(groupby_column):
        # Skip empty names
        if pd.isna(name) or str(name).strip() == '':
            continue
            
        # Sort by start time
        if 'start_time' in column_mapping:
            group = group.sort_values(column_mapping['start_time'])
        
        # Get asset ID if we're grouping by driver
        asset_id = group[column_mapping['asset']].iloc[0] if 'asset' in column_mapping else 'Unknown'
        
        # Calculate first and last activity times
        first_activity = group[column_mapping['start_time']].min() if 'start_time' in column_mapping else None
        last_activity = None
        
        if 'end_time' in column_mapping:
            last_activity = group[column_mapping['end_time']].max()
        
        # Extract job site/location if available
        location = "Unknown"
        location_columns = ['job_site', 'jobsite', 'site', 'location', 'address', 'city', 'project']
        
        for loc_col in location_columns:
            if loc_col in df.columns and not group[loc_col].isna().all():
                location = group[loc_col].iloc[0]
                break
        
        # Store processed data
        driver_name = name if groupby_column == column_mapping['driver'] else "Unknown"
        driver_key = str(name).strip()
        
        if driver_key not in activity_data:
            activity_data[driver_key] = {
                'driver_name': driver_name,
                'asset_id': asset_id,
                'first_activity': first_activity,
                'last_activity': last_activity,
                'location': location,
                'activity_count': len(group)
            }
    
    logger.info(f"Found {len(activity_data)} activity detail records for {date_str}")
    return activity_data

def process_assets_time_on_site(file_path, date_str):
    """
    Process assets time on site data to validate job site presence
    
    Args:
        file_path (str): Path to assets time on site file
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        dict: Processed onsite data by asset ID
    """
    logger.info(f"Processing assets time on site file: {file_path}")
    
    # Read file
    df = read_file_with_multiple_encodings(file_path)
    
    if df is None:
        return {}
    
    # Standardize column names
    df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
    
    # Look for essential columns
    expected_columns = [
        # Different possible column names for asset
        ['asset', 'asset_id', 'assetid', 'vehicle', 'vehicle_id', 'equipment'],
        # Different possible column names for site
        ['site', 'job_site', 'jobsite', 'location', 'project'],
        # Different possible column names for time in
        ['time_in', 'timein', 'arrival', 'arrival_time', 'start'],
        # Different possible column names for time out
        ['time_out', 'timeout', 'departure', 'departure_time', 'end']
    ]
    
    # Find actual column names in the file
    column_mapping = {}
    for category, possible_names in enumerate(expected_columns):
        found = False
        for name in possible_names:
            if name in df.columns:
                if category == 0:
                    column_mapping['asset'] = name
                elif category == 1:
                    column_mapping['site'] = name
                elif category == 2:
                    column_mapping['time_in'] = name
                elif category == 3:
                    column_mapping['time_out'] = name
                found = True
                break
    
    # If we couldn't map all necessary columns, log and return
    required_columns = ['asset', 'site', 'time_in']
    if not all(key in column_mapping for key in required_columns):
        missing = [key for key in required_columns if key not in column_mapping]
        logger.error(f"Could not identify essential columns in {file_path}: {missing}")
        return {}
    
    # Convert time columns to datetime if needed
    for time_col in ['time_in', 'time_out']:
        if time_col in column_mapping and not pd.api.types.is_datetime64_any_dtype(df[column_mapping[time_col]]):
            try:
                df[column_mapping[time_col]] = pd.to_datetime(df[column_mapping[time_col]])
            except:
                # Try multiple formats
                timestamp_formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%m/%d/%Y %H:%M:%S',
                    '%m/%d/%Y %I:%M:%S %p',
                    '%Y-%m-%dT%H:%M:%S',
                    '%I:%M:%S %p'
                ]
                
                for fmt in timestamp_formats:
                    try:
                        df[column_mapping[time_col]] = pd.to_datetime(df[column_mapping[time_col]], format=fmt)
                        break
                    except:
                        continue
    
    # Filter by date if specified
    if date_str:
        date_obj = pd.to_datetime(date_str)
        
        # Try to filter by time in if it's a datetime
        if pd.api.types.is_datetime64_any_dtype(df[column_mapping['time_in']]):
            date_min = date_obj.normalize()  # Start of day
            date_max = date_min + timedelta(days=1)  # Start of next day
            
            df = df[(df[column_mapping['time_in']] >= date_min) & 
                    (df[column_mapping['time_in']] < date_max)]
            
            if len(df) == 0:
                logger.warning(f"No records found for {date_str} in {file_path}")
                return {}
    
    # Process onsite data
    onsite_data = {}
    
    # Group by asset ID
    for asset_id, group in df.groupby(column_mapping['asset']):
        # Skip empty asset IDs
        if pd.isna(asset_id) or str(asset_id).strip() == '':
            continue
            
        # Calculate total time on site for each job site
        for site, site_group in group.groupby(column_mapping['site']):
            # Skip empty sites
            if pd.isna(site) or str(site).strip() == '':
                continue
                
            # Get time in and time out
            time_in = site_group[column_mapping['time_in']].min()
            
            if 'time_out' in column_mapping:
                time_out = site_group[column_mapping['time_out']].max()
            else:
                time_out = None
            
            # Generate a key for this asset
            asset_key = str(asset_id).strip()
            
            if asset_key not in onsite_data:
                onsite_data[asset_key] = []
            
            # Add site record
            onsite_data[asset_key].append({
                'site': site,
                'time_in': time_in,
                'time_out': time_out,
                'total_minutes': (time_out - time_in).total_seconds() / 60 if time_out is not None else None
            })
    
    logger.info(f"Found {len(onsite_data)} asset onsite records for {date_str}")
    return onsite_data

def process_start_time_job(file_path):
    """
    Process start time and job data to get scheduled times and job sites
    
    Args:
        file_path (str): Path to start time and job file
        
    Returns:
        dict: Processed schedule data by driver ID
    """
    logger.info(f"Processing start time and job file: {file_path}")
    
    # Read file
    df = read_file_with_multiple_encodings(file_path)
    
    if df is None:
        return {}
    
    # Standardize column names
    df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
    
    # Look for essential columns
    expected_columns = [
        # Different possible column names for driver
        ['driver', 'driver_name', 'drivername', 'employee', 'employee_name', 'name'],
        # Different possible column names for asset
        ['asset', 'asset_id', 'assetid', 'vehicle', 'vehicle_id', 'equipment'],
        # Different possible column names for start time
        ['start_time', 'starttime', 'scheduled_start', 'job_start', 'shift_start'],
        # Different possible column names for end time
        ['end_time', 'endtime', 'scheduled_end', 'job_end', 'shift_end'],
        # Different possible column names for job site
        ['job_site', 'jobsite', 'site', 'location', 'project', 'job', 'assignment']
    ]
    
    # Find actual column names in the file
    column_mapping = {}
    for category, possible_names in enumerate(expected_columns):
        found = False
        for name in possible_names:
            if name in df.columns:
                if category == 0:
                    column_mapping['driver'] = name
                elif category == 1:
                    column_mapping['asset'] = name
                elif category == 2:
                    column_mapping['start_time'] = name
                elif category == 3:
                    column_mapping['end_time'] = name
                elif category == 4:
                    column_mapping['job_site'] = name
                found = True
                break
    
    # If we couldn't map driver column, log and return
    if 'driver' not in column_mapping:
        logger.error(f"Could not identify driver column in {file_path}")
        return {}
    
    # Process schedule data
    schedule_data = {}
    
    # Process each row
    for _, row in df.iterrows():
        driver_name = row[column_mapping['driver']]
        
        # Skip empty driver names
        if pd.isna(driver_name) or str(driver_name).strip() == '':
            continue
        
        # Get asset ID if available
        asset_id = row[column_mapping['asset']] if 'asset' in column_mapping else None
        
        # Get start and end times
        start_time = None
        end_time = None
        
        if 'start_time' in column_mapping:
            start_time = row[column_mapping['start_time']]
            
            # Convert to string time format if it's a datetime
            if pd.api.types.is_datetime64_any_dtype(start_time) or isinstance(start_time, (pd.Timestamp, datetime)):
                start_time = start_time.strftime('%I:%M %p')
            elif isinstance(start_time, (int, float)):
                # Handle Excel time format (fraction of day)
                if 0 <= start_time < 1:
                    hours = int(start_time * 24)
                    minutes = int((start_time * 24 - hours) * 60)
                    am_pm = 'AM' if hours < 12 else 'PM'
                    hours = hours % 12
                    if hours == 0:
                        hours = 12
                    start_time = f"{hours:02d}:{minutes:02d} {am_pm}"
        
        if 'end_time' in column_mapping:
            end_time = row[column_mapping['end_time']]
            
            # Convert to string time format if it's a datetime
            if pd.api.types.is_datetime64_any_dtype(end_time) or isinstance(end_time, (pd.Timestamp, datetime)):
                end_time = end_time.strftime('%I:%M %p')
            elif isinstance(end_time, (int, float)):
                # Handle Excel time format (fraction of day)
                if 0 <= end_time < 1:
                    hours = int(end_time * 24)
                    minutes = int((end_time * 24 - hours) * 60)
                    am_pm = 'AM' if hours < 12 else 'PM'
                    hours = hours % 12
                    if hours == 0:
                        hours = 12
                    end_time = f"{hours:02d}:{minutes:02d} {am_pm}"
        
        # Default start/end times if not specified
        if not start_time:
            start_time = "06:00 AM"
        
        if not end_time:
            end_time = "03:30 PM"
        
        # Get job site
        job_site = row[column_mapping['job_site']] if 'job_site' in column_mapping else None
        
        # Store in schedule data
        driver_key = str(driver_name).strip()
        
        schedule_data[driver_key] = {
            'driver_name': driver_name,
            'asset_id': asset_id,
            'scheduled_start': start_time,
            'scheduled_end': end_time,
            'job_site': job_site
        }
    
    logger.info(f"Found {len(schedule_data)} schedule records")
    return schedule_data

def determine_driver_status(driver_name, scheduled_data, actual_data, onsite_data):
    """
    Determine the status of a driver based on scheduled and actual data
    
    Args:
        driver_name (str): Driver name or ID
        scheduled_data (dict): Scheduled time and job site
        actual_data (dict): Actual activity data
        onsite_data (dict): Asset onsite data
        
    Returns:
        dict: Driver status information
    """
    # Start with scheduled data as the base
    status_info = {
        'driver_name': driver_name,
        'scheduled_start': scheduled_data.get('scheduled_start', '06:00 AM'),
        'scheduled_end': scheduled_data.get('scheduled_end', '03:30 PM'),
        'assigned_job_site': scheduled_data.get('job_site', 'Unknown'),
        'asset_id': scheduled_data.get('asset_id', 'Unknown'),
        'status': 'Not On Job',  # Default status
        'status_reason': 'No activity data'
    }
    
    # If no actual data, return now with Not On Job status
    if not actual_data:
        return status_info
    
    # Update with actual data
    status_info.update({
        'asset_id': actual_data.get('asset_id', status_info['asset_id']),
        'actual_start': actual_data.get('first_activity'),
        'actual_end': actual_data.get('last_activity'),
        'key_on_time': actual_data.get('key_on_time'),
        'key_off_time': actual_data.get('key_off_time'),
        'location': actual_data.get('location', 'Unknown')
    })
    
    # Convert scheduled times to datetime for comparison
    try:
        scheduled_start_time = datetime.strptime(status_info['scheduled_start'], '%I:%M %p').time()
    except:
        try:
            scheduled_start_time = datetime.strptime(status_info['scheduled_start'], '%H:%M').time()
        except:
            scheduled_start_time = datetime.strptime('06:00 AM', '%I:%M %p').time()
    
    try:
        scheduled_end_time = datetime.strptime(status_info['scheduled_end'], '%I:%M %p').time()
    except:
        try:
            scheduled_end_time = datetime.strptime(status_info['scheduled_end'], '%H:%M').time()
        except:
            scheduled_end_time = datetime.strptime('03:30 PM', '%I:%M %p').time()
    
    # Format actual times for display
    if status_info.get('actual_start'):
        if isinstance(status_info['actual_start'], (datetime, pd.Timestamp)):
            status_info['actual_start_display'] = status_info['actual_start'].strftime('%I:%M %p')
        else:
            status_info['actual_start_display'] = str(status_info['actual_start'])
    else:
        status_info['actual_start_display'] = "N/A"
        
    if status_info.get('actual_end'):
        if isinstance(status_info['actual_end'], (datetime, pd.Timestamp)):
            status_info['actual_end_display'] = status_info['actual_end'].strftime('%I:%M %p')
        else:
            status_info['actual_end_display'] = str(status_info['actual_end'])
    else:
        status_info['actual_end_display'] = "N/A"
    
    # Check if driver is at the correct job site
    correct_job_site = True
    
    # First check the location from telematics
    if status_info['location'] != 'Unknown' and status_info['assigned_job_site'] != 'Unknown':
        # Simple string matching for now - could be enhanced with fuzzy matching
        if status_info['assigned_job_site'] not in status_info['location'] and status_info['location'] not in status_info['assigned_job_site']:
            correct_job_site = False
            status_info['status'] = 'Not On Job'
            status_info['status_reason'] = f"At incorrect location: {status_info['location']}"
    
    # If job site seems wrong, check the onsite data for confirmation
    if not correct_job_site and status_info['asset_id'] in onsite_data:
        # Check if asset was detected at correct job site
        for site_record in onsite_data[status_info['asset_id']]:
            if status_info['assigned_job_site'] in site_record['site'] or site_record['site'] in status_info['assigned_job_site']:
                correct_job_site = True
                break
    
    # If job site is correct, check arrival and departure times
    if correct_job_site and status_info.get('actual_start') is not None:
        actual_start_time = status_info['actual_start'].time() if isinstance(status_info['actual_start'], (datetime, pd.Timestamp)) else None
        actual_end_time = status_info['actual_end'].time() if isinstance(status_info['actual_end'], (datetime, pd.Timestamp)) else None
        
        if actual_start_time:
            # Calculate minutes late
            scheduled_minutes = scheduled_start_time.hour * 60 + scheduled_start_time.minute
            actual_minutes = actual_start_time.hour * 60 + actual_start_time.minute
            
            minutes_late = actual_minutes - scheduled_minutes
            status_info['minutes_late'] = minutes_late if minutes_late > 0 else 0
            
            # Check if late
            if minutes_late > LATE_THRESHOLD_MINUTES:
                status_info['status'] = 'Late'
                status_info['status_reason'] = f"{minutes_late} minutes late"
                return status_info
        
        if actual_end_time:
            # Calculate minutes early
            scheduled_minutes = scheduled_end_time.hour * 60 + scheduled_end_time.minute
            actual_minutes = actual_end_time.hour * 60 + actual_end_time.minute
            
            minutes_early = scheduled_minutes - actual_minutes
            status_info['minutes_early'] = minutes_early if minutes_early > 0 else 0
            
            # Check if early end
            if minutes_early > EARLY_END_THRESHOLD_MINUTES:
                # Only mark as early end if not already marked as late
                if status_info['status'] != 'Late':
                    status_info['status'] = 'Early End'
                    status_info['status_reason'] = f"{minutes_early} minutes early"
                return status_info
        
        # If we got here, driver is on time
        if status_info['status'] == 'Not On Job':
            status_info['status'] = 'On Time'
            status_info['status_reason'] = None
    
    return status_info

def generate_daily_driver_report(date_str):
    """
    Generate a comprehensive daily driver report for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        dict: Complete driver report
    """
    logger.info(f"Generating daily driver report for {date_str}")
    
    try:
        # Find all relevant source files
        source_files = find_source_files(date_str)
        
        # Initialize data containers
        driving_data = {}
        activity_data = {}
        onsite_data = {}
        schedule_data = {}
        
        # Process driving history files
        for file_path in source_files['driving_history']:
            driving_results = process_driving_history(file_path, date_str)
            
            # Merge with existing data
            for driver_key, data in driving_results.items():
                if driver_key not in driving_data:
                    driving_data[driver_key] = data
                else:
                    # Keep earliest first activity and latest last activity
                    if data.get('first_activity') and (
                        not driving_data[driver_key].get('first_activity') or
                        data['first_activity'] < driving_data[driver_key]['first_activity']
                    ):
                        driving_data[driver_key]['first_activity'] = data['first_activity']
                    
                    if data.get('last_activity') and (
                        not driving_data[driver_key].get('last_activity') or
                        data['last_activity'] > driving_data[driver_key]['last_activity']
                    ):
                        driving_data[driver_key]['last_activity'] = data['last_activity']
                    
                    # Update other fields as needed
                    for field in ['key_on_time', 'key_off_time', 'location']:
                        if field in data and data[field]:
                            driving_data[driver_key][field] = data[field]
                    
                    # Sum activity counts
                    driving_data[driver_key]['activity_count'] += data.get('activity_count', 0)
        
        # Process activity detail files
        for file_path in source_files['activity_detail']:
            activity_results = process_activity_detail(file_path, date_str)
            
            # Merge with existing data
            for driver_key, data in activity_results.items():
                if driver_key not in activity_data:
                    activity_data[driver_key] = data
                else:
                    # Keep earliest first activity and latest last activity
                    if data.get('first_activity') and (
                        not activity_data[driver_key].get('first_activity') or
                        data['first_activity'] < activity_data[driver_key]['first_activity']
                    ):
                        activity_data[driver_key]['first_activity'] = data['first_activity']
                    
                    if data.get('last_activity') and (
                        not activity_data[driver_key].get('last_activity') or
                        data['last_activity'] > activity_data[driver_key]['last_activity']
                    ):
                        activity_data[driver_key]['last_activity'] = data['last_activity']
                    
                    # Sum activity counts
                    activity_data[driver_key]['activity_count'] += data.get('activity_count', 0)
        
        # Process assets time on site files
        for file_path in source_files['assets_time_on_site']:
            onsite_results = process_assets_time_on_site(file_path, date_str)
            
            # Merge with existing data
            for asset_key, site_records in onsite_results.items():
                if asset_key not in onsite_data:
                    onsite_data[asset_key] = site_records
                else:
                    onsite_data[asset_key].extend(site_records)
        
        # Process start time and job files (static baseline)
        for file_path in source_files['start_time_job']:
            schedule_results = process_start_time_job(file_path)
            
            # Merge with existing data
            for driver_key, data in schedule_results.items():
                if driver_key not in schedule_data:
                    schedule_data[driver_key] = data
        
        # If we don't have any schedule data, report error
        if not schedule_data:
            logger.error(f"No schedule data found for {date_str}")
            return {
                'error': f"No schedule data found for {date_str}",
                'date': date_str,
                'drivers': [],
                'total_drivers': 0
            }
        
        # Combine driving and activity data
        combined_data = {}
        
        # First add all driving data
        for driver_key, data in driving_data.items():
            combined_data[driver_key] = data.copy()
        
        # Then merge activity data
        for driver_key, data in activity_data.items():
            if driver_key not in combined_data:
                combined_data[driver_key] = data.copy()
            else:
                # Keep earliest first activity and latest last activity
                if data.get('first_activity') and (
                    not combined_data[driver_key].get('first_activity') or
                    data['first_activity'] < combined_data[driver_key]['first_activity']
                ):
                    combined_data[driver_key]['first_activity'] = data['first_activity']
                
                if data.get('last_activity') and (
                    not combined_data[driver_key].get('last_activity') or
                    data['last_activity'] > combined_data[driver_key]['last_activity']
                ):
                    combined_data[driver_key]['last_activity'] = data['last_activity']
                
                # Sum activity counts
                combined_data[driver_key]['activity_count'] = (
                    combined_data[driver_key].get('activity_count', 0) + 
                    data.get('activity_count', 0)
                )
        
        # Determine status for each driver
        all_drivers = []
        late_drivers = []
        early_end_drivers = []
        not_on_job_drivers = []
        on_time_drivers = []
        
        # Start with scheduled drivers
        for driver_key, scheduled in schedule_data.items():
            # Get actual data if available
            actual_data = combined_data.get(driver_key, None)
            
            # Get onsite data for this driver's asset
            asset_id = actual_data.get('asset_id', scheduled.get('asset_id', None))
            driver_onsite_data = onsite_data.get(asset_id, {}) if asset_id else {}
            
            # Determine status
            status_info = determine_driver_status(
                driver_name=driver_key,
                scheduled_data=scheduled,
                actual_data=actual_data,
                onsite_data=driver_onsite_data
            )
            
            # Add to appropriate list based on status
            all_drivers.append(status_info)
            
            if status_info['status'] == 'Late':
                late_drivers.append(status_info)
            elif status_info['status'] == 'Early End':
                early_end_drivers.append(status_info)
            elif status_info['status'] == 'Not On Job':
                not_on_job_drivers.append(status_info)
            else:  # On Time
                on_time_drivers.append(status_info)
        
        # Compile all unscheduled drivers with activity
        for driver_key, actual_data in combined_data.items():
            if driver_key not in schedule_data:
                # This driver had activity but wasn't scheduled
                status_info = {
                    'driver_name': actual_data.get('driver_name', driver_key),
                    'asset_id': actual_data.get('asset_id', 'Unknown'),
                    'actual_start': actual_data.get('first_activity'),
                    'actual_end': actual_data.get('last_activity'),
                    'key_on_time': actual_data.get('key_on_time'),
                    'key_off_time': actual_data.get('key_off_time'),
                    'location': actual_data.get('location', 'Unknown'),
                    'status': 'Unscheduled',
                    'status_reason': 'Driver not on schedule'
                }
                
                # Format actual times for display
                if status_info.get('actual_start'):
                    if isinstance(status_info['actual_start'], (datetime, pd.Timestamp)):
                        status_info['actual_start_display'] = status_info['actual_start'].strftime('%I:%M %p')
                    else:
                        status_info['actual_start_display'] = str(status_info['actual_start'])
                else:
                    status_info['actual_start_display'] = "N/A"
                    
                if status_info.get('actual_end'):
                    if isinstance(status_info['actual_end'], (datetime, pd.Timestamp)):
                        status_info['actual_end_display'] = status_info['actual_end'].strftime('%I:%M %p')
                    else:
                        status_info['actual_end_display'] = str(status_info['actual_end'])
                else:
                    status_info['actual_end_display'] = "N/A"
                
                all_drivers.append(status_info)
                not_on_job_drivers.append(status_info)
        
        # Parse date for formatting
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Create summary report
        report = {
            'date': date_str,
            'formatted_date': formatted_date,
            'report_date': formatted_date,
            'all_drivers': all_drivers,
            'late_drivers': late_drivers,
            'early_end_drivers': early_end_drivers,
            'not_on_job_drivers': not_on_job_drivers,
            'summary': {
                'total_drivers': len(all_drivers),
                'on_time_drivers': len(on_time_drivers),
                'late_drivers': len(late_drivers),
                'early_end_drivers': len(early_end_drivers),
                'not_on_job_drivers': len(not_on_job_drivers)
            }
        }
        
        # Create export directory
        export_dir = os.path.join('exports', 'daily_reports')
        os.makedirs(export_dir, exist_ok=True)
        
        # Save report to JSON file
        report_path = os.path.join(export_dir, f"daily_report_{date_str}.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Generated daily driver report for {date_str}: {len(all_drivers)} drivers")
        return report
    
    except Exception as e:
        logger.error(f"Error generating daily driver report for {date_str}: {e}")
        logger.error(traceback.format_exc())
        return {
            'error': f"Error generating report: {str(e)}",
            'date': date_str,
            'drivers': [],
            'total_drivers': 0
        }