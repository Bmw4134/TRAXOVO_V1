#!/usr/bin/env python3
"""
TRAXORA Fleet Management System - Automatic Daily Attendance Processing

This script automatically generates attendance reports by processing the filtered driving data
for the previous day. It can be scheduled to run daily to ensure reports are always up-to-date.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_attendance.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import legacy formula connector
from utils.legacy_formula_connector import process_daily_driver_report

def ensure_dirs():
    """Ensure all required directories exist"""
    os.makedirs('data', exist_ok=True)
    os.makedirs('reports/daily_driver_reports', exist_ok=True)
    os.makedirs('exports/daily', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

def get_yesterday_date():
    """Get yesterday's date string in YYYY-MM-DD format"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')

def process_daily_attendance(date_str=None):
    """
    Process attendance for a specific date
    
    Args:
        date_str (str): Date to process in YYYY-MM-DD format
                        If None, process yesterday's data
    
    Returns:
        tuple: (json_path, excel_path) paths to the generated report files, or (None, None) if failed
    """
    # Ensure directories exist
    ensure_dirs()
    
    # Use yesterday's date if not specified
    if date_str is None:
        date_str = get_yesterday_date()
    
    logger.info(f"Processing daily attendance for date: {date_str}")
    
    # Find potential data files for the specified date
    data_dir = 'data'
    driving_history_file = None
    activity_detail_file = None
    assets_time_file = None
    
    # First, look for files with date in the name
    for filename in os.listdir(data_dir):
        file_path = os.path.join(data_dir, filename)
        if date_str in filename:
            if 'driving' in filename.lower() or 'history' in filename.lower():
                driving_history_file = file_path
            elif 'activity' in filename.lower() or 'detail' in filename.lower():
                activity_detail_file = file_path
            elif 'assets' in filename.lower() or 'time' in filename.lower() or 'site' in filename.lower():
                assets_time_file = file_path
    
    # If no files found with date in name, look for any recent files
    if not driving_history_file and not activity_detail_file and not assets_time_file:
        logger.info(f"No date-specific files found for {date_str}, looking for recent files")
        
        for filename in os.listdir(data_dir):
            file_path = os.path.join(data_dir, filename)
            file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            # Check if file was modified within the last 7 days
            if (datetime.now() - file_modified).days <= 7:
                if 'driving' in filename.lower() or 'history' in filename.lower():
                    driving_history_file = file_path
                elif 'activity' in filename.lower() or 'detail' in filename.lower():
                    activity_detail_file = file_path
                elif 'assets' in filename.lower() or 'time' in filename.lower() or 'site' in filename.lower():
                    assets_time_file = file_path
    
    # If still no files found, check attached_assets directory
    if not driving_history_file and not activity_detail_file and not assets_time_file:
        logger.info(f"No recent files found in data directory, checking attached_assets")
        attached_dir = 'attached_assets'
        
        if os.path.exists(attached_dir):
            for filename in os.listdir(attached_dir):
                file_path = os.path.join(attached_dir, filename)
                if 'driving' in filename.lower() or 'history' in filename.lower():
                    driving_history_file = file_path
                elif 'activity' in filename.lower() or 'detail' in filename.lower():
                    activity_detail_file = file_path
                elif 'assets' in filename.lower() or 'time' in filename.lower() or 'site' in filename.lower():
                    assets_time_file = file_path
    
    # Log found files
    logger.info(f"Found driving history file: {driving_history_file}")
    logger.info(f"Found activity detail file: {activity_detail_file}")
    logger.info(f"Found assets time file: {assets_time_file}")
    
    # Process report if at least one file was found
    if driving_history_file or activity_detail_file or assets_time_file:
        try:
            # Process the daily driver report
            result = process_daily_driver_report(
                date_str=date_str,
                driving_history_file=driving_history_file,
                activity_detail_file=activity_detail_file,
                assets_time_file=assets_time_file
            )
            
            if result.get('success', False):
                logger.info(f"Successfully processed daily attendance for {date_str}")
                return (result.get('json_report'), result.get('excel_report'))
            else:
                logger.error(f"Failed to process daily attendance: {result.get('error', 'Unknown error')}")
                return (None, None)
        
        except Exception as e:
            logger.error(f"Error processing daily attendance: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return (None, None)
    
    else:
        logger.error(f"No data files found for date: {date_str}")
        return (None, None)

def main():
    """Main function"""
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = get_yesterday_date()
    
    json_path, excel_path = process_daily_attendance(date_str)
    
    if json_path and excel_path:
        print(f"Successfully processed daily attendance for {date_str}")
        print(f"JSON report saved to: {json_path}")
        print(f"Excel report saved to: {excel_path}")
        return 0
    else:
        print(f"Failed to process daily attendance for {date_str}")
        return 1

if __name__ == "__main__":
    sys.exit(main())