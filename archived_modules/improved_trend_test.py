#!/usr/bin/env python3
"""
Improved Trend Analysis Test

This script tests the multi-day attendance trend analysis functionality 
with special focus on identifying chronic lateness, repeated absences,
and unstable shift patterns.
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
from driver_utils import normalize_driver_name

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thresholds from trend analyzer
CHRONIC_LATE_THRESHOLD = 3     # Number of late days to flag as chronic
REPEATED_ABSENCE_THRESHOLD = 2  # Number of absent days to flag as repeated
UNSTABLE_SHIFT_THRESHOLD = 180  # Minutes (3 hours) of shift time variation

def create_test_attendance_data(file_pattern=None):
    """Create test attendance data with known patterns"""
    # Define our test cases with specific patterns
    test_patterns = {
        'JOHN ALWAYS_LATE': {
            'pattern': 'chronic_late',
            'days': 5,
            'times': ['07:30 AM', '07:35 AM', '07:32 AM', '07:40 AM', '07:25 AM']
        },
        'MARIA LEAVES_EARLY': {
            'pattern': 'early_end',
            'days': 4, 
            'times': ['02:30 PM', '02:45 PM', '02:15 PM', '02:40 PM', '03:30 PM']
        },
        'ROBERT MOSTLY_ABSENT': {
            'pattern': 'absent',
            'days': [0, 1, 3],  # Absent on these days (indices)
        },
        'JAMES UNSTABLE_SHIFTS': {
            'pattern': 'unstable',
            'start_times': ['06:00 AM', '09:00 AM', '07:00 AM', '09:30 AM', '06:30 AM'],
            'end_times': ['02:30 PM', '05:30 PM', '03:30 PM', '06:00 PM', '03:00 PM']
        },
        'SARAH COMBINED_ISSUES': {
            'pattern': 'combined',
            'late_days': [0, 2, 4],  # Late on these days (indices)
            'absent_days': [1, 3]    # Absent on these days (indices)
        }
    }
    
    # Regular drivers (no issues)
    regular_drivers = [
        'DAVID REGULAR', 'LISA ONTIME', 'MICHAEL GOODWORKER', 
        'JENNIFER CONSISTENT', 'WILLIAM RELIABLE'
    ]
    
    # Hard-code dates for consistent testing (use today and previous 4 days)
    today = datetime.now()
    dates = []
    for i in range(5):
        date = (today - timedelta(days=4-i)).strftime('%Y-%m-%d')
        dates.append(date)
    
    logger.info(f"Generated test dates: {dates}")
    
    # Create attendance data for each date
    all_attendance_data = {}
    
    for day_idx, date in enumerate(dates):
        attendance_data = {
            'date': date,
            'all_drivers': [],
            'late_drivers': [],
            'early_end_drivers': [],
            'not_on_job_drivers': []
        }
        
        # Add test pattern drivers
        for name, pattern in test_patterns.items():
            driver_info = {
                'driver': name,
                'asset': f"{'ET' if day_idx % 2 == 0 else 'PT'}-{day_idx+10} {name}",
                'job_site': f"Site {chr(65 + day_idx % 5)}",  # Sites A-E
                'time_start': '07:00 AM',
                'time_stop': '03:30 PM',
                'status': 'Active'
            }
            
            # Apply pattern for this day
            pattern_type = pattern['pattern']
            
            if pattern_type == 'chronic_late':
                # Always late - all 5 days with different late times
                driver_info['time_start'] = pattern['times'][day_idx]
                attendance_data['late_drivers'].append(driver_info.copy())
                logger.info(f"Date {date}: {name} is LATE, arrived at {pattern['times'][day_idx]}")
                    
            elif pattern_type == 'early_end':
                # Always leaves early on 4 of 5 days
                driver_info['time_stop'] = pattern['times'][day_idx]
                if day_idx < 4:  # First 4 days
                    attendance_data['early_end_drivers'].append(driver_info.copy())
                    logger.info(f"Date {date}: {name} LEFT EARLY at {pattern['times'][day_idx]}")
                    
            elif pattern_type == 'absent':
                # Absent on specific days
                if day_idx in pattern['days']:
                    driver_info['time_start'] = ''
                    driver_info['time_stop'] = ''
                    attendance_data['not_on_job_drivers'].append(driver_info.copy())
                    logger.info(f"Date {date}: {name} is ABSENT")
                    
            elif pattern_type == 'unstable':
                # Highly variable shift times
                driver_info['time_start'] = pattern['start_times'][day_idx]
                driver_info['time_stop'] = pattern['end_times'][day_idx]
                if driver_info['time_start'] > '07:15 AM':
                    attendance_data['late_drivers'].append(driver_info.copy())
                logger.info(f"Date {date}: {name} has UNSTABLE shift: {pattern['start_times'][day_idx]} - {pattern['end_times'][day_idx]}")
                    
            elif pattern_type == 'combined':
                # Mix of late and absent days
                if day_idx in pattern.get('late_days', []):
                    driver_info['time_start'] = '07:35 AM'
                    attendance_data['late_drivers'].append(driver_info.copy())
                    logger.info(f"Date {date}: {name} is LATE")
                    
                if day_idx in pattern.get('absent_days', []):
                    driver_info['time_start'] = ''
                    driver_info['time_stop'] = ''
                    attendance_data['not_on_job_drivers'].append(driver_info.copy())
                    logger.info(f"Date {date}: {name} is ABSENT")
            
            # Add to all drivers list (regardless of attendance status)
            attendance_data['all_drivers'].append(driver_info)
        
        # Add regular drivers (no issues)
        for name in regular_drivers:
            driver_info = {
                'driver': name,
                'asset': f"{'ET' if day_idx % 2 == 0 else 'PT'}-{day_idx+20} {name}",
                'job_site': f"Site {chr(65 + day_idx % 5)}",  # Sites A-E
                'time_start': '07:00 AM',
                'time_stop': '03:30 PM',
                'status': 'Active'
            }
            attendance_data['all_drivers'].append(driver_info)
            
        # Ensure our test drivers are in the appropriate lists
        logger.info(f"Date {date}: {len(attendance_data['late_drivers'])} late drivers, " +
                   f"{len(attendance_data['early_end_drivers'])} early end drivers, " +
                   f"{len(attendance_data['not_on_job_drivers'])} absent drivers")
            
        all_attendance_data[date] = attendance_data
    
    return all_attendance_data, dates

def main():
    """Main function to run the improved trend test"""
    logger.info("Starting improved trend analysis test")
    
    # Create test attendance data
    test_data, dates = create_test_attendance_data()
    logger.info(f"Created test data for {len(dates)} dates: {', '.join(dates)}")
    
    # Temporarily override the process_attendance_data function
    import utils.attendance_processor as processor
    original_process_func = processor.process_attendance_data
    
    try:
        def mock_process_attendance_data(date=None):
            """Mock process_attendance_data to use our test data"""
            if date and date in test_data:
                logger.info(f"Processing test data for date: {date}")
                logger.info(f"Late drivers: {len(test_data[date]['late_drivers'])}")
                logger.info(f"Absent drivers: {len(test_data[date]['not_on_job_drivers'])}")
                return test_data[date]
            return {}
        
        # Apply our mock function
        processor.process_attendance_data = mock_process_attendance_data
        
        # Run the trend analysis
        results = analyze_trends(specific_dates=dates)
        
        # Save results
        output_file = 'improved_trend_analysis_results.json'
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
        
        # Check expectations
        logger.info("\nChecking if our test pattern drivers were correctly flagged:")
        
        expected_flags = {
            normalize_driver_name('JOHN ALWAYS_LATE'): ['CHRONIC_LATE'],
            normalize_driver_name('ROBERT MOSTLY_ABSENT'): ['REPEATED_ABSENCE'],
            normalize_driver_name('JAMES UNSTABLE_SHIFTS'): ['UNSTABLE_SHIFT'],
            normalize_driver_name('SARAH COMBINED_ISSUES'): ['CHRONIC_LATE', 'REPEATED_ABSENCE']
        }
        
        for driver in results['driver_trends']:
            name = normalize_driver_name(driver['name'])
            logger.info(f"Driver: {driver['name']}")
            logger.info(f"  Flags: {', '.join(driver['flags'])}")
            logger.info(f"  Late count: {driver['late_count']}")
            logger.info(f"  Absence count: {driver['absence_count']}")
            logger.info(f"  Early end count: {driver['early_end_count']}")
            
            # Check if this driver's flags match expectations
            if name in expected_flags:
                expected = set(expected_flags[name])
                actual = set(driver['flags'])
                if expected == actual:
                    logger.info(f"  ✓ Correctly flagged with {', '.join(expected)}")
                else:
                    logger.info(f"  ✗ Expected flags {', '.join(expected)} but got {', '.join(actual)}")
            logger.info("")
        
        # Check for missing drivers
        analyzed_drivers = {normalize_driver_name(d['name']) for d in results['driver_trends']}
        for name, flags in expected_flags.items():
            if name not in analyzed_drivers:
                logger.warning(f"Driver {name} was not flagged as expected with {', '.join(flags)}")
    
    finally:
        # Restore the original function
        processor.process_attendance_data = original_process_func
    
    logger.info("Improved trend analysis test completed")

if __name__ == "__main__":
    main()