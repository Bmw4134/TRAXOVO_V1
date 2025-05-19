#!/usr/bin/env python3
"""
Data Integration Script

This script serves as the entry point for data integration and synchronization,
automatically running the attendance data pipeline at scheduled intervals.
"""

import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import schedule

from utils.attendance_pipeline import run_attendance_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'data_integration.log'))
    ]
)
logger = logging.getLogger(__name__)

def run_integration():
    """Run the data integration process"""
    try:
        logger.info("Starting data integration process")
        
        # Ensure directories exist
        Path('data').mkdir(exist_ok=True)
        Path('logs').mkdir(exist_ok=True)
        Path('data/processed').mkdir(exist_ok=True)
        
        # Run attendance data pipeline
        processed_dates = run_attendance_pipeline()
        
        if processed_dates:
            logger.info(f"Successfully processed attendance data for dates: {', '.join(processed_dates)}")
        else:
            logger.info("No new attendance data processed")
        
        logger.info("Data integration process completed")
        return True
    except Exception as e:
        logger.error(f"Error in data integration process: {e}")
        return False

def schedule_jobs():
    """Schedule data integration jobs"""
    # Run the integration process every hour
    schedule.every().hour.do(run_integration)
    
    # Also run at specific times (e.g., after shift end)
    schedule.every().day.at("17:00").do(run_integration)  # 5 PM
    schedule.every().day.at("08:00").do(run_integration)  # 8 AM

    logger.info("Data integration jobs scheduled")
    logger.info("Next run times:")
    for job in schedule.get_jobs():
        logger.info(f" - {job}")

def main():
    """Main function"""
    logger.info("Starting data integration service")
    
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)
    
    # Run once at startup
    run_integration()
    
    # Schedule future runs
    schedule_jobs()
    
    # Keep the script running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Data integration service stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in data integration service: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())