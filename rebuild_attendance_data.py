#!/usr/bin/env python3
"""
Rebuild Attendance Data

This script forces a refresh of the attendance data for a specified date range
and regenerates the daily driver reports.
"""

import sys
import logging
from datetime import datetime, timedelta

# Configure basic logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import attendance pipeline modules
from utils.attendance_pipeline_connector import (
    get_attendance_data, 
    get_trend_data,
    get_driver_list
)

def rebuild_attendance_data(start_date_str, end_date_str):
    """
    Rebuild attendance data for a specified date range.
    
    Args:
        start_date_str (str): Start date in YYYY-MM-DD format
        end_date_str (str): End date in YYYY-MM-DD format
    """
    logger.info(f"Starting attendance data rebuild for {start_date_str} to {end_date_str}")
    
    # Parse dates
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    except ValueError:
        logger.error("Invalid date format. Please use YYYY-MM-DD.")
        return False
    
    # Generate list of dates to process
    current_date = start_date
    date_list = []
    
    while current_date <= end_date:
        date_list.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    logger.info(f"Processing {len(date_list)} dates: {', '.join(date_list)}")
    
    # Process each date individually first
    for date_str in date_list:
        logger.info(f"Processing attendance data for {date_str}")
        try:
            # Force refresh the attendance data
            attendance_data = get_attendance_data(date_str, force_refresh=True)
            
            # Log the results
            late_count = attendance_data.get('late_count', 0)
            early_count = attendance_data.get('early_count', 0)
            missing_count = attendance_data.get('missing_count', 0)
            total_drivers = attendance_data.get('total_drivers', 0)
            
            logger.info(f"Processed attendance data for {date_str}: "
                       f"{total_drivers} total drivers, "
                       f"{late_count} late, "
                       f"{early_count} early end, "
                       f"{missing_count} not on job")
        except Exception as e:
            logger.error(f"Error processing {date_str}: {e}")
    
    # Now rebuild trend data for the entire range
    try:
        logger.info(f"Rebuilding trend data for {start_date_str} to {end_date_str}")
        trend_data = get_trend_data(start_date_str, end_date_str, 
                                   days=(end_date - start_date).days + 1,
                                   force_refresh=True)
        
        # Log trend analysis results
        chronic_late_count = len(trend_data.get('chronic_lates', []))
        repeated_absence_count = len(trend_data.get('repeated_absences', []))
        unstable_shift_count = len(trend_data.get('unstable_shifts', []))
        
        logger.info(f"Trend analysis results: "
                   f"{chronic_late_count} chronic late, "
                   f"{repeated_absence_count} repeated absences, "
                   f"{unstable_shift_count} unstable shifts")
    except Exception as e:
        logger.error(f"Error rebuilding trend data: {e}")
    
    # Finally, rebuild the driver list
    try:
        logger.info(f"Rebuilding driver list for {start_date_str} to {end_date_str}")
        driver_list = get_driver_list(start_date_str, end_date_str, 
                                     days=(end_date - start_date).days + 1,
                                     force_refresh=True)
        
        total_drivers = len(driver_list.get('drivers', []))
        logger.info(f"Rebuilt driver list with {total_drivers} drivers")
    except Exception as e:
        logger.error(f"Error rebuilding driver list: {e}")
    
    logger.info("Attendance data rebuild complete")
    return True

if __name__ == "__main__":
    # Check arguments
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} START_DATE END_DATE")
        print("Example: python rebuild_attendance_data.py 2025-05-15 2025-05-19")
        sys.exit(1)
    
    start_date = sys.argv[1]
    end_date = sys.argv[2]
    
    # Run the rebuild
    success = rebuild_attendance_data(start_date, end_date)
    
    if success:
        print(f"Successfully rebuilt attendance data for {start_date} to {end_date}")
        sys.exit(0)
    else:
        print(f"Failed to rebuild attendance data for {start_date} to {end_date}")
        sys.exit(1)