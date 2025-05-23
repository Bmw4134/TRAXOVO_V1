#!/usr/bin/env python3
"""
TRAXORA Weekly Driver Report Generator

This script automates the process of generating driver reports for an entire week
using multiple data sources including driving history, activity detail, and assets on site.
It also processes timecard data for comparison with GPS data.

Usage:
    python weekly_driver_report_generator.py --start-date 2025-05-18 --end-date 2025-05-24 
    --driving-history-path "path/to/DrivingHistory.csv" 
    --activity-detail-path "path/to/ActivityDetail.csv"
    --assets-on-site-path "path/to/AssetsTimeOnSite.csv"
    --timecard-path "path/to/Timecards.xlsx"
"""

import os
import sys
import json
import argparse
import logging
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import project modules
sys.path.append('.')  # Ensure the script can find modules in the project root
try:
    from driver_pipeline import DriverPipeline
    from utils.timecard_processor import process_groundworks_timecards, compare_timecards_with_gps
except ImportError as e:
    logger.error(f"Error importing project modules: {e}")
    logger.error("Make sure to run this script from the project root directory")
    sys.exit(1)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Generate driver reports for an entire week')
    
    parser.add_argument('--start-date', required=True, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', required=True, help='End date in YYYY-MM-DD format')
    parser.add_argument('--driving-history-path', required=True, help='Path to driving history CSV file')
    parser.add_argument('--activity-detail-path', required=True, help='Path to activity detail CSV file')
    parser.add_argument('--assets-on-site-path', help='Path to assets on site CSV file (optional)')
    parser.add_argument('--speeding-report-path', help='Path to speeding report CSV file (optional)')
    parser.add_argument('--equipment-billing-path', help='Path to equipment billing Excel file (optional)')
    parser.add_argument('--timecard-path', help='Path to timecard Excel file (optional)')
    parser.add_argument('--output-dir', default='reports', help='Output directory for reports')
    
    return parser.parse_args()

def validate_date_range(start_date_str, end_date_str):
    """Validate date range and return list of dates"""
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        if end_date < start_date:
            logger.error("End date cannot be before start date")
            sys.exit(1)
        
        # Calculate date range
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        return date_range
    
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        sys.exit(1)

def filter_data_by_date(file_path, date_str, date_column):
    """Filter CSV data by date"""
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Check if the date column exists
        if date_column not in df.columns:
            logger.error(f"Date column '{date_column}' not found in {file_path}")
            return None
        
        # Filter data by date
        df[date_column] = pd.to_datetime(df[date_column])
        filtered_df = df[df[date_column].dt.strftime('%Y-%m-%d') == date_str]
        
        if len(filtered_df) == 0:
            logger.warning(f"No data found for date {date_str} in {file_path}")
            return None
        
        # Create a temporary file for the filtered data
        temp_file = f"temp_{Path(file_path).stem}_{date_str}.csv"
        filtered_df.to_csv(temp_file, index=False)
        
        return temp_file
    
    except Exception as e:
        logger.error(f"Error filtering data by date: {e}")
        return None

def process_job_assignments(file_path):
    """Process job assignments from equipment billing file"""
    try:
        # For XLSX files
        if file_path.endswith('.xlsx'):
            # Get the "Drivers" sheet
            df = pd.read_excel(file_path, sheet_name='Drivers')
            # Extract driver name and job number
            drivers = {}
            for _, row in df.iterrows():
                driver_name = row.get('Driver', '')
                job_number = row.get('Job #', '')
                if driver_name and job_number:
                    drivers[driver_name] = job_number
            return drivers
        return {}
    except Exception as e:
        logger.error(f"Error processing job assignments file {file_path}: {e}")
        return {}

def get_data_directory():
    """Get data directory, creating it if needed"""
    data_dir = os.path.join('data', 'driver_reports')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_reports_directory():
    """Get reports directory, creating it if needed"""
    reports_dir = os.path.join('reports', 'driver_reports')
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir

def generate_report_for_date(date_str, args):
    """Generate a driver report for a specific date"""
    logger.info(f"Generating report for {date_str}")
    
    # Filter driving history data by date
    driving_history_file = filter_data_by_date(
        args.driving_history_path, 
        date_str, 
        'Timestamp'
    )
    if not driving_history_file:
        logger.warning(f"Skipping report for {date_str} due to missing driving history data")
        return False
    
    # Filter activity detail data by date
    activity_detail_file = filter_data_by_date(
        args.activity_detail_path, 
        date_str, 
        'Timestamp'
    )
    if not activity_detail_file:
        logger.warning(f"Skipping report for {date_str} due to missing activity detail data")
        os.remove(driving_history_file)
        return False
    
    # Filter assets on site data by date (if provided)
    assets_on_site_file = None
    if args.assets_on_site_path:
        assets_on_site_file = filter_data_by_date(
            args.assets_on_site_path, 
            date_str, 
            'Timestamp'  # Adjust column name if needed
        )
    
    # Process job assignments (if provided)
    job_assignments = {}
    if args.equipment_billing_path:
        job_assignments = process_job_assignments(args.equipment_billing_path)
    
    try:
        # Run the driver pipeline
        pipeline = DriverPipeline(config={
            'date_str': date_str,
            'driving_history_files': [driving_history_file],
            'activity_detail_files': [activity_detail_file],
            'assets_on_site_files': [assets_on_site_file] if assets_on_site_file else [],
            'job_assignments': job_assignments
        })
        
        # Generate detailed report
        pipeline.run()
        logger.info(f"Successfully generated report for {date_str}")
        
        # Clean up temporary files
        if driving_history_file:
            os.remove(driving_history_file)
        if activity_detail_file:
            os.remove(activity_detail_file)
        if assets_on_site_file:
            os.remove(assets_on_site_file)
        
        return True
    
    except Exception as e:
        logger.error(f"Error generating report for {date_str}: {e}")
        
        # Clean up temporary files
        if driving_history_file and os.path.exists(driving_history_file):
            os.remove(driving_history_file)
        if activity_detail_file and os.path.exists(activity_detail_file):
            os.remove(activity_detail_file)
        if assets_on_site_file and os.path.exists(assets_on_site_file):
            os.remove(assets_on_site_file)
        
        return False

def process_timecard_comparison(args, date_range):
    """Process timecard comparison with GPS data"""
    if not args.timecard_path:
        logger.info("No timecard file provided, skipping timecard comparison")
        return
    
    logger.info(f"Processing timecard comparison for date range {date_range[0]} to {date_range[-1]}")
    
    try:
        # Process the timecards
        timecard_data = process_groundworks_timecards(
            args.timecard_path, 
            start_date=date_range[0], 
            end_date=date_range[-1]
        )
        
        # Load existing driver reports for comparison
        reports_dir = get_reports_directory()
        gps_data = {}
        dates_processed = []
        
        for date_str in date_range:
            report_dir = os.path.join(reports_dir, date_str)
            if os.path.exists(report_dir):
                # Find JSON report
                for filename in os.listdir(report_dir):
                    if filename.endswith('.json') and not filename.startswith('summary'):
                        with open(os.path.join(report_dir, filename), 'r') as f:
                            report_data = json.load(f)
                            gps_data[date_str] = report_data
                            dates_processed.append(date_str)
        
        if not dates_processed:
            logger.warning("No driver reports found for timecard comparison")
            return
        
        # Compare timecards with GPS data
        comparisons = []
        for date_str in dates_processed:
            comparison = compare_timecards_with_gps(
                args.timecard_path,
                gps_data,
                target_date=date_str
            )
            comparisons.extend(comparison)
        
        # Save comparison results
        data_dir = get_data_directory()
        with open(os.path.join(data_dir, 'timecard_comparisons.json'), 'w') as f:
            json.dump(comparisons, f, indent=2)
        
        logger.info(f"Timecard comparison complete: {len(comparisons)} records processed")
    
    except Exception as e:
        logger.error(f"Error processing timecard comparison: {e}")

def main():
    """Main function"""
    args = parse_arguments()
    
    # Validate date range
    date_range = validate_date_range(args.start_date, args.end_date)
    logger.info(f"Processing date range: {date_range}")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Generate reports for each date in the range
    successful_dates = []
    for date_str in date_range:
        if generate_report_for_date(date_str, args):
            successful_dates.append(date_str)
    
    if not successful_dates:
        logger.error("Failed to generate any reports")
        return
    
    logger.info(f"Successfully generated reports for dates: {successful_dates}")
    
    # Process timecard comparison if timecard file is provided
    if args.timecard_path:
        process_timecard_comparison(args, successful_dates)
    
    logger.info("Weekly driver report generation complete")

if __name__ == "__main__":
    main()