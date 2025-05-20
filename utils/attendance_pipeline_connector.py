"""
Attendance Pipeline Connector

This module serves as a centralized interface between the data processing pipeline
and the UI components, providing consistent data structures and caching.
"""

import os
import json
from datetime import datetime, timedelta
import logging
from pathlib import Path
import random

# Import structured logger
from utils.structured_logger import get_pipeline_logger

# Import pipeline processor
from utils.attendance_pipeline import process_attendance_data

# Import Start Time & Job parser
from utils.start_time_parser import extract_start_time_data, merge_start_time_with_attendance

# Get logger
logger = get_pipeline_logger()

# Cache for attendance data
_attendance_cache = {}
_trend_cache = {}
_driver_list_cache = {}
_audit_log = []

# Constants
DEFAULT_CACHE_TTL = 3600  # 1 hour in seconds


def _log_audit(action, details=None):
    """Log an audit entry"""
    audit_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'action': action,
        'details': details or {}
    }
    _audit_log.append(audit_entry)
    logger.info(f"Audit: {action}", extra=audit_entry)
    
    # Keep audit log size limited
    if len(_audit_log) > 1000:
        _audit_log.pop(0)


def _is_cache_valid(cache_key, cache_dict, ttl=DEFAULT_CACHE_TTL):
    """Check if cache is valid"""
    if cache_key not in cache_dict:
        return False
    
    cached_data = cache_dict[cache_key]
    if 'timestamp' not in cached_data:
        return False
    
    # Check if cache is expired
    cache_age = (datetime.now() - cached_data['timestamp']).total_seconds()
    return cache_age < ttl


def _get_or_create_attendance_data(date_str=None, force_refresh=False):
    """Get or create attendance data for a specific date"""
    # Use today's date if not specified
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Check if we have valid cached data
    if not force_refresh and _is_cache_valid(date_str, _attendance_cache):
        logger.info(f"Using cached attendance data for {date_str}")
        return _attendance_cache[date_str]['data']
    
    # Process attendance data
    logger.info(f"Processing attendance data for {date_str}")
    attendance_records = process_attendance_data(date_str)
    
    # Try to get additional data from Start Time & Job sheet
    start_time_data = extract_start_time_data(date_str)
    if start_time_data is not None:
        logger.info(f"Found Start Time & Job data for {date_str} with {len(start_time_data)} records")
    else:
        logger.info(f"No Start Time & Job data found for {date_str}")
    
    # Categorize records
    late_start_records = []
    early_end_records = []
    not_on_job_records = []
    
    for record in attendance_records:
        # Late starts
        if 'late_minutes' in record and record['late_minutes'] > 0:
            late_start_records.append({
                'driver_name': record['driver_name'],
                'job_site': record.get('job_site', 'Unknown'),
                'scheduled_start': record.get('scheduled_start', '07:00'),
                'actual_start': record.get('actual_start', ''),
                'late_minutes': record['late_minutes'],
                'asset_id': record.get('asset_id', '')
            })
        
        # Early ends
        if 'early_minutes' in record and record['early_minutes'] > 0:
            early_end_records.append({
                'driver_name': record['driver_name'],
                'job_site': record.get('job_site', 'Unknown'),
                'scheduled_end': record.get('scheduled_end', '17:00'),
                'actual_end': record.get('actual_end', ''),
                'early_minutes': record['early_minutes'],
                'asset_id': record.get('asset_id', '')
            })
        
        # Not on job (missing actual_start)
        if not record.get('actual_start') and record.get('scheduled_start'):
            not_on_job_records.append({
                'driver_name': record['driver_name'],
                'job_site': record.get('job_site', 'Unknown'),
                'scheduled_start': record.get('scheduled_start', '07:00'),
                'asset_id': record.get('asset_id', '')
            })
    
    # Create structured data
    structured_data = {
        'date': date_str,
        'total_drivers': len(attendance_records),
        'late_start_records': sorted(late_start_records, key=lambda x: x.get('late_minutes', 0), reverse=True),
        'early_end_records': sorted(early_end_records, key=lambda x: x.get('early_minutes', 0), reverse=True),
        'not_on_job_records': not_on_job_records,
        'late_count': len(late_start_records),
        'early_count': len(early_end_records),
        'missing_count': len(not_on_job_records),
        'on_time_percent': round(100 * (len(attendance_records) - len(late_start_records) - len(not_on_job_records)) / 
                                max(1, len(attendance_records)), 1),
        'drivers': attendance_records  # Include the full driver records for merging
    }
    
    # Merge with Start Time & Job data if available
    if start_time_data is not None:
        structured_data = merge_start_time_with_attendance(structured_data, start_time_data)
        logger.info(f"Merged Start Time & Job data with attendance records")
    
    # Cache the data
    _attendance_cache[date_str] = {
        'timestamp': datetime.now(),
        'data': structured_data
    }
    
    # Log audit entry
    _log_audit('attendance_data_processed', {
        'date': date_str,
        'total_records': len(attendance_records),
        'late_count': len(late_start_records),
        'early_count': len(early_end_records),
        'missing_count': len(not_on_job_records),
        'start_time_data_integrated': start_time_data is not None
    })
    
    return structured_data


