"""
Data Audit and Parser Validation Module

This module provides functions to audit and validate the data parsing process
to ensure that raw source data is correctly ingested and processed.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime
import traceback

# Set up logging
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('logs/data_audit.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

def audit_source_data(source_path, source_type, date_str=None):
    """
    Audit the source data file to verify content and structure
    
    Args:
        source_path (str): Path to the source data file
        source_type (str): Type of source data (driving_history, activity_detail, start_time_job)
        date_str (str): Date to filter data for in YYYY-MM-DD format
        
    Returns:
        dict: Audit results with metadata and sample records
    """
    logger.info(f"Auditing {source_type} source data from {source_path}")
    
    results = {
        'source_file': source_path,
        'source_type': source_type,
        'date': date_str,
        'record_count': 0,
        'sample_records': [],
        'status': 'success',
        'errors': []
    }
    
    try:
        if source_path.endswith('.csv'):
            # Handle CSV files
            df = pd.read_csv(source_path)
            results['record_count'] = len(df)
            results['columns'] = df.columns.tolist()
            results['sample_records'] = df.head(5).to_dict('records')
            
            # Verify required columns based on source type
            required_columns = get_required_columns(source_type)
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                results['status'] = 'warning'
                results['errors'].append(f"Missing required columns: {missing_columns}")
                
        elif source_path.endswith('.xlsx'):
            # Handle Excel files
            df = pd.read_excel(source_path)
            results['record_count'] = len(df)
            results['columns'] = df.columns.tolist()
            results['sample_records'] = df.head(5).to_dict('records')
            
            # Verify required columns based on source type
            required_columns = get_required_columns(source_type)
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                results['status'] = 'warning'
                results['errors'].append(f"Missing required columns: {missing_columns}")
        
        # If date filter is provided, check data for that date
        if date_str:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            date_formatted = date_obj.strftime('%m/%d/%Y')
            
            # Check various date column formats
            date_columns = ['Date', 'DATE', 'date', 'Timestamp', 'TIMESTAMP']
            records_for_date = 0
            
            for col in date_columns:
                if col in df.columns:
                    date_records = df[df[col].astype(str).str.contains(date_str) | 
                                     df[col].astype(str).str.contains(date_formatted)]
                    records_for_date = len(date_records)
                    if records_for_date > 0:
                        results['records_for_date'] = records_for_date
                        results['sample_date_records'] = date_records.head(5).to_dict('records')
                        break
                    
            if records_for_date == 0:
                results['status'] = 'warning'
                results['errors'].append(f"No records found for date {date_str}")
    
    except Exception as e:
        results['status'] = 'error'
        results['errors'].append(str(e))
        logger.error(f"Error auditing {source_path}: {e}")
        logger.error(traceback.format_exc())
    
    # Save audit results for reference
    audit_dir = 'logs/audits'
    os.makedirs(audit_dir, exist_ok=True)
    audit_file = f"{audit_dir}/{source_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(audit_file, 'w') as f:
        # Remove sample records to reduce file size if too large
        audit_results = results.copy()
        if len(str(audit_results['sample_records'])) > 10000:
            audit_results['sample_records'] = audit_results['sample_records'][:2]
            audit_results['truncated'] = True
        
        json.dump(audit_results, f, indent=2, default=str)
    
    return results

def get_required_columns(source_type):
    """Get required columns based on source type"""
    if source_type == 'driving_history':
        return ['Asset', 'Driver', 'EventType', 'Timestamp']
    elif source_type == 'activity_detail':
        return ['Asset', 'Driver', 'StartTime', 'EndTime', 'Duration']
    elif source_type == 'start_time_job':
        return ['EmployeeName', 'JobNumber', 'StartTime', 'EndTime']
    else:
        return []

def validate_driver_record(driver_record, validation_rules=None):
    """
    Validate a driver record against defined rules
    
    Args:
        driver_record (dict): Driver record to validate
        validation_rules (dict): Rules to validate against
        
    Returns:
        dict: Validation results
    """
    if validation_rules is None:
        validation_rules = {
            'required_fields': [
                'name', 'asset', 'date', 'first_activity', 'last_activity'
            ],
            'time_constraints': {
                'min_first_activity': '03:00 AM',
                'max_last_activity': '08:00 PM'
            }
        }
    
    results = {
        'record': driver_record,
        'is_valid': True,
        'missing_fields': [],
        'validation_errors': []
    }
    
    # Check required fields
    for field in validation_rules['required_fields']:
        if field not in driver_record or not driver_record[field]:
            results['missing_fields'].append(field)
            results['is_valid'] = False
    
    # Validate time constraints if timestamps are available
    if 'first_activity' in driver_record and 'last_activity' in driver_record:
        try:
            # Convert timestamps to datetime objects for comparison
            if isinstance(driver_record['first_activity'], (int, float)) and driver_record['first_activity'] > 1000000000000:
                # Unix timestamp in milliseconds
                first_activity = datetime.fromtimestamp(driver_record['first_activity'] / 1000)
                last_activity = datetime.fromtimestamp(driver_record['last_activity'] / 1000)
                
                # Extract time components for constraints check
                first_activity_time = first_activity.strftime('%H:%M')
                last_activity_time = last_activity.strftime('%H:%M')
                
                # Check if times are within acceptable ranges
                min_time = datetime.strptime(validation_rules['time_constraints']['min_first_activity'], '%I:%M %p').strftime('%H:%M')
                max_time = datetime.strptime(validation_rules['time_constraints']['max_last_activity'], '%I:%M %p').strftime('%H:%M')
                
                if first_activity_time < min_time:
                    results['validation_errors'].append(f"First activity time {first_activity_time} is earlier than minimum {min_time}")
                    results['is_valid'] = False
                    
                if last_activity_time > max_time:
                    results['validation_errors'].append(f"Last activity time {last_activity_time} is later than maximum {max_time}")
                    results['is_valid'] = False
                    
        except Exception as e:
            results['validation_errors'].append(f"Error validating timestamps: {e}")
            results['is_valid'] = False
    
    # Log validation results
    if not results['is_valid']:
        log_msg = f"Driver record validation failed: {driver_record.get('name', 'Unknown Driver')}"
        if results['missing_fields']:
            log_msg += f", Missing fields: {results['missing_fields']}"
        if results['validation_errors']:
            log_msg += f", Errors: {results['validation_errors']}"
        logger.warning(log_msg)
    
    return results

def compare_pre_post_join(pre_join_data, post_join_data, date_str):
    """
    Compare driver data before and after joining different data sources
    
    Args:
        pre_join_data (list): Driver data before joining
        post_join_data (list): Driver data after joining
        date_str (str): Date of the data
        
    Returns:
        dict: Comparison results
    """
    results = {
        'date': date_str,
        'pre_join_count': len(pre_join_data),
        'post_join_count': len(post_join_data),
        'dropped_records': [],
        'modified_records': [],
        'sample_comparisons': []
    }
    
    # Create dictionaries for easier comparison
    pre_join_dict = {record.get('driver_name', ''): record for record in pre_join_data if 'driver_name' in record}
    post_join_dict = {record.get('driver_name', ''): record for record in post_join_data if 'driver_name' in record}
    
    # Find dropped records
    for driver_name, record in pre_join_dict.items():
        if driver_name not in post_join_dict:
            results['dropped_records'].append({
                'driver_name': driver_name,
                'pre_join_data': record
            })
    
    # Find modified records
    for driver_name, post_record in post_join_dict.items():
        if driver_name in pre_join_dict:
            pre_record = pre_join_dict[driver_name]
            
            # Collect fields that were modified during join
            modified_fields = {}
            for key in pre_record:
                if key in post_record and pre_record[key] != post_record[key]:
                    modified_fields[key] = {
                        'pre_join': pre_record[key],
                        'post_join': post_record[key]
                    }
            
            # Add new fields that were added during join
            for key in post_record:
                if key not in pre_record:
                    modified_fields[key] = {
                        'pre_join': None,
                        'post_join': post_record[key]
                    }
            
            if modified_fields:
                results['modified_records'].append({
                    'driver_name': driver_name,
                    'modified_fields': modified_fields
                })
    
    # Create sample comparisons for a few records
    max_samples = min(5, len(post_join_dict))
    sample_drivers = list(post_join_dict.keys())[:max_samples]
    
    for driver_name in sample_drivers:
        post_record = post_join_dict[driver_name]
        pre_record = pre_join_dict.get(driver_name, {})
        
        results['sample_comparisons'].append({
            'driver_name': driver_name,
            'pre_join': pre_record,
            'post_join': post_record
        })
    
    # Log results
    logger.info(f"Pre-post join comparison for {date_str}: {results['pre_join_count']} pre-join records, "
                f"{results['post_join_count']} post-join records")
    
    if results['dropped_records']:
        logger.warning(f"Dropped {len(results['dropped_records'])} records during join process")
        for record in results['dropped_records']:
            logger.warning(f"Dropped record: {record['driver_name']}")
    
    # Save comparison results
    audit_dir = 'logs/audits'
    os.makedirs(audit_dir, exist_ok=True)
    comparison_file = f"{audit_dir}/join_comparison_{date_str}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(comparison_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    return results

def audit_status_mapping(driver_records):
    """
    Audit the status mapping process (late/early/absent)
    
    Args:
        driver_records (list): Driver records with status mappings
        
    Returns:
        dict: Audit results
    """
    results = {
        'total_records': len(driver_records),
        'status_counts': {
            'On Time': 0,
            'Late': 0,
            'Early End': 0,
            'NOJ': 0,
            'Unknown': 0
        },
        'sample_records': {
            'On Time': [],
            'Late': [],
            'Early End': [],
            'NOJ': []
        }
    }
    
    # Count status types and collect samples
    for record in driver_records:
        status = record.get('status', 'Unknown')
        results['status_counts'][status] = results['status_counts'].get(status, 0) + 1
        
        # Add sample records for each status type (up to 2 samples per type)
        if status in results['sample_records'] and len(results['sample_records'][status]) < 2:
            results['sample_records'][status].append(record)
    
    logger.info(f"Status mapping audit: {results['status_counts']}")
    
    # Save audit results
    audit_dir = 'logs/audits'
    os.makedirs(audit_dir, exist_ok=True)
    audit_file = f"{audit_dir}/status_mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(audit_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    return results

def log_driver_data_sample(driver_data, label='Driver Data Sample'):
    """Utility function to log a sample of driver data"""
    sample_size = min(5, len(driver_data))
    sample = driver_data[:sample_size]
    
    logger.info(f"{label} ({len(driver_data)} total records, showing {sample_size}):")
    for i, driver in enumerate(sample):
        logger.info(f"  {i+1}. {driver.get('driver_name', 'Unknown')}: "
                   f"Asset={driver.get('asset', 'N/A')}, "
                   f"Status={driver.get('status', 'N/A')}, "
                   f"First Activity={driver.get('first_activity', 'N/A')}, "
                   f"Last Activity={driver.get('last_activity', 'N/A')}")
    
    return sample