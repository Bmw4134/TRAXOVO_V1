#!/usr/bin/env python3
"""
Test Overnight Shifts in Attendance Processing

This script tests the enhanced attendance processor's ability to handle overnight shifts with next-day markers
by creating specialized test data and running it through the processor.
"""

import sys
import json
import csv
import os
from datetime import datetime, timedelta
import random

def create_test_data_with_overnight_shifts():
    """Create test data file with overnight shift scenarios"""
    print("Creating test data with overnight shift scenarios...")
    
    # Test data file path
    test_file = 'overnight_test.csv'
    
    # Create the headers and basic structure - mimicking DailyUsage.csv format
    headers = [
        'Asset', 'Driver', 'Company', 'Job Site', 'Date', 
        'Time Start', 'Time Stop', 'Duration', 'Status'
    ]
    
    # Today's date for test data
    today = datetime.now().strftime('%Y-%m-%d')
    
    # List of test drivers with various overnight shift scenarios
    test_drivers = [
        # Regular day shifts (control group)
        {
            'Asset': 'PT-01 JOHN SMITH', 
            'Driver': 'JOHN SMITH',
            'Company': 'CONSTRUCTION INC', 
            'Job Site': 'Site A', 
            'Date': today,
            'Time Start': '07:00 AM', 
            'Time Stop': '03:30 PM',
            'Duration': '8.5',
            'Status': 'Active'
        },
        {
            'Asset': 'ET-02 JANE DOE', 
            'Driver': 'JANE DOE',
            'Company': 'CONSTRUCTION INC', 
            'Job Site': 'Site B', 
            'Date': today,
            'Time Start': '07:15 AM', 
            'Time Stop': '03:15 PM',
            'Duration': '8.0',
            'Status': 'Active'
        },
        
        # Overnight shifts with (+1) format
        {
            'Asset': 'PT-03 ROBERT JOHNSON', 
            'Driver': 'ROBERT JOHNSON',
            'Company': 'NIGHT CONSTRUCTION', 
            'Job Site': 'Site C', 
            'Date': today,
            'Time Start': '10:00 PM', 
            'Time Stop': '06:00 AM (+1)',
            'Duration': '8.0',
            'Status': 'Active'
        },
        {
            'Asset': 'CT-04 MARIA GARCIA', 
            'Driver': 'MARIA GARCIA',
            'Company': 'NIGHT CONSTRUCTION', 
            'Job Site': 'Site D', 
            'Date': today,
            'Time Start': '11:30 PM', 
            'Time Stop': '07:30 AM (+1)',
            'Duration': '8.0',
            'Status': 'Active'
        },
        
        # Overnight shifts with (Next Day) format
        {
            'Asset': 'ET-05 JAMES WILSON', 
            'Driver': 'JAMES WILSON',
            'Company': 'NIGHT CONSTRUCTION', 
            'Job Site': 'Site E', 
            'Date': today,
            'Time Start': '09:00 PM', 
            'Time Stop': '05:00 AM (Next Day)',
            'Duration': '8.0',
            'Status': 'Active'
        },
        
        # Overnight shift starting late
        {
            'Asset': 'PT-06 JENNIFER BROWN', 
            'Driver': 'JENNIFER BROWN',
            'Company': 'NIGHT CONSTRUCTION', 
            'Job Site': 'Site F', 
            'Date': today,
            'Time Start': '11:15 PM', 
            'Time Stop': '06:00 AM (+1)',
            'Duration': '6.75',
            'Status': 'Active'
        },
        
        # Overnight shift ending early
        {
            'Asset': 'CT-07 DAVID MILLER', 
            'Driver': 'DAVID MILLER',
            'Company': 'NIGHT CONSTRUCTION', 
            'Job Site': 'Site G', 
            'Date': today,
            'Time Start': '10:00 PM', 
            'Time Stop': '04:30 AM (+1)',
            'Duration': '6.5',
            'Status': 'Active'
        },
        
        # Mixed format with time zone
        {
            'Asset': 'ET-08 SARAH JACKSON [HOU]', 
            'Driver': 'SARAH JACKSON',
            'Company': 'HOUSTON DIVISION', 
            'Job Site': 'Site H', 
            'Date': today,
            'Time Start': '10:30 PM CT', 
            'Time Stop': '06:30 AM CST (+1)',
            'Duration': '8.0',
            'Status': 'Active'
        },
        
        # With both start and end next day markers (unusual but possible edge case)
        {
            'Asset': 'PT-09 MICHAEL DAVIS', 
            'Driver': 'MICHAEL DAVIS',
            'Company': 'SPECIAL OPS', 
            'Job Site': 'Site I', 
            'Date': today,
            'Time Start': '12:15 AM (+1)', 
            'Time Stop': '08:15 AM (+1)',
            'Duration': '8.0',
            'Status': 'Active'
        }
    ]
    
    # Write test data to CSV file
    with open(test_file, 'w', newline='') as f:
        # Add header rows mimicking real DailyUsage.csv
        for i in range(7):
            if i == 0:
                f.write('DailyUsage Report\n')
            elif i == 1:
                f.write(f'Date: {today}\n')
            else:
                f.write('\n')
        
        # Create the CSV writer and write the data
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(test_drivers)
    
    print(f"Created test file {test_file} with {len(test_drivers)} test drivers")
    return test_file

