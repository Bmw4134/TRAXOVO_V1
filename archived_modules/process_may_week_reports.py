"""
Process May Week Reports

This script processes the May 18-24, 2025 data set and generates daily driver reports
with proper classification using the existing Status field in the data.
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure we can import from utils directory
sys.path.append('.')

from utils.enhanced_data_ingestion import load_csv_file, load_excel_file
from utils.daily_driver_report_generator import generate_daily_report

def create_directories():
    """Create necessary directories for reports and data"""
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports/daily_driver_reports", exist_ok=True)
    os.makedirs("uploads/daily_reports", exist_ok=True)

def filter_driving_records_by_date(driving_data, date_str):
    """Filter driving records for a specific date and map fields correctly"""
    filtered_records = []
    
    # Print what we're looking for
    logger.info(f"Looking for records with Date: {date_str}")
    
    # Log the first few keys to help with debugging
    if driving_data and len(driving_data) > 0:
        logger.info(f"First record keys: {list(driving_data[0].keys())}")
        sample_record = driving_data[0]
        if 'Date' in sample_record:
            logger.info(f"Sample record date: {sample_record['Date']}")
    
    for record in driving_data:
        # Check if this record is for the specified date
        # Some CSVs might have 'date' (lowercase) instead of 'Date'
        record_date = record.get('Date') or record.get('date')
        
        # In case date field is missing or values don't match, print some debug info
        if not record_date:
            continue
        
        # Get driver name (may be capitalized or lowercase in the CSV)
        driver_name = record.get('Driver Name') or record.get('driver_name', '')
        
        # Skip records without a driver name
        if not driver_name or driver_name.strip() == '':
            continue
        
        # Check exact date match
        if record_date == date_str:
            # Get status (may be capitalized or lowercase in the CSV)
            status = record.get('Status') or record.get('status', 'not_on_job')
            
            # Normalize status values if needed
            if status == 'on_time':
                normalized_status = 'on_time'
            elif status == 'late':
                normalized_status = 'late'
            elif status == 'early_end':
                normalized_status = 'early_end'  
            elif status == 'not_on_job':
                normalized_status = 'not_on_job'
            else:
                normalized_status = 'not_on_job'  # Default to not_on_job for unknown status
            
            # Create a properly mapped record
            mapped_record = {
                'Driver': driver_name,
                'EmployeeID': record.get('Employee ID') or record.get('employee_id', ''),
                'Status': normalized_status,
                'JobSite': record.get('Job Site') or record.get('job_site', 'Unknown'),
                'FirstSeen': record.get('First Seen') or record.get('first_seen', ''),
                'LastSeen': record.get('Last Seen') or record.get('last_seen', ''),
                'Hours': record.get('Hours') or record.get('hours', '0'),
                'Source': record.get('Source') or record.get('source', 'gps'),
                'Date': date_str
            }
            
            # Set EventDateTime to FirstSeen if available, otherwise use date with default time
            if mapped_record['FirstSeen']:
                mapped_record['EventDateTime'] = mapped_record['FirstSeen']
            else:
                mapped_record['EventDateTime'] = f"{date_str} 07:00:00"
            
            # Set Location to JobSite
            mapped_record['Location'] = mapped_record['JobSite']
            
            filtered_records.append(mapped_record)
    
    return filtered_records

def process_date(date_str, driving_history_file, timecard_file):
    """Process data for a specific date"""
    logger.info(f"Processing data for date: {date_str}")
    
    try:
        # Load data files
        driving_data = load_csv_file(driving_history_file)
        timecard_data = load_excel_file(timecard_file)
        
        if not driving_data:
            logger.error(f"Failed to load driving history data from {driving_history_file}")
            return False
            
        if not timecard_data:
            logger.warning(f"No timecard data available from {timecard_file}")
            
        # Filter driving records for this date
        filtered_driving_data = filter_driving_records_by_date(driving_data, date_str)
        logger.info(f"Found {len(filtered_driving_data)} driving records for {date_str}")
        
        # Save filtered data as JSON for inspection
        filtered_data_path = os.path.join("data", f"filtered_driving_data_{date_str}.json")
        with open(filtered_data_path, 'w') as f:
            json.dump(filtered_driving_data, f, indent=2)
        
        # Generate Excel report
        _, excel_path = generate_daily_report(
            date_str=date_str,
            driving_history_data=filtered_driving_data,
            timecard_data=timecard_data
        )
        
        if excel_path and os.path.exists(excel_path):
            logger.info(f"Generated report: {excel_path}")
            return True
        else:
            logger.warning(f"Failed to generate Excel report for date: {date_str}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing data for {date_str}: {str(e)}")
        return False

def process_may_week():
    """Process the entire May 18-24 week"""
    driving_history_file = "attached_assets/weekly_driver_report_2025-05-18_to_2025-05-24.csv"
    timecard_file = "attached_assets/Timecards - 2025-05-18 - 2025-05-24 (3).xlsx"
    
    # Dates to process
    dates = [
        "2025-05-18",  # Sunday
        "2025-05-19",  # Monday
        "2025-05-20",  # Tuesday
        "2025-05-21",  # Wednesday
        "2025-05-22",  # Thursday
        "2025-05-23",  # Friday
        "2025-05-24"   # Saturday
    ]
    
    # Process each date
    results = []
    for date_str in dates:
        success = process_date(date_str, driving_history_file, timecard_file)
        results.append({
            'date': date_str,
            'success': success
        })
    
    # Generate a summary report
    summary = {
        'start_date': dates[0],
        'end_date': dates[-1],
        'total_days': len(dates),
        'successful_days': sum(1 for r in results if r['success']),
        'details': results
    }
    
    summary_path = os.path.join("reports", f"may_week_summary_{dates[0]}_to_{dates[-1]}.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Week summary saved to: {summary_path}")
    logger.info(f"Processed {summary['successful_days']} out of {summary['total_days']} days successfully")
    
    return summary

if __name__ == "__main__":
    create_directories()
    process_may_week()