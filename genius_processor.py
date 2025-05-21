"""
TRAXORA Genius Processor

This module implements a robust, production-grade data processor for the Daily Driver Report
system with extensive validation, error handling, and data integrity checks.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
from pathlib import Path
import traceback
from typing import Dict, List, Tuple, Any, Optional, Set, Union

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Create genius processor log file
file_handler = logging.FileHandler('logs/genius_processor.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Import validation core for consistent standards
try:
    from validation_core import validate_source_files, validate_data_integrity, validate_output_files
except ImportError:
    logger.error("validation_core module not found. Please ensure it's available.")
    raise

# Constants for status determination
LATE_THRESHOLD_MINUTES = 15
EARLY_END_THRESHOLD_MINUTES = 30

class DataProcessingError(Exception):
    """Custom exception for data processing errors"""
    pass

def load_source_data(date_str: str) -> Dict[str, Any]:
    """
    Load and validate all source data for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        Dict[str, Any]: Dictionary containing all loaded and validated source data
    """
    logger.info(f"Loading source data for {date_str}")
    
    # Step 1: Validate source files using validation core
    source_files = validate_source_files(date_str)
    
    # Initialize result dictionary
    source_data = {
        'driving_history': {},
        'activity_detail': {},
        'assets_time_on_site': {},
        'start_time_job': {},
        'row_counts': {},
        'metadata': {
            'date': date_str,
            'processed_at': datetime.now().isoformat(),
            'source_files': {k: [os.path.basename(f) for f in v] for k, v in source_files.items()}
        }
    }
    
    # Step 2: Process driving history files
    for file_path in source_files.get('driving_history', []):
        try:
            logger.info(f"Processing driving history file: {file_path}")
            
            # Determine file type
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                logger.warning(f"Unsupported file type for driving history: {file_path}")
                continue
                
            # Save row count
            source_data['row_counts'][os.path.basename(file_path)] = len(df)
                
            # Standardize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Map standard columns
            column_mapping = {}
            for std_col, possible_cols in [
                ('driver', ['driver', 'driver_name', 'drivername', 'employee', 'employee_name', 'name']),
                ('asset', ['asset', 'asset_id', 'assetid', 'vehicle', 'vehicle_id', 'equipment']),
                ('datetime', ['datetime', 'date_time', 'time', 'timestamp', 'event_time']),
                ('event_type', ['event_type', 'eventtype', 'event', 'activity', 'status']),
                ('location', ['location', 'site', 'job_site', 'jobsite', 'position', 'gps'])
            ]:
                for col in possible_cols:
                    if col in df.columns:
                        column_mapping[std_col] = col
                        break
            
            # Verify essential columns are mapped
            if not all(col in column_mapping for col in ['driver', 'asset', 'datetime', 'event_type']):
                missing = [col for col in ['driver', 'asset', 'datetime', 'event_type'] if col not in column_mapping]
                logger.error(f"Missing essential columns in driving history file {file_path}: {missing}")
                continue
            
            # Extract key on/off events
            for _, row in df.iterrows():
                driver = str(row[column_mapping['driver']]).strip()
                asset = str(row[column_mapping['asset']]).strip()
                event_time = row[column_mapping['datetime']]
                event_type = str(row[column_mapping['event_type']]).strip().lower()
                location = str(row[column_mapping['location']]) if 'location' in column_mapping else "Unknown"
                
                # Skip empty driver names
                if not driver or driver.lower() in ['nan', 'none', 'null', '']:
                    continue
                
                # Convert datetime to standard format
                if isinstance(event_time, str):
                    try:
                        # Try different date formats
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y %I:%M:%S %p']:
                            try:
                                event_time = datetime.strptime(event_time, fmt)
                                break
                            except ValueError:
                                continue
                    except Exception:
                        logger.warning(f"Could not parse datetime {event_time} for driver {driver}")
                        continue
                
                # Skip events for other dates
                event_date = event_time.strftime('%Y-%m-%d') if isinstance(event_time, datetime) else None
                if event_date != date_str:
                    continue
                
                # Determine event type
                is_key_on = any(term in event_type for term in ['on', 'start', 'begin', 'arrive'])
                is_key_off = any(term in event_type for term in ['off', 'end', 'finish', 'exit', 'leave'])
                
                # Skip invalid event types
                if not (is_key_on or is_key_off):
                    continue
                
                # Create driver key
                driver_key = f"{driver}|{asset}"
                
                # Initialize driver entry if not exists
                if driver_key not in source_data['driving_history']:
                    source_data['driving_history'][driver_key] = {
                        'driver': driver,
                        'asset': asset,
                        'events': [],
                        'first_key_on': None,
                        'last_key_off': None,
                        'location': location
                    }
                
                # Add event to driver events
                event = {
                    'time': event_time,
                    'type': 'key_on' if is_key_on else 'key_off',
                    'location': location
                }
                source_data['driving_history'][driver_key]['events'].append(event)
                
                # Update first key on and last key off
                if is_key_on:
                    if (source_data['driving_history'][driver_key]['first_key_on'] is None or 
                            event_time < source_data['driving_history'][driver_key]['first_key_on']):
                        source_data['driving_history'][driver_key]['first_key_on'] = event_time
                        source_data['driving_history'][driver_key]['location'] = location
                
                if is_key_off:
                    if (source_data['driving_history'][driver_key]['last_key_off'] is None or 
                            event_time > source_data['driving_history'][driver_key]['last_key_off']):
                        source_data['driving_history'][driver_key]['last_key_off'] = event_time
            
            logger.info(f"Processed {len(source_data['driving_history'])} drivers from driving history file {file_path}")
            
        except Exception as e:
            logger.error(f"Error processing driving history file {file_path}: {e}")
            logger.error(traceback.format_exc())
    
    # Step 3: Process activity detail files
    for file_path in source_files.get('activity_detail', []):
        try:
            logger.info(f"Processing activity detail file: {file_path}")
            
            # Determine file type
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                logger.warning(f"Unsupported file type for activity detail: {file_path}")
                continue
                
            # Save row count
            source_data['row_counts'][os.path.basename(file_path)] = len(df)
                
            # Standardize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Map standard columns
            column_mapping = {}
            for std_col, possible_cols in [
                ('driver', ['driver', 'driver_name', 'drivername', 'employee', 'employee_name', 'name']),
                ('asset', ['asset', 'asset_id', 'assetid', 'vehicle', 'vehicle_id', 'equipment']),
                ('datetime', ['datetime', 'date_time', 'time', 'timestamp', 'event_time']),
                ('activity', ['activity', 'event', 'event_type', 'status', 'action']),
                ('duration', ['duration', 'minutes', 'hours', 'time_spent']),
                ('location', ['location', 'site', 'job_site', 'jobsite', 'position', 'gps'])
            ]:
                for col in possible_cols:
                    if col in df.columns:
                        column_mapping[std_col] = col
                        break
            
            # Verify essential columns are mapped
            if not all(col in column_mapping for col in ['driver', 'asset', 'datetime', 'activity']):
                missing = [col for col in ['driver', 'asset', 'datetime', 'activity'] if col not in column_mapping]
                logger.error(f"Missing essential columns in activity detail file {file_path}: {missing}")
                continue
            
            # Extract activity data
            for _, row in df.iterrows():
                driver = str(row[column_mapping['driver']]).strip()
                asset = str(row[column_mapping['asset']]).strip()
                activity_time = row[column_mapping['datetime']]
                activity = str(row[column_mapping['activity']]).strip().lower()
                duration = row[column_mapping['duration']] if 'duration' in column_mapping else 0
                location = str(row[column_mapping['location']]) if 'location' in column_mapping else "Unknown"
                
                # Skip empty driver names
                if not driver or driver.lower() in ['nan', 'none', 'null', '']:
                    continue
                
                # Convert datetime to standard format
                if isinstance(activity_time, str):
                    try:
                        # Try different date formats
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y %I:%M:%S %p']:
                            try:
                                activity_time = datetime.strptime(activity_time, fmt)
                                break
                            except ValueError:
                                continue
                    except Exception:
                        logger.warning(f"Could not parse datetime {activity_time} for driver {driver}")
                        continue
                
                # Skip activities for other dates
                activity_date = activity_time.strftime('%Y-%m-%d') if isinstance(activity_time, datetime) else None
                if activity_date != date_str:
                    continue
                
                # Create driver key
                driver_key = f"{driver}|{asset}"
                
                # Initialize driver entry if not exists
                if driver_key not in source_data['activity_detail']:
                    source_data['activity_detail'][driver_key] = {
                        'driver': driver,
                        'asset': asset,
                        'activities': [],
                        'total_duration': 0,
                        'location': location
                    }
                
                # Add activity to driver activities
                activity_record = {
                    'time': activity_time,
                    'activity': activity,
                    'duration': float(duration) if duration else 0,
                    'location': location
                }
                source_data['activity_detail'][driver_key]['activities'].append(activity_record)
                
                # Update total duration
                source_data['activity_detail'][driver_key]['total_duration'] += float(duration) if duration else 0
            
            logger.info(f"Processed {len(source_data['activity_detail'])} drivers from activity detail file {file_path}")
            
        except Exception as e:
            logger.error(f"Error processing activity detail file {file_path}: {e}")
            logger.error(traceback.format_exc())
    
    # Step 4: Process assets time on site files
    for file_path in source_files.get('assets_time_on_site', []):
        try:
            logger.info(f"Processing assets time on site file: {file_path}")
            
            # Determine file type
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                logger.warning(f"Unsupported file type for assets time on site: {file_path}")
                continue
                
            # Save row count
            source_data['row_counts'][os.path.basename(file_path)] = len(df)
                
            # Standardize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Map standard columns
            column_mapping = {}
            for std_col, possible_cols in [
                ('asset', ['asset', 'asset_id', 'assetid', 'vehicle', 'vehicle_id', 'equipment']),
                ('site', ['site', 'job_site', 'jobsite', 'location', 'position']),
                ('time_in', ['time_in', 'timein', 'arrival', 'start_time', 'start']),
                ('time_out', ['time_out', 'timeout', 'departure', 'end_time', 'end']),
                ('duration', ['duration', 'total_minutes', 'total_time', 'minutes', 'hours'])
            ]:
                for col in possible_cols:
                    if col in df.columns:
                        column_mapping[std_col] = col
                        break
            
            # Verify essential columns are mapped
            if not all(col in column_mapping for col in ['asset', 'site', 'time_in']):
                missing = [col for col in ['asset', 'site', 'time_in'] if col not in column_mapping]
                logger.error(f"Missing essential columns in assets time on site file {file_path}: {missing}")
                continue
            
            # Extract onsite data
            for _, row in df.iterrows():
                asset = str(row[column_mapping['asset']]).strip()
                site = str(row[column_mapping['site']]).strip()
                time_in = row[column_mapping['time_in']]
                time_out = row[column_mapping['time_out']] if 'time_out' in column_mapping else None
                duration = row[column_mapping['duration']] if 'duration' in column_mapping else 0
                
                # Skip empty asset IDs
                if not asset or asset.lower() in ['nan', 'none', 'null', '']:
                    continue
                
                # Convert datetime to standard format
                if isinstance(time_in, str):
                    try:
                        # Try different date formats
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y %I:%M:%S %p']:
                            try:
                                time_in = datetime.strptime(time_in, fmt)
                                break
                            except ValueError:
                                continue
                    except Exception:
                        logger.warning(f"Could not parse time_in {time_in} for asset {asset}")
                        continue
                
                if time_out and isinstance(time_out, str):
                    try:
                        # Try different date formats
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y %I:%M:%S %p']:
                            try:
                                time_out = datetime.strptime(time_out, fmt)
                                break
                            except ValueError:
                                continue
                    except Exception:
                        logger.warning(f"Could not parse time_out {time_out} for asset {asset}")
                        time_out = None
                
                # Skip records for other dates
                time_in_date = time_in.strftime('%Y-%m-%d') if isinstance(time_in, datetime) else None
                if time_in_date != date_str:
                    continue
                
                # Initialize asset entry if not exists
                if asset not in source_data['assets_time_on_site']:
                    source_data['assets_time_on_site'][asset] = {
                        'asset': asset,
                        'sites': []
                    }
                
                # Add site record
                site_record = {
                    'site': site,
                    'time_in': time_in,
                    'time_out': time_out,
                    'duration': float(duration) if duration else 0
                }
                source_data['assets_time_on_site'][asset]['sites'].append(site_record)
            
            logger.info(f"Processed {len(source_data['assets_time_on_site'])} assets from onsite file {file_path}")
            
        except Exception as e:
            logger.error(f"Error processing assets time on site file {file_path}: {e}")
            logger.error(traceback.format_exc())
    
    # Step 5: Process start time and job files
    for file_path in source_files.get('start_time_job', []):
        try:
            logger.info(f"Processing start time and job file: {file_path}")
            
            # Determine file type
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    df = pd.DataFrame(json.load(f))
            else:
                logger.warning(f"Unsupported file type for start time and job: {file_path}")
                continue
                
            # Save row count
            source_data['row_counts'][os.path.basename(file_path)] = len(df)
                
            # Standardize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Special case for baseline.csv which we know has specific columns
            if os.path.basename(file_path) == 'baseline.csv':
                column_mapping = {
                    'driver': 'driver_name',
                    'asset': 'asset_id',
                    'start_time': 'scheduled_start',
                    'end_time': 'scheduled_end',
                    'job_site': 'job_site'
                }
            else:
                # Map standard columns
                column_mapping = {}
                for std_col, possible_cols in [
                    ('driver', ['driver', 'driver_name', 'drivername', 'employee', 'employee_name', 'name']),
                    ('asset', ['asset', 'asset_id', 'assetid', 'vehicle', 'vehicle_id', 'equipment']),
                    ('start_time', ['start_time', 'starttime', 'scheduled_start', 'job_start', 'shift_start']),
                    ('end_time', ['end_time', 'endtime', 'scheduled_end', 'job_end', 'shift_end']),
                    ('job_site', ['job_site', 'jobsite', 'site', 'location', 'project', 'job', 'assignment'])
                ]:
                    for col in possible_cols:
                        if col in df.columns:
                            column_mapping[std_col] = col
                            break
            
            # Verify essential columns are mapped
            if not all(col in column_mapping for col in ['driver', 'start_time', 'job_site']):
                missing = [col for col in ['driver', 'start_time', 'job_site'] if col not in column_mapping]
                logger.error(f"Missing essential columns in start time and job file {file_path}: {missing}")
                continue
            
            # Extract schedule data
            for _, row in df.iterrows():
                driver = str(row[column_mapping['driver']]).strip()
                asset = str(row[column_mapping['asset']]) if 'asset' in column_mapping else "Unknown"
                job_site = str(row[column_mapping['job_site']]).strip()
                start_time = row[column_mapping['start_time']]
                end_time = row[column_mapping['end_time']] if 'end_time' in column_mapping else None
                
                # Skip empty driver names
                if not driver or driver.lower() in ['nan', 'none', 'null', '']:
                    continue
                
                # Convert start time to standard format
                try:
                    if isinstance(start_time, str):
                        # Try different time formats
                        for fmt in ['%H:%M:%S', '%I:%M:%S %p', '%I:%M %p', '%H:%M']:
                            try:
                                start_time = datetime.strptime(start_time, fmt).time()
                                break
                            except ValueError:
                                continue
                    elif isinstance(start_time, (int, float)):
                        # Handle Excel time format (fraction of day)
                        if 0 <= start_time < 1:
                            hours = int(start_time * 24)
                            minutes = int((start_time * 24 - hours) * 60)
                            start_time = time(hours, minutes)
                except Exception:
                    logger.warning(f"Could not parse start time {start_time} for driver {driver}")
                    start_time = time(6, 0)  # Default to 6:00 AM
                
                # Convert end time to standard format
                try:
                    if isinstance(end_time, str):
                        # Try different time formats
                        for fmt in ['%H:%M:%S', '%I:%M:%S %p', '%I:%M %p', '%H:%M']:
                            try:
                                end_time = datetime.strptime(end_time, fmt).time()
                                break
                            except ValueError:
                                continue
                    elif isinstance(end_time, (int, float)):
                        # Handle Excel time format (fraction of day)
                        if 0 <= end_time < 1:
                            hours = int(end_time * 24)
                            minutes = int((end_time * 24 - hours) * 60)
                            end_time = time(hours, minutes)
                except Exception:
                    logger.warning(f"Could not parse end time {end_time} for driver {driver}")
                    end_time = time(15, 30)  # Default to 3:30 PM
                
                # Create driver key
                driver_key = driver
                
                # Initialize driver entry if not exists or update with more info
                if driver_key not in source_data['start_time_job']:
                    source_data['start_time_job'][driver_key] = {
                        'driver': driver,
                        'asset': asset,
                        'job_site': job_site,
                        'start_time': start_time,
                        'end_time': end_time
                    }
                else:
                    # Update with additional info if available
                    if asset != "Unknown":
                        source_data['start_time_job'][driver_key]['asset'] = asset
                    if job_site != "Unknown":
                        source_data['start_time_job'][driver_key]['job_site'] = job_site
            
            logger.info(f"Processed {len(source_data['start_time_job'])} drivers from schedule file {file_path}")
            
        except Exception as e:
            logger.error(f"Error processing start time and job file {file_path}: {e}")
            logger.error(traceback.format_exc())
    
    # Step 6: Verify data consistency across sources
    asset_driver_map = {}
    
    # Build asset to driver mapping from all sources
    for driver_key, data in source_data['driving_history'].items():
        driver, asset = driver_key.split('|')
        if asset not in asset_driver_map:
            asset_driver_map[asset] = driver
    
    for driver_key, data in source_data['activity_detail'].items():
        driver, asset = driver_key.split('|')
        if asset not in asset_driver_map:
            asset_driver_map[asset] = driver
    
    for driver, data in source_data['start_time_job'].items():
        asset = data['asset']
        if asset not in asset_driver_map and asset != "Unknown":
            asset_driver_map[asset] = driver
    
    # Save asset to driver mapping
    source_data['metadata']['asset_driver_map'] = asset_driver_map
    
    # Log overall stats
    logger.info(f"Loaded data for {date_str}:")
    logger.info(f"  - Driving history: {len(source_data['driving_history'])} drivers")
    logger.info(f"  - Activity detail: {len(source_data['activity_detail'])} drivers")
    logger.info(f"  - Assets time on site: {len(source_data['assets_time_on_site'])} assets")
    logger.info(f"  - Start time and job: {len(source_data['start_time_job'])} drivers")
    
    return source_data

def compute_driver_status(driver_data: Dict, source_data: Dict) -> Dict:
    """
    Compute driver status based on all available data
    
    Args:
        driver_data (Dict): Driver data entry
        source_data (Dict): All source data
        
    Returns:
        Dict: Status information for the driver
    """
    driver_name = driver_data['driver_name']
    asset_id = driver_data['asset_id']
    job_site = driver_data['job_site']
    
    # Default status values
    status_info = {
        'driver_name': driver_name,
        'asset_id': asset_id,
        'assigned_job_site': job_site,
        'scheduled_start': driver_data['scheduled_start'],
        'scheduled_end': driver_data['scheduled_end'],
        'actual_start': None,
        'actual_end': None,
        'actual_start_display': "N/A",
        'actual_end_display': "N/A",
        'status': "Unknown",
        'status_reason': "",
        'minutes_late': 0,
        'minutes_early': 0,
        'location': "Unknown",
        'activity_count': 0,
        'total_duration': 0
    }
    
    # Parse scheduled times
    try:
        scheduled_start_time = datetime.strptime(driver_data['scheduled_start'], '%I:%M %p').time()
        scheduled_end_time = datetime.strptime(driver_data['scheduled_end'], '%I:%M %p').time()
    except ValueError:
        # Try alternative formats
        try:
            scheduled_start_time = datetime.strptime(driver_data['scheduled_start'], '%H:%M').time()
            scheduled_end_time = datetime.strptime(driver_data['scheduled_end'], '%H:%M').time()
        except ValueError:
            logger.error(f"Could not parse scheduled times for driver {driver_name}")
            scheduled_start_time = time(6, 0)  # Default to 6:00 AM
            scheduled_end_time = time(15, 30)  # Default to 3:30 PM
    
    # Look for driver in driving history
    driver_key_options = [
        f"{driver_name}|{asset_id}",
        f"{driver_name.upper()}|{asset_id}",
        f"{driver_name.lower()}|{asset_id}"
    ]
    
    driving_data = None
    for key in driver_key_options:
        if key in source_data['driving_history']:
            driving_data = source_data['driving_history'][key]
            break
    
    # Look for driver in activity detail
    activity_data = None
    for key in driver_key_options:
        if key in source_data['activity_detail']:
            activity_data = source_data['activity_detail'][key]
            break
    
    # Look for asset in onsite data
    onsite_data = []
    if asset_id in source_data['assets_time_on_site']:
        onsite_data = source_data['assets_time_on_site'][asset_id]['sites']
    
    # Update status info with actual data
    if driving_data:
        status_info['actual_start'] = driving_data.get('first_key_on')
        status_info['actual_end'] = driving_data.get('last_key_off')
        status_info['location'] = driving_data.get('location', "Unknown")
        
        if status_info['actual_start']:
            status_info['actual_start_display'] = status_info['actual_start'].strftime('%I:%M %p')
        
        if status_info['actual_end']:
            status_info['actual_end_display'] = status_info['actual_end'].strftime('%I:%M %p')
    
    if activity_data:
        status_info['activity_count'] = len(activity_data.get('activities', []))
        status_info['total_duration'] = activity_data.get('total_duration', 0)
        
        # Use activity location if driving location is unknown
        if status_info['location'] == "Unknown":
            status_info['location'] = activity_data.get('location', "Unknown")
    
    # Check if driver has any actual data
    if status_info['actual_start'] is None and status_info['activity_count'] == 0 and not onsite_data:
        status_info['status'] = "Not On Job"
        status_info['status_reason'] = "No activity detected"
        return status_info
    
    # Check if driver is at the correct job site
    correct_job_site = True
    
    # First check the location from telematics
    if status_info['location'] != "Unknown" and status_info['assigned_job_site'] != "Unknown":
        # Simple string matching for now - could be enhanced with fuzzy matching
        if status_info['assigned_job_site'] not in status_info['location'] and status_info['location'] not in status_info['assigned_job_site']:
            correct_job_site = False
            status_info['status'] = "Not On Job"
            status_info['status_reason'] = f"At incorrect location: {status_info['location']}"
    
    # If job site seems wrong, check the onsite data for confirmation
    if not correct_job_site and onsite_data:
        # Check if asset was detected at correct job site
        for site_record in onsite_data:
            if status_info['assigned_job_site'] in site_record['site'] or site_record['site'] in status_info['assigned_job_site']:
                correct_job_site = True
                break
    
    # If job site is correct, check arrival and departure times
    if correct_job_site and status_info['actual_start'] is not None:
        actual_start_time = status_info['actual_start'].time()
        actual_end_time = status_info['actual_end'].time() if status_info['actual_end'] else None
        
        # Calculate minutes late
        scheduled_minutes = scheduled_start_time.hour * 60 + scheduled_start_time.minute
        actual_minutes = actual_start_time.hour * 60 + actual_start_time.minute
        
        minutes_late = actual_minutes - scheduled_minutes
        status_info['minutes_late'] = minutes_late if minutes_late > 0 else 0
        
        # Check if late
        if minutes_late > LATE_THRESHOLD_MINUTES:
            status_info['status'] = "Late"
            status_info['status_reason'] = f"{minutes_late} minutes late"
        elif actual_end_time:
            # Calculate minutes early
            scheduled_minutes = scheduled_end_time.hour * 60 + scheduled_end_time.minute
            actual_minutes = actual_end_time.hour * 60 + actual_end_time.minute
            
            minutes_early = scheduled_minutes - actual_minutes
            status_info['minutes_early'] = minutes_early if minutes_early > 0 else 0
            
            # Check if early end
            if minutes_early > EARLY_END_THRESHOLD_MINUTES:
                status_info['status'] = "Early End"
                status_info['status_reason'] = f"{minutes_early} minutes early"
            else:
                status_info['status'] = "On Time"
        else:
            status_info['status'] = "On Time"
    elif correct_job_site:
        status_info['status'] = "On Time"  # Assume on time if job site is correct but no key on time
    
    return status_info

def process_date(date_str: str) -> Dict[str, Any]:
    """
    Process all data for a specific date and generate a comprehensive report
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        Dict[str, Any]: Complete report data
    """
    logger.info(f"Processing data for {date_str}")
    
    try:
        # Step 1: Load and validate source data
        source_data = load_source_data(date_str)
        
        # Step 2: Prepare driver list from all sources
        all_drivers = set()
        
        # Add drivers from driving history
        for driver_key in source_data['driving_history']:
            driver, _ = driver_key.split('|')
            all_drivers.add(driver)
        
        # Add drivers from activity detail
        for driver_key in source_data['activity_detail']:
            driver, _ = driver_key.split('|')
            all_drivers.add(driver)
        
        # Add drivers from start time and job
        for driver in source_data['start_time_job']:
            all_drivers.add(driver)
        
        logger.info(f"Found {len(all_drivers)} unique drivers across all sources")
        
        # Step 3: Build complete driver list with all data
        drivers_data = []
        
        for driver in all_drivers:
            # Get schedule data if available
            schedule_data = source_data['start_time_job'].get(driver)
            
            # Skip drivers without schedule data
            if not schedule_data:
                logger.warning(f"No schedule data for driver {driver}, skipping")
                continue
            
            # Build driver entry
            driver_entry = {
                'driver_name': driver,
                'asset_id': schedule_data.get('asset', "Unknown"),
                'job_site': schedule_data.get('job_site', "Unknown"),
                'scheduled_start': schedule_data.get('start_time').strftime('%I:%M %p') if isinstance(schedule_data.get('start_time'), time) else "06:00 AM",
                'scheduled_end': schedule_data.get('end_time').strftime('%I:%M %p') if isinstance(schedule_data.get('end_time'), time) else "03:30 PM"
            }
            
            # Add to drivers list
            drivers_data.append(driver_entry)
        
        # Step 4: Compute status for each driver
        for driver_entry in drivers_data:
            status_info = compute_driver_status(driver_entry, source_data)
            
            # Update driver entry with status info
            driver_entry.update({
                'actual_start': status_info['actual_start_display'],
                'actual_end': status_info['actual_end_display'],
                'status': status_info['status'],
                'status_reason': status_info['status_reason']
            })
        
        # Step 5: Generate summary counts
        summary = {
            'date': date_str,
            'total': len(drivers_data),
            'late': sum(1 for d in drivers_data if d.get('status') == 'Late'),
            'early_end': sum(1 for d in drivers_data if d.get('status') == 'Early End'),
            'not_on_job': sum(1 for d in drivers_data if d.get('status') == 'Not On Job'),
            'on_time': sum(1 for d in drivers_data if d.get('status') == 'On Time')
        }
        
        # Step 6: Build final report data
        report_data = {
            'date': date_str,
            'drivers': drivers_data,
            'summary': summary,
            'metadata': {
                'processed_at': datetime.now().isoformat(),
                'source_files': source_data['metadata']['source_files'],
                'row_counts': source_data['row_counts']
            }
        }
        
        # Step 7: Validate data integrity
        is_valid = validate_data_integrity(report_data, source_data['metadata']['source_files'])
        
        if not is_valid:
            logger.error(f"Data integrity validation failed for {date_str}")
            report_data['metadata']['validation_status'] = "FAILED"
        else:
            logger.info(f"Data integrity validation passed for {date_str}")
            report_data['metadata']['validation_status'] = "PASSED"
        
        return report_data
        
    except Exception as e:
        logger.error(f"Error processing data for {date_str}: {e}")
        logger.error(traceback.format_exc())
        return None

def export_report(report_data: Dict[str, Any], date_str: str) -> Dict[str, str]:
    """
    Export report data to all required output formats
    
    Args:
        report_data (Dict[str, Any]): Report data to export
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        Dict[str, str]: Dictionary of output file paths by format
    """
    logger.info(f"Exporting report data for {date_str}")
    
    try:
        # Step 1: Create output directories
        reports_dir = Path('reports/daily_drivers')
        exports_dir = Path('exports/daily_reports')
        
        reports_dir.mkdir(parents=True, exist_ok=True)
        exports_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 2: Save as JSON
        json_path_reports = reports_dir / f"daily_report_{date_str}.json"
        json_path_exports = exports_dir / f"daily_report_{date_str}.json"
        
        with open(json_path_reports, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
            
        with open(json_path_exports, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
            
        logger.info(f"JSON report saved to {json_path_reports} and {json_path_exports}")
        
        # Step 3: Save as Excel
        try:
            import pandas as pd
            
            # Convert drivers list to DataFrame
            df = pd.DataFrame(report_data['drivers'])
            
            # Save to Excel
            excel_path_reports = reports_dir / f"daily_report_{date_str}.xlsx"
            excel_path_exports = exports_dir / f"{date_str}_DailyDriverReport.xlsx"
            legacy_excel_exports = exports_dir / f"daily_report_{date_str}.xlsx"
            
            df.to_excel(excel_path_reports, index=False)
            df.to_excel(excel_path_exports, index=False)
            df.to_excel(legacy_excel_exports, index=False)
            
            logger.info(f"Excel report saved to {excel_path_reports}, {excel_path_exports}, and {legacy_excel_exports}")
        except Exception as e:
            logger.error(f"Error exporting Excel report: {e}")
        
        # Step 4: Generate PDF
        try:
            from generate_pdf_report import generate_pdf_report
            pdf_path = generate_pdf_report(date_str)
            if pdf_path:
                logger.info(f"PDF report generated at {pdf_path}")
            else:
                logger.warning("PDF generation returned no path")
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
        
        # Step 5: Validate output files
        if not validate_output_files(date_str):
            logger.error(f"Output files validation failed for {date_str}")
            return {
                'status': 'FAILED',
                'error': 'Output files validation failed'
            }
        
        # Return output paths
        return {
            'status': 'SUCCESS',
            'json': str(json_path_reports),
            'excel': str(excel_path_reports),
            'pdf': str(reports_dir / f"daily_report_{date_str}.pdf")
        }
        
    except Exception as e:
        logger.error(f"Error exporting report for {date_str}: {e}")
        logger.error(traceback.format_exc())
        return {
            'status': 'FAILED',
            'error': str(e)
        }

def process_and_export(date_str: str) -> Dict[str, Any]:
    """
    Process data and export report for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        Dict[str, Any]: Processing and export results
    """
    logger.info(f"Processing and exporting report for {date_str}")
    
    try:
        # Step 1: Process data
        report_data = process_date(date_str)
        
        if not report_data:
            logger.error(f"Data processing failed for {date_str}")
            return {
                'status': 'FAILED',
                'error': 'Data processing failed'
            }
        
        # Step 2: Export report
        export_results = export_report(report_data, date_str)
        
        if export_results['status'] != 'SUCCESS':
            logger.error(f"Report export failed for {date_str}: {export_results['error']}")
            return {
                'status': 'FAILED',
                'error': f"Report export failed: {export_results['error']}"
            }
        
        # Step 3: Return success
        return {
            'status': 'SUCCESS',
            'date': date_str,
            'summary': report_data['summary'],
            'file_paths': export_results
        }
        
    except Exception as e:
        logger.error(f"Error in process_and_export for {date_str}: {e}")
        logger.error(traceback.format_exc())
        return {
            'status': 'FAILED',
            'error': str(e)
        }

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TRAXORA Genius Processor')
    parser.add_argument('date', help='Date to process in YYYY-MM-DD format')
    parser.add_argument('--validate-only', action='store_true', help='Only validate data without processing')
    
    args = parser.parse_args()
    
    if args.validate_only:
        logger.info(f"Validating data for {args.date}")
        source_files = validate_source_files(args.date)
        print(f"Validation complete. Found files: {source_files}")
    else:
        logger.info(f"Processing and exporting report for {args.date}")
        results = process_and_export(args.date)
        print(f"Results: {json.dumps(results, indent=2, default=str)}")

if __name__ == "__main__":
    main()