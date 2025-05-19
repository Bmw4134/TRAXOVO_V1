#!/usr/bin/env python3
"""
Attendance Data Processor

This script automates the processing of attendance data from raw source files,
runs the data pipeline, and updates the database with structured records.
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from utils.attendance_pipeline import run_attendance_pipeline, generate_daily_report
from utils.attendance_trends_api import get_driver_trends

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/attendance_processor.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function to process attendance data"""
    # Make sure logs directory exists
    Path('logs').mkdir(exist_ok=True)
    
    logger.info("Starting attendance data processor")
    
    # Run the attendance pipeline
    processed_dates = run_attendance_pipeline()
    
    if processed_dates:
        logger.info(f"Successfully processed attendance data for {len(processed_dates)} dates")
        
        # Generate trend data for the processed dates
        latest_date = processed_dates[-1]
        trends_end_date = latest_date
        
        # Try to get trend data (5-day window)
        try:
            trend_data = get_driver_trends(end_date=trends_end_date, days=5)
            num_drivers = len(trend_data.get('driver_trends', {}))
            logger.info(f"Generated attendance trends for {num_drivers} drivers")
            
            # Log trend statistics
            summary = trend_data.get('summary', {})
            chronic_late_count = summary.get('chronic_late_count', 0)
            repeated_absence_count = summary.get('repeated_absence_count', 0)
            unstable_shift_count = summary.get('unstable_shift_count', 0)
            
            logger.info(f"Trend analysis results: {chronic_late_count} chronic late, "
                       f"{repeated_absence_count} repeated absences, "
                       f"{unstable_shift_count} unstable shifts")
        except Exception as e:
            logger.error(f"Error generating trend data: {e}")
        
        # Generate daily report for the latest date
        try:
            report = generate_daily_report(latest_date)
            total_drivers = report.get('stats', {}).get('total_count', 0)
            late_count = report.get('stats', {}).get('late_count', 0)
            early_count = report.get('stats', {}).get('early_count', 0)
            
            logger.info(f"Generated daily report for {latest_date}: "
                       f"{total_drivers} drivers, {late_count} late, {early_count} early")
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
    else:
        logger.warning("No attendance data processed")
    
    logger.info("Attendance data processor completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())