#!/usr/bin/env python3
"""
Attendance Audit CLI

This script provides command-line tools for querying and analyzing attendance data,
showing processed dates, their completeness, and file sources used for each date.
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta

from utils.attendance_audit import (get_date_audit_details, get_processed_dates,
                               generate_audit_report, setup_audit_database)
from utils.attendance_pipeline import run_attendance_pipeline, setup_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def list_dates_command(args):
    """List all processed dates command"""
    min_completeness = args.min_completeness
    
    dates = get_processed_dates(min_completeness)
    
    if not dates:
        print("No processed dates found in the system.")
        return
    
    print(f"\nProcessed Attendance Dates ({len(dates)} total):")
    print("="*80)
    print(f"{'Date':<12} {'Status':<10} {'Completeness':<15} {'Drivers':<8} {'Files':<6} {'Types':<20}")
    print("-"*80)
    
    for date_info in dates:
        date = date_info['date']
        status = date_info['status']
        completeness = f"{date_info['completeness_score']*100:.1f}%"
        drivers = date_info['total_drivers']
        files = date_info['total_files_processed']
        file_types = date_info['file_types']
        
        # Truncate file types if too long
        if len(file_types) > 20:
            file_types = file_types[:17] + "..."
        
        # Color coding for status
        if status == 'complete':
            status_str = f"\033[92m{status}\033[0m"  # Green
        elif status == 'partial':
            status_str = f"\033[93m{status}\033[0m"  # Yellow
        else:
            status_str = status
        
        print(f"{date:<12} {status_str:<10} {completeness:<15} {drivers:<8} {files:<6} {file_types:<20}")
    
    print("="*80)
    print("Use 'date-details <date>' command for more information about a specific date.")

def date_details_command(args):
    """Show details for a specific date command"""
    date = args.date
    
    details = get_date_audit_details(date)
    
    if 'error' in details:
        print(f"Error: {details['error']}")
        return
    
    summary = details['summary']
    file_details = details['file_details']
    driver_stats = details['driver_stats']
    
    print(f"\nAttendance Details for {date}")
    print("="*80)
    
    # Summary section
    print("SUMMARY:")
    print(f"  Status:       {summary['status']}")
    print(f"  Completeness: {summary['completeness_score']*100:.1f}%")
    print(f"  Last Updated: {summary['last_updated']}")
    print(f"  Total Drivers: {summary['total_drivers']}")
    print(f"  Files Processed: {summary['total_files_processed']}")
    
    # Driver statistics
    print("\nDRIVER STATISTICS:")
    print(f"  Unique Drivers: {driver_stats['unique_drivers']}")
    print(f"  Late Count:     {driver_stats['late_count']}")
    print(f"  Early Count:    {driver_stats['early_count']}")
    print(f"  Total Records:  {driver_stats['total_records']}")
    
    # File processing details
    print("\nFILE SOURCES:")
    print(f"{'Timestamp':<20} {'File Type':<15} {'Drivers':<8} {'Records':<8} {'Status':<10} {'File Path'}")
    print("-"*100)
    
    for file in file_details:
        timestamp = file['timestamp'].split('T')[1][:8]  # Just show time HH:MM:SS
        file_type = file['file_type']
        driver_count = file['driver_count']
        records_added = file['records_added']
        status = file['status']
        file_path = file['file_path']
        
        # Truncate file path if too long
        if len(file_path) > 40:
            file_path_parts = file_path.split('/')
            file_path = f".../{file_path_parts[-1]}"
        
        # Color coding for status
        if status == 'success':
            status_str = f"\033[92m{status}\033[0m"  # Green
        elif status == 'partial':
            status_str = f"\033[93m{status}\033[0m"  # Yellow
        elif status == 'failed':
            status_str = f"\033[91m{status}\033[0m"  # Red
        else:
            status_str = status
        
        print(f"{timestamp:<20} {file_type:<15} {driver_count:<8} {records_added:<8} {status_str:<10} {file_path}")

def generate_report_command(args):
    """Generate audit report command"""
    output_path = args.output
    
    if not output_path:
        # Default to data/audit/attendance_report_YYYY-MM-DD.json
        today = datetime.now().strftime('%Y-%m-%d')
        output_path = f"data/audit/attendance_report_{today}.json"
    
    print(f"Generating attendance audit report to {output_path}...")
    report = generate_audit_report(output_path)
    
    print(f"Report generated with {report['total_dates_processed']} processed dates.")
    print(f"Complete dates: {report['dates_by_completeness']['complete']}")
    print(f"Partial dates: {report['dates_by_completeness']['partial']}")
    print(f"Report saved to {output_path}")

def run_pipeline_command(args):
    """Run the attendance pipeline command"""
    # Set up the database and audit tables
    setup_database()
    setup_audit_database()
    
    # Run the pipeline
    print("Running attendance data pipeline...")
    processed_dates = run_attendance_pipeline()
    
    if processed_dates:
        print(f"Successfully processed {len(processed_dates)} dates:")
        for date in processed_dates:
            print(f"  - {date}")
    else:
        print("No attendance data processed.")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Attendance Audit CLI')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List dates command
    list_parser = subparsers.add_parser('list-dates', help='List all processed dates')
    list_parser.add_argument('--min-completeness', type=float, default=0.0,
                           help='Minimum completeness score (0.0-1.0) to include')
    
    # Date details command
    details_parser = subparsers.add_parser('date-details', help='Show details for a specific date')
    details_parser.add_argument('date', help='Date in YYYY-MM-DD format')
    
    # Generate report command
    report_parser = subparsers.add_parser('generate-report', help='Generate audit report')
    report_parser.add_argument('--output', help='Path to save the JSON report')
    
    # Run pipeline command
    run_parser = subparsers.add_parser('run-pipeline', help='Run the attendance pipeline')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up audit database
    setup_audit_database()
    
    if args.command == 'list-dates':
        list_dates_command(args)
    elif args.command == 'date-details':
        date_details_command(args)
    elif args.command == 'generate-report':
        generate_report_command(args)
    elif args.command == 'run-pipeline':
        run_pipeline_command(args)
    else:
        parser.print_help()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())