def _detect_chronic_lates(driver_data, threshold=3, days=5):
    """Detect drivers with chronic lateness"""
    chronic_lates = []
    
    for driver_name, data in driver_data.items():
        late_days = data.get('late_days', [])
        if len(late_days) >= threshold:
            recent_lates = [date for date in late_days 
                            if (datetime.now() - datetime.strptime(date, '%Y-%m-%d')).days <= days]
            if len(recent_lates) >= threshold:
                chronic_lates.append({
                    'name': driver_name,
                    'count': len(recent_lates),
                    'dates': recent_lates
                })
    
    return sorted(chronic_lates, key=lambda x: x['count'], reverse=True)


def _detect_repeated_absences(driver_data, threshold=2, days=7):
    """Detect drivers with repeated absences"""
    repeated_absences = []
    
    for driver_name, data in driver_data.items():
        absent_days = data.get('not_on_job_days', [])
        if len(absent_days) >= threshold:
            recent_absences = [date for date in absent_days 
                               if (datetime.now() - datetime.strptime(date, '%Y-%m-%d')).days <= days]
            if len(recent_absences) >= threshold:
                repeated_absences.append({
                    'name': driver_name,
                    'count': len(recent_absences),
                    'dates': recent_absences
                })
    
    return sorted(repeated_absences, key=lambda x: x['count'], reverse=True)


def _detect_unstable_shifts(driver_data, threshold=180):  # 3 hours in minutes
    """Detect drivers with unstable shift patterns"""
    unstable_shifts = []
    
    for driver_name, data in driver_data.items():
        start_times = data.get('start_times', [])
        if len(start_times) >= 3:  # Need at least 3 days to detect patterns
            # Convert time strings to minutes
            minute_values = []
            for time_str in start_times:
                if time_str:
                    try:
                        time_obj = datetime.strptime(time_str, '%H:%M')
                        minutes = time_obj.hour * 60 + time_obj.minute
                        minute_values.append(minutes)
                    except ValueError:
                        pass
            
            if len(minute_values) >= 3:
                earliest = min(minute_values)
                latest = max(minute_values)
                variance = latest - earliest
                
                if variance >= threshold:
                    unstable_shifts.append({
                        'name': driver_name,
                        'variance_minutes': variance,
                        'earliest': earliest,
                        'latest': latest,
                        'count': len(minute_values)
                    })
    
    return sorted(unstable_shifts, key=lambda x: x['variance_minutes'], reverse=True)