def process_test_data(test_file):
    """Process the test data with overnight shifts using the attendance processor"""
    print("Processing test data with overnight shifts...")
    
    # Import the attendance processor
    from utils.attendance_processor import read_daily_usage_file
    
    # Process the test data
    result = read_daily_usage_file(test_file)
    
    # Save the results
    results_file = 'overnight_test_report.json'
    with open(results_file, 'w') as f:
        json.dump(result, f, default=str, indent=2)
    
    print(f"Results saved to {results_file}")
    return result

def analyze_results(result):
    """Analyze the test results to verify proper handling of overnight shifts"""
    print("\nAnalyzing Results:")
    print("-----------------")
    
    # Check how many drivers were identified with issues
    late_count = len(result.get('late_drivers', []))
    early_end_count = len(result.get('early_end_drivers', []))
    not_on_job_count = len(result.get('not_on_job_drivers', []))
    
    print(f"Late drivers: {late_count}")
    print(f"Early end drivers: {early_end_count}")
    print(f"Not on job drivers: {not_on_job_count}")
    
    # Analyze overnight shifts
    print("\nOvernight Shift Analysis:")
    
    # Check for overnight markers in late drivers
    overnight_late_drivers = [
        driver for driver in result.get('late_drivers', [])
        if driver.get('start_is_overnight', False) or 
           '(+1)' in driver.get('time_start', '') or 
           '(Next Day)' in driver.get('time_start', '')
    ]
    print(f"  Overnight late drivers: {len(overnight_late_drivers)}")
    for i, driver in enumerate(overnight_late_drivers, 1):
        print(f"    {i}. {driver.get('driver', 'Unknown')} - {driver.get('time_start', '')} to {driver.get('time_stop', '')}")
        print(f"       Minutes late: {driver.get('minutes_late', 'N/A')}; Lateness text: {driver.get('lateness_text', 'N/A')}")
    
    # Check for overnight markers in early end drivers
    overnight_early_end_drivers = [
        driver for driver in result.get('early_end_drivers', [])
        if driver.get('end_is_overnight', False) or 
           '(+1)' in driver.get('time_stop', '') or 
           '(Next Day)' in driver.get('time_stop', '')
    ]
    print(f"  Overnight early end drivers: {len(overnight_early_end_drivers)}")
    for i, driver in enumerate(overnight_early_end_drivers, 1):
        print(f"    {i}. {driver.get('driver', 'Unknown')} - {driver.get('time_start', '')} to {driver.get('time_stop', '')}")
        print(f"       Minutes early: {driver.get('minutes_early', 'N/A')}; Early text: {driver.get('early_text', 'N/A')}")
    
    # Overall assessment
    if overnight_late_drivers or overnight_early_end_drivers:
        print("\n✅ SUCCESS: Overnight shifts are being properly detected and processed!")
    else:
        print("\n❌ FAILURE: Overnight shifts are not being properly detected.")

def main():
    """Main function to run the overnight shift test"""
    # Create test data with overnight shift scenarios
    test_file = create_test_data_with_overnight_shifts()
    
    # Process the test data
    result = process_test_data(test_file)
    
    # Analyze the results
    analyze_results(result)

if __name__ == "__main__":
    sys.path.append('.')
    main()