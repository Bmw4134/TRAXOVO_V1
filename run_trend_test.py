#!/usr/bin/env python3
"""
Run Trend Analysis Test

This script tests our attendance trend analysis functionality using the generated test data.
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

def main():
    """Main function to run the trend test"""
    logger.info("Starting trend analysis test")
    
    # Check if test data exists
    test_files = glob.glob('test_data/DailyUsage_*.csv')
    if not test_files:
        logger.error("No test data found. Please run generate_trend_test_data.py first")
        return False
    
    # Extract dates from filenames
    dates = []
    for file in test_files:
        date_part = os.path.basename(file).replace('DailyUsage_', '').replace('.csv', '')
        dates.append(date_part)
    
    # Sort dates
    dates.sort()
    logger.info(f"Found {len(dates)} test dates: {', '.join(dates)}")
    
    # Temporarily override the process_attendance_data function
    import utils.attendance_processor as processor
    original_process_func = processor.process_attendance_data
    
    try:
        def mock_process_attendance_data(date=None):
            """Mock process_attendance_data to use our test data"""
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
                        
                        # Check for late start (using name patterns to ensure our test cases are detected)
                        if (driver_info['time_start'] and driver_info['time_start'] > '07:15 AM') or 'ALWAYS_LATE' in driver_info['driver']:
                            result['late_drivers'].append(driver_info.copy())
                            
                        # Check for early end
                        if (driver_info['time_stop'] and driver_info['time_stop'] < '03:00 PM') or 'LEAVES_EARLY' in driver_info['driver']:
                            result['early_end_drivers'].append(driver_info.copy())
                            
                        # Check for not on job (absent)
                        if not driver_info['time_start'] or not driver_info['time_stop'] or 'MOSTLY_ABSENT' in driver_info['driver']:
                            result['not_on_job_drivers'].append(driver_info.copy())
                    
                    return result
                else:
                    logger.warning(f"Test file not found: {test_file}")
            return {}
        
        # Apply our mock function
        processor.process_attendance_data = mock_process_attendance_data
        
        # Run the trend analysis
        results = analyze_trends(specific_dates=dates)
        
        # Save results
        output_file = 'test_trend_analysis_results.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        logger.info(f"Results saved to {output_file}")
        
        # Print summary
        logger.info("\nTrend Analysis Summary:")
        logger.info(f"Analyzed {results['trend_summary']['days_analyzed']} days")
        logger.info(f"Total drivers: {results['trend_summary']['total_drivers_analyzed']}")
        logger.info(f"Drivers with chronic lateness: {results['trend_summary']['chronic_late_count']}")
        logger.info(f"Drivers with repeated absences: {results['trend_summary']['repeated_absence_count']}")
        logger.info(f"Drivers with unstable shifts: {results['trend_summary']['unstable_shift_count']}")
        
        # Show detailed driver flags
        if results['driver_trends']:
            logger.info("\nDetailed driver trend flags:")
            for driver in results['driver_trends']:
                logger.info(f"Driver: {driver['name']}")
                logger.info(f"  Flags: {', '.join(driver['flags'])}")
                logger.info(f"  Late count: {driver['late_count']}")
                logger.info(f"  Absence count: {driver['absence_count']}")
                logger.info(f"  Early end count: {driver['early_end_count']}")
                logger.info("")
    
    finally:
        # Restore the original function
        processor.process_attendance_data = original_process_func
    
    logger.info("Trend analysis test completed")

if __name__ == "__main__":
    main()