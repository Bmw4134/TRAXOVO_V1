#!/usr/bin/env python3
"""
Quick Test for Driver Reporting Pipeline

This script performs a basic test of the driver reporting functionality by running
the pipeline directly with sample data files.
"""

import os
import sys
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Use the specific CSV files provided by the user
DRIVING_HISTORY_PATH = "attached_assets/DrivingHistory (14).csv"
ACTIVITY_DETAIL_PATH = "attached_assets/ActivityDetail (10).csv"
ASSETS_TIME_ON_SITE_PATH = "attached_assets/AssetsTimeOnSite (6).csv"
DATE_STR = "2025-05-22"  # Use today's date from the provided files

# Verify files exist
if not os.path.exists(DRIVING_HISTORY_PATH):
    logger.error(f"Driving history file not found: {DRIVING_HISTORY_PATH}")
    # Check for alternatives
    alternatives = [
        "attached_assets/DrivingHistory (13).csv",
        "attached_assets/DrivingHistory.csv",
        "attached_assets/DrivingHistory.xlsx", 
        "attached_assets/Driving_History.csv"
    ]
    for alt in alternatives:
        if os.path.exists(alt):
            DRIVING_HISTORY_PATH = alt
            logger.info(f"Using alternative driving history file: {alt}")
            break

if not os.path.exists(ACTIVITY_DETAIL_PATH):
    logger.error(f"Activity detail file not found: {ACTIVITY_DETAIL_PATH}")
    # Check for alternatives
    alternatives = [
        "attached_assets/ActivityDetail (9).csv",
        "attached_assets/ActivityDetail (7).csv",
        "attached_assets/ActivityDetail (6).csv",
        "attached_assets/ActivityDetail.csv"
    ]
    for alt in alternatives:
        if os.path.exists(alt):
            ACTIVITY_DETAIL_PATH = alt
            logger.info(f"Using alternative activity detail file: {alt}")
            break

if not os.path.exists(ASSETS_TIME_ON_SITE_PATH):
    logger.warning(f"Assets time on site file not found: {ASSETS_TIME_ON_SITE_PATH}")
    # Check for alternatives
    alternatives = [
        "attached_assets/AssetsTimeOnSite (5).csv",
        "attached_assets/AssetsTimeOnSite (4).csv",
        "attached_assets/AssetsTimeOnSite (3).csv",
        "attached_assets/AssetsTimeOnSite.csv"
    ]
    for alt in alternatives:
        if os.path.exists(alt):
            ASSETS_TIME_ON_SITE_PATH = alt
            logger.info(f"Using alternative assets time on site file: {alt}")
            break

def ensure_dirs():
    """Ensure all required directories exist"""
    directories = [
        'data',
        'data/driving_history',
        'data/activity_detail',
        'reports',
        'reports/daily_drivers',
        'exports',
        'exports/daily_reports'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    logger.info("Created required directories")

def test_pipeline():
    """Run a simplified test of the pipeline"""
    logger.info("Starting quick test of driver reporting pipeline")
    
    ensure_dirs()
    
    # Copy sample files to the expected locations
    date_formatted = DATE_STR.replace('-', '')
    driving_history_target = f"data/driving_history/DrivingHistory_{date_formatted}.csv"
    activity_detail_target = f"data/activity_detail/ActivityDetail_{date_formatted}.csv"
    
    shutil.copy(DRIVING_HISTORY_PATH, driving_history_target)
    shutil.copy(ACTIVITY_DETAIL_PATH, activity_detail_target)
    logger.info(f"Copied test files to {driving_history_target} and {activity_detail_target}")
    
    # Initialize and run the pipeline
    from daily_report_pipeline_revision import DriverReportPipeline
    
    pipeline = DriverReportPipeline(DATE_STR)
    
    try:
        logger.info("Extracting equipment billing data...")
        pipeline.extract_equipment_billing_data()
        
        logger.info("Extracting driving history...")
        pipeline.extract_driving_history()
        logger.info(f"Found {len(pipeline.driving_history_data)} driving history records")
        
        logger.info("Extracting activity detail...")
        pipeline.extract_activity_detail()
        logger.info(f"Found {len(pipeline.activity_detail_data)} activity detail records")
        
        logger.info("Processing drivers...")
        pipeline.process_drivers()
        logger.info(f"Processed {len(pipeline.all_driver_records)} driver records")
        logger.info(f"Matched to asset list: {pipeline.total_matched_to_asset_list}")
        
        logger.info("Generating report...")
        report_data = pipeline.generate_report()
        
        # Save the report
        report_file = f"reports/daily_drivers/quick_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Print summary
        print("\n=== DRIVER REPORT SUMMARY ===")
        print(f"Date: {DATE_STR}")
        
        # Handle different report formats gracefully
        if 'summary' in report_data:
            print(f"Total drivers: {report_data['summary'].get('total', 0)}")
            print(f"On time: {report_data['summary'].get('on_time', 0)}")
            print(f"Late: {report_data['summary'].get('late', 0)}")
            print(f"Early end: {report_data['summary'].get('early_end', 0)}")
            print(f"Not on job: {report_data['summary'].get('not_on_job', 0)}")
        else:
            # For newer format where summary might be calculated differently
            print(f"Total drivers processed: {len(report_data.get('drivers', []))}")
            
            # Count statuses directly from driver records
            statuses = {}
            for driver in report_data.get('drivers', []):
                status = driver.get('status', 'unknown')
                statuses[status] = statuses.get(status, 0) + 1
                
            print(f"Status breakdown:")
            for status, count in statuses.items():
                print(f"  - {status}: {count}")
        
        print(f"Report saved to: {report_file}")
        
        return True, report_data
    
    except Exception as e:
        logger.error(f"Error running pipeline: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False, None

if __name__ == "__main__":
    print("TRAXORA GENIUS CORE | Quick Driver Reporting Test")
    print("================================================")
    
    success, report_data = test_pipeline()
    
    if success:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed. See logs for details.")