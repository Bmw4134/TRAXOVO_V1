#!/usr/bin/env python3
"""
TRAXORA Enhanced Genius Processor

This module implements a robust, production-grade data processor for the Daily Driver Report
with strict adherence to the master source hierarchy:
- Driver identity → Employee List
- Actual activity → DrivingHistory + ActivityDetail
- Job assignment → Job list files (DFW, HOU, WT)
- Job site confirmation → AssetsTimeOnSite.csv
- Scheduled times → Pulled from Start Time & Job or calculated directly
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
file_handler = logging.FileHandler('logs/enhanced_genius_processor.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Constants for status determination
LATE_THRESHOLD_MINUTES = 15
EARLY_END_THRESHOLD_MINUTES = 30

# Define paths to master source files
EMPLOYEE_LIST_PATH = 'attached_assets/Consolidated_Employee_And_Job_Lists_Corrected.xlsx'
JOB_LIST_PATHS = [
    'attached_assets/01 - DFW APR 2025.csv',
    'attached_assets/02 - HOU APR 2025.csv',
    'attached_assets/03 - WT APR 2025.csv'
]
START_TIME_JOB_PATH = 'data/start_time_job/baseline.csv'

class DataProcessingError(Exception):
    """Custom exception for data processing errors"""
    pass

def load_employee_list() -> Dict[str, Dict[str, Any]]:
    """
    Load master employee list
    
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of employee data by normalized name
    """
    employee_data = {}
    
    if not os.path.exists(EMPLOYEE_LIST_PATH):
        logger.warning(f"Employee list not found: {EMPLOYEE_LIST_PATH}")
        return employee_data
    
    try:
        # Load employee list
        df = pd.read_excel(EMPLOYEE_LIST_PATH)
        
        # Look for employee name column
        employee_cols = ['name', 'employee_name', 'full_name', 'driver_name', 'employee']
        employee_col = None
        for col in employee_cols:
            if col in df.columns:
                employee_col = col
                break
                
        if not employee_col:
            logger.error("Employee name column not found in employee list")
            return employee_data
            
        # Process each employee
        for _, row in df.iterrows():
            name = str(row[employee_col]).strip()
            if name and name.lower() not in ['nan', 'none', 'null', '']:
                normalized_name = name.lower()
                
                # Extract other employee data
                employee_record = {'name': name, 'normalized_name': normalized_name}
                
                # Add any other available fields
                for col in df.columns:
                    if col != employee_col:
                        employee_record[col] = row[col]
                
                employee_data[normalized_name] = employee_record
                
        logger.info(f"Loaded {len(employee_data)} employees from master list")
        
    except Exception as e:
        logger.error(f"Error loading employee list: {e}")
        logger.error(traceback.format_exc())
    
    return employee_data

def load_job_assignments() -> Dict[str, Dict[str, Any]]:
    """
    Load job assignments from job list files
    
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of job assignments by job ID
    """
    job_assignments = {}
    
    for job_list_path in JOB_LIST_PATHS:
        if not os.path.exists(job_list_path):
            logger.warning(f"Job list not found: {job_list_path}")
            continue
            
        try:
            # Determine file type
            if job_list_path.endswith('.csv'):
                df = pd.read_csv(job_list_path)
            elif job_list_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(job_list_path)
            else:
                logger.warning(f"Unsupported file type: {job_list_path}")
                continue
                
            # Standardize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Look for job ID and location columns
            job_id_cols = ['job_id', 'job', 'job_number', 'jobid', 'jobnumber']
            location_cols = ['location', 'job_site', 'site', 'address']
            
            job_id_col = None
            location_col = None
            
            for col in job_id_cols:
                if col in df.columns:
                    job_id_col = col
                    break
                    
            for col in location_cols:
                if col in df.columns:
                    location_col = col
                    break
            
            if not job_id_col:
                logger.warning(f"Job ID column not found in {job_list_path}")
                continue
                
            # Process each job
            for _, row in df.iterrows():
                job_id = str(row[job_id_col]).strip()
                if job_id and job_id.lower() not in ['nan', 'none', 'null', '']:
                    # Extract location if available
                    location = str(row[location_col]).strip() if location_col else "Unknown"
                    
                    # Create job record
                    job_record = {
                        'job_id': job_id,
                        'location': location,
                        'source_file': os.path.basename(job_list_path)
                    }
                    
                    # Add any other available fields
                    for col in df.columns:
                        if col not in [job_id_col, location_col]:
                            job_record[col] = row[col]
                    
                    job_assignments[job_id] = job_record
                    
            logger.info(f"Loaded {len(job_assignments)} job assignments from {job_list_path}")
            
        except Exception as e:
            logger.error(f"Error loading job list {job_list_path}: {e}")
            logger.error(traceback.format_exc())
    
    return job_assignments

def load_scheduled_times() -> Dict[str, Dict[str, Any]]:
    """
    Load scheduled times from Start Time & Job file
    
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of scheduled times by driver name
    """
    scheduled_times = {}
    
    if not os.path.exists(START_TIME_JOB_PATH):
        logger.warning(f"Start Time & Job file not found: {START_TIME_JOB_PATH}")
        return scheduled_times
        
    try:
        # Load file
        df = pd.read_csv(START_TIME_JOB_PATH)
        
        # Standardize column names
        df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
        
        # Extract driver, asset, job site, and scheduled times
        driver_col = 'driver_name' if 'driver_name' in df.columns else None
        asset_col = 'asset_id' if 'asset_id' in df.columns else None
        job_site_col = 'job_site' if 'job_site' in df.columns else None
        start_time_col = 'scheduled_start' if 'scheduled_start' in df.columns else None
        end_time_col = 'scheduled_end' if 'scheduled_end' in df.columns else None
        
        if not all([driver_col, start_time_col]):
            logger.error("Missing required columns in Start Time & Job file")
            return scheduled_times
            
        # Process each row
        for _, row in df.iterrows():
            driver_name = str(row[driver_col]).strip()
            if driver_name and driver_name.lower() not in ['nan', 'none', 'null', '']:
                normalized_name = driver_name.lower()
                
                # Extract asset and job site if available
                asset_id = str(row[asset_col]).strip() if asset_col else "Unknown"
                job_site = str(row[job_site_col]).strip() if job_site_col else "Unknown"
                
                # Extract scheduled times
                start_time = row[start_time_col]
                end_time = row[end_time_col] if end_time_col else None
                
                # Convert to time objects
                try:
                    if isinstance(start_time, str):
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
                    start_time = time(6, 0)  # Default to 6:00 AM
                    
                try:
                    if isinstance(end_time, str):
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
                    end_time = time(15, 30)  # Default to 3:30 PM
                
                # Create scheduled time record
                scheduled_times[normalized_name] = {
                    'driver_name': driver_name,
                    'asset_id': asset_id,
                    'job_site': job_site,
                    'start_time': start_time,
                    'end_time': end_time
                }
                
        logger.info(f"Loaded {len(scheduled_times)} scheduled times from Start Time & Job file")
        
    except Exception as e:
        logger.error(f"Error loading scheduled times: {e}")
        logger.error(traceback.format_exc())
    
    return scheduled_times

def load_source_data(date_str: str) -> Dict[str, Any]:
    """
    Load and validate all source data for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        Dict[str, Any]: Dictionary containing all loaded and validated source data
    """
    logger.info(f"Loading source data for {date_str}")
    
    # Initialize result dictionary
    source_data = {
        'driving_history': {},
        'activity_detail': {},
        'assets_time_on_site': {},
        'row_counts': {},
        'metadata': {
            'date': date_str,
            'processed_at': datetime.now().isoformat()
        }
    }
    
    # Load master sources
    employee_list = load_employee_list()
    job_assignments = load_job_assignments()
    scheduled_times = load_scheduled_times()
    
    # Add master sources to metadata
    source_data['metadata']['employee_count'] = len(employee_list)
    source_data['metadata']['job_assignment_count'] = len(job_assignments)
    source_data['metadata']['scheduled_times_count'] = len(scheduled_times)
    
    # Load source data files for the date
    source_files = {}
    
    # Define directories to search
    source_dirs = {
        'driving_history': 'data/driving_history',
        'activity_detail': 'data/activity_detail',
        'assets_time_on_site': 'data/assets_time_on_site'
    }
    
    # Find files for the date
    for source_type, dir_path in source_dirs.items():
        source_files[source_type] = []
        
        if os.path.exists(dir_path):
            for file_name in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file_name)
                
                # Skip files with exclusions
                if '_verified' in file_name:
                    continue
                    
                # Check if file matches the date
                if date_str.replace('-', '') in file_name or date_str in file_name:
                    source_files[source_type].append(file_path)
    
    # Add source files to metadata
    source_data['metadata']['source_files'] = {
        k: [os.path.basename(f) for f in v] for k, v in source_files.items()
    }
    
    # Process driving history files
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
                
                # Normalize driver name
                normalized_driver = driver.lower()
                
                # Skip empty driver names
                if not driver or driver.lower() in ['nan', 'none', 'null', '']:
                    continue
                
                # Verify driver exists in master employee list
                if normalized_driver not in employee_list:
                    logger.warning(f"Driver '{driver}' not found in master employee list, skipping")
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
                driver_key = normalized_driver
                
                # Initialize driver entry if not exists
                if driver_key not in source_data['driving_history']:
                    source_data['driving_history'][driver_key] = {
                        'driver': driver,
                        'normalized_driver': normalized_driver,
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
    
    # Process activity detail files
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
            if not all(col in column_mapping for col in ['driver', 'datetime', 'activity']):
                missing = [col for col in ['driver', 'datetime', 'activity'] if col not in column_mapping]
                logger.error(f"Missing essential columns in activity detail file {file_path}: {missing}")
                continue
            
            # Extract activity data
            for _, row in df.iterrows():
                driver = str(row[column_mapping['driver']]).strip()
                asset = str(row[column_mapping['asset']]).strip() if 'asset' in column_mapping else "Unknown"
                activity_time = row[column_mapping['datetime']]
                activity = str(row[column_mapping['activity']]).strip().lower()
                duration = row[column_mapping['duration']] if 'duration' in column_mapping else 0
                location = str(row[column_mapping['location']]) if 'location' in column_mapping else "Unknown"
                
                # Normalize driver name
                normalized_driver = driver.lower()
                
                # Skip empty driver names
                if not driver or driver.lower() in ['nan', 'none', 'null', '']:
                    continue
                    
                # Verify driver exists in master employee list
                if normalized_driver not in employee_list:
                    logger.warning(f"Driver '{driver}' not found in master employee list, skipping")
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
                driver_key = normalized_driver
                
                # Initialize driver entry if not exists
                if driver_key not in source_data['activity_detail']:
                    source_data['activity_detail'][driver_key] = {
                        'driver': driver,
                        'normalized_driver': normalized_driver,
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
    
    # Process assets time on site files
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
    
    # Add master sources to source data
    source_data['employee_list'] = employee_list
    source_data['job_assignments'] = job_assignments
    source_data['scheduled_times'] = scheduled_times
    
    # Log overall stats
    logger.info(f"Loaded data for {date_str}:")
    logger.info(f"  - Employee list: {len(employee_list)} employees")
    logger.info(f"  - Driving history: {len(source_data['driving_history'])} drivers")
    logger.info(f"  - Activity detail: {len(source_data['activity_detail'])} drivers")
    logger.info(f"  - Assets time on site: {len(source_data['assets_time_on_site'])} assets")
    logger.info(f"  - Job assignments: {len(job_assignments)} jobs")
    logger.info(f"  - Scheduled times: {len(scheduled_times)} drivers")
    
    return source_data

def get_expected_job_site(driver_key: str, source_data: Dict[str, Any]) -> str:
    """
    Determine the expected job site for a driver
    
    Args:
        driver_key (str): Normalized driver name
        source_data (Dict[str, Any]): Source data
        
    Returns:
        str: Expected job site or 'Unknown'
    """
    # First check if driver has scheduled job site in Start Time & Job
    if driver_key in source_data['scheduled_times']:
        job_site = source_data['scheduled_times'][driver_key].get('job_site')
        if job_site and job_site != "Unknown":
            return job_site
    
    # If driver has job assignment, use that
    if driver_key in source_data['employee_list']:
        employee_data = source_data['employee_list'][driver_key]
        
        # Look for job assignment in employee data
        job_id = None
        for field in ['job_id', 'job', 'job_number', 'assignment']:
            if field in employee_data:
                job_id = employee_data[field]
                break
                
        if job_id and str(job_id) in source_data['job_assignments']:
            job_data = source_data['job_assignments'][str(job_id)]
            return job_data.get('location', "Unknown")
    
    # If no job site found, return Unknown
    return "Unknown"

def get_scheduled_times(driver_key: str, source_data: Dict[str, Any]) -> Tuple[Optional[time], Optional[time]]:
    """
    Get scheduled start and end times for a driver
    
    Args:
        driver_key (str): Normalized driver name
        source_data (Dict[str, Any]): Source data
        
    Returns:
        Tuple[Optional[time], Optional[time]]: Scheduled start and end times
    """
    # First check if driver has scheduled times in Start Time & Job
    if driver_key in source_data['scheduled_times']:
        start_time = source_data['scheduled_times'][driver_key].get('start_time')
        end_time = source_data['scheduled_times'][driver_key].get('end_time')
        
        if start_time and end_time:
            return start_time, end_time
    
    # Default to standard times if not found
    return time(6, 0), time(15, 30)

def is_driver_at_expected_job_site(driver_key: str, asset_id: str, source_data: Dict[str, Any]) -> bool:
    """
    Check if driver is at the expected job site
    
    Args:
        driver_key (str): Normalized driver name
        asset_id (str): Asset ID
        source_data (Dict[str, Any]): Source data
        
    Returns:
        bool: True if driver is at expected job site, False otherwise
    """
    # Get expected job site
    expected_job_site = get_expected_job_site(driver_key, source_data)
    
    if expected_job_site == "Unknown":
        # If expected job site is unknown, can't verify
        return True
    
    # Check driving history location
    if driver_key in source_data['driving_history']:
        location = source_data['driving_history'][driver_key].get('location', "Unknown")
        
        # Simple string matching - could be enhanced with fuzzy matching
        if expected_job_site in location or location in expected_job_site:
            return True
    
    # Check activity detail location
    if driver_key in source_data['activity_detail']:
        location = source_data['activity_detail'][driver_key].get('location', "Unknown")
        
        # Simple string matching - could be enhanced with fuzzy matching
        if expected_job_site in location or location in expected_job_site:
            return True
    
    # Check assets time on site
    if asset_id in source_data['assets_time_on_site']:
        sites = source_data['assets_time_on_site'][asset_id].get('sites', [])
        
        for site_record in sites:
            site = site_record.get('site', "Unknown")
            
            # Simple string matching - could be enhanced with fuzzy matching
            if expected_job_site in site or site in expected_job_site:
                return True
    
    # No match found
    return False

def compute_driver_status(driver_data: Dict, source_data: Dict[str, Any]) -> Dict:
    """
    Compute driver status based on all available data
    
    Args:
        driver_data (Dict): Driver data entry
        source_data (Dict[str, Any]): Source data
        
    Returns:
        Dict: Status information for the driver
    """
    driver_name = driver_data['driver_name']
    normalized_driver = driver_name.lower()
    asset_id = driver_data.get('asset_id', "Unknown")
    job_site = get_expected_job_site(normalized_driver, source_data)
    
    # Get scheduled times
    scheduled_start, scheduled_end = get_scheduled_times(normalized_driver, source_data)
    
    # Default status values
    status_info = {
        'driver_name': driver_name,
        'normalized_driver': normalized_driver,
        'asset_id': asset_id,
        'assigned_job_site': job_site,
        'scheduled_start': scheduled_start.strftime('%I:%M %p') if scheduled_start else "Unknown",
        'scheduled_end': scheduled_end.strftime('%I:%M %p') if scheduled_end else "Unknown",
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
        'total_duration': 0,
        'is_verified': driver_name.lower() in source_data['employee_list']
    }
    
    # Look for driver in driving history
    if normalized_driver in source_data['driving_history']:
        driving_data = source_data['driving_history'][normalized_driver]
        status_info['actual_start'] = driving_data.get('first_key_on')
        status_info['actual_end'] = driving_data.get('last_key_off')
        status_info['location'] = driving_data.get('location', "Unknown")
        status_info['asset_id'] = driving_data.get('asset', asset_id)
        
        if status_info['actual_start']:
            status_info['actual_start_display'] = status_info['actual_start'].strftime('%I:%M %p')
        
        if status_info['actual_end']:
            status_info['actual_end_display'] = status_info['actual_end'].strftime('%I:%M %p')
    
    # Look for driver in activity detail
    if normalized_driver in source_data['activity_detail']:
        activity_data = source_data['activity_detail'][normalized_driver]
        status_info['activity_count'] = len(activity_data.get('activities', []))
        status_info['total_duration'] = activity_data.get('total_duration', 0)
        
        # Use activity location if driving location is unknown
        if status_info['location'] == "Unknown":
            status_info['location'] = activity_data.get('location', "Unknown")
            
        # Use asset from activity if not found in driving history
        if status_info['asset_id'] == "Unknown":
            status_info['asset_id'] = activity_data.get('asset', "Unknown")
    
    # Assign status based on all collected data
    
    # First check if driver is verified in employee list
    if not status_info['is_verified']:
        status_info['status'] = "Unverified"
        status_info['status_reason'] = "Driver not found in employee list"
        return status_info
    
    # Check if driver has any actual data
    has_gps_activity = status_info['actual_start'] is not None or status_info['activity_count'] > 0
    
    if not has_gps_activity:
        status_info['status'] = "No GPS Activity"
        status_info['status_reason'] = "No telematics data found"
        return status_info
    
    # Check if driver is at the correct job site
    at_correct_site = is_driver_at_expected_job_site(normalized_driver, status_info['asset_id'], source_data)
    
    if not at_correct_site:
        status_info['status'] = "Not On Job"
        status_info['status_reason'] = f"Not at assigned location: {job_site}"
        return status_info
    
    # Driver is verified, has GPS activity, and is at correct job site - check punctuality
    if status_info['actual_start'] is not None and scheduled_start:
        actual_start_time = status_info['actual_start'].time()
        
        # Calculate minutes late
        scheduled_minutes = scheduled_start.hour * 60 + scheduled_start.minute
        actual_minutes = actual_start_time.hour * 60 + actual_start_time.minute
        
        minutes_late = actual_minutes - scheduled_minutes
        status_info['minutes_late'] = minutes_late if minutes_late > 0 else 0
        
        # Check if late
        if minutes_late > LATE_THRESHOLD_MINUTES:
            status_info['status'] = "Late"
            status_info['status_reason'] = f"{minutes_late} minutes late"
        elif status_info['actual_end'] and scheduled_end:
            # Calculate minutes early
            actual_end_time = status_info['actual_end'].time()
            scheduled_minutes = scheduled_end.hour * 60 + scheduled_end.minute
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
    else:
        # No key on time but presence confirmed at job site
        status_info['status'] = "Present"
        status_info['status_reason'] = "Activity at job site but no key on time"
    
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
        
        # Step 2: Prepare driver list from master employee list
        all_drivers = []
        
        # Add ALL drivers from employee list to ensure full population
        for driver_key, employee_data in source_data['employee_list'].items():
            driver_entry = {
                'driver_name': employee_data.get('name', driver_key),
                'normalized_driver': driver_key,
                'asset_id': "Unknown",
                'job_site': "Unknown"
            }
            all_drivers.append(driver_entry)
        
        logger.info(f"Added {len(all_drivers)} drivers from master employee list")
        
        # Step 3: Compute status for each driver
        driver_statuses = []
        
        for driver_entry in all_drivers:
            status_info = compute_driver_status(driver_entry, source_data)
            driver_statuses.append(status_info)
        
        # Step 4: Filter to include only drivers with GPS activity (do not use Start Time & Job for filtering)
        active_drivers = [d for d in driver_statuses if d['status'] not in ["No GPS Activity", "Unknown"]]
        
        # Step 5: Generate summary counts
        summary = {
            'date': date_str,
            'total': len(active_drivers),
            'late': sum(1 for d in active_drivers if d['status'] == 'Late'),
            'early_end': sum(1 for d in active_drivers if d['status'] == 'Early End'),
            'not_on_job': sum(1 for d in active_drivers if d['status'] == 'Not On Job'),
            'on_time': sum(1 for d in active_drivers if d['status'] == 'On Time'),
            'present': sum(1 for d in active_drivers if d['status'] == 'Present'),
            'unverified': sum(1 for d in active_drivers if d['status'] == 'Unverified')
        }
        
        # Step 6: Build final report data
        report_data = {
            'date': date_str,
            'drivers': active_drivers,
            'summary': summary,
            'metadata': {
                'processed_at': datetime.now().isoformat(),
                'source_files': source_data['metadata']['source_files'],
                'employee_count': source_data['metadata']['employee_count'],
                'job_assignment_count': source_data['metadata']['job_assignment_count'],
                'scheduled_times_count': source_data['metadata']['scheduled_times_count'],
                'row_counts': source_data['row_counts'],
                'inactive_drivers': len(driver_statuses) - len(active_drivers)
            }
        }
        
        logger.info(f"Generated report for {date_str} with {len(active_drivers)} active drivers")
        
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
    
    parser = argparse.ArgumentParser(description='TRAXORA Enhanced Genius Processor')
    parser.add_argument('date', help='Date to process in YYYY-MM-DD format')
    
    args = parser.parse_args()
    
    logger.info(f"Processing and exporting report for {args.date}")
    results = process_and_export(args.date)
    print(f"Results: {json.dumps(results, indent=2, default=str)}")

if __name__ == "__main__":
    main()