def _get_or_create_trend_data(start_date=None, end_date=None, days=7, force_refresh=False):
    """Get or create trend data for a date range"""
    # Default to last 7 days if not specified
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    if not start_date:
        start_date = (datetime.now() - timedelta(days=days-1)).strftime('%Y-%m-%d')
    
    # Create cache key
    cache_key = f"{start_date}_{end_date}"
    
    # Check if we have valid cached data
    if not force_refresh and _is_cache_valid(cache_key, _trend_cache):
        logger.info(f"Using cached trend data for {start_date} to {end_date}")
        return _trend_cache[cache_key]['data']
    
    # Generate date range
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    date_range = []
    current_dt = start_dt
    
    while current_dt <= end_dt:
        date_range.append(current_dt.strftime('%Y-%m-%d'))
        current_dt += timedelta(days=1)
    
    # Get attendance data for each date
    daily_data = []
    late_trend = []
    early_end_trend = []
    not_on_job_trend = []
    dates = []
    
    # Collect driver-specific data for trend analysis
    driver_data = {}
    
    for date_str in date_range:
        attendance_data = _get_or_create_attendance_data(date_str)
        daily_data.append(attendance_data)
        
        # Calculate percentages for trends
        total_drivers = attendance_data['total_drivers']
        if total_drivers > 0:
            late_percent = round(100 * attendance_data['late_count'] / total_drivers, 1)
            early_percent = round(100 * attendance_data['early_count'] / total_drivers, 1)
            not_on_job_percent = round(100 * attendance_data['missing_count'] / total_drivers, 1)
        else:
            late_percent = 0
            early_percent = 0
            not_on_job_percent = 0
        
        late_trend.append(late_percent)
        early_end_trend.append(early_percent)
        not_on_job_trend.append(not_on_job_percent)
        dates.append(date_str)
        
        # Collect driver-specific data
        for record in attendance_data['late_start_records']:
            driver_name = record['driver_name']
            if driver_name not in driver_data:
                driver_data[driver_name] = {
                    'late_days': [],
                    'early_end_days': [],
                    'not_on_job_days': [],
                    'late_minutes': [],
                    'early_minutes': [],
                    'start_times': []
                }
            
            driver_data[driver_name]['late_days'].append(date_str)
            driver_data[driver_name]['late_minutes'].append(record.get('late_minutes', 0))
            driver_data[driver_name]['start_times'].append(record.get('actual_start'))
        
        for record in attendance_data['early_end_records']:
            driver_name = record['driver_name']
            if driver_name not in driver_data:
                driver_data[driver_name] = {
                    'late_days': [],
                    'early_end_days': [],
                    'not_on_job_days': [],
                    'late_minutes': [],
                    'early_minutes': [],
                    'start_times': []
                }
            
            driver_data[driver_name]['early_end_days'].append(date_str)
            driver_data[driver_name]['early_minutes'].append(record.get('early_minutes', 0))
        
        for record in attendance_data['not_on_job_records']:
            driver_name = record['driver_name']
            if driver_name not in driver_data:
                driver_data[driver_name] = {
                    'late_days': [],
                    'early_end_days': [],
                    'not_on_job_days': [],
                    'late_minutes': [],
                    'early_minutes': [],
                    'start_times': []
                }
            
            driver_data[driver_name]['not_on_job_days'].append(date_str)
    
    # Calculate trend analyses
    chronic_lates = _detect_chronic_lates(driver_data)
    repeated_absences = _detect_repeated_absences(driver_data)
    unstable_shifts = _detect_unstable_shifts(driver_data)
    
    # Calculate total metrics
    total_late_minutes = []
    total_early_minutes = []
    
    for driver_name, data in driver_data.items():
        total_late_minutes.extend(data['late_minutes'])
        total_early_minutes.extend(data['early_minutes'])
    
    avg_late_minutes = round(sum(total_late_minutes) / max(1, len(total_late_minutes)), 1)
    avg_early_minutes = round(sum(total_early_minutes) / max(1, len(total_early_minutes)), 1)
    
    # Create structured trend data
    trend_data = {
        'start_date': start_date,
        'end_date': end_date,
        'days': len(date_range),
        'daily_data': daily_data,
        'trends': {
            'late_trend': late_trend,
            'early_end_trend': early_end_trend,
            'not_on_job_trend': not_on_job_trend,
            'dates': dates,
            'average_late_minutes': avg_late_minutes,
            'average_early_minutes': avg_early_minutes,
            'total_drivers': len(driver_data)
        },
        'chronic_lates': chronic_lates,
        'repeated_absences': repeated_absences,
        'unstable_shifts': unstable_shifts
    }
    
    # Cache the data
    _trend_cache[cache_key] = {
        'timestamp': datetime.now(),
        'data': trend_data
    }
    
    # Log audit entry
    _log_audit('trend_data_processed', {
        'start_date': start_date,
        'end_date': end_date,
        'days': len(date_range),
        'total_drivers': len(driver_data)
    })
    
    return trend_data


