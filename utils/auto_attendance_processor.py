"""
TRAXORA Fleet Management System - Automatic Attendance Processor

This module provides an automated processor for the attendance pipeline,
allowing scheduled processing of attendance data files and generation of reports.
"""

import os
import logging
import pandas as pd
from datetime import datetime, timedelta
import json
from pathlib import Path

# Import the simplified attendance pipeline
from utils.attendance_pipeline_slim import process_attendance_data_v2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define constants
DATA_DIR = "data"
PROCESSED_DIR = "processed"
REPORTS_DIR = "reports"
ARCHIVE_DIR = "data/archive"

def ensure_directories():
    """Ensure all required directories exist"""
    for dir_path in [DATA_DIR, PROCESSED_DIR, REPORTS_DIR, ARCHIVE_DIR]:
        os.makedirs(dir_path, exist_ok=True)

def get_date_from_filename(filename):
    """Extract date from filename"""
    try:
        # Try to find date in format YYYY-MM-DD
        import re
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            return date_match.group(1)
            
        # Try MM-DD-YYYY format
        date_match = re.search(r'(\d{2}-\d{2}-\d{4})', filename)
        if date_match:
            parts = date_match.group(1).split('-')
            return f"{parts[2]}-{parts[0]}-{parts[1]}"
            
        # If no date in filename, use today's date
        return datetime.now().strftime('%Y-%m-%d')
    except Exception as e:
        logger.error(f"Error extracting date from filename: {e}")
        return datetime.now().strftime('%Y-%m-%d')

def find_data_files(date_str=None):
    """Find data files for processing"""
    ensure_directories()
    
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
        
    # Files to look for by type
    file_types = {
        'driving_history': [],
        'time_on_site': [],
        'activity_detail': []
    }
    
    # List all files in data directory
    for file_path in Path(DATA_DIR).glob('*.csv'):
        filename = file_path.name.lower()
        file_date = get_date_from_filename(filename)
        
        # Check if file is for the requested date
        if date_str in file_path.name or file_date == date_str:
            # Categorize file by type
            if 'driving' in filename or 'driver' in filename:
                file_types['driving_history'].append(str(file_path))
            elif 'time' in filename or 'site' in filename:
                file_types['time_on_site'].append(str(file_path))
            elif 'activity' in filename or 'detail' in filename:
                file_types['activity_detail'].append(str(file_path))
                
    return file_types, date_str

def load_data_file(file_path):
    """Load data file into DataFrame"""
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
            
        # Load file based on extension
        if file_path.lower().endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.lower().endswith('.xlsx') or file_path.lower().endswith('.xls'):
            return pd.read_excel(file_path)
        else:
            logger.error(f"Unsupported file format: {file_path}")
            return None
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}")
        return None

def process_attendance(date_str=None, force=False):
    """Process attendance data and generate report"""
    try:
        # Find data files
        file_types, date_str = find_data_files(date_str)
        
        # Check if we have enough data
        if (not file_types['driving_history'] and 
            not file_types['time_on_site'] and 
            not file_types['activity_detail']):
            
            if not force:
                logger.warning(f"No data files found for {date_str}. Use force=True to process anyway.")
                return None
            else:
                logger.warning(f"No data files found for {date_str}, but force=True so processing with empty data.")
        
        # Load data files
        driving_history_data = None
        time_on_site_data = None
        activity_detail_data = None
        
        # Load driving history
        if file_types['driving_history']:
            driving_history_df = load_data_file(file_types['driving_history'][0])
            if driving_history_df is not None:
                driving_history_data = driving_history_df.to_dict('records')
                
        # Load time on site
        if file_types['time_on_site']:
            time_on_site_df = load_data_file(file_types['time_on_site'][0])
            if time_on_site_df is not None:
                time_on_site_data = time_on_site_df.to_dict('records')
                
        # Load activity detail
        if file_types['activity_detail']:
            activity_detail_df = load_data_file(file_types['activity_detail'][0])
            if activity_detail_df is not None:
                activity_detail_data = activity_detail_df.to_dict('records')
        
        # Process attendance data
        report = process_attendance_data_v2(
            driving_history_data=driving_history_data,
            time_on_site_data=time_on_site_data,
            activity_detail_data=activity_detail_data,
            date_str=date_str
        )
        
        # Save report
        if report:
            ensure_directories()
            report_file = os.path.join(REPORTS_DIR, f"attendance_report_{date_str}.json")
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Attendance report saved to {report_file}")
            return report_file
        else:
            logger.error(f"Failed to generate report for {date_str}")
            return None
            
    except Exception as e:
        logger.error(f"Error processing attendance: {e}")
        return None

def process_date_range(start_date, end_date=None, force=False):
    """Process attendance for a range of dates"""
    try:
        # Parse dates
        start = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end = start
            
        # Process each date
        current = start
        reports = []
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            report_file = process_attendance(date_str, force)
            if report_file:
                reports.append(report_file)
            current += timedelta(days=1)
            
        return reports
    except Exception as e:
        logger.error(f"Error processing date range: {e}")
        return []

def auto_process_today():
    """Automatically process today's attendance data"""
    today = datetime.now().strftime('%Y-%m-%d')
    return process_attendance(today, force=True)

def auto_process_yesterday():
    """Automatically process yesterday's attendance data"""
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    return process_attendance(yesterday, force=True)

if __name__ == "__main__":
    """Run auto processor as standalone script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automatic Attendance Processor")
    parser.add_argument('--date', help='Date to process (YYYY-MM-DD)')
    parser.add_argument('--start', help='Start date for range (YYYY-MM-DD)')
    parser.add_argument('--end', help='End date for range (YYYY-MM-DD)')
    parser.add_argument('--today', action='store_true', help='Process today')
    parser.add_argument('--yesterday', action='store_true', help='Process yesterday')
    parser.add_argument('--force', action='store_true', help='Force processing even if no files found')
    
    args = parser.parse_args()
    
    if args.today:
        auto_process_today()
    elif args.yesterday:
        auto_process_yesterday()
    elif args.start:
        process_date_range(args.start, args.end, args.force)
    elif args.date:
        process_attendance(args.date, args.force)
    else:
        auto_process_today()