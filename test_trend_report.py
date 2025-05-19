#!/usr/bin/env python3
"""
Test the Attendance Trend Report Generator with synthetic test data.

This script creates test data for drivers with various attendance patterns
and runs it through the trend report generator to verify pattern detection.
"""

import sys
import json
import logging
from datetime import datetime, timedelta

# Local imports
from trend_report import generate_trend_report, DriverRecord
from driver_utils import normalize_driver_name

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_data():
    """Create test data with known attendance patterns"""
    # Define attendance patterns
    patterns = {
        "JOHN ALWAYS_LATE": {
            "pattern": "chronic_late",
            "late_days": 5,  # Late all 5 days
            "times": ["07:30 AM", "07:45 AM", "07:35 AM", "07:40 AM", "07:25 AM"]
        },
        "MARIA LEAVES_EARLY": {
            "pattern": "early_end",
            "early_days": 4,  # Leaves early 4 out of 5 days
            "times": ["02:30 PM", "02:45 PM", "02:15 PM", "02:40 PM", "03:30 PM"]
        },
        "ROBERT MOSTLY_ABSENT": {
            "pattern": "absent",
            "absent_days": [0, 1, 3]  # Absent on day indices 0, 1, and 3
        },
        "JAMES UNSTABLE_SHIFTS": {
            "pattern": "unstable",
            "start_times": ["06:00 AM", "09:30 AM", "07:00 AM", "09:00 AM", "06:30 AM"],
            "end_times": ["02:30 PM", "06:00 PM", "03:30 PM", "05:30 PM", "03:00 PM"]
        }, 
        "SARAH COMBINED_ISSUES": {
            "pattern": "combined",
            "late_days": [0, 2, 4],  # Late on indices 0, 2, and 4
            "absent_days": [1, 3]    # Absent on indices 1 and 3
        }
    }
    
    # Generate dates for testing (today and past 4 days)
    today = datetime.now()
    dates = []
    for i in range(5):
        date = (today - timedelta(days=4-i)).strftime('%Y-%m-%d')
        dates.append(date)
    
    # Create mock attendance data for each date
    mock_data = {}
    
    for mock_process_attendance_data in _create_mock_processor(patterns, dates):
        # Replace the real process_attendance_data function temporarily
        import trend_report
        original_function = trend_report.process_attendance_data
        trend_report.process_attendance_data = mock_process_attendance_data
        
        # Generate the report
        output_path = "test_trend_report_results.json"
        report = generate_trend_report(dates=dates, output_path=output_path)
        
        # Restore original function
        trend_report.process_attendance_data = original_function
        
        # Verify results
        print("\nTest Trend Report Results:")
        print(f"Total drivers analyzed: {report['summary']['total_drivers']}")
        print(f"Chronic late drivers: {report['summary']['chronic_late_count']}")
        print(f"Repeated absence drivers: {report['summary']['repeated_absence_count']}")
        print(f"Unstable shift drivers: {report['summary']['unstable_shift_count']}")
        
        # Check if our pattern drivers were correctly flagged
        expected_flags = {
            normalize_driver_name("JOHN ALWAYS_LATE"): ["CHRONIC_LATE"],
            normalize_driver_name("ROBERT MOSTLY_ABSENT"): ["REPEATED_ABSENCE"],
            normalize_driver_name("JAMES UNSTABLE_SHIFTS"): ["UNSTABLE_SHIFT"],
            normalize_driver_name("SARAH COMBINED_ISSUES"): ["CHRONIC_LATE", "REPEATED_ABSENCE"]
        }
        
        print("\nChecking driver flag detection:")
        for driver_data in report['drivers']:
            name = normalize_driver_name(driver_data['name'])
            if name in expected_flags:
                expected = set(expected_flags[name])
                actual = set(driver_data['flags'])
                match = expected == actual
                
                print(f"{driver_data['name']}:")
                print(f"  Expected: {', '.join(expected_flags[name])}")
                print(f"  Actual: {', '.join(driver_data['flags'])}")
                print(f"  Status: {'✓ PASS' if match else '✗ FAIL'}")
                print(f"  Days: late={driver_data['late_count']}, absent={driver_data['absence_count']}")
                
        # Return report for further inspection
        return report

