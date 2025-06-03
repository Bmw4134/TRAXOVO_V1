#!/usr/bin/env python3
"""
Rebuild Daily Reports

This script rebuilds all daily driver reports for the specified date range,
ensuring consistent processing and output format using the unified data processor.
"""

import os
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Import unified data processor
from utils.unified_data_processor import UnifiedDataProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/rebuild_reports.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def find_input_files(date_str=None):
    """Find input files for the specified date"""
    logger.info(f"Finding input files for date: {date_str}")
    
    assets_dir = Path('attached_assets')
    
    # Find driving history files
    driving_history_files = []
    for file in assets_dir.glob('*'):
        if file.is_file() and ('DrivingHistory' in file.name or 'Driving_History' in file.name):
            driving_history_files.append(file)
    
    # Find activity detail files
    activity_detail_files = []
    for file in assets_dir.glob('*'):
        if file.is_file() and ('ActivityDetail' in file.name or 'Activity_Detail' in file.name):
            activity_detail_files.append(file)
    
    # Find asset time on site files
    asset_onsite_files = []
    for file in assets_dir.glob('*'):
        if file.is_file() and ('AssetsTimeOnSite' in file.name or 'FleetUtilization' in file.name):
            asset_onsite_files.append(file)
    
    # Find Start Time & Job files
    start_time_job_files = []
    for file in assets_dir.glob('*.xlsx'):
        if file.is_file() and ('DAILY' in file.name and 'NOJ' in file.name):
            start_time_job_files.append(file)
    
    # Find employee data files
    employee_files = []
    for file in assets_dir.glob('*.xlsx'):
        if file.is_file() and ('ELIST' in file.name or 'Employee' in file.name or 'Consolidated' in file.name):
            employee_files.append(file)
    
    # Sort by recency, newest first
    driving_history_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    activity_detail_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    asset_onsite_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    start_time_job_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    employee_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    # Return the newest file of each type
    return {
        'driving_history': driving_history_files[0] if driving_history_files else None,
        'activity_detail': activity_detail_files[0] if activity_detail_files else None,
        'asset_onsite': asset_onsite_files[0] if asset_onsite_files else None,
        'start_time_job': start_time_job_files[0] if start_time_job_files else None,
        'employee_data': employee_files[0] if employee_files else None
    }

def process_date(date_str):
    """Process a single date"""
    logger.info(f"Processing date: {date_str}")
    
    # Find input files
    input_files = find_input_files(date_str)
    
    # Log found files
    for file_type, file_path in input_files.items():
        if file_path:
            logger.info(f"Found {file_type} file: {file_path}")
        else:
            logger.warning(f"No {file_type} file found for {date_str}")
    
    # Create processor
    processor = UnifiedDataProcessor(date_str)
    
    # Process files
    if input_files['driving_history']:
        processor.process_driving_history(str(input_files['driving_history']))
    
    if input_files['activity_detail']:
        processor.process_activity_detail(str(input_files['activity_detail']))
    
    if input_files['asset_onsite']:
        processor.process_asset_onsite(str(input_files['asset_onsite']))
    
    if input_files['start_time_job']:
        processor.process_start_time_job_sheet(str(input_files['start_time_job']))
    
    if input_files['employee_data']:
        processor.process_employee_data(str(input_files['employee_data']))
    
    # Generate attendance report
    processor.generate_attendance_report()
    
    # Export to Excel and PDF
    processor.export_excel_report()
    processor.export_pdf_report()
    
    logger.info(f"Completed processing for date: {date_str}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Rebuild daily driver reports')
    parser.add_argument('--dates', nargs='+', help='List of dates in YYYY-MM-DD format')
    parser.add_argument('--start', help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end', help='End date in YYYY-MM-DD format')
    args = parser.parse_args()
    
    # Determine dates to process
    dates_to_process = []
    
    if args.dates:
        # Use provided dates
        dates_to_process = args.dates
    elif args.start and args.end:
        # Generate date range
        start_date = datetime.strptime(args.start, '%Y-%m-%d')
        end_date = datetime.strptime(args.end, '%Y-%m-%d')
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        dates_to_process = date_range
    else:
        # Default to May 15-20, 2025
        dates_to_process = [
            '2025-05-15',
            '2025-05-16',
            '2025-05-17',
            '2025-05-18',
            '2025-05-19',
            '2025-05-20'
        ]
    
    logger.info(f"Processing dates: {dates_to_process}")
    
    # Process each date
    for date_str in dates_to_process:
        process_date(date_str)
    
    logger.info("Completed rebuilding all reports")

if __name__ == "__main__":
    main()