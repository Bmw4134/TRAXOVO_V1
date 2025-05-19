#!/usr/bin/env python3
"""
Attendance Trend Report Generator

This script analyzes multi-day attendance data to identify patterns 
such as chronic lateness, repeated absences, and unstable shift times.
It outputs a JSON trend report with detailed driver statistics.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.attendance_processor import process_attendance_data
from driver_utils import normalize_driver_name

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Threshold settings for trend detection
CHRONIC_LATE_THRESHOLD = 3      # Late 3+ times in a week
REPEATED_ABSENCE_THRESHOLD = 2  # Absent 2+ times in a week 
UNSTABLE_SHIFT_THRESHOLD = 180  # Shift time variance >3 hours (180 minutes)

class DriverRecord:
    """Track a driver's attendance across multiple days"""
    
    def __init__(self, name):
        self.name = name
        self.late_count = 0
        self.early_end_count = 0
        self.absence_count = 0
        self.daily_records = {}  # date -> {late: bool, early: bool, absent: bool}
        self.start_times = []  # [(date, time), ...]
        self.end_times = []    # [(date, time), ...]
        
    def add_late(self, date, start_time):
        """Mark the driver as late on a specific date"""
        if date not in self.daily_records:
            self.daily_records[date] = {'late': False, 'early': False, 'absent': False}
            
        # Only count once per day
        if not self.daily_records[date]['late']:
            self.late_count += 1
            self.daily_records[date]['late'] = True
            
        # Add start time for shift stability analysis
        if start_time:
            self.start_times.append((date, start_time))
            
    def add_early_end(self, date, end_time):
        """Mark the driver as leaving early on a specific date"""
        if date not in self.daily_records:
            self.daily_records[date] = {'late': False, 'early': False, 'absent': False}
            
        # Only count once per day
        if not self.daily_records[date]['early']:
            self.early_end_count += 1
            self.daily_records[date]['early'] = True
            
        # Add end time for shift stability analysis
        if end_time:
            self.end_times.append((date, end_time))
            
    def add_absence(self, date):
        """Mark the driver as absent on a specific date"""
        if date not in self.daily_records:
            self.daily_records[date] = {'late': False, 'early': False, 'absent': False}
            
        # Only count once per day
        if not self.daily_records[date]['absent']:
            self.absence_count += 1
            self.daily_records[date]['absent'] = True
    
    def get_flags(self):
        """Get list of attendance issue flags for this driver"""
        flags = []
        
        if self.late_count >= CHRONIC_LATE_THRESHOLD:
            flags.append('CHRONIC_LATE')
            
        if self.absence_count >= REPEATED_ABSENCE_THRESHOLD:
            flags.append('REPEATED_ABSENCE')
            
        if has_unstable_shifts(self.start_times, self.end_times):
            flags.append('UNSTABLE_SHIFT')
            
        return flags
        
    def to_dict(self):
        """Convert driver record to dictionary for JSON output"""
        return {
            'name': self.name,
            'late_count': self.late_count,
            'early_end_count': self.early_end_count,
            'absence_count': self.absence_count,
            'days_analyzed': len(self.daily_records),
            'flags': self.get_flags(),
            'daily_records': self.daily_records
        }
        
    def __str__(self):
        return f"{self.name}: late={self.late_count}, early={self.early_end_count}, absent={self.absence_count}, days={len(self.daily_records)}"

def parse_time_to_minutes(time_str):
    """Convert time string to minutes since midnight"""
    try:
        # Handle common time formats (with AM/PM)
        if 'AM' in time_str or 'PM' in time_str:
            time_obj = datetime.strptime(time_str, '%I:%M %p')
            # Convert 12-hour format to 24-hour
            hour = time_obj.hour
            if 'PM' in time_str and hour < 12:
                hour += 12
            elif 'AM' in time_str and hour == 12:
                hour = 0
        else:
            time_obj = datetime.strptime(time_str, '%H:%M')
            hour = time_obj.hour
            
        return hour * 60 + time_obj.minute
    except (ValueError, TypeError):
        logger.warning(f"Could not parse time string: {time_str}")
        return None

