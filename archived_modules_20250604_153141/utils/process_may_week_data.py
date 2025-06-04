"""
Process May 18-24 Week Data

This script processes the attendance data for the May 18-24, 2025 week,
using our new Daily Driver Engine 2.0 pipeline.
"""

import os
import logging
import pandas as pd
from datetime import datetime, timedelta
import json

from attendance_pipeline_v2 import process_attendance_data_v2
from enhanced_data_ingestion import load_csv_file, load_excel_file
from daily_driver_report_generator import generate_daily_report

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure required directories exist"""
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports/daily_driver_reports", exist_ok=True)
    os.makedirs("uploads/daily_reports", exist_ok=True)

def process_driving_history_file(file_path):
    """Process a driving history file"""
    logger.info(f"Processing driving history file: {file_path}")
    try:
        if file_path.endswith('.csv'):
            data = load_csv_file(file_path)
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            data = load_excel_file(file_path)
        else:
            logger.warning(f"Unsupported file format: {file_path}")
            return None
        
        logger.info(f"Successfully loaded {len(data)} records from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return None

def process_timecard_file(file_path):
    """Process a timecard file"""
    logger.info(f"Processing timecard file: {file_path}")
    try:
        if file_path.endswith('.csv'):
            data = load_csv_file(file_path)
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            data = load_excel_file(file_path)
        else:
            logger.warning(f"Unsupported file format: {file_path}")
            return None
        
        logger.info(f"Successfully loaded {len(data)} records from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return None

def process_date(date_str, driving_history_path, timecard_path):
    """Process data for a specific date"""
    logger.info(f"Processing data for date: {date_str}")
    
    # Load data
    driving_history_data = process_driving_history_file(driving_history_path)
    timecard_data = process_timecard_file(timecard_path)
    
    if not driving_history_data:
        logger.warning(f"No driving history data available for date: {date_str}")
        return False
    
    # Process data using the v2 attendance pipeline
    attendance_report = process_attendance_data_v2(
        driving_history_data=driving_history_data,
        time_on_site_data=[],  # Not using this source for now
        activity_detail_data=[],  # Not using this source for now
        timecard_data=timecard_data or [],
        date_str=date_str
    )
    
    if not attendance_report:
        logger.warning(f"Failed to generate attendance report for date: {date_str}")
        return False
    
    # Save JSON version for inspection
    json_path = os.path.join("reports", "daily_driver_reports", f"driver_report_{date_str}.json")
    with open(json_path, 'w') as f:
        json.dump(attendance_report, f, indent=2)
    
    # Generate Excel report
    _, excel_path = generate_daily_report(
        date_str=date_str,
        driving_history_data=driving_history_data,
        timecard_data=timecard_data
    )
    
    if excel_path and os.path.exists(excel_path):
        logger.info(f"Generated report: {excel_path}")
        return True
    else:
        logger.warning(f"Failed to generate Excel report for date: {date_str}")
        return False

def process_week(start_date_str, end_date_str, driving_history_file, timecard_file):
    """Process an entire week of data"""
    logger.info(f"Processing week from {start_date_str} to {end_date_str}")
    
    # Convert dates to datetime objects
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    # Process each day in the range
    current_date = start_date
    results = []
    
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        success = process_date(date_str, driving_history_file, timecard_file)
        results.append({
            'date': date_str,
            'success': success
        })
        current_date += timedelta(days=1)
    
    # Generate weekly summary report
    weekly_summary = {
        'week_start': start_date_str,
        'week_end': end_date_str,
        'days_processed': len(results),
        'days_successful': sum(1 for r in results if r['success']),
        'details': results
    }
    
    weekly_report_path = os.path.join("reports", f"weekly_summary_{start_date_str}_to_{end_date_str}.json")
    with open(weekly_report_path, 'w') as f:
        json.dump(weekly_summary, f, indent=2)
    
    logger.info(f"Weekly summary saved to: {weekly_report_path}")
    logger.info(f"Processed {weekly_summary['days_successful']} out of {weekly_summary['days_processed']} days successfully")
    
    return weekly_summary

def main():
    """Main function"""
    # Ensure directories exist
    ensure_dirs()
    
    # May 18-24, 2025 week
    start_date = "2025-05-18"
    end_date = "2025-05-24"
    
    # Use the attached May week data
    driving_history_file = "attached_assets/weekly_driver_report_2025-05-18_to_2025-05-24.csv"
    timecard_file = "attached_assets/Timecards - 2025-05-18 - 2025-05-24 (3).xlsx"
    
    # Process the week
    weekly_summary = process_week(start_date, end_date, driving_history_file, timecard_file)
    
    return weekly_summary

if __name__ == "__main__":
    main()