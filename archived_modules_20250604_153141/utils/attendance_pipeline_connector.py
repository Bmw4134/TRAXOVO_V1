"""
Attendance Pipeline Connector

This module connects the various attendance data sources and provides a unified
interface for retrieving attendance data for a specific date.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Import the consistency engine for status determination
from utils.consistency_engine import compute_driver_status, build_driver_summary, generate_daily_report
from utils.data_audit import audit_source_data, compare_pre_post_join, audit_status_mapping, log_driver_data_sample

# Set up logging
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('logs/attendance_pipeline.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

# Define directories
DATA_DIR = "data"
EXPORTS_DIR = "exports"
LOG_DIR = "logs"
AUDIT_DIR = os.path.join(LOG_DIR, "audits")

# Ensure directories exist
for directory in [DATA_DIR, EXPORTS_DIR, LOG_DIR, AUDIT_DIR, 
                  os.path.join(EXPORTS_DIR, "daily_reports")]:
    os.makedirs(directory, exist_ok=True)

def get_source_data_paths(date_str=None):
    """
    Get paths to source data files for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        dict: Paths to source data files
    """
    # Find all relevant source files
    source_files = {
        'driving_history': [],
        'activity_detail': [],
        'start_time_job': []
    }
    
    # Look in the data directory and attached_assets directory
    search_dirs = ['data', 'attached_assets']
    
    for directory in search_dirs:
        if not os.path.exists(directory):
            continue
            
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            
            if not os.path.isfile(file_path):
                continue
                
            file_lower = file.lower()
            
            # Categorize file based on name
            if 'driving' in file_lower or 'gps' in file_lower:
                source_files['driving_history'].append(file_path)
                
            elif 'activity' in file_lower or 'detail' in file_lower:
                source_files['activity_detail'].append(file_path)
                
            elif 'start' in file_lower and ('time' in file_lower or 'job' in file_lower):
                source_files['start_time_job'].append(file_path)
    
    # Filter by date if provided
    if date_str:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        date_formats = [
            date_obj.strftime('%Y-%m-%d'),
            date_obj.strftime('%m/%d/%Y'),
            date_obj.strftime('%d_%m_%Y'),
            date_obj.strftime('%Y%m%d')
        ]
        
        # Filter each category
        for category in source_files:
            date_filtered = []
            
            for file_path in source_files[category]:
                # Check if any date format is in the filename
                for date_format in date_formats:
                    if date_format in file_path:
                        date_filtered.append(file_path)
                        break
            
            # Only use filtered list if it's not empty
            if date_filtered:
                source_files[category] = date_filtered
    
    return source_files

def load_assignment_data(date_str):
    """
    Load driver assignment data for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        dict: Driver assignments indexed by driver ID/name
    """
    assignments = {}
    
    # Get source file paths
    source_files = get_source_data_paths(date_str)
    
    # Load start time and job data
    for file_path in source_files['start_time_job']:
        try:
            # Audit the file
            audit_results = audit_source_data(file_path, 'start_time_job', date_str)
            
            if audit_results['status'] != 'success':
                logger.warning(f"Audit of {file_path} found issues: {audit_results['errors']}")
                continue
            
            # Process file and extract assignments
            # Note: The actual parsing code would depend on the file format
            
            # For now, use sample data as a placeholder
            sample_assignments = {
                # Sample data structure - would be populated from actual file
                '123456': {
                    'start_time': '06:30 AM',
                    'end_time': '03:30 PM',
                    'assigned_site': 'Job Site A',
                    'job_number': 'J12345'
                }
            }
            
            # Merge with assignments dictionary
            assignments.update(sample_assignments)
            
        except Exception as e:
            logger.error(f"Error loading assignment data from {file_path}: {e}")
    
    return assignments

def load_telematics_data(date_str):
    """
    Load telematics data for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        dict: Telematics data indexed by driver ID/name
    """
    telematics_data = {}
    
    # Get source file paths
    source_files = get_source_data_paths(date_str)
    
    # Load driving history data
    for file_path in source_files['driving_history']:
        try:
            # Audit the file
            audit_results = audit_source_data(file_path, 'driving_history', date_str)
            
            if audit_results['status'] != 'success':
                logger.warning(f"Audit of {file_path} found issues: {audit_results['errors']}")
                continue
            
            # Process file and extract telematics data
            # Note: The actual parsing code would depend on the file format
            
            # For now, use a placeholder method to parse driving history
            driving_data = parse_driving_history(file_path, date_str)
            
            # Merge with telematics data dictionary
            for driver_id, data in driving_data.items():
                if driver_id not in telematics_data:
                    telematics_data[driver_id] = data
                else:
                    # Merge data if driver already exists
                    merged_data = telematics_data[driver_id].copy()
                    merged_data.update(data)
                    telematics_data[driver_id] = merged_data
            
        except Exception as e:
            logger.error(f"Error loading driving history data from {file_path}: {e}")
    
    # Load activity detail data
    for file_path in source_files['activity_detail']:
        try:
            # Audit the file
            audit_results = audit_source_data(file_path, 'activity_detail', date_str)
            
            if audit_results['status'] != 'success':
                logger.warning(f"Audit of {file_path} found issues: {audit_results['errors']}")
                continue
            
            # Process file and extract activity data
            # Note: The actual parsing code would depend on the file format
            
            # For now, use a placeholder method to parse activity detail
            activity_data = parse_activity_detail(file_path, date_str)
            
            # Merge with telematics data dictionary
            for driver_id, data in activity_data.items():
                if driver_id not in telematics_data:
                    telematics_data[driver_id] = data
                else:
                    # Merge data if driver already exists
                    merged_data = telematics_data[driver_id].copy()
                    merged_data.update(data)
                    telematics_data[driver_id] = merged_data
            
        except Exception as e:
            logger.error(f"Error loading activity detail data from {file_path}: {e}")
    
    return telematics_data

def get_driver_list(date_str):
    """
    Get consolidated list of drivers for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        list: List of driver records
    """
    # Get assignment and telematics data
    assignment_data = load_assignment_data(date_str)
    telematics_data = load_telematics_data(date_str)
    
    # Combine driver lists from both sources
    all_driver_ids = set(assignment_data.keys()).union(set(telematics_data.keys()))
    
    # Create driver records
    drivers = []
    
    for driver_id in all_driver_ids:
        driver_record = {
            'employee_id': driver_id
        }
        
        # Add data from assignment if available
        if driver_id in assignment_data:
            assignment = assignment_data[driver_id]
            driver_record.update({
                'name': assignment.get('driver_name', f"Driver {driver_id}"),
                'asset': assignment.get('asset', 'Unknown'),
                'job_site': assignment.get('assigned_site', 'Unknown')
            })
        
        # Add data from telematics if available
        if driver_id in telematics_data:
            telematics = telematics_data[driver_id]
            
            # Only update fields that aren't already set
            for field in ['name', 'asset', 'job_site']:
                if field not in driver_record or not driver_record[field] or driver_record[field] == 'Unknown':
                    driver_record[field] = telematics.get(field, driver_record.get(field, 'Unknown'))
        
        drivers.append(driver_record)
    
    return drivers

def parse_driving_history(file_path, date_str):
    """
    Parse driving history data from a file
    
    Args:
        file_path (str): Path to driving history file
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        dict: Driving history data indexed by driver ID
    """
    # For testing/placeholder purposes, return a sample result
    # This would be replaced with actual parsing logic for the specific file format
    return {
        '123456': {
            'first_activity': '06:45 AM',
            'last_activity': '03:15 PM',
            'job_site': 'Job Site A',
            'total_driving_time': 120,  # minutes
            'idle_time': 30  # minutes
        },
        '234567': {
            'first_activity': '07:15 AM',
            'last_activity': '02:45 PM',
            'job_site': 'Job Site B',
            'total_driving_time': 90,
            'idle_time': 45
        }
    }

def parse_activity_detail(file_path, date_str):
    """
    Parse activity detail data from a file
    
    Args:
        file_path (str): Path to activity detail file
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        dict: Activity data indexed by driver ID
    """
    # For testing/placeholder purposes, return a sample result
    # This would be replaced with actual parsing logic for the specific file format
    return {
        '123456': {
            'num_trips': 5,
            'num_stops': 7,
            'first_activity': '06:45 AM',
            'last_activity': '03:15 PM'
        },
        '234567': {
            'num_trips': 3,
            'num_stops': 4,
            'first_activity': '07:15 AM',
            'last_activity': '02:45 PM'
        }
    }

def process_attendance_data(date_str):
    """
    Process attendance data for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        dict: Processed attendance data with driver statuses
    """
    logger.info(f"Processing attendance data for {date_str}")
    
    try:
        # Get assignment and telematics data
        assignment_data = load_assignment_data(date_str)
        telematics_data = load_telematics_data(date_str)
        
        # Get driver list
        drivers = get_driver_list(date_str)
        
        # Pre-join data - save for audit
        pre_join_data = drivers.copy()
        
        # Build driver summary
        driver_summary = build_driver_summary(drivers, assignment_data, telematics_data)
        
        # Post-join data - for comparison
        post_join_data = driver_summary['driver_summary']
        
        # Audit join process
        compare_pre_post_join(pre_join_data, post_join_data, date_str)
        
        # Audit status mapping
        audit_status_mapping(post_join_data)
        
        # Generate daily report
        daily_report = generate_daily_report(date_str, driver_summary)
        
        # Return the processed data
        return daily_report
        
    except Exception as e:
        logger.error(f"Error processing attendance data for {date_str}: {e}")
        return None

def load_attendance_data(date_str):
    """
    Load processed attendance data for a specific date from cache/file
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        dict: Processed attendance data
    """
    # Check if we have a cached report
    report_path = f"exports/daily_reports/daily_report_{date_str}.json"
    
    if os.path.exists(report_path):
        try:
            with open(report_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cached report: {e}")
    
    # Process data if no cached report
    return process_attendance_data(date_str)

def get_attendance_data(date_str=None):
    """
    Get attendance data for a specific date or the current date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format or None for current date
        
    Returns:
        dict: Attendance data for the specified date
    """
    # Use current date if not specified
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # First check if we have the data in cache
    attendance_data = load_attendance_data(date_str)
    
    # If no data found, process new data
    if not attendance_data:
        attendance_data = process_attendance_data(date_str)
    
    # Log results
    if attendance_data:
        logger.info(f"Retrieved attendance data for {date_str}: "
                   f"{attendance_data['summary']['total_drivers']} total drivers, "
                   f"{attendance_data['summary']['late_drivers']} late, "
                   f"{attendance_data['summary']['early_end_drivers']} early end, "
                   f"{attendance_data['summary']['not_on_job_drivers']} not on job")
    else:
        logger.error(f"Failed to retrieve attendance data for {date_str}")
    
    return attendance_data

def get_trend_data(start_date=None, end_date=None, days=7):
    """
    Get attendance trend data for a date range
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format or None for (end_date - days)
        end_date (str): End date in YYYY-MM-DD format or None for current date
        days (int): Number of days to include if start_date is None
        
    Returns:
        dict: Trend data for the date range
    """
    # Use current date if end_date not specified
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
        
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Calculate start_date if not specified
    if not start_date:
        start_date_obj = end_date_obj - timedelta(days=days)
        start_date = start_date_obj.strftime('%Y-%m-%d')
    else:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    
    # Generate date range
    date_range = []
    current_date = start_date_obj
    while current_date <= end_date_obj:
        date_range.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    # Initialize trend data
    trend_data = {
        'dates': date_range,
        'late_counts': [],
        'early_end_counts': [],
        'not_on_job_counts': [],
        'total_drivers': []
    }
    
    # Populate with attendance data for each date
    for date_str in date_range:
        attendance_data = get_attendance_data(date_str)
        
        if attendance_data:
            trend_data['late_counts'].append(attendance_data['summary']['late_drivers'])
            trend_data['early_end_counts'].append(attendance_data['summary']['early_end_drivers'])
            trend_data['not_on_job_counts'].append(attendance_data['summary']['not_on_job_drivers'])
            trend_data['total_drivers'].append(attendance_data['summary']['total_drivers'])
        else:
            # Use zeros if no data available
            trend_data['late_counts'].append(0)
            trend_data['early_end_counts'].append(0)
            trend_data['not_on_job_counts'].append(0)
            trend_data['total_drivers'].append(0)
    
    return trend_data

def get_audit_record(date_str):
    """
    Get audit record for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        dict: Audit record for the date
    """
    # Look for audit files for this date
    audit_dir = os.path.join(LOG_DIR, "audits")
    audit_record = {
        'date': date_str,
        'source_files': [],
        'processing_steps': [],
        'errors': []
    }
    
    # Find all audit files for this date
    for filename in os.listdir(audit_dir):
        if date_str in filename:
            file_path = os.path.join(audit_dir, filename)
            
            try:
                with open(file_path, 'r') as f:
                    audit_data = json.load(f)
                    
                # Extract source file information
                if 'source_file' in audit_data:
                    if audit_data['source_file'] not in [source['path'] for source in audit_record['source_files']]:
                        audit_record['source_files'].append({
                            'path': audit_data['source_file'],
                            'type': audit_data.get('source_type', 'Unknown'),
                            'record_count': audit_data.get('record_count', 0),
                            'status': audit_data.get('status', 'Unknown')
                        })
                
                # Extract processing steps
                if 'status' in audit_data:
                    audit_record['processing_steps'].append({
                        'step': filename.split('_')[0],
                        'status': audit_data['status'],
                        'timestamp': filename.split('_')[-1].replace('.json', '')
                    })
                
                # Extract errors
                if 'errors' in audit_data and audit_data['errors']:
                    audit_record['errors'].extend(audit_data['errors'])
                    
            except Exception as e:
                logger.error(f"Error reading audit file {file_path}: {e}")
    
    return audit_record