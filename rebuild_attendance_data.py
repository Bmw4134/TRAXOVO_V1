#!/usr/bin/env python3
"""
Rebuild Attendance Data

This script forces a refresh of the attendance data for a specified date range
and regenerates the daily driver reports with enhanced job and employee information.
It also ensures that the exported reports include all necessary fields for analysis.
"""

import sys
import os
import logging
import traceback
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Configure robust logging with file output
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'attendance_rebuild.log'

# Set up multi-destination logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import attendance pipeline modules
from utils.attendance_pipeline_connector import (
    get_attendance_data, 
    get_trend_data,
    get_driver_list,
    clear_cache
)

# Import export utilities
from utils.export_utils import export_daily_report

def load_employee_job_data():
    """
    Load and process employee and job data from the consolidated workbook
    
    Returns:
        tuple: (employee_data, job_data) - DataFrames with employee and job information
    """
    try:
        # Find the consolidated employee and job lists workbook
        employee_job_file = "attached_assets/Consolidated_Employee_And_Job_Lists_Corrected.xlsx"
        
        if not os.path.exists(employee_job_file):
            logger.warning(f"Consolidated employee/job file not found: {employee_job_file}")
            return None, None
        
        # Load employee data from Employee_Contacts sheet
        employee_data = pd.read_excel(employee_job_file, sheet_name="Employee_Contacts")
        
        # Create a combined Employee Name field for matching with driver names
        employee_data['Employee Name'] = employee_data['First Name'] + ' ' + employee_data['Last Name']
        
        # Add employee_id field for join operations
        employee_data['employee_id'] = employee_data['Employee No']
        
        logger.info(f"Loaded {len(employee_data)} employee records from Employee_Contacts")
        
        # Load employee metadata if needed for additional details
        try:
            employee_metadata = pd.read_excel(employee_job_file, sheet_name="Employee_Metadata")
            logger.info(f"Loaded {len(employee_metadata)} employee metadata records")
            
            # Merge metadata with contacts if needed
            # employee_data = pd.merge(employee_data, employee_metadata, on='Employee No', how='left')
        except Exception as e:
            logger.warning(f"Could not load employee metadata: {e}")
        
        # Load job data from Job_Lists sheet
        job_data = pd.read_excel(employee_job_file, sheet_name="Job_Lists")
        
        # Create a Job Number field for matching with driver job assignments
        job_data['Job Number'] = job_data['Job No']
        
        # Add Division field from Geographic Area
        job_data['Division'] = job_data['Geographic Area']
        
        # Add Region field (can be extracted from Geographic Area if needed)
        job_data['Region'] = job_data['Geographic Area']
        
        logger.info(f"Loaded {len(job_data)} job records from Job_Lists")
        
        return employee_data, job_data
    
    except Exception as e:
        logger.error(f"Error loading employee/job data: {e}")
        logger.debug(traceback.format_exc())
        return None, None

def rebuild_attendance_data(date_list=None):
    """
    Rebuild attendance data for a specified list of dates.
    
    Args:
        date_list (list): List of dates in YYYY-MM-DD format
    
    Returns:
        bool: True if successful, False otherwise
    """
    # If no date list is provided, use the specific dates requested
    if date_list is None:
        date_list = ['2025-05-15', '2025-05-16', '2025-05-19']
    
    logger.info(f"Starting attendance data rebuild for dates: {', '.join(date_list)}")
    
    # First, clear the cache to ensure fresh data
    try:
        logger.info("Clearing attendance data cache")
        clear_cache()
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
    
    # Load employee and job data for enrichment
    employee_data, job_data = load_employee_job_data()
    
    # Create export directory
    export_dir = Path('exports/daily_reports')
    export_dir.mkdir(exist_ok=True, parents=True)
    
    # Process each date individually
    all_dates_success = True
    processed_dates = []
    
    for date_str in date_list:
        logger.info(f"Processing attendance data for {date_str}")
        try:
            # Force refresh the attendance data
            attendance_data = get_attendance_data(date_str, force_refresh=True)
            
            if attendance_data:
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
                
                # Export the data to Excel
                try:
                    export_path = export_dir / f"daily_report_{date_str}.xlsx"
                    export_success = export_daily_report(
                        date_str, 
                        export_path,
                        attendance_data=attendance_data,
                        employee_data=employee_data,
                        job_data=job_data
                    )
                    if export_success:
                        logger.info(f"Exported report to {export_path}")
                    else:
                        logger.warning(f"Failed to export report for {date_str}")
                except Exception as e:
                    logger.error(f"Error exporting report for {date_str}: {e}")
                
                processed_dates.append(date_str)
            else:
                logger.error(f"Failed to get attendance data for {date_str}")
                all_dates_success = False
        except Exception as e:
            logger.error(f"Error processing {date_str}: {e}")
            logger.debug(traceback.format_exc())
            all_dates_success = False
    
    # Now rebuild trend data for the processed dates
    if processed_dates:
        try:
            logger.info(f"Rebuilding trend data for processed dates")
            # Use min and max of processed dates to get range
            start_date = min(processed_dates)
            end_date = max(processed_dates)
            days = len(processed_dates)
            
            trend_data = get_trend_data(start_date, end_date, 
                                       days=days,
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
            logger.debug(traceback.format_exc())
    
    # Finally, rebuild the driver list
    try:
        if processed_dates:
            logger.info(f"Rebuilding driver list for processed dates")
            driver_list = get_driver_list(start_date, end_date, 
                                         days=days,
                                         force_refresh=True)
            
            # Handle different types of return values from get_driver_list
            if isinstance(driver_list, dict):
                total_drivers = len(driver_list.get('drivers', []))
            elif isinstance(driver_list, list):
                total_drivers = len(driver_list)
            else:
                total_drivers = 0
                
            logger.info(f"Rebuilt driver list with {total_drivers} drivers")
    except Exception as e:
        logger.error(f"Error rebuilding driver list: {e}")
        logger.debug(traceback.format_exc())
    
    logger.info("Attendance data rebuild complete")
    return all_dates_success

if __name__ == "__main__":
    # Check if specific dates are provided as arguments
    if len(sys.argv) > 1:
        # Get dates from arguments
        date_list = []
        for arg in sys.argv[1:]:
            if arg.startswith("--"):
                continue  # Skip flags
            try:
                # Validate date format
                datetime.strptime(arg, '%Y-%m-%d')
                date_list.append(arg)
            except ValueError:
                logger.error(f"Invalid date format: {arg}, expected YYYY-MM-DD")
                continue
        
        if date_list:
            logger.info(f"Using provided dates: {', '.join(date_list)}")
            success = rebuild_attendance_data(date_list)
        else:
            logger.error("No valid dates provided")
            sys.exit(1)
    else:
        # Default behavior - use the hardcoded dates
        logger.info("No dates provided, using default dates: 2025-05-15, 2025-05-16, 2025-05-19")
        success = rebuild_attendance_data()  # Will use the default dates
    
    if success:
        logger.info("Successfully rebuilt attendance data")
        sys.exit(0)
    else:
        logger.error("Failed to rebuild attendance data")
        sys.exit(1)