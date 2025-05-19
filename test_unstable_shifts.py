#!/usr/bin/env python3
"""
Specific test for the unstable shift detection functionality
"""

import logging
from trend_report import parse_time_to_minutes, has_unstable_shifts, UNSTABLE_SHIFT_THRESHOLD

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_unstable_shifts_detection():
    """Test the unstable shift detection function with clear test cases"""
    print("Testing unstable shift detection")
    
    # Test case 1: Highly variable start times (should be detected)
    start_times_1 = [
        ("2025-05-15", "06:00 AM"),
        ("2025-05-16", "09:30 AM"),  # 3.5 hour difference
        ("2025-05-17", "07:00 AM"),
        ("2025-05-18", "09:00 AM"),
        ("2025-05-19", "06:30 AM")
    ]
    
    end_times_1 = [
        ("2025-05-15", "02:30 PM"),
        ("2025-05-16", "06:00 PM"),
        ("2025-05-17", "03:30 PM"),
        ("2025-05-18", "05:30 PM"),
        ("2025-05-19", "03:00 PM")
    ]
    
    print("\nTest Case 1: Highly variable start/end times")
    print("Start times:", [t[1] for t in start_times_1])
    print("End times:", [t[1] for t in end_times_1])
    
    # Print parsed minutes for debugging
    print("\nStart times (minutes since midnight):")
    for date, time_str in start_times_1:
        minutes = parse_time_to_minutes(time_str)
        print(f"{time_str} = {minutes} minutes")
    
    print("\nEnd times (minutes since midnight):")
    for date, time_str in end_times_1:
        minutes = parse_time_to_minutes(time_str)
        print(f"{time_str} = {minutes} minutes")
        
    # Calculate expected time differences
    start_minutes = [parse_time_to_minutes(t[1]) for t in start_times_1]
    start_diff = max(start_minutes) - min(start_minutes)
    
    end_minutes = [parse_time_to_minutes(t[1]) for t in end_times_1]
    end_diff = max(end_minutes) - min(end_minutes)
    
    print(f"\nStart time variation: {start_diff} minutes")
    print(f"End time variation: {end_diff} minutes")
    print(f"Threshold: {UNSTABLE_SHIFT_THRESHOLD} minutes")
    
    result_1 = has_unstable_shifts(start_times_1, end_times_1)
    print(f"Result: {'UNSTABLE' if result_1 else 'STABLE'}")
    
    # Test case 2: Consistent times (should NOT be detected)
    start_times_2 = [
        ("2025-05-15", "07:00 AM"),
        ("2025-05-16", "07:15 AM"),
        ("2025-05-17", "07:05 AM"),
        ("2025-05-18", "07:10 AM"),
        ("2025-05-19", "07:00 AM")
    ]
    
    end_times_2 = [
        ("2025-05-15", "03:30 PM"),
        ("2025-05-16", "03:45 PM"),
        ("2025-05-17", "03:30 PM"),
        ("2025-05-18", "04:00 PM"),
        ("2025-05-19", "03:30 PM")
    ]
    
    print("\nTest Case 2: Consistent times")
    result_2 = has_unstable_shifts(start_times_2, end_times_2)
    print(f"Result: {'UNSTABLE' if result_2 else 'STABLE'}")
    
    return

if __name__ == "__main__":
    test_unstable_shifts_detection()