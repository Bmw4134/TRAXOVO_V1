#!/usr/bin/env python3
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
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
Path('logs').mkdir(exist_ok=True)

# Import our custom modules
try:
    from utils.email_service import send_daily_report_email, validate_email_recipients
except ImportError:
    logger.error("Failed to import email_service module. Make sure it's available.")
    sys.exit(1)


def process_date(date_str, force_refresh=False, email_report=False, recipients=None):
    """
    Process a specific date through the entire pipeline
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        force_refresh (bool): Force refresh of cached data
        email_report (bool): Send email with report
        recipients (list): List of email recipients
        
    Returns:
        dict: Processing results
    """
    logger.info(f"Starting pipeline processing for date: {date_str}")
    
    try:
        # Import simple_processor here to avoid circular imports
        sys.path.append('.')
        from simple_processor import process_date as simple_process
        
        # Process the date
        report_data = simple_process(date_str)
        
        if not report_data:
            logger.error(f"Failed to process date: {date_str}")
            return None
            
        # Create output directory
        output_dir = Path('reports/daily_drivers')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine if files already exist and if we should overwrite
        json_file = output_dir / f'daily_report_{date_str}.json'
        excel_file = output_dir / f'daily_report_{date_str}.xlsx'
        
        if json_file.exists() and excel_file.exists() and not force_refresh:
            logger.info(f"Using existing report files for {date_str}")
            
            # Load existing report
            with open(json_file, 'r') as f:
                report_data = json.load(f)
        else:
            # Import pandas here to avoid including it in the global scope
            import pandas as pd
            
            # Save as JSON
            with open(json_file, 'w') as f:
                json.dump(report_data, f, indent=2)
                
            # Save as Excel
            df = pd.DataFrame(report_data['drivers'])
            df.to_excel(excel_file, index=False)
            
            logger.info(f"Saved report files for {date_str}")
        
        # Print summary information
        summary = report_data.get('summary', {})
        logger.info(f"Report summary for {date_str}:")
        logger.info(f"Total drivers: {summary.get('total', 0)}")
        logger.info(f"Late: {summary.get('late', 0)}")
        logger.info(f"Early End: {summary.get('early_end', 0)}")
        logger.info(f"Not On Job: {summary.get('not_on_job', 0)}")
        logger.info(f"On Time: {summary.get('on_time', 0)}")
        
        # Send email if requested
        if email_report:
            if recipients is None:
                recipients = []
                
            result = send_daily_report_email(date_str, recipients)
            
            if result:
                logger.info(f"Email sent for {date_str}")
            else:
                logger.error(f"Failed to send email for {date_str}")
        
        return report_data
        
    except Exception as e:
        logger.error(f"Error processing date {date_str}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def process_date_range(start_date, end_date, force_refresh=False, email_report=False, recipients=None):
    """
    Process a range of dates through the entire pipeline
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        force_refresh (bool): Force refresh of cached data
        email_report (bool): Send email with report
        recipients (list): List of email recipients
        
    Returns:
        dict: Processing results by date
    """
    logger.info(f"Processing date range: {start_date} to {end_date}")
    
    try:
        # Parse dates
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Ensure start date is before end date
        if start > end:
            start, end = end, start
            
        # Process each date
        results = {}
        current = start
        
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            result = process_date(date_str, force_refresh, email_report, recipients)
            results[date_str] = result
            current += timedelta(days=1)
            
        return results
        
    except Exception as e:
        logger.error(f"Error processing date range: {str(e)}")
        return {}


def list_available_dates():
    """
    List all dates for which source data is available
    
    Returns:
        list: Available dates in YYYY-MM-DD format
    """
    available_dates = set()
    
    # Check for driving history files
    driving_dir = Path('data/driving_history')
    if driving_dir.exists():
        for file in driving_dir.glob('driving_history_*.csv'):
            try:
                date_str = file.name.replace('driving_history_', '').replace('.csv', '')
                if validate_date_str(date_str):
                    available_dates.add(date_str)
            except:
                pass
    
    # Check for activity detail files
    activity_dir = Path('data/activity_detail')
    if activity_dir.exists():
        for file in activity_dir.glob('activity_detail_*.csv'):
            try:
                date_str = file.name.replace('activity_detail_', '').replace('.csv', '')
                if validate_date_str(date_str):
                    available_dates.add(date_str)
            except:
                pass
    
    # Check for assets time on site files
    assets_dir = Path('data/assets_time_on_site')
    if assets_dir.exists():
        for file in assets_dir.glob('assets_onsite_*.csv'):
            try:
                date_str = file.name.replace('assets_onsite_', '').replace('.csv', '')
                if validate_date_str(date_str):
                    available_dates.add(date_str)
            except:
                pass
    
    # Check for existing reports
    reports_dir = Path('reports/daily_drivers')
    if reports_dir.exists():
        for file in reports_dir.glob('daily_report_*.json'):
            try:
                date_str = file.name.replace('daily_report_', '').replace('.json', '')
                if validate_date_str(date_str):
                    available_dates.add(date_str)
            except:
                pass
    
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
    parser = argparse.ArgumentParser(description='Driver Reporting Pipeline')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List dates command
    list_parser = subparsers.add_parser('list', help='List available dates')
    
    # Process date command
    process_parser = subparsers.add_parser('process', help='Process a specific date')
    process_parser.add_argument('date', help='Date in YYYY-MM-DD format')
    process_parser.add_argument('--force', action='store_true', help='Force refresh of cached data')
    process_parser.add_argument('--email', action='store_true', help='Send email with report')
    process_parser.add_argument('--recipients', help='Comma-separated list of email recipients')
    
    # Process range command
    range_parser = subparsers.add_parser('range', help='Process a range of dates')
    range_parser.add_argument('start_date', help='Start date in YYYY-MM-DD format')
    range_parser.add_argument('end_date', help='End date in YYYY-MM-DD format')
    range_parser.add_argument('--force', action='store_true', help='Force refresh of cached data')
    range_parser.add_argument('--email', action='store_true', help='Send email with report')
    range_parser.add_argument('--recipients', help='Comma-separated list of email recipients')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the appropriate command
    if args.command == 'list':
        dates = list_available_dates()
        if dates:
            print("Available dates:")
            for date in dates:
                print(f"  {date}")
        else:
            print("No available dates found.")
    
    elif args.command == 'process':
        # Validate date
        if not validate_date_str(args.date):
            print(f"Invalid date format: {args.date}")
            return
        
        # Process recipients
        recipients = None
        if args.recipients:
            recipients = validate_email_recipients(args.recipients)
        
        # Process the date
        result = process_date(args.date, args.force, args.email, recipients)
        
        if result:
            print(f"Successfully processed {args.date}")
        else:
            print(f"Failed to process {args.date}")
    
    elif args.command == 'range':
        # Validate dates
        if not validate_date_str(args.start_date) or not validate_date_str(args.end_date):
            print(f"Invalid date format: {args.start_date} or {args.end_date}")
            return
        
        # Process recipients
        recipients = None
        if args.recipients:
            recipients = validate_email_recipients(args.recipients)
        
        # Process the date range
        results = process_date_range(args.start_date, args.end_date, args.force, args.email, recipients)
        
        success_count = sum(1 for result in results.values() if result)
        total_count = len(results)
        
        print(f"Successfully processed {success_count} of {total_count} dates")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()