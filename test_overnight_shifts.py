#!/usr/bin/env python3
"""
Test Overnight Shifts Parsing

This script tests the enhanced time parser's ability to handle overnight shifts with next-day markers.
"""

import sys
from datetime import datetime, time
from time_utils import (
    parse_time, 
    parse_time_with_day_marker, 
    parse_time_with_tz,
    calculate_time_difference,
    calculate_lateness
)

def test_time_parsing():
    """Test time parsing with various formats and next-day markers"""
    print("Testing Time Parsing With Next-Day Markers")
    print("-----------------------------------------")
    
    test_cases = [
        # Normal times (no next-day markers)
        "07:30 AM",
        "15:45",
        "11:00 PM",
        
        # With next-day markers
        "06:00 AM (+1)",
        "07:15 AM (Next Day)",
        "05:30 (+1)",
        "04:45 PM (next day)",
        "06:30 AM Next Day",
        "05:45 +1",
        
        # With timezone markers
        "07:30 AM CT",
        "15:45 ET",
        "06:30 AM CST (+1)",
        "05:15 PM EST (Next Day)"
    ]
    
    print("\nBasic Time Parsing:")
    for tc in test_cases:
        time_obj = parse_time(tc)
        print(f"  {tc:20} -> {time_obj}")
    
    print("\nParsing with Day Markers:")
    for tc in test_cases:
        time_obj, is_next_day = parse_time_with_day_marker(tc)
        print(f"  {tc:20} -> {time_obj} (Next Day: {is_next_day})")
    
    print("\nParsing with Timezone Support:")
    for tc in test_cases:
        time_obj, is_next_day, tz = parse_time_with_tz(tc)
        print(f"  {tc:20} -> {time_obj} (Next Day: {is_next_day}, TZ: {tz})")

def test_time_diff_calculation():
    """Test time difference calculation with next-day markers"""
    print("\nTesting Time Difference Calculation")
    print("---------------------------------")
    
    # Create some test times
    start_times = [
        time(7, 0),   # 7:00 AM
        time(22, 0),  # 10:00 PM
        time(23, 0),  # 11:00 PM
    ]
    
    end_times = [
        time(15, 30),  # 3:30 PM
        time(6, 0),    # 6:00 AM
        time(7, 30),   # 7:30 AM
    ]
    
    # Test different combinations
    for start in start_times:
        for end in end_times:
            # Test without next-day marker
            diff_regular = calculate_time_difference(start, end)
            
            # Test with next-day marker
            diff_next_day = calculate_time_difference(start, end, True)
            
            print(f"  {start.strftime('%I:%M %p')} to {end.strftime('%I:%M %p')}:")
            print(f"    Regular: {diff_regular} minutes")
            print(f"    Next Day: {diff_next_day} minutes")

def test_lateness_calculation():
    """Test lateness calculation with next-day markers"""
    print("\nTesting Lateness Calculation")
    print("---------------------------")
    
    # Define some test cases: (actual time, expected time, threshold, is_next_day)
    test_cases = [
        # Regular same-day scenarios
        (time(7, 15), time(7, 0), 10, False),  # 15 minutes late
        (time(7, 5), time(7, 0), 10, False),   # 5 minutes late (within threshold)
        (time(6, 50), time(7, 0), 5, False),   # Early (negative lateness)
        
        # Overnight shift scenarios
        (time(6, 30), time(7, 0), 10, True),   # Overnight shift, arriving at 6:30 AM next day
        (time(7, 30), time(23, 0), 10, True),  # Overnight shift, arriving at 7:30 AM next day
        (time(0, 15), time(23, 0), 15, True),  # Overnight shift, arriving at 00:15 AM next day
    ]
    
    for i, (actual, expected, threshold, is_next_day) in enumerate(test_cases, 1):
        is_late, minutes_late, formatted = calculate_lateness(
            actual, expected, threshold, is_next_day
        )
        
        actual_str = actual.strftime("%I:%M %p")
        expected_str = expected.strftime("%I:%M %p")
        next_day_str = "(Next Day)" if is_next_day else ""
        
        print(f"  Case {i}: Actual: {actual_str} {next_day_str}, Expected: {expected_str}")
        print(f"    Late: {is_late}, Minutes Late: {minutes_late}, Formatted: {formatted}")

if __name__ == "__main__":
    sys.path.append('.')
    test_time_parsing()
    test_time_diff_calculation()
    test_lateness_calculation()