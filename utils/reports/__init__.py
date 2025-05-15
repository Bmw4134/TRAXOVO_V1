"""
Reports Utility Module

This module handles the generation of daily and periodic reports, including:
- Prior day attendance reports (Late Start, Early End, Not On Job)
- Current day early status reports (Late Start, Not On Job)
- Billing comparison and validation reports
- Region-based billing export generation
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from pathlib import Path

from app import db
from models import Asset

# Initialize logger
logger = logging.getLogger(__name__)

def ensure_report_dirs():
    """Ensure all necessary report directories exist"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Create base report directories
    os.makedirs(f'reports/{today}', exist_ok=True)
    os.makedirs('exports/billings', exist_ok=True)
    os.makedirs(f'exports/billings/{today}', exist_ok=True)
    
    return {
        'daily_reports': f'reports/{today}',
        'billing_exports': f'exports/billings/{today}'
    }

def get_latest_activity_files():
    """
    Find the most recently uploaded activity detail and driving history files
    
    Returns:
        dict: Dictionary with paths to the latest files
    """
    try:
        # This is a placeholder - in production we would actually scan the uploads directory
        # and find the most recent files based on upload or file date
        
        latest_files = {
            'activity_detail': 'uploads/activity_detail/latest.xlsx',
            'driving_history': 'uploads/driving_history/latest.xlsx',
            'last_updated': datetime.now()
        }
        
        # Check if files exist
        missing_files = []
        for key, path in latest_files.items():
            if key != 'last_updated' and not os.path.exists(path):
                missing_files.append(key)
        
        if missing_files:
            logger.warning(f"Missing expected input files: {', '.join(missing_files)}")
            latest_files['status'] = 'incomplete'
            latest_files['missing'] = missing_files
        else:
            latest_files['status'] = 'complete'
            
        return latest_files
    except Exception as e:
        logger.error(f"Error identifying latest activity files: {e}")
        return {'status': 'error', 'message': str(e)}

def get_latest_billing_files():
    """
    Find the most recently uploaded billing files
    
    Returns:
        dict: Dictionary with paths to the latest files
    """
    try:
        # This is a placeholder - in production we would scan the uploads directory
        
        latest_files = {
            'original_billing': 'attached_assets/RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm',
            'edited_billing': 'attached_assets/EQMO. BILLING ALLOCATIONS - APRIL 2025 (TR-FINAL REVISIONS BY 05.15.2025).xlsx',
            'last_updated': datetime.now()
        }
        
        # Check if files exist
        missing_files = []
        for key, path in latest_files.items():
            if key != 'last_updated' and not os.path.exists(path):
                missing_files.append(key)
        
        if missing_files:
            logger.warning(f"Missing expected billing files: {', '.join(missing_files)}")
            latest_files['status'] = 'incomplete'
            latest_files['missing'] = missing_files
        else:
            latest_files['status'] = 'complete'
            
        return latest_files
    except Exception as e:
        logger.error(f"Error identifying latest billing files: {e}")
        return {'status': 'error', 'message': str(e)}

def generate_prior_day_report():
    """
    Generate the prior day Late Start, Early End, Not On Job report
    
    This report analyzes yesterday's data for the full day (12:01 AM - 11:59 PM)
    
    Returns:
        dict: Report generation status and path
    """
    try:
        # Ensure report directories exist
        dirs = ensure_report_dirs()
        
        # Get latest activity files
        files = get_latest_activity_files()
        if files['status'] != 'complete':
            return {'status': 'error', 'message': 'Missing required input files'}
            
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        report_path = f"{dirs['daily_reports']}/prior_day_attendance_{yesterday}.xlsx"
        
        # Log the process
        logger.info(f"Generating prior day report for {yesterday}")
        
        # Import here to avoid circular imports
        from utils.attendance_processor import process_prior_day_attendance, create_attendance_excel
        
        # Process attendance data
        attendance_data = process_prior_day_attendance(yesterday)
        if attendance_data['status'] != 'success':
            return {'status': 'error', 'message': attendance_data.get('message', 'Failed to process attendance data')}
        
        # Create Excel report
        excel_path = create_attendance_excel(attendance_data, 'prior_day')
        if not excel_path:
            return {'status': 'error', 'message': 'Failed to create Excel report'}
        
        # Log success
        logger.info(f"Prior day attendance report saved to {excel_path}")
        
        return {
            'status': 'success',
            'path': excel_path,
            'date': yesterday,
            'summary': attendance_data['data']['summary']
        }
    except Exception as e:
        logger.error(f"Error generating prior day report: {e}")
        return {'status': 'error', 'message': str(e)}

