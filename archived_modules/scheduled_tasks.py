#!/usr/bin/env python3
"""
Scheduled Tasks for TRAXORA

This script runs scheduled tasks for the TRAXORA system.
It checks for input files hourly and processes the daily report at 7 PM.
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'scheduled_tasks.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_auto_daily_report():
    """
    Run the auto daily report script
    """
    logger.info("Running auto daily report script")
    
    try:
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Run the script
        os.system(f"python auto_daily_report.py {today}")
        
        logger.info("Auto daily report script completed")
    except Exception as e:
        logger.error(f"Error running auto daily report script: {e}")
        import traceback
        logger.error(traceback.format_exc())

def check_hourly():
    """
    Check for input files hourly
    """
    logger.info("Running hourly check for input files")
    
    try:
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Check current hour
        current_hour = datetime.now().hour
        
        # Import the check function directly
        from auto_daily_report import check_input_files
        
        # Check for files
        files_available = check_input_files(today)
        
        logger.info(f"Files available: {files_available}")
        
        # If files are available, process the report
        if files_available:
            logger.info("All required files are available, processing report")
            from auto_daily_report import process_report
            process_report(today)
        else:
            logger.info("Not all required files are available")
            
            # If it's 7 PM or later, process anyway
            if current_hour >= 19:
                logger.info("It's 7 PM or later, processing report anyway")
                from auto_daily_report import process_report
                process_report(today, force=True)
    
    except Exception as e:
        logger.error(f"Error in hourly check: {e}")
        import traceback
        logger.error(traceback.format_exc())

def main():
    """
    Main function - runs scheduled tasks
    """
    logger.info("Starting scheduled tasks")
    
    # Get current time
    current_time = datetime.now()
    logger.info(f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run initial check
    check_hourly()
    
    # Schedule tasks to run at specific times
    while True:
        # Get current time
        current_time = datetime.now()
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        # Check if it's time to run hourly check (at the top of each hour)
        if current_minute == 0:
            logger.info(f"Running hourly check at {current_hour}:00")
            check_hourly()
        
        # Check if it's 7 PM
        if current_hour == 19 and current_minute == 0:
            logger.info("It's 7 PM, running daily report")
            run_auto_daily_report()
        
        # Sleep for a minute
        time.sleep(60)

if __name__ == "__main__":
    main()
