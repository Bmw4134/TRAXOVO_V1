#!/usr/bin/env python3
"""
TRAXORA GENIUS CORE | Driver Reporting Test Script

This script tests the driver reporting pipeline by processing 
sample driving history and activity detail files, generating reports,
and verifying the results.
"""

import os
import sys
import json
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Import our daily report pipeline
sys.path.append('.')
from daily_report_pipeline_revision import DriverReportPipeline
from utils.genius_core_driver_processor import process_uploaded_files

# Sample data paths
DRIVING_HISTORY_PATH = "attached_assets/DrivingHistory.csv"
ACTIVITY_DETAIL_PATH = "attached_assets/ActivityDetail (6).csv"

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

def test_driver_reporting_pipeline():
    """Test the driver reporting pipeline directly"""
    logger.info("Testing driver reporting pipeline directly")
    
    ensure_dirs()
    
    # Determine the date from the driving history file
    date_str = None
    try:
        import pandas as pd
        df = pd.read_csv(DRIVING_HISTORY_PATH)
        if 'Date' in df.columns:
            # Get the first date in the file
            date_str = df['Date'].iloc[0]
            
            # Try to parse the date
            if isinstance(date_str, str):
                # Try different formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        date_obj = datetime.strptime(date_str, fmt).date()
                        date_str = date_obj.strftime('%Y-%m-%d')
                        break
                    except ValueError:
                        continue
    except Exception as e:
        logger.error(f"Error determining date from driving history: {e}")
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    logger.info(f"Using date: {date_str}")
    
    # Copy sample files to the expected locations
    date_formatted = date_str.replace('-', '')
    driving_history_target = f"data/driving_history/DrivingHistory_{date_formatted}.csv"
    activity_detail_target = f"data/activity_detail/ActivityDetail_{date_formatted}.csv"
    
    shutil.copy(DRIVING_HISTORY_PATH, driving_history_target)
    shutil.copy(ACTIVITY_DETAIL_PATH, activity_detail_target)
    
    # Initialize and run the pipeline
    pipeline = DriverReportPipeline(date_str)
    
    pipeline.extract_equipment_billing_data()
    pipeline.extract_driving_history()
    pipeline.extract_activity_detail()
    pipeline.process_drivers()
    report_data = pipeline.generate_report()
    
    # Save the report data to JSON file
    json_path = f"reports/daily_drivers/daily_report_{date_str}.json"
    with open(json_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    # Save as Excel for easy viewing
    try:
        import pandas as pd
        excel_path = f"reports/daily_drivers/daily_report_{date_str}.xlsx"
        df = pd.DataFrame(report_data['drivers'])
        df.to_excel(excel_path, index=False)
    except Exception as e:
        logger.error(f"Error saving Excel report: {e}")
    
    # Print report summary
    print("\n== DRIVER REPORT SUMMARY ==")
    print(f"Date: {date_str}")
    print(f"Total drivers: {report_data['summary']['total']}")
    print(f"On time: {report_data['summary']['on_time']}")
    print(f"Late: {report_data['summary']['late']}")
    print(f"Early end: {report_data['summary']['early_end']}")
    print(f"Not on job: {report_data['summary']['not_on_job']}")
    print(f"Unmatched: {report_data['summary'].get('unmatched', 0)}")
    print(f"Report file: {json_path}")
    
    return report_data

def test_processor_integration():
    """Test the integration with the web processor"""
    logger.info("Testing processor integration")
    
    # Process the files using the web processor
    result = process_uploaded_files(
        DRIVING_HISTORY_PATH,
        ACTIVITY_DETAIL_PATH
    )
    
    print("\n== PROCESSOR INTEGRATION TEST ==")
    if result.get('success'):
        print(f"Success: {result.get('success')}")
        print(f"Date: {result.get('date')}")
        print(f"Message: {result.get('message')}")
        summary = result.get('summary', {})
        print(f"Total drivers: {summary.get('total', 0)}")
        print(f"On time: {summary.get('on_time', 0)}")
        print(f"Late: {summary.get('late', 0)}")
        print(f"Early end: {summary.get('early_end', 0)}")
        print(f"Not on job: {summary.get('not_on_job', 0)}")
    else:
        print(f"Error: {result.get('error')}")
    
    return result

if __name__ == "__main__":
    print("TRAXORA GENIUS CORE | Driver Reporting Test")
    print("===========================================")
    
    # Test the pipeline directly
    print("\nRunning direct pipeline test...")
    pipeline_result = test_driver_reporting_pipeline()
    
    # Test the processor integration
    print("\nRunning processor integration test...")
    processor_result = test_processor_integration()
    
    print("\nTest complete!")