def _get_or_create_driver_list(start_date=None, end_date=None, days=30, force_refresh=False):
    """Get or create driver list with attendance history"""
    # Default to last 30 days if not specified
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    if not start_date:
        start_date = (datetime.now() - timedelta(days=days-1)).strftime('%Y-%m-%d')
    
    # Create cache key
    cache_key = f"{start_date}_{end_date}"
    
    # Check if we have valid cached data
    if not force_refresh and _is_cache_valid(cache_key, _driver_list_cache):
        logger.info(f"Using cached driver list for {start_date} to {end_date}")
        return _driver_list_cache[cache_key]['data']
    
    # Get trend data for date range
    trend_data = _get_or_create_trend_data(start_date, end_date, force_refresh=force_refresh)
    
    # Create driver list from trend data
    driver_records = {}
    
    # Process daily data
    for day_data in trend_data['daily_data']:
        date = day_data['date']
        
        # Process late starts
        for record in day_data['late_start_records']:
            driver_name = record['driver_name']
            if driver_name not in driver_records:
                driver_records[driver_name] = {
                    'name': driver_name,
                    'total_days': 0,
                    'late_days': 0,
                    'early_end_days': 0,
                    'not_on_job_days': 0,
                    'total_late_minutes': 0,
                    'total_early_minutes': 0,
                    'job_sites': set(),
                    'assets': set()
                }
            
            driver_records[driver_name]['total_days'] += 1
            driver_records[driver_name]['late_days'] += 1
            driver_records[driver_name]['total_late_minutes'] += record.get('late_minutes', 0)
            
            if record.get('job_site'):
                driver_records[driver_name]['job_sites'].add(record['job_site'])
            
            if record.get('asset_id'):
                driver_records[driver_name]['assets'].add(record['asset_id'])
        
        # Process early ends
        for record in day_data['early_end_records']:
            driver_name = record['driver_name']
            if driver_name not in driver_records:
                driver_records[driver_name] = {
                    'name': driver_name,
                    'total_days': 0,
                    'late_days': 0,
                    'early_end_days': 0,
                    'not_on_job_days': 0,
                    'total_late_minutes': 0,
                    'total_early_minutes': 0,
                    'job_sites': set(),
                    'assets': set()
                }
            
            if driver_records[driver_name]['total_days'] == 0:
                driver_records[driver_name]['total_days'] += 1
                
            driver_records[driver_name]['early_end_days'] += 1
            driver_records[driver_name]['total_early_minutes'] += record.get('early_minutes', 0)
            
            if record.get('job_site'):
                driver_records[driver_name]['job_sites'].add(record['job_site'])
            
            if record.get('asset_id'):
                driver_records[driver_name]['assets'].add(record['asset_id'])
        
        # Process not on job
        for record in day_data['not_on_job_records']:
            driver_name = record['driver_name']
            if driver_name not in driver_records:
                driver_records[driver_name] = {
                    'name': driver_name,
                    'total_days': 0,
                    'late_days': 0,
                    'early_end_days': 0,
                    'not_on_job_days': 0,
                    'total_late_minutes': 0,
                    'total_early_minutes': 0,
                    'job_sites': set(),
                    'assets': set()
                }
            
            driver_records[driver_name]['total_days'] += 1
            driver_records[driver_name]['not_on_job_days'] += 1
            
            if record.get('job_site'):
                driver_records[driver_name]['job_sites'].add(record['job_site'])
            
            if record.get('asset_id'):
                driver_records[driver_name]['assets'].add(record['asset_id'])
    
    # Calculate metrics for each driver
    drivers_list = []
    for driver_name, record in driver_records.items():
        on_time_days = record['total_days'] - record['late_days'] - record['not_on_job_days']
        on_time_percent = round(100 * on_time_days / max(1, record['total_days']), 1)
        
        avg_late_minutes = round(record['total_late_minutes'] / max(1, record['late_days']), 1)
        avg_early_minutes = round(record['total_early_minutes'] / max(1, record['early_end_days']), 1)
        
        driver_data = {
            'name': driver_name,
            'total_days': record['total_days'],
            'late_days': record['late_days'],
            'early_end_days': record['early_end_days'],
            'not_on_job_days': record['not_on_job_days'],
            'on_time_percent': on_time_percent,
            'avg_late_minutes': avg_late_minutes,
            'avg_early_minutes': avg_early_minutes,
            'job_sites': list(record['job_sites']),
            'assets': list(record['assets'])
        }
        
        drivers_list.append(driver_data)
    
    # Sort by name
    drivers_list.sort(key=lambda x: x['name'])
    
    # Cache the data
    _driver_list_cache[cache_key] = {
        'timestamp': datetime.now(),
        'data': drivers_list
    }
    
    # Log audit entry
    _log_audit('driver_list_processed', {
        'start_date': start_date,
        'end_date': end_date,
        'total_drivers': len(drivers_list)
    })
    
    return drivers_list


