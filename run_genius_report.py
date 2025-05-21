#!/usr/bin/env python3
"""
Run Genius Report

This script runs the TRAXORA Genius Processor to generate and validate a Daily Driver Report
for the specified date with full data integrity checks and validation.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Make sure logs directory exists
os.makedirs('logs', exist_ok=True)

# Add file handler for this script
file_handler = logging.FileHandler('logs/run_genius_report.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

def verify_report_consistency(date_str):
    """Verify report consistency across all output formats"""
    logger.info(f"Verifying report consistency for {date_str}")
    
    reports_dir = Path('reports/daily_drivers')
    exports_dir = Path('exports/daily_reports')
    
    # Define expected files
    expected_files = {
        'reports_json': reports_dir / f"daily_report_{date_str}.json",
        'reports_excel': reports_dir / f"daily_report_{date_str}.xlsx",
        'reports_pdf': reports_dir / f"daily_report_{date_str}.pdf",
        'exports_json': exports_dir / f"daily_report_{date_str}.json",
        'exports_excel': exports_dir / f"{date_str}_DailyDriverReport.xlsx",
        'exports_excel_legacy': exports_dir / f"daily_report_{date_str}.xlsx",
        'exports_pdf': exports_dir / f"{date_str}_DailyDriverReport.pdf",
        'exports_pdf_legacy': exports_dir / f"daily_report_{date_str}.pdf"
    }
    
    # Check file existence
    missing_files = []
    for file_type, file_path in expected_files.items():
        if not file_path.exists():
            missing_files.append(f"{file_type}: {file_path}")
    
    if missing_files:
        logger.error(f"Missing files: {', '.join(missing_files)}")
        return False
    
    # Load JSON data from reports directory
    try:
        with open(expected_files['reports_json'], 'r') as f:
            reports_data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading reports JSON: {e}")
        return False
    
    # Load JSON data from exports directory
    try:
        with open(expected_files['exports_json'], 'r') as f:
            exports_data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading exports JSON: {e}")
        return False
    
    # Verify summary counts match between files
    reports_summary = reports_data.get('summary', {})
    exports_summary = exports_data.get('summary', {})
    
    if reports_summary.get('total') != exports_summary.get('total'):
        logger.error(f"Total count mismatch: {reports_summary.get('total')} != {exports_summary.get('total')}")
        return False
    
    if reports_summary.get('late') != exports_summary.get('late'):
        logger.error(f"Late count mismatch: {reports_summary.get('late')} != {exports_summary.get('late')}")
        return False
    
    if reports_summary.get('early_end') != exports_summary.get('early_end'):
        logger.error(f"Early end count mismatch: {reports_summary.get('early_end')} != {exports_summary.get('early_end')}")
        return False
    
    if reports_summary.get('not_on_job') != exports_summary.get('not_on_job'):
        logger.error(f"Not on job count mismatch: {reports_summary.get('not_on_job')} != {exports_summary.get('not_on_job')}")
        return False
    
    if reports_summary.get('on_time') != exports_summary.get('on_time'):
        logger.error(f"On time count mismatch: {reports_summary.get('on_time')} != {exports_summary.get('on_time')}")
        return False
    
    # Verify driver count matches summary total
    reports_drivers = reports_data.get('drivers', [])
    exports_drivers = exports_data.get('drivers', [])
    
    if len(reports_drivers) != reports_summary.get('total'):
        logger.error(f"Driver count mismatch in reports: {len(reports_drivers)} != {reports_summary.get('total')}")
        return False
    
    if len(exports_drivers) != exports_summary.get('total'):
        logger.error(f"Driver count mismatch in exports: {len(exports_drivers)} != {exports_summary.get('total')}")
        return False
    
    # Verify PDF file sizes are reasonable (not empty)
    min_pdf_size = 1024  # 1 KB minimum
    
    for pdf_path in [expected_files['reports_pdf'], expected_files['exports_pdf'], expected_files['exports_pdf_legacy']]:
        if pdf_path.stat().st_size < min_pdf_size:
            logger.error(f"PDF file too small (possibly corrupt): {pdf_path}, size: {pdf_path.stat().st_size} bytes")
            return False
    
    logger.info(f"Report consistency verified for {date_str}")
    return True

def generate_and_verify_report(date_str):
    """Generate and verify a report for the specified date"""
    logger.info(f"Generating and verifying report for {date_str}")
    
    try:
        # Import the genius processor
        sys.path.append('.')
        from genius_processor import process_and_export
        
        # Start timer
        start_time = datetime.now()
        
        # Process and export report
        result = process_and_export(date_str)
        
        # End timer
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if result['status'] != 'SUCCESS':
            logger.error(f"Report generation failed: {result.get('error', 'Unknown error')}")
            return False
        
        logger.info(f"Report generated successfully in {duration:.2f} seconds")
        
        # Verify report consistency
        if not verify_report_consistency(date_str):
            logger.error("Report consistency verification failed")
            return False
        
        # Print summary information
        summary = result.get('summary', {})
        logger.info(f"Report summary for {date_str}:")
        logger.info(f"  - Total drivers: {summary.get('total')}")
        logger.info(f"  - Late: {summary.get('late')}")
        logger.info(f"  - Early end: {summary.get('early_end')}")
        logger.info(f"  - Not on job: {summary.get('not_on_job')}")
        logger.info(f"  - On time: {summary.get('on_time')}")
        
        # Calculate percentages
        total = summary.get('total', 0)
        if total > 0:
            late_pct = summary.get('late', 0) / total * 100
            early_end_pct = summary.get('early_end', 0) / total * 100
            not_on_job_pct = summary.get('not_on_job', 0) / total * 100
            on_time_pct = summary.get('on_time', 0) / total * 100
            
            logger.info(f"Percentage breakdown:")
            logger.info(f"  - Late: {late_pct:.1f}%")
            logger.info(f"  - Early end: {early_end_pct:.1f}%")
            logger.info(f"  - Not on job: {not_on_job_pct:.1f}%")
            logger.info(f"  - On time: {on_time_pct:.1f}%")
        
        # Print output file paths
        file_paths = result.get('file_paths', {})
        logger.info("Output files:")
        for file_type, file_path in file_paths.items():
            if file_type != 'status':
                logger.info(f"  - {file_type}: {file_path}")
        
        logger.info("Report generation and verification completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error generating or verifying report: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Genius Report')
    parser.add_argument('date', help='Date in YYYY-MM-DD format')
    parser.add_argument('--verify-only', action='store_true', help='Only verify consistency without generating')
    
    args = parser.parse_args()
    
    if args.verify_only:
        logger.info(f"Verifying report consistency for {args.date}")
        if verify_report_consistency(args.date):
            print(f"Report for {args.date} is consistent across all output formats.")
        else:
            print(f"Report for {args.date} has consistency issues. See logs for details.")
    else:
        logger.info(f"Generating and verifying report for {args.date}")
        if generate_and_verify_report(args.date):
            print(f"Report for {args.date} generated and verified successfully.")
        else:
            print(f"Report for {args.date} failed generation or verification. See logs for details.")

if __name__ == '__main__':
    main()