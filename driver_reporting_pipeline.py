"""
Driver Reporting Pipeline

This script serves as the main entry point for the daily driver report generation pipeline,
integrating all the components to process driver attendance data consistently.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
import traceback

# Import utility modules
from utils.data_audit import audit_source_data, compare_pre_post_join, audit_status_mapping
from utils.consistency_engine import compute_driver_status, build_driver_summary, generate_daily_report
from utils.attendance_pipeline_connector import get_attendance_data, get_trend_data, get_source_data_paths
from utils.export_sync import sync_exports, update_report_links, process_specific_date
from utils.email_service import email_daily_report, get_user_email_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('logs/driver_reporting_pipeline.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Ensure directories exist
for directory in ['logs', 'exports', 'exports/daily_reports', 'exports/pdf_reports', 'exports/excel_reports', 'data']:
    os.makedirs(directory, exist_ok=True)

def process_date(date_str, force_refresh=False, email_report=False, recipients=None):
    """
    Process a specific date through the entire pipeline
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        force_refresh (bool): Force refresh of cached data
        email_report (bool): Send email with report
        recipients (str): Comma-separated list of email recipients
        
    Returns:
        dict: Processing results
    """
    logger.info(f"Processing date {date_str}")
    try:
        # Step 1: Get attendance data (processes data if not cached, or if force_refresh=True)
        if force_refresh:
            logger.info(f"Forcing refresh of attendance data for {date_str}")
            # Remove cached data if exists
            cached_file = f"exports/daily_reports/daily_report_{date_str}.json"
            if os.path.exists(cached_file):
                os.remove(cached_file)
        
        # Process attendance data
        attendance_data = get_attendance_data(date_str)
        
        if not attendance_data:
            logger.error(f"Failed to retrieve attendance data for {date_str}")
            return {
                'status': 'error',
                'message': f"Failed to retrieve attendance data for {date_str}"
            }
        
        # Step 2: Sync exports (PDF, Excel)
        export_paths = sync_exports(date_str, attendance_data)
        
        if not export_paths:
            logger.error(f"Failed to sync exports for {date_str}")
            return {
                'status': 'error',
                'message': f"Failed to sync exports for {date_str}"
            }
        
        # Step 3: Update report links in JSON
        update_status = update_report_links(date_str, export_paths)
        
        if not update_status:
            logger.warning(f"Failed to update report links for {date_str}")
        
        # Step 4: Send email if requested
        if email_report:
            email_config = get_user_email_config()
            
            # Override recipients if provided
            if recipients:
                email_config['recipients'] = recipients
            
            email_result = email_daily_report(date_str, email_config)
            
            if email_result.get('success', False):
                logger.info(f"Successfully sent email report for {date_str}")
            else:
                logger.error(f"Failed to send email report: {email_result.get('message', 'Unknown error')}")
                
            return {
                'status': 'success',
                'export_paths': export_paths,
                'email_status': email_result
            }
        
        return {
            'status': 'success',
            'export_paths': export_paths
        }
    
    except Exception as e:
        logger.error(f"Error processing date {date_str}: {e}")
        logger.error(traceback.format_exc())
        return {
            'status': 'error',
            'message': str(e)
        }

def process_date_range(start_date, end_date, force_refresh=False, email_report=False, recipients=None):
    """
    Process a range of dates through the entire pipeline
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        force_refresh (bool): Force refresh of cached data
        email_report (bool): Send email with report
        recipients (str): Comma-separated list of email recipients
        
    Returns:
        dict: Processing results by date
    """
    logger.info(f"Processing date range {start_date} to {end_date}")
    
    results = {}
    
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    
    current_date = start_date_obj
    while current_date <= end_date_obj:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Process each date
        result = process_date(date_str, force_refresh, email_report, recipients)
        results[date_str] = result
        
        # Go to next date
        current_date += timedelta(days=1)
    
    return results

def list_available_dates():
    """
    List all dates for which source data is available
    
    Returns:
        list: Available dates in YYYY-MM-DD format
    """
    # Get all source data paths (without date filter)
    source_files = get_source_data_paths()
    
    # Extract dates from filenames
    available_dates = set()
    
    for category, files in source_files.items():
        for file_path in files:
            # Extract potential dates from filename
            filename = os.path.basename(file_path)
            
            # Try different date formats
            for date_format in ['%Y-%m-%d', '%Y%m%d', '%m-%d-%Y', '%m/%d/%Y']:
                try:
                    # For each format, try sliding window approach
                    for i in range(len(filename) - 8):
                        potential_date = filename[i:i+10]  # Assuming YYYY-MM-DD or similar length
                        try:
                            date_obj = datetime.strptime(potential_date, date_format)
                            # Only consider reasonable dates (last 5 years)
                            if date_obj.year > datetime.now().year - 5:
                                available_dates.add(date_obj.strftime('%Y-%m-%d'))
                        except ValueError:
                            continue
                except Exception:
                    continue
    
    # Sort dates
    return sorted(list(available_dates))

def validate_date_str(date_str):
    """
    Validate a date string in YYYY-MM-DD format
    
    Args:
        date_str (str): Date string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def main():
    """
    Main function to run the pipeline from command line
    """
    parser = argparse.ArgumentParser(description="Driver Reporting Pipeline")
    
    # Date arguments
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument('--date', type=str, help="Process a specific date (YYYY-MM-DD)")
    date_group.add_argument('--range', type=str, nargs=2, metavar=('START_DATE', 'END_DATE'), 
                          help="Process a date range (YYYY-MM-DD to YYYY-MM-DD)")
    date_group.add_argument('--today', action='store_true', help="Process today's date")
    date_group.add_argument('--yesterday', action='store_true', help="Process yesterday's date")
    date_group.add_argument('--list-dates', action='store_true', help="List available dates with source data")
    
    # Processing options
    parser.add_argument('--force', action='store_true', help="Force refresh of cached data")
    parser.add_argument('--email', action='store_true', help="Send email with report")
    parser.add_argument('--recipients', type=str, help="Comma-separated list of email recipients")
    
    args = parser.parse_args()
    
    # List available dates if requested
    if args.list_dates:
        available_dates = list_available_dates()
        print(f"Available dates with source data ({len(available_dates)}):")
        for date_str in available_dates:
            print(f"  {date_str}")
        return
    
    # Default to today if no date specified
    if not args.date and not args.range and not args.today and not args.yesterday:
        args.today = True
    
    # Process today
    if args.today:
        date_str = datetime.now().strftime('%Y-%m-%d')
        print(f"Processing today's date: {date_str}")
        result = process_date(date_str, args.force, args.email, args.recipients)
        print(f"Result: {result['status']}")
        if result['status'] == 'error':
            print(f"Error: {result.get('message', 'Unknown error')}")
        return
    
    # Process yesterday
    if args.yesterday:
        date_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"Processing yesterday's date: {date_str}")
        result = process_date(date_str, args.force, args.email, args.recipients)
        print(f"Result: {result['status']}")
        if result['status'] == 'error':
            print(f"Error: {result.get('message', 'Unknown error')}")
        return
    
    # Process specific date
    if args.date:
        if not validate_date_str(args.date):
            print(f"Invalid date format: {args.date}. Please use YYYY-MM-DD.")
            return
        
        print(f"Processing date: {args.date}")
        result = process_date(args.date, args.force, args.email, args.recipients)
        print(f"Result: {result['status']}")
        if result['status'] == 'error':
            print(f"Error: {result.get('message', 'Unknown error')}")
        return
    
    # Process date range
    if args.range:
        start_date, end_date = args.range
        
        if not validate_date_str(start_date) or not validate_date_str(end_date):
            print(f"Invalid date format in range. Please use YYYY-MM-DD.")
            return
        
        print(f"Processing date range: {start_date} to {end_date}")
        results = process_date_range(start_date, end_date, args.force, args.email, args.recipients)
        
        # Print summary of results
        print("\nProcessing Summary:")
        success_count = sum(1 for result in results.values() if result['status'] == 'success')
        error_count = sum(1 for result in results.values() if result['status'] == 'error')
        print(f"Total: {len(results)}, Success: {success_count}, Errors: {error_count}")
        
        if error_count > 0:
            print("\nErrors:")
            for date_str, result in results.items():
                if result['status'] == 'error':
                    print(f"  {date_str}: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main()