def generate_current_day_report():
    """
    Generate the current day Late Start, Not On Job report
    
    This report analyzes the current day's data up to 8:30 AM
    
    Returns:
        dict: Report generation status and path
    """
    try:
        # Ensure report directories exist
        dirs = ensure_report_dirs()
        
        # Get latest activity files
        files = get_latest_activity_files()
        if files['status'] != 'complete':
            return {'status': 'error', 'message': 'Missing required input files'}
            
        today = datetime.now().strftime('%Y-%m-%d')
        report_path = f"{dirs['daily_reports']}/current_day_attendance_{today}.xlsx"
        
        # Log the process
        logger.info(f"Generating current day report for {today} (as of 8:30 AM)")
        
        # Import here to avoid circular imports
        from utils.attendance_processor import process_current_day_attendance, create_attendance_excel
        
        # Process attendance data
        attendance_data = process_current_day_attendance()
        if attendance_data['status'] != 'success':
            return {'status': 'error', 'message': attendance_data.get('message', 'Failed to process attendance data')}
        
        # Create Excel report
        excel_path = create_attendance_excel(attendance_data, 'current_day')
        if not excel_path:
            return {'status': 'error', 'message': 'Failed to create Excel report'}
        
        # Log success
        logger.info(f"Current day attendance report saved to {excel_path}")
        
        return {
            'status': 'success',
            'path': excel_path,
            'date': today,
            'report_time': attendance_data.get('report_time', '8:30 AM'),
            'summary': attendance_data['data']['summary']
        }
    except Exception as e:
        logger.error(f"Error generating current day report: {e}")
        return {'status': 'error', 'message': str(e)}

def compare_billing_files():
    """
    Compare original and edited billing files to identify changes
    
    Returns:
        dict: Comparison results with changes identified
    """
    try:
        # Get latest billing files
        files = get_latest_billing_files()
        if files['status'] != 'complete':
            return {'status': 'error', 'message': 'Missing required billing files'}
            
        logger.info("Comparing original and edited billing files")
        
        # Import here to avoid circular imports
        from utils.billing_processor import load_billing_files, compare_billing_data, create_comparison_report
        
        # Load billing files
        original_df, edited_df = load_billing_files(files['original_billing'], files['edited_billing'])
        if original_df is None or edited_df is None:
            return {'status': 'error', 'message': 'Failed to load billing files'}
        
        # Compare billing data
        comparison_result = compare_billing_data(original_df, edited_df)
        if comparison_result['status'] != 'success':
            return {'status': 'error', 'message': comparison_result.get('message', 'Comparison failed')}
        
        # Create comparison report
        report_path = create_comparison_report(comparison_result, 'APRIL')
        if not report_path:
            return {'status': 'error', 'message': 'Failed to create comparison report'}
        
        # Return comparison results with report path
        comparison_result['report_path'] = report_path
        return comparison_result
    except Exception as e:
        logger.error(f"Error comparing billing files: {e}")
        return {'status': 'error', 'message': str(e)}

def generate_region_billing_exports(approved_changes=None):
    """
    Generate region-based billing exports after approval
    
    Args:
        approved_changes (dict): Changes approved by the user
    
    Returns:
        dict: Export status and paths
    """
    try:
        # Ensure export directories exist
        dirs = ensure_report_dirs()
        
        # Get latest billing files
        files = get_latest_billing_files()
        if files['status'] != 'complete':
            return {'status': 'error', 'message': 'Missing required billing files'}
            
        logger.info("Generating region-based billing exports")
        
        # Import here to avoid circular imports
        from utils.billing_processor import generate_all_region_exports
        
        # Generate exports for all regions
        result = generate_all_region_exports(files['edited_billing'], 'APRIL', '2025')
        if result['status'] != 'success':
            return {'status': 'error', 'message': result.get('message', 'Export generation failed')}
        
        logger.info(f"Successfully generated region exports: {list(result['exports'].keys())}")
        
        return {
            'status': 'success',
            'exports': result['exports']
        }
    except Exception as e:
        logger.error(f"Error generating region billing exports: {e}")
        return {'status': 'error', 'message': str(e)}

def run_daily_reports():
    """
    Run all daily reports
    
    Returns:
        dict: Status of all report generation processes
    """
    results = {
        'prior_day': generate_prior_day_report(),
        'current_day': generate_current_day_report()
    }
    
    # Log overall status
    all_successful = all(result['status'] == 'success' for result in results.values())
    if all_successful:
        logger.info("All daily reports generated successfully")
    else:
        logger.warning("Some daily reports failed to generate")
        
    return results