def _create_mock_processor(patterns, dates):
    """Create a mock attendance data processor function"""
    
    def mock_process_attendance_data(date=None):
        """Mock implementation of process_attendance_data"""
        if not date or date not in dates:
            return {}
        
        day_idx = dates.index(date)
        
        # Initialize attendance data structure
        attendance_data = {
            'date': date,
            'all_drivers': [],
            'late_drivers': [],
            'early_end_drivers': [],
            'not_on_job_drivers': []
        }
        
        # Add pattern drivers
        for name, pattern_data in patterns.items():
            driver_info = {
                'driver': name,
                'asset': f"{'ET' if day_idx % 2 == 0 else 'PT'}-{day_idx+10} {name}",
                'job_site': f"Site {chr(65 + day_idx % 5)}",  # Sites A-E
                'time_start': '07:00 AM',
                'time_stop': '03:30 PM',
                'status': 'Active'
            }
            
            pattern_type = pattern_data['pattern']
            
            # Apply the specific pattern for this day
            if pattern_type == 'chronic_late':
                driver_info['time_start'] = pattern_data['times'][day_idx]
                attendance_data['late_drivers'].append(driver_info.copy())
                logger.info(f"Date {date}: {name} is LATE, arrived at {pattern_data['times'][day_idx]}")
                
            elif pattern_type == 'early_end':
                driver_info['time_stop'] = pattern_data['times'][day_idx]
                
                # Only add to early_end list if truly early
                if pattern_data['times'][day_idx] < '03:00 PM':
                    attendance_data['early_end_drivers'].append(driver_info.copy())
                    logger.info(f"Date {date}: {name} LEFT EARLY at {pattern_data['times'][day_idx]}")
                
            elif pattern_type == 'absent':
                if day_idx in pattern_data['absent_days']:
                    driver_info['time_start'] = ''
                    driver_info['time_stop'] = ''
                    attendance_data['not_on_job_drivers'].append(driver_info.copy())
                    logger.info(f"Date {date}: {name} is ABSENT")
                
            elif pattern_type == 'unstable':
                driver_info['time_start'] = pattern_data['start_times'][day_idx]
                driver_info['time_stop'] = pattern_data['end_times'][day_idx]
                
                # Add to late if appropriate
                if pattern_data['start_times'][day_idx] > '07:15 AM':
                    attendance_data['late_drivers'].append(driver_info.copy())
                    
                logger.info(f"Date {date}: {name} SHIFT {pattern_data['start_times'][day_idx]} - {pattern_data['end_times'][day_idx]}")
                
            elif pattern_type == 'combined':
                # Apply late pattern if applicable
                if 'late_days' in pattern_data and day_idx in pattern_data['late_days']:
                    driver_info['time_start'] = '07:35 AM'
                    attendance_data['late_drivers'].append(driver_info.copy())
                    logger.info(f"Date {date}: {name} is LATE")
                
                # Apply absent pattern if applicable
                if 'absent_days' in pattern_data and day_idx in pattern_data['absent_days']:
                    driver_info['time_start'] = ''
                    driver_info['time_stop'] = ''
                    attendance_data['not_on_job_drivers'].append(driver_info.copy())
                    logger.info(f"Date {date}: {name} is ABSENT")
            
            # Always add to all_drivers unless absent
            if pattern_type != 'absent' or day_idx not in pattern_data.get('absent_days', []):
                if not (pattern_type == 'combined' and day_idx in pattern_data.get('absent_days', [])):
                    attendance_data['all_drivers'].append(driver_info)
        
        # Add some regular drivers (no issues)
        for i, name in enumerate(['DAVID REGULAR', 'LISA ONTIME', 'MICHAEL GOODWORKER']):
            driver_info = {
                'driver': name,
                'asset': f"{'PT' if day_idx % 2 == 0 else 'ET'}-{i+30}",
                'job_site': f"Site {chr(65 + (day_idx + i) % 5)}",
                'time_start': '07:00 AM',
                'time_stop': '03:30 PM',
                'status': 'Active'
            }
            attendance_data['all_drivers'].append(driver_info)
        
        # Log the data created for this date
        logger.info(f"Generated mock data for {date}: {len(attendance_data['late_drivers'])} late, "
                    f"{len(attendance_data['early_end_drivers'])} early end, "
                    f"{len(attendance_data['not_on_job_drivers'])} absent")
                   
        return attendance_data
    
    return [mock_process_attendance_data]

if __name__ == "__main__":
    create_test_data()