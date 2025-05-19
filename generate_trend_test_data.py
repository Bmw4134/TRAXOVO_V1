#!/usr/bin/env python3
"""
Generate Test Data for Attendance Trend Analysis

This script creates sample attendance data spanning multiple days 
with intentional patterns like chronic lateness, repeated absences,
and unstable shift times to test the trend analysis system.
"""

import os
import sys
import csv
import json
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from time_utils import parse_time, format_time
from driver_utils import normalize_driver_name

# Configure test parameters
NUM_DAYS = 5
NUM_DRIVERS = 10
TEST_DATE = datetime.now() - timedelta(days=NUM_DAYS)
OUTPUT_DIR = 'test_data'

# Driver patterns for testing
DRIVER_PATTERNS = [
    {
        'name': 'JOHN ALWAYS_LATE',
        'pattern': 'chronic_late',
        'details': {'late_days': 4, 'start_variance': 30}  # minutes late
    },
    {
        'name': 'MARIA LEAVES_EARLY',
        'pattern': 'early_end',
        'details': {'early_days': 3, 'end_variance': 45}  # minutes early
    },
    {
        'name': 'ROBERT MOSTLY_ABSENT',
        'pattern': 'absent',
        'details': {'absent_days': 3}
    },
    {
        'name': 'JAMES UNSTABLE_SHIFTS',
        'pattern': 'unstable',
        'details': {'shift_variance': 180}  # 3 hours variance
    },
    {
        'name': 'SARAH COMBINED_ISSUES',
        'pattern': 'combined',
        'details': {
            'late_days': 3,
            'absent_days': 2,
            'start_variance': 25
        }
    },
    # Regular drivers with no issues
    {'name': 'DAVID REGULAR', 'pattern': 'normal'},
    {'name': 'LISA ONTIME', 'pattern': 'normal'},
    {'name': 'MICHAEL GOODWORKER', 'pattern': 'normal'},
    {'name': 'JENNIFER CONSISTENT', 'pattern': 'normal'},
    {'name': 'WILLIAM RELIABLE', 'pattern': 'normal'},
]

def generate_test_data():
    """Generate test data for trend analysis"""
    print(f"Generating test data for {NUM_DAYS} days...")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Generate data for each day
    for day_offset in range(NUM_DAYS):
        current_date = TEST_DATE + timedelta(days=day_offset)
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Prepare daily data
        output_file = os.path.join(OUTPUT_DIR, f'DailyUsage_{date_str}.csv')
        daily_data = generate_daily_usage(date_str, day_offset)
        
        # Write to CSV
        with open(output_file, 'w', newline='') as f:
            # Write header rows
            f.write('DailyUsage Report\n')
            f.write(f'Date: {date_str}\n')
            for _ in range(5):
                f.write('\n')
                
            # Write actual data
            fieldnames = ['Asset', 'Driver', 'Company', 'Job Site', 'Date', 
                         'Time Start', 'Time Stop', 'Duration', 'Status']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(daily_data)
            
        print(f"Created {output_file} with {len(daily_data)} records")
    
    print("Test data generation complete!")

def generate_daily_usage(date_str, day_offset):
    """Generate daily usage data for a specific date"""
    records = []
    
    for i, driver in enumerate(DRIVER_PATTERNS):
        # Base record with standard shift
        record = {
            'Asset': f"{'ET' if i % 2 == 0 else 'PT'}-{i+10} {driver['name']}",
            'Driver': driver['name'],
            'Company': 'TEST COMPANY INC',
            'Job Site': f"Site {chr(65 + i % 5)}",  # Sites A-E
            'Date': date_str,
            'Time Start': '07:00 AM',
            'Time Stop': '03:30 PM',
            'Duration': '8.5',
            'Status': 'Active'
        }
        
        # Apply pattern modifications
        pattern = driver['pattern']
        details = driver.get('details', {})
        
        if pattern == 'chronic_late':
            # Driver is late on most days
            late_days = details.get('late_days', 3)
            if day_offset < late_days:
                late_minutes = random.randint(15, details.get('start_variance', 60))
                start_time = parse_time('07:00 AM')
                start_time_with_delay = datetime.combine(datetime.today(), start_time) + timedelta(minutes=late_minutes)
                record['Time Start'] = start_time_with_delay.strftime('%I:%M %p')
                
        elif pattern == 'early_end':
            # Driver leaves early on some days
            early_days = details.get('early_days', 2)
            if day_offset < early_days:
                early_minutes = random.randint(20, details.get('end_variance', 60))
                end_time = parse_time('03:30 PM')
                end_time_early = datetime.combine(datetime.today(), end_time) - timedelta(minutes=early_minutes)
                record['Time Stop'] = end_time_early.strftime('%I:%M %p')
                
        elif pattern == 'absent':
            # Driver is absent on specified days
            absent_days = details.get('absent_days', 2)
            if day_offset < absent_days:
                # Remove time data for absent days
                record['Time Start'] = ''
                record['Time Stop'] = ''
                record['Duration'] = '0'
                
        elif pattern == 'unstable':
            # Driver has highly variable shift times
            if day_offset % 2 == 0:
                # Early shift
                record['Time Start'] = '06:00 AM'
                record['Time Stop'] = '02:30 PM'
            else:
                # Late shift
                variance = details.get('shift_variance', 180)  # 3 hours
                record['Time Start'] = '09:00 AM'
                record['Time Stop'] = '05:30 PM'
                
        elif pattern == 'combined':
            # Driver with multiple issues
            if day_offset % 3 == 0:
                # Late day
                late_minutes = random.randint(15, details.get('start_variance', 30))
                start_time = parse_time('07:00 AM')
                start_time_with_delay = datetime.combine(datetime.today(), start_time) + timedelta(minutes=late_minutes)
                record['Time Start'] = start_time_with_delay.strftime('%I:%M %p')
            elif day_offset % 3 == 1:
                # Absent day
                record['Time Start'] = ''
                record['Time Stop'] = ''
                record['Duration'] = '0'
        
        # Add the record
        records.append(record)
    
    return records

if __name__ == "__main__":
    generate_test_data()