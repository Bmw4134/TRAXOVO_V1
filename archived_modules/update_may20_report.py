#!/usr/bin/env python3
"""
Update May 20 Report

This script updates the daily driver report for May 20, 2025 using the
newly processed driving history data.
"""

import os
import logging
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_FILE = 'processed/driving_history_2025-05-20.json'
REPORT_DIR = Path('exports/daily_reports')
REPORT_DIR.mkdir(exist_ok=True, parents=True)
OUTPUT_JSON = REPORT_DIR / 'attendance_data_2025-05-20.json'

def load_driving_history():
    """
    Load the processed driving history data for May 20
    """
    if not os.path.exists(DATA_FILE):
        logger.error(f"Driving history data file not found: {DATA_FILE}")
        return None
    
    try:
        logger.info(f"Loading driving history data from: {DATA_FILE}")
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        
        logger.info(f"Loaded {len(data)} driver records")
        return data
    
    except Exception as e:
        logger.error(f"Error loading driving history data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def prepare_attendance_data(driving_history):
    """
    Prepare attendance data for May 20 report
    """
    if not driving_history:
        logger.error("No driving history data available")
        return None
    
    try:
        # Create attendance report structure
        attendance_data = {
            'date': '2025-05-20',
            'total_drivers': len(driving_history),
            'late_start_records': [],
            'early_end_records': [],
            'not_on_job_records': [],
            'drivers': []
        }
        
        # Set standard shift times
        start_time = '07:00'
        end_time = '17:00'
        
        # Process each driver
        for driver in driving_history:
            # Create a standardized driver record
            driver_record = {
                'driver_name': driver.get('driver_name', ''),
                'employee_id': driver.get('employee_id', ''),
                'asset_id': '',  # May be populated from Start Time & Job sheet
                'job_number': '',  # May be populated from Start Time & Job sheet
                'scheduled_start': start_time,
                'scheduled_end': end_time,
                'source': 'driving_history_may20'
            }
            
            # Add actual start and end times if available
            if 'first_key_on' in driver and driver['first_key_on']:
                actual_start = pd.to_datetime(driver['first_key_on'])
                driver_record['actual_start'] = actual_start.strftime('%H:%M')
                
                # Check if late
                scheduled_start = datetime.strptime(f"2025-05-20 {start_time}", '%Y-%m-%d %H:%M')
                if actual_start > scheduled_start:
                    # Calculate late minutes
                    late_minutes = int((actual_start - scheduled_start).total_seconds() / 60)
                    if late_minutes > 10:  # Consider late if more than 10 minutes
                        driver_record['late_minutes'] = late_minutes
                        
                        # Add to late start records
                        late_record = {
                            'driver_name': driver_record['driver_name'],
                            'job_site': driver.get('locations', '').split(';')[0] if driver.get('locations') else 'Unknown',
                            'scheduled_start': start_time,
                            'actual_start': driver_record['actual_start'],
                            'late_minutes': late_minutes,
                            'asset_id': driver_record.get('asset_id', '')
                        }
                        attendance_data['late_start_records'].append(late_record)
            
            # Add actual end time if available
            if 'last_key_off' in driver and driver['last_key_off']:
                actual_end = pd.to_datetime(driver['last_key_off'])
                driver_record['actual_end'] = actual_end.strftime('%H:%M')
                
                # Check if early end
                scheduled_end = datetime.strptime(f"2025-05-20 {end_time}", '%Y-%m-%d %H:%M')
                if actual_end < scheduled_end:
                    # Calculate early minutes
                    early_minutes = int((scheduled_end - actual_end).total_seconds() / 60)
                    if early_minutes > 10:  # Consider early if more than 10 minutes
                        driver_record['early_minutes'] = early_minutes
                        
                        # Add to early end records
                        early_record = {
                            'driver_name': driver_record['driver_name'],
                            'job_site': driver.get('locations', '').split(';')[0] if driver.get('locations') else 'Unknown',
                            'scheduled_end': end_time,
                            'actual_end': driver_record['actual_end'],
                            'early_minutes': early_minutes,
                            'asset_id': driver_record.get('asset_id', '')
                        }
                        attendance_data['early_end_records'].append(early_record)
            
            # Add locations
            if 'locations' in driver and driver['locations']:
                locations = driver['locations'].split(';')
                if locations:
                    # Extract job information
                    for location in locations:
                        # Check if location contains a job number
                        if '20' in location and '-' in location:
                            job_parts = location.split(',')[0].strip()
                            # Look for job numbers like 2023-006 or 2024-024
                            if '20' in job_parts and '-' in job_parts:
                                job_number = job_parts.split('(')[0].strip() if '(' in job_parts else job_parts
                                driver_record['job_number'] = job_number
                                break
                    
                    # Set job site
                    driver_record['job_site'] = locations[0].strip()
            
            # Add driver record to the list
            attendance_data['drivers'].append(driver_record)
        
        # Add not on job records (for demonstration - these would be pulled from the Start Time & Job sheet)
        # This placeholder is just to show the structure - actual implementation would look for drivers in the
        # Start Time & Job sheet who do not appear in the driving history
        
        # Update count fields
        attendance_data['late_count'] = len(attendance_data['late_start_records'])
        attendance_data['early_count'] = len(attendance_data['early_end_records'])
        attendance_data['missing_count'] = len(attendance_data['not_on_job_records'])
        
        # Calculate on-time percentage
        total = max(1, attendance_data['total_drivers'])
        on_time_count = total - attendance_data['late_count'] - attendance_data['missing_count']
        attendance_data['on_time_percent'] = round(100 * on_time_count / total, 1)
        
        # Sort records for better readability
        attendance_data['late_start_records'] = sorted(
            attendance_data['late_start_records'], 
            key=lambda x: x.get('late_minutes', 0), 
            reverse=True
        )
        
        attendance_data['early_end_records'] = sorted(
            attendance_data['early_end_records'], 
            key=lambda x: x.get('early_minutes', 0), 
            reverse=True
        )
        
        logger.info(f"Prepared attendance data with {len(attendance_data['drivers'])} drivers")
        return attendance_data
    
    except Exception as e:
        logger.error(f"Error preparing attendance data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def update_attendance_with_job_data(attendance_data):
    """
    This function would update the attendance data with job assignments from the Start Time & Job sheet
    """
    # Import the Start Time & Job parser
    try:
        from utils.start_time_parser import extract_start_time_data, merge_start_time_with_attendance
        
        # Extract data from Start Time & Job sheet
        start_time_data = extract_start_time_data('2025-05-20')
        
        if start_time_data is not None:
            # Merge the data
            attendance_data = merge_start_time_with_attendance(attendance_data, start_time_data)
            logger.info("Updated attendance data with Start Time & Job information")
        else:
            logger.warning("No Start Time & Job data found for 2025-05-20")
    
    except Exception as e:
        logger.error(f"Error updating with job data: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return attendance_data

def save_attendance_data(attendance_data):
    """
    Save the attendance data to JSON
    """
    if not attendance_data:
        logger.error("No attendance data to save")
        return False
    
    try:
        # Ensure directory exists
        REPORT_DIR.mkdir(exist_ok=True, parents=True)
        
        # Save to JSON
        with open(OUTPUT_JSON, 'w') as f:
            json.dump(attendance_data, f, indent=2, default=str)
        
        logger.info(f"Saved attendance data to {OUTPUT_JSON}")
        
        # Also save as Excel for easier viewing
        excel_file = REPORT_DIR / 'daily_report_2025-05-20.xlsx'
        
        # Create DataFrames for each section
        drivers_df = pd.DataFrame(attendance_data['drivers'])
        late_df = pd.DataFrame(attendance_data['late_start_records'])
        early_df = pd.DataFrame(attendance_data['early_end_records'])
        
        # Create Excel writer
        with pd.ExcelWriter(excel_file) as writer:
            drivers_df.to_excel(writer, sheet_name='Drivers', index=False)
            late_df.to_excel(writer, sheet_name='Late Start', index=False)
            early_df.to_excel(writer, sheet_name='Early End', index=False)
        
        logger.info(f"Saved Excel report to {excel_file}")
        
        # Save a standard filename version for the downloads
        standard_file = REPORT_DIR / '2025-05-20_DailyDriverReport.xlsx'
        import shutil
        shutil.copy2(excel_file, standard_file)
        logger.info(f"Saved standardized report to {standard_file}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error saving attendance data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """
    Main function
    """
    logger.info("Starting May 20 report update")
    
    # Load the driving history data
    driving_history = load_driving_history()
    
    if driving_history:
        # Prepare attendance data
        attendance_data = prepare_attendance_data(driving_history)
        
        if attendance_data:
            # Update with job data from Start Time & Job sheet
            attendance_data = update_attendance_with_job_data(attendance_data)
            
            # Save the data
            save_attendance_data(attendance_data)
    
    logger.info("May 20 report update complete")

if __name__ == "__main__":
    main()