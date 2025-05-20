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

# Import unified data processor
from utils.unified_data_processor import UnifiedDataProcessor
from utils.attendance_audit import get_audit_record

# Set up logging
logger = logging.getLogger(__name__)

def get_attendance_data(date_str, force_refresh=False):
    """
    Get attendance data for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        force_refresh (bool): Force refresh of data
        
    Returns:
        dict: Attendance data
    """
    # Check if data already exists in exports directory
    json_path = Path(f"exports/daily_reports/attendance_data_{date_str}.json")
    
    # Return existing data if available and not forcing refresh
    if not force_refresh and json_path.exists():
        try:
            with open(json_path, 'r') as f:
                attendance_data = json.load(f)
                logger.info(f"Loaded existing attendance data for {date_str}")
                return attendance_data
        except Exception as e:
            logger.error(f"Error loading attendance data: {e}")
    
    # If force refresh or data doesn't exist, process data
    try:
        logger.info(f"Processing attendance data for {date_str}")
        
        # Check if audit record exists
        audit_record = get_audit_record(date_str)
        
        # If audit record exists and is completed, use source files from audit
        if audit_record and audit_record.get('status') == 'completed':
            logger.info(f"Using source files from audit record for {date_str}")
            
            # Create processor
            processor = UnifiedDataProcessor(date_str)
            
            # Process source files from audit record
            for source_file in audit_record.get('sources', []):
                file_path = source_file.get('path')
                file_type = source_file.get('type')
                
                if not file_path or not os.path.exists(file_path):
                    continue
                
                if file_type == 'driving_history':
                    processor.process_driving_history(file_path)
                elif file_type == 'activity_detail':
                    processor.process_activity_detail(file_path)
                elif file_type == 'asset_onsite':
                    processor.process_asset_onsite(file_path)
                elif file_type == 'start_time_job':
                    processor.process_start_time_job_sheet(file_path)
                elif file_type == 'employee_data':
                    processor.process_employee_data(file_path)
            
            # Generate attendance report
            processor.generate_attendance_report()
            
            # Export Excel and PDF
            processor.export_excel_report()
            processor.export_pdf_report()
        else:
            # Find and process files
            logger.info(f"Finding files for {date_str}")
            
            # Create processor
            processor = UnifiedDataProcessor(date_str)
            
            # Find available files
            assets_dir = Path('attached_assets')
            for file_path in assets_dir.glob('*'):
                file_name = file_path.name
                
                # Skip directories and hidden files
                if not file_path.is_file() or file_name.startswith('.'):
                    continue
                
                file_path_str = str(file_path)
                
                if 'DrivingHistory' in file_name:
                    processor.process_driving_history(file_path_str)
                
                elif 'ActivityDetail' in file_name:
                    processor.process_activity_detail(file_path_str)
                
                elif 'AssetsTimeOnSite' in file_name or 'FleetUtilization' in file_name:
                    processor.process_asset_onsite(file_path_str)
                
                elif 'ELIST' in file_name or 'Employee' in file_name:
                    processor.process_employee_data(file_path_str)
                
                elif 'DAILY' in file_name and ('NOJ' in file_name or 'REPORT' in file_name) and file_name.endswith('.xlsx'):
                    processor.process_start_time_job_sheet(file_path_str)
            
            # Generate attendance report
            processor.generate_attendance_report()
            
            # Export Excel and PDF
            processor.export_excel_report()
            processor.export_pdf_report()
        
        # Load generated data
        if json_path.exists():
            with open(json_path, 'r') as f:
                attendance_data = json.load(f)
                logger.info(f"Loaded newly generated attendance data for {date_str}")
                return attendance_data
        else:
            raise Exception(f"Failed to generate attendance data for {date_str}")
    
    except Exception as e:
        logger.error(f"Error processing attendance data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Return empty data
        return {
            'date': date_str,
            'status': 'error',
            'error': str(e),
            'total_drivers': 0,
            'drivers': [],
            'late_start_records': [],
            'early_end_records': [],
            'not_on_job_records': []
        }

def get_date_range_data(start_date, end_date, force_refresh=False):
    """
    Get attendance data for a date range
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        force_refresh (bool): Force refresh of data
        
    Returns:
        list: List of attendance data for each date
    """
    # Convert to datetime objects
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Generate date range
    date_range = []
    current_date = start_date_obj
    while current_date <= end_date_obj:
        date_range.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    # Get data for each date
    results = []
    for date_str in date_range:
        attendance_data = get_attendance_data(date_str, force_refresh)
        results.append(attendance_data)
    
    return results

def regenerate_all_reports(date_list=None):
    """
    Regenerate all reports for the specified dates
    
    Args:
        date_list (list): List of dates to regenerate
        
    Returns:
        dict: Results of regeneration
    """
    if date_list is None:
        # Default to May 15-20, 2025
        date_list = [
            '2025-05-15',
            '2025-05-16',
            '2025-05-17',
            '2025-05-18',
            '2025-05-19',
            '2025-05-20'
        ]
    
    results = {}
    
    # Process each date
    for date_str in date_list:
        logger.info(f"Regenerating report for {date_str}")
        
        try:
            # Force refresh
            attendance_data = get_attendance_data(date_str, force_refresh=True)
            
            # Check success
            if attendance_data and 'error' not in attendance_data:
                results[date_str] = {
                    'status': 'success',
                    'total_drivers': attendance_data.get('total_drivers', 0),
                    'late_count': len(attendance_data.get('late_start_records', [])),
                    'early_count': len(attendance_data.get('early_end_records', [])),
                    'missing_count': len(attendance_data.get('not_on_job_records', []))
                }
            else:
                results[date_str] = {
                    'status': 'error',
                    'error': attendance_data.get('error', 'Unknown error')
                }
        
        except Exception as e:
            logger.error(f"Error regenerating report for {date_str}: {e}")
            results[date_str] = {
                'status': 'error',
                'error': str(e)
            }
    
    return results

def get_audit_summary():
    """
    Get summary of audit records
    
    Returns:
        dict: Audit summary
    """
    # Get audit directory
    audit_dir = Path('logs/attendance')
    
    # Check if directory exists
    if not audit_dir.exists():
        return {
            'status': 'error',
            'error': 'Audit directory does not exist',
            'dates': []
        }
    
    # Find audit files
    audit_files = list(audit_dir.glob('*_audit.json'))
    
    # Extract dates from filenames
    dates = []
    for audit_file in audit_files:
        try:
            # Extract date from filename
            date_str = audit_file.name.split('_')[0]
            
            # Load audit record
            with open(audit_file, 'r') as f:
                audit_record = json.load(f)
            
            # Add date to list
            dates.append({
                'date': date_str,
                'status': audit_record.get('status', 'unknown'),
                'total_drivers': audit_record.get('stats', {}).get('total_drivers', 0),
                'late_drivers': audit_record.get('stats', {}).get('late_drivers', 0),
                'early_end_drivers': audit_record.get('stats', {}).get('early_end_drivers', 0),
                'on_time_percent': audit_record.get('stats', {}).get('on_time_percent', 0)
            })
        except Exception as e:
            logger.error(f"Error processing audit file {audit_file}: {e}")
    
    # Sort dates
    dates.sort(key=lambda x: x['date'])
    
    return {
        'status': 'success',
        'total_dates': len(dates),
        'dates': dates
    }