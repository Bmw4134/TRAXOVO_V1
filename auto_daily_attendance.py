#!/usr/bin/env python3
"""
TRAXORA Fleet Management System - Automatic Daily Attendance Processing

This script automatically generates attendance reports by processing the filtered driving data
for the previous day. It can be scheduled to run daily to ensure reports are always up-to-date.
"""

import os
import sys
import logging
import json
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'auto_attendance.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.process_filtered_data import process_filtered_data

def ensure_dirs():
    """Ensure all required directories exist"""
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    logger.info("Directory structure verified")

def get_yesterday_date():
    """Get yesterday's date string in YYYY-MM-DD format"""
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    return yesterday

def process_daily_attendance(date_str=None):
    """
    Process attendance for a specific date
    
    Args:
        date_str (str): Date to process in YYYY-MM-DD format
                        If None, process yesterday's data
    
    Returns:
        tuple: (json_path, excel_path) paths to the generated report files, or (None, None) if failed
    """
    try:
        # Get date to process
        if date_str is None:
            date_str = get_yesterday_date()
            
        logger.info(f"Processing attendance data for {date_str}")
        
        # Process filtered data - now returns both JSON and Excel paths
        json_path, excel_path = process_filtered_data(date_str)
        
        if json_path and excel_path:
            logger.info(f"Successfully generated attendance reports:")
            logger.info(f"  - JSON: {json_path}")
            logger.info(f"  - Excel: {excel_path}")
            return json_path, excel_path
        else:
            logger.error(f"Failed to generate one or more attendance reports for {date_str}")
            return None, None
            
    except Exception as e:
        logger.error(f"Error processing daily attendance: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None, None

def main():
    """Main function"""
    ensure_dirs()
    
    # Process command-line arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--yesterday':
        # Process yesterday's data
        date_to_process = get_yesterday_date()
    elif len(sys.argv) > 1 and sys.argv[1].startswith('--date='):
        # Process specific date
        date_to_process = sys.argv[1].split('=')[1]
    else:
        # Default to yesterday
        date_to_process = get_yesterday_date()
    
    # Process attendance data - now returns tuple of (json_path, excel_path)
    json_path, excel_path = process_daily_attendance(date_to_process)
    
    if json_path and excel_path:
        # Both reports generated successfully
        logger.info(f"Daily attendance processing completed successfully for {date_to_process}")
        logger.info(f"Reports available at:")
        logger.info(f"  - JSON: {json_path}")
        logger.info(f"  - Excel: {excel_path}")
        logger.info(f"  - Excel Report: reports/daily_driver_reports/DAILY_DRIVER_REPORT_{date_to_process.replace('-', '_')}.xlsx")
        # Return success
        sys.exit(0)
    else:
        # One or both reports failed
        logger.error(f"Daily attendance processing failed for {date_to_process}")
        # Return failure
        sys.exit(1)

if __name__ == "__main__":
    main()