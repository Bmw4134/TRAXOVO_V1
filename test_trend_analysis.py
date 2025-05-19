#!/usr/bin/env python3
"""
Test the Trend Analysis Module with Generated Test Data

This script uses the test data we've generated to verify the trend analysis
functionality is correctly detecting attendance patterns.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
import glob

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.trend_analyzer_fixed import analyze_trends

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_test_environment():
    """Set up the test environment for testing attendance trends"""
    # Check if test data exists
    test_files = glob.glob('test_data/DailyUsage_*.csv')
    
    if not test_files:
        logger.error("No test data found. Please run generate_trend_test_data.py first")
        return False
        
    # Sort files by date
    test_files.sort()
    logger.info(f"Found {len(test_files)} test data files")
    
    # Get dates from filenames
    dates = []
    for file in test_files:
        date_part = os.path.basename(file).replace('DailyUsage_', '').replace('.csv', '')
        dates.append(date_part)
    
    return dates

def run_trend_analysis(dates):
    """Run trend analysis on the test data"""
    # Temporarily override the default data source
    import utils.attendance_processor as processor
    original_read_func = processor.read_daily_usage_file
    
    def mock_read_daily_usage(date=None, file_path=None, return_all_data=False):
        """Override to read from test data instead of production data"""
        if date:
            test_file = f'test_data/DailyUsage_{date}.csv'
            if os.path.exists(test_file):
                logger.info(f"Reading test data from {test_file}")
                
                # Manual parsing for our test data
                data = []
                with open(test_file, 'r') as f:
                    import csv
                    # Skip the header rows
                    for _ in range(7):  # Skip the first 7 lines
                        next(f, None)
                        
                    # Read the CSV
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row and 'Asset' in row and row['Asset']:
                            data.append(row)
                            
                if return_all_data:
                    return data
                
                # Process the data and return the same structure as the real function
                result = {
                    'date': date,
                    'all_drivers': [],
                    'late_drivers': [],
                    'early_end_drivers': [],
                    'not_on_job_drivers': []
                }
                
                for row in data:
                    driver_info = {
                        'driver': row.get('Driver', ''),
                        'asset': row.get('Asset', ''),
                        'job_site': row.get('Job Site', ''),
                        'time_start': row.get('Time Start', ''),
                        'time_stop': row.get('Time Stop', ''),
                        'status': row.get('Status', '')
                    }
                    
                    # Add to all drivers list
                    if driver_info['driver']:
                        result['all_drivers'].append(driver_info)
                    
                    # Check for late start
                    if driver_info['time_start'] and driver_info['time_start'] > '07:15 AM':
                        result['late_drivers'].append(driver_info)
                        
                    # Check for early end
                    if driver_info['time_stop'] and driver_info['time_stop'] < '03:00 PM':
                        result['early_end_drivers'].append(driver_info)
                        
                    # Check for not on job
                    if not driver_info['time_start'] or not driver_info['time_stop']:
                        result['not_on_job_drivers'].append(driver_info)
                
                return result
            else:
                logger.warning(f"Test file not found: {test_file}")
        return {}
    
    # Apply our override
    processor.read_daily_usage_file = mock_read_daily_usage
    
    try:
        # Run the trend analysis
        results = analyze_trends(specific_dates=dates)
        
        # Save results
        with open('test_trend_analysis_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        logger.info("Trend analysis complete")
        
        # Log the detected trends
        logger.info(f"Analyzed {results['trend_summary']['days_analyzed']} days")
        logger.info(f"Total drivers: {results['trend_summary']['total_drivers_analyzed']}")
        logger.info(f"Drivers with chronic lateness: {results['trend_summary']['chronic_late_count']}")
        logger.info(f"Drivers with repeated absences: {results['trend_summary']['repeated_absence_count']}")
        logger.info(f"Drivers with unstable shifts: {results['trend_summary']['unstable_shift_count']}")
        
        # Print detailed driver trend information
        if results['driver_trends']:
            logger.info("\nDetailed driver trend information:")
            for driver in results['driver_trends']:
                logger.info(f"Driver: {driver['name']}")
                logger.info(f"  Flags: {', '.join(driver['flags'])}")
                logger.info(f"  Late count: {driver['late_count']}")
                logger.info(f"  Absence count: {driver['absence_count']}")
                logger.info(f"  Early end count: {driver['early_end_count']}")
                logger.info("")
        
        return results
    finally:
        # Restore the original function
        processor.read_daily_usage_file = original_read_func

def main():
    """Main function"""
    logger.info("Starting trend analysis test")
    
    dates = setup_test_environment()
    if not dates:
        return
    
    results = run_trend_analysis(dates)
    
    if results:
        logger.info("Test completed successfully")
    else:
        logger.error("Test failed")

if __name__ == "__main__":
    main()