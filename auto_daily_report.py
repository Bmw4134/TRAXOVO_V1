#!/usr/bin/env python3
"""
Auto Daily Report

This script automatically processes the Daily Driver Report for the current day.
It checks for input files and processes the report when all required files are available.
If files are not available by 7 PM, it will process with whatever data is available.
"""

import os
import sys
import time
import logging
import traceback
from datetime import datetime
from pathlib import Path

# Setup logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'auto_daily_report.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_input_files(date_str=None):
    """
    Check if input files are available for the specified date
    """
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    logger.info(f"Checking input files for {date_str}")
    
    # Check for required files
    activity_files = [f for f in os.listdir('attached_assets') if f.startswith('ActivityDetail')]
    driving_files = [f for f in os.listdir('attached_assets') if f.startswith('DrivingHistory')]
    asset_files = [f for f in os.listdir('attached_assets') if f.startswith('AssetsTimeOnSite') or f.startswith('FleetUtilization')]
    timecard_files = [f for f in os.listdir('attached_assets') if f.startswith('Timecards')]
    
    logger.info(f"Found {len(activity_files)} activity files")
    logger.info(f"Found {len(driving_files)} driving history files")
    logger.info(f"Found {len(asset_files)} asset/fleet files")
    logger.info(f"Found {len(timecard_files)} timecard files")
    
    # Check if all required files are available
    if len(activity_files) > 0 and len(driving_files) > 0:
        logger.info("All critical files are available")
        return True
    else:
        logger.warning("Not all critical files are available")
        if len(activity_files) == 0:
            logger.warning("Missing activity files")
        if len(driving_files) == 0:
            logger.warning("Missing driving history files")
        return False

def process_report(date_str=None, force=False):
    """
    Process the Daily Driver Report for the specified date
    """
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    logger.info(f"Processing Daily Driver Report for {date_str}")
    
    # Check if files are available
    files_ready = check_input_files(date_str)
    
    if not files_ready and not force:
        logger.warning(f"Cannot process report for {date_str} - required files not available")
        return False
    
    try:
        # Run the rebuild script
        from rebuild_attendance_data import main as rebuild_attendance
        
        # Save original argv
        original_argv = sys.argv.copy()
        
        # Set new argv
        sys.argv = ['rebuild_attendance_data.py', date_str]
        
        # Run rebuild
        rebuild_attendance()
        
        # Restore original argv
        sys.argv = original_argv
        
        logger.info(f"Successfully processed report for {date_str}")
        
        # Verify outputs
        source_xlsx = f'exports/daily_reports/daily_report_{date_str}.xlsx'
        source_pdf = f'exports/daily_reports/daily_report_{date_str}.pdf'
        
        target_xlsx = f'exports/daily_reports/{date_str}_DailyDriverReport.xlsx'
        target_pdf = f'exports/daily_reports/{date_str}_DailyDriverReport.pdf'
        
        # Copy files to required format if they exist
        if os.path.exists(source_xlsx):
            import shutil
            shutil.copy2(source_xlsx, target_xlsx)
            logger.info(f"Copied Excel report to {target_xlsx}")
        else:
            logger.error(f"Excel report not found: {source_xlsx}")
        
        if os.path.exists(source_pdf):
            import shutil
            shutil.copy2(source_pdf, target_pdf)
            logger.info(f"Copied PDF report to {target_pdf}")
        else:
            logger.warning(f"PDF report not found: {source_pdf}")
            
            # Try to create PDF directly
            try:
                from utils.attendance_pipeline_connector import get_attendance_data
                from utils.pdf_export import export_daily_report_to_pdf
                
                attendance_data = get_attendance_data(date_str, force_refresh=False)
                if attendance_data:
                    export_daily_report_to_pdf(attendance_data, target_pdf)
                    logger.info(f"Created PDF report directly: {target_pdf}")
                else:
                    logger.error(f"No attendance data available for {date_str}")
            except Exception as e:
                logger.error(f"Error creating PDF directly: {e}")
                traceback.print_exc()
        
        logger.info(f"Report processing complete for {date_str}")
        return True
    
    except Exception as e:
        logger.error(f"Error processing report: {e}")
        traceback.print_exc()
        return False

def main():
    """
    Main function
    """
    logger.info("Starting Auto Daily Report")
    
    # Set target date
    target_date = '2025-05-20'
    
    # Check for arguments
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    
    logger.info(f"Target date: {target_date}")
    
    # Get current time
    current_time = datetime.now()
    current_hour = current_time.hour
    
    logger.info(f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Current hour: {current_hour}")
    
    # Check file availability
    file_check_result = check_input_files(target_date)
    
    # Process based on time and file availability
    if current_hour >= 19 or file_check_result:
        # Either it's past 7 PM or all files are available
        force_mode = current_hour >= 19
        logger.info(f"Processing report with force={force_mode}")
        process_report(target_date, force=force_mode)
    else:
        logger.info("Files not available and it's before 7 PM, not processing report yet")
        logger.info("Will check again at 7 PM")
    
    logger.info("Auto Daily Report completed")

if __name__ == "__main__":
    main()