def has_unstable_shifts(start_times, end_times):
    """
    Determine if a driver has unstable shift times.
    
    Args:
        start_times: List of (date, time_str) tuples
        end_times: List of (date, time_str) tuples
        
    Returns:
        bool: True if shifts are unstable, False otherwise
    """
    if len(start_times) < 2 or len(end_times) < 2:
        return False
        
    # Extract and convert times to minutes after midnight
    start_minutes = []
    for date, time_str in start_times:
        minutes = parse_time_to_minutes(time_str)
        if minutes is not None:
            start_minutes.append((date, minutes))
            
    end_minutes = []
    for date, time_str in end_times:
        minutes = parse_time_to_minutes(time_str)
        if minutes is not None:
            end_minutes.append((date, minutes))
    
    # Need at least 2 valid times for comparison
    if len(start_minutes) < 2:
        return False
        
    # Check for unstable start times (maximum variation)
    start_values = [minutes for _, minutes in start_minutes]
    if start_values:
        start_min = min(start_values)
        start_max = max(start_values)
        start_diff = start_max - start_min
        
        logger.info(f"Start time variation: {start_diff} minutes (min={start_min}, max={start_max})")
        if start_diff >= UNSTABLE_SHIFT_THRESHOLD:
            logger.info(f"UNSTABLE_SHIFT: Start time variation of {start_diff} minutes exceeds threshold of {UNSTABLE_SHIFT_THRESHOLD}")
            return True
            
    # Check for unstable end times (maximum variation)
    end_values = [minutes for _, minutes in end_minutes]
    if end_values and len(end_values) >= 2:
        end_min = min(end_values)
        end_max = max(end_values)
        end_diff = end_max - end_min
        
        logger.info(f"End time variation: {end_diff} minutes (min={end_min}, max={end_max})")
        if end_diff >= UNSTABLE_SHIFT_THRESHOLD:
            logger.info(f"UNSTABLE_SHIFT: End time variation of {end_diff} minutes exceeds threshold of {UNSTABLE_SHIFT_THRESHOLD}")
            return True
    
    # Check for shift duration stability
    if len(start_minutes) >= 2 and len(end_minutes) >= 2:
        # Build map of dates to shift durations
        shift_durations = {}
        
        for date, start_minute in start_minutes:
            for end_date, end_minute in end_minutes:
                if date == end_date:
                    duration = end_minute - start_minute
                    if duration > 0:  # Valid shift duration
                        shift_durations[date] = duration
        
        # Check variation in shift duration if we have at least 2 valid days
        if len(shift_durations) >= 2:
            durations = list(shift_durations.values())
            min_duration = min(durations)
            max_duration = max(durations)
            duration_diff = max_duration - min_duration
            
            logger.info(f"Shift duration variation: {duration_diff} minutes (min={min_duration}, max={max_duration})")
            if duration_diff >= UNSTABLE_SHIFT_THRESHOLD:
                logger.info(f"UNSTABLE_SHIFT: Shift duration variation of {duration_diff} minutes exceeds threshold of {UNSTABLE_SHIFT_THRESHOLD}")
                return True
            
    return False

def generate_trend_report(dates=None, days=5, output_path=None):
    """
    Generate a trend report for the specified dates or recent days.
    
    Args:
        dates: List of specific dates to analyze in 'YYYY-MM-DD' format
        days: Number of recent days to analyze (if dates not provided)
        output_path: Path to save the JSON report
        
    Returns:
        dict: Trend analysis report
    """
    # Determine dates to analyze
    if not dates:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days-1)
        dates = []
        for i in range(days):
            date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            dates.append(date)
            
    logger.info(f"Analyzing attendance trends for {len(dates)} days: {', '.join(dates)}")
    
    # Create result structure
    report = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'date_range': {
            'start': dates[0],
            'end': dates[-1]
        },
        'days_analyzed': len(dates),
        'daily_summaries': {},
        'drivers': [],
        'summary': {
            'total_drivers': 0,
            'chronic_late_count': 0,
            'repeated_absence_count': 0,
            'unstable_shift_count': 0
        }
    }
    
    # Track all drivers across all dates
    driver_records = {}  # normalized_name -> DriverRecord
    
    # Process attendance data for each date
    for date in dates:
        attendance_data = process_attendance_data(date)
        if not attendance_data:
            logger.warning(f"No attendance data found for {date}")
            continue
            
        # Add daily summary
        report['daily_summaries'][date] = {
            'late_count': len(attendance_data.get('late_drivers', [])),
            'early_end_count': len(attendance_data.get('early_end_drivers', [])),
            'absent_count': len(attendance_data.get('not_on_job_drivers', []))
        }
        
        # Process late drivers
        for driver in attendance_data.get('late_drivers', []):
            name = driver.get('driver', '')
            if not name:
                continue
                
            normalized_name = normalize_driver_name(name)
            
            # Create record if this is first occurrence
            if normalized_name not in driver_records:
                driver_records[normalized_name] = DriverRecord(name)
                
            # Update driver record
            start_time = driver.get('time_start', '')
            driver_records[normalized_name].add_late(date, start_time)
            
        # Process early end drivers
        for driver in attendance_data.get('early_end_drivers', []):
            name = driver.get('driver', '')
            if not name:
                continue
                
            normalized_name = normalize_driver_name(name)
            
            # Create record if this is first occurrence
            if normalized_name not in driver_records:
                driver_records[normalized_name] = DriverRecord(name)
                
            # Update driver record
            end_time = driver.get('time_stop', '')
            driver_records[normalized_name].add_early_end(date, end_time)
            
        # Process absent drivers
        for driver in attendance_data.get('not_on_job_drivers', []):
            name = driver.get('driver', '')
            if not name:
                continue
                
            normalized_name = normalize_driver_name(name)
            
            # Create record if this is first occurrence
            if normalized_name not in driver_records:
                driver_records[normalized_name] = DriverRecord(name)
                
            # Update driver record
            driver_records[normalized_name].add_absence(date)
    
    # Generate driver trend entries
    flagged_drivers = {
        'CHRONIC_LATE': 0,
        'REPEATED_ABSENCE': 0,
        'UNSTABLE_SHIFT': 0
    }
    
    for record in driver_records.values():
        driver_entry = record.to_dict()
        report['drivers'].append(driver_entry)
        
        # Update summary counts
        for flag in driver_entry['flags']:
            if flag in flagged_drivers:
                flagged_drivers[flag] += 1
    
    # Update summary statistics
    report['summary']['total_drivers'] = len(driver_records)
    report['summary']['chronic_late_count'] = flagged_drivers['CHRONIC_LATE']
    report['summary']['repeated_absence_count'] = flagged_drivers['REPEATED_ABSENCE']
    report['summary']['unstable_shift_count'] = flagged_drivers['UNSTABLE_SHIFT']
    
    # Save report if output path provided
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Trend report saved to {output_path}")
    
    return report

def main():
    """Main function to generate trend report for current date"""
    today = datetime.now().strftime('%Y-%m-%d')
    output_path = f'trend_report_{today}.json'
    
    report = generate_trend_report(days=5, output_path=output_path)
    
    # Print summary
    print("\nAttendance Trend Report Summary:")
    print(f"Analyzed {report['days_analyzed']} days")
    print(f"Total drivers: {report['summary']['total_drivers']}")
    print(f"Drivers with chronic lateness: {report['summary']['chronic_late_count']}")
    print(f"Drivers with repeated absences: {report['summary']['repeated_absence_count']}")
    print(f"Drivers with unstable shifts: {report['summary']['unstable_shift_count']}")
    print(f"\nFull report saved to {output_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())