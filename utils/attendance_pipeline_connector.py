"""
Attendance Pipeline Connector

This module serves as a centralized connector between data sources and UI views.
It standardizes access to attendance data across the application, ensuring consistent
data flow from processors to templates.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd

# Import utility modules
from utils.attendance_pipeline import process_attendance_data
from utils.attendance_processor import analyze_attendance_records
from utils.trend_analyzer import detect_attendance_trends, identify_chronic_issues
from utils.attendance_audit import get_data_audit_log

# Configure logging
logger = logging.getLogger(__name__)

# Global cache to reduce processing overhead
_attendance_data_cache = {}
_trend_data_cache = {}
_audit_log_cache = None
_driver_list_cache = None


def get_attendance_data(date_str=None):
    """
    Get processed attendance data for the specified date.
    
    Args:
        date_str (str): Date string in format YYYY-MM-DD, defaults to today
        
    Returns:
        dict: Processed attendance data with late, early end, and not-on-job records
    """
    global _attendance_data_cache
    
    # Default to today if no date provided
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Return cached data if available
    if date_str in _attendance_data_cache:
        logger.info(f"Using cached attendance data for {date_str}")
        return _attendance_data_cache[date_str]
    
    try:
        # Process raw attendance data through the pipeline
        attendance_records = process_attendance_data(date_str)
        
        # Analyze records to categorize them
        late_start_records, early_end_records, not_on_job_records = analyze_attendance_records(attendance_records)
        
        # Calculate summary statistics
        total_drivers = len(set([r.get('driver_name') for r in attendance_records if r.get('driver_name')]))
        late_count = len(late_start_records)
        early_count = len(early_end_records)
        missing_count = len(not_on_job_records)
        
        # Format timestamps to ensure consistent display
        for records in [late_start_records, early_end_records, not_on_job_records]:
            for record in records:
                # Ensure time fields are properly formatted for display
                for field in ['scheduled_start', 'actual_start', 'scheduled_end', 'actual_end']:
                    if field in record and record[field] and isinstance(record[field], datetime):
                        record[field] = record[field].strftime('%H:%M')
        
        # Create result dictionary with all needed data
        result = {
            'date': date_str,
            'total_drivers': total_drivers,
            'late_start_records': late_start_records,
            'early_end_records': early_end_records,
            'not_on_job_records': not_on_job_records,
            'late_count': late_count,
            'early_count': early_count,
            'missing_count': missing_count,
            'on_time_percent': round(100 * (total_drivers - late_count) / total_drivers if total_drivers > 0 else 0, 1)
        }
        
        # Cache the results
        _attendance_data_cache[date_str] = result
        logger.info(f"Loaded attendance data for {date_str}: {len(attendance_records)} records")
        
        return result
    except Exception as e:
        logger.error(f"Error loading attendance data: {e}")
        # Return empty data structure on error
        return {
            'date': date_str,
            'total_drivers': 0,
            'late_start_records': [],
            'early_end_records': [],
            'not_on_job_records': [],
            'late_count': 0,
            'early_count': 0,
            'missing_count': 0,
            'on_time_percent': 0
        }


def get_trend_data(end_date_str=None, days=7):
    """
    Get attendance trend data for the specified date range.
    
    Args:
        end_date_str (str): End date string in format YYYY-MM-DD, defaults to today
        days (int): Number of days to analyze, defaults to 7
        
    Returns:
        dict: Attendance trend data with chronic issues
    """
    global _trend_data_cache
    
    # Generate cache key based on parameters
    if end_date_str is None:
        end_date_str = datetime.now().strftime('%Y-%m-%d')
    
    cache_key = f"{end_date_str}_{days}"
    
    # Return cached data if available
    if cache_key in _trend_data_cache:
        logger.info(f"Using cached trend data for {cache_key}")
        return _trend_data_cache[cache_key]
    
    try:
        # Calculate date range
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        start_date = end_date - timedelta(days=days-1)
        
        # Get attendance data for each day in the range
        daily_data = []
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            current_date_str = current_date.strftime('%Y-%m-%d')
            
            # Get data for each day
            data = get_attendance_data(current_date_str)
            daily_data.append(data)
        
        # Detect trends across the date range
        trends = detect_attendance_trends(daily_data)
        
        # Identify chronic issues
        chronic_lates, repeated_absences, unstable_shifts = identify_chronic_issues(daily_data)
        
        # Compile all trend data
        result = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date_str,
            'days': days,
            'daily_data': daily_data,
            'trends': trends,
            'chronic_lates': chronic_lates,
            'repeated_absences': repeated_absences,
            'unstable_shifts': unstable_shifts
        }
        
        # Cache the results
        _trend_data_cache[cache_key] = result
        
        return result
    except Exception as e:
        logger.error(f"Error calculating trend data: {e}")
        # Return empty data structure on error
        return {
            'start_date': start_date.strftime('%Y-%m-%d') if 'start_date' in locals() else None,
            'end_date': end_date_str,
            'days': days,
            'daily_data': [],
            'trends': {},
            'chronic_lates': [],
            'repeated_absences': [],
            'unstable_shifts': []
        }


def get_attendance_audit_log():
    """
    Get audit log of data processing activities.
    
    Returns:
        list: List of audit log entries
    """
    global _audit_log_cache
    
    # Use cached data if available
    if _audit_log_cache is not None:
        return _audit_log_cache
    
    try:
        # Get audit log entries
        audit_log = get_data_audit_log()
        
        # Cache the results
        _audit_log_cache = audit_log
        
        return audit_log
    except Exception as e:
        logger.error(f"Error getting audit log: {e}")
        return []


def get_driver_list():
    """
    Get list of all drivers with attendance history.
    
    Returns:
        list: List of driver records with attendance history
    """
    global _driver_list_cache
    
    # Use cached data if available
    if _driver_list_cache is not None:
        return _driver_list_cache
    
    try:
        # Get data for the last 30 days
        end_date = datetime.now()
        end_date_str = end_date.strftime('%Y-%m-%d')
        start_date = end_date - timedelta(days=30)
        
        # Get attendance data for each day in the range
        all_records = []
        driver_stats = defaultdict(lambda: {
            'name': '',
            'total_days': 0,
            'late_days': 0,
            'early_end_days': 0,
            'not_on_job_days': 0,
            'on_time_percent': 0,
            'avg_late_minutes': 0,
            'avg_early_minutes': 0
        })
        
        # Analyze each day
        current_date = start_date
        while current_date <= end_date:
            current_date_str = current_date.strftime('%Y-%m-%d')
            
            # Get data for the day
            data = get_attendance_data(current_date_str)
            
            # Process late start records
            for record in data.get('late_start_records', []):
                driver_name = record.get('driver_name')
                if driver_name:
                    driver_stats[driver_name]['name'] = driver_name
                    driver_stats[driver_name]['total_days'] += 1
                    driver_stats[driver_name]['late_days'] += 1
                    
                    # Calculate average late minutes
                    late_minutes = record.get('late_minutes', 0)
                    current_avg = driver_stats[driver_name]['avg_late_minutes']
                    current_count = driver_stats[driver_name]['late_days']
                    driver_stats[driver_name]['avg_late_minutes'] = ((current_avg * (current_count - 1)) + late_minutes) / current_count
            
            # Process early end records
            for record in data.get('early_end_records', []):
                driver_name = record.get('driver_name')
                if driver_name:
                    driver_stats[driver_name]['name'] = driver_name
                    driver_stats[driver_name]['total_days'] += 1
                    driver_stats[driver_name]['early_end_days'] += 1
                    
                    # Calculate average early minutes
                    early_minutes = record.get('early_minutes', 0)
                    current_avg = driver_stats[driver_name]['avg_early_minutes']
                    current_count = driver_stats[driver_name]['early_end_days']
                    driver_stats[driver_name]['avg_early_minutes'] = ((current_avg * (current_count - 1)) + early_minutes) / current_count
            
            # Process not on job records
            for record in data.get('not_on_job_records', []):
                driver_name = record.get('driver_name')
                if driver_name:
                    driver_stats[driver_name]['name'] = driver_name
                    driver_stats[driver_name]['total_days'] += 1
                    driver_stats[driver_name]['not_on_job_days'] += 1
            
            # Move to next day
            current_date += timedelta(days=1)
        
        # Calculate on-time percentage for each driver
        for driver_name, stats in driver_stats.items():
            if stats['total_days'] > 0:
                stats['on_time_percent'] = round(100 * (stats['total_days'] - stats['late_days']) / stats['total_days'], 1)
        
        # Convert defaultdict to list and sort by name
        driver_list = list(driver_stats.values())
        driver_list.sort(key=lambda x: x['name'])
        
        # Cache the results
        _driver_list_cache = driver_list
        
        return driver_list
    except Exception as e:
        logger.error(f"Error getting driver list: {e}")
        return []


def clear_caches():
    """
    Clear all data caches to force fresh data retrieval.
    """
    global _attendance_data_cache, _trend_data_cache, _audit_log_cache, _driver_list_cache
    
    _attendance_data_cache = {}
    _trend_data_cache = {}
    _audit_log_cache = None
    _driver_list_cache = None
    
    logger.info("Cleared all attendance data caches")