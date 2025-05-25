"""
TRAXORA Fleet Management System - Process Filtered Data

This utility script processes the filtered driving data JSON files
and generates attendance reports using the simplified attendance pipeline.
This is optimized for the specific TRAXORA data structure.
"""

import os
import json
import logging
import sys
from datetime import datetime, timedelta

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.attendance_pipeline_slim import process_attendance_data_v2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define constants
DATA_DIR = "data"
REPORTS_DIR = "reports"
LATE_START_TIME = "07:30:00"  # After this time is considered late
EARLY_END_TIME = "16:00:00"   # Before this time is considered early end

def process_filtered_data(date_str):
    """Process filtered data for a specific date
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        str: Path to the generated report file, or None if failed
    """
    try:
        # Find filtered data file
        filtered_file = os.path.join(DATA_DIR, f"filtered_driving_data_{date_str}.json")
        
        if not os.path.exists(filtered_file):
            logger.error(f"Filtered data file not found for {date_str}")
            return None
            
        # Load filtered data
        with open(filtered_file, 'r') as f:
            filtered_data = json.load(f)
            
        # Convert to expected format for attendance pipeline
        driving_history_data = []
        
        for record in filtered_data:
            # Use exact field names from TRAXORA data structure
            driving_record = {
                'driver_name': record.get('Driver', '').strip(),
                'date': record.get('Date', date_str),
                'first_start': record.get('FirstSeen'),
                'last_end': record.get('LastSeen'),
                'job_site': record.get('JobSite', 'Unknown'),
                'employee_id': record.get('EmployeeID'),
                'status': record.get('Status'),
                'hours': record.get('Hours', 0),
                'source': record.get('Source', 'gps'),
                'event_datetime': record.get('EventDateTime'),
                'location': record.get('Location')
            }
            driving_history_data.append(driving_record)
            
        # Process attendance data with TRAXORA specific classification rules
        report = process_attendance_data_v2(
            driving_history_data=driving_history_data,
            date_str=date_str,
            late_start_time=LATE_START_TIME,
            early_end_time=EARLY_END_TIME
        )
        
        # Save report
        os.makedirs(REPORTS_DIR, exist_ok=True)
        report_file = os.path.join(REPORTS_DIR, f"attendance_report_{date_str}.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        logger.info(f"Attendance report saved to {report_file}")
        return report_file
    
    except Exception as e:
        logger.error(f"Error processing filtered data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

if __name__ == "__main__":
    import argparse
    from datetime import timedelta
    
    parser = argparse.ArgumentParser(description="Process filtered driving data")
    parser.add_argument('--date', help='Date to process (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    if args.date:
        process_filtered_data(args.date)
    else:
        # Process yesterday's data by default
        yesterday = (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')
        process_filtered_data(yesterday)