# Public API functions
def get_attendance_data(date_str=None, force_refresh=False):
    """
    Get attendance data for a specific date.
    
    Args:
        date_str (str): Date string in format YYYY-MM-DD, defaults to today
        force_refresh (bool): Whether to force refresh the data
        
    Returns:
        dict: Structured attendance data
    """
    return _get_or_create_attendance_data(date_str, force_refresh)


def get_trend_data(start_date=None, end_date=None, days=7, force_refresh=False):
    """
    Get trend data for a date range.
    
    Args:
        start_date (str): Start date string in format YYYY-MM-DD
        end_date (str): End date string in format YYYY-MM-DD
        days (int): Number of days if start_date is not specified
        force_refresh (bool): Whether to force refresh the data
        
    Returns:
        dict: Structured trend data
    """
    return _get_or_create_trend_data(start_date, end_date, days, force_refresh)


def get_driver_list(start_date=None, end_date=None, days=30, force_refresh=False):
    """
    Get driver list with attendance history.
    
    Args:
        start_date (str): Start date string in format YYYY-MM-DD
        end_date (str): End date string in format YYYY-MM-DD
        days (int): Number of days if start_date is not specified
        force_refresh (bool): Whether to force refresh the data
        
    Returns:
        list: List of driver records with attendance history
    """
    return _get_or_create_driver_list(start_date, end_date, days, force_refresh)


def get_audit_log(limit=100):
    """
    Get audit log entries.
    
    Args:
        limit (int): Maximum number of entries to return
        
    Returns:
        list: List of audit log entries
    """
    return list(reversed(_audit_log))[:limit]


def clear_cache():
    """Clear all caches"""
    global _attendance_cache, _trend_cache, _driver_list_cache
    _attendance_cache = {}
    _trend_cache = {}
    _driver_list_cache = {}
    _log_audit('cache_cleared')
    return True