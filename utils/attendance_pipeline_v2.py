"""
TRAXORA Fleet Management System - Attendance Pipeline V2

This module provides the core attendance processing logic for the Daily Driver Engine 2.0,
implementing strict classification for on-time, late start, early end, and not on job cases.

Functions:
- normalize_driver_name: Normalize driver name for consistent matching
- parse_datetime: Parse date and time strings into datetime object
- classify_attendance: Classify driver attendance based on start/end times
- process_attendance_data: Process attendance data from multiple sources
- generate_attendance_report: Generate complete attendance report
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

# Define constants for attendance classification
DEFAULT_START_TIME = "07:30:00"  # 7:30 AM cutoff for late
DEFAULT_END_TIME = "16:00:00"    # 4:00 PM cutoff for early end
LATE_THRESHOLD_MINUTES = 1       # Any minutes after start time is late
EARLY_END_THRESHOLD_MINUTES = 1  # Any minutes before end time is early end

def normalize_driver_name(name: str) -> str:
    """
    Normalize driver name for consistent matching between data sources
    
    Args:
        name: Driver name to normalize
        
    Returns:
        str: Normalized name
    """
    if not name:
        return ""
    
    # Remove extra spaces, convert to lowercase
    name = " ".join(name.strip().split()).lower()
    
    # Handle common variations (last name first)
    if "," in name:
        parts = name.split(",", 1)
        if len(parts) == 2:
            last, first = parts
            name = f"{first.strip()} {last.strip()}"
    
    return name

def parse_date_time(date_str: str, time_str: str) -> Optional[datetime]:
    """
    Parse date and time strings into datetime object
    
    Args:
        date_str: Date string (YYYY-MM-DD)
        time_str: Time string (various formats supported)
        
    Returns:
        datetime: Parsed datetime or None if parsing failed
    """
    try:
        if not time_str:
            return None
            
        # Try different time formats
        time_formats = [
            '%H:%M:%S', '%H:%M', '%I:%M:%S %p', '%I:%M %p',
            '%I:%M%p', '%I%p', '%H:%M:%S.%f'
        ]
        
        parsed_time = None
        for fmt in time_formats:
            try:
                parsed_time = datetime.strptime(time_str, fmt).time()
                break
            except ValueError:
                continue
                
        if not parsed_time:
            # Try direct conversion if string is just a timestamp
            try:
                parsed_time = pd.to_datetime(time_str).time()
            except:
                return None
        
        # Combine date and time
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        return datetime.combine(date_obj, parsed_time)
    
    except Exception as e:
        logger.debug(f"Error parsing date/time ({date_str}, {time_str}): {str(e)}")
        return None

def classify_attendance(start_time: Optional[datetime], end_time: Optional[datetime], 
                       date_str: str) -> Dict[str, Any]:
    """
    Classify driver attendance based on start and end times
    
    Args:
        start_time: Start time datetime
        end_time: End time datetime
        date_str: Date string (YYYY-MM-DD)
        
    Returns:
        dict: Classification details with status (on_time, late, early_end, not_on_job)
    """
    # Create date objects for comparison
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_cutoff = datetime.combine(date_obj, datetime.strptime(DEFAULT_START_TIME, '%H:%M:%S').time())
        end_cutoff = datetime.combine(date_obj, datetime.strptime(DEFAULT_END_TIME, '%H:%M:%S').time())
    except Exception as e:
        logger.error(f"Error creating cutoff times: {str(e)}")
        start_cutoff = None
        end_cutoff = None
    
    # Initialize classification result
    result = {
        'status': 'unknown',
        'start_time': start_time.strftime('%H:%M:%S') if start_time else None,
        'end_time': end_time.strftime('%H:%M:%S') if end_time else None,
        'expected_start': DEFAULT_START_TIME,
        'expected_end': DEFAULT_END_TIME,
        'details': {}
    }
    
    # Case 1: No start time recorded - Not on job
    if not start_time:
        result['status'] = 'not_on_job'
        result['details']['reason'] = 'No start time recorded'
        return result
        
    # Case 2: Start time after cutoff - Late start
    if start_cutoff and start_time > start_cutoff:
        result['status'] = 'late'
        late_minutes = round((start_time - start_cutoff).total_seconds() / 60)
        result['details']['late_by_minutes'] = late_minutes
        result['details']['reason'] = f'Started {late_minutes} minutes after {DEFAULT_START_TIME}'
        
    # Case 3: End time before cutoff - Early end
    # Only check if we have a valid end time and the driver wasn't already marked as late
    if end_time and end_cutoff and end_time < end_cutoff and result['status'] != 'late':
        result['status'] = 'early_end'
        early_minutes = round((end_cutoff - end_time).total_seconds() / 60)
        result['details']['early_by_minutes'] = early_minutes
        result['details']['reason'] = f'Ended {early_minutes} minutes before {DEFAULT_END_TIME}'
        
    # Case 4: On time (default if no other conditions met)
    if result['status'] == 'unknown':
        result['status'] = 'on_time'
        result['details']['reason'] = 'Started on time and ended on time'
    
    # Calculate total hours
    if start_time and end_time:
        total_seconds = (end_time - start_time).total_seconds()
        total_hours = round(total_seconds / 3600, 2)  # Round to 2 decimal places
        result['total_hours'] = total_hours
        
    return result
    
    if end_time:
        classification['end_time'] = end_time.strftime('%H:%M:%S')
        
        # Calculate hours worked (as decimal)
        hours_worked = (end_time - start_time).total_seconds() / 3600
        classification['hours'] = round(hours_worked, 2)
    
    # Check if late
    if start_time > default_start:
        late_minutes = int((start_time - default_start).total_seconds() / 60)
        if late_minutes >= LATE_THRESHOLD_MINUTES:
            classification['classification'] = 'late'
            classification['late_minutes'] = late_minutes
    
    # Check if early end (only if we have both start and end times)
    elif end_time and end_time < default_end:
        early_end_minutes = int((default_end - end_time).total_seconds() / 60)
        if early_end_minutes >= EARLY_END_THRESHOLD_MINUTES:
            classification['classification'] = 'early_end'
            classification['early_end_minutes'] = early_end_minutes
    
    # If not late and not early end, classify as on time
    elif classification['classification'] == 'not_on_job':
        classification['classification'] = 'on_time'
    
    return classification

def extract_job_data(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract job information from a record
    
    Args:
        record: Data record
        
    Returns:
        dict: Job information
    """
    job_data = {
        'job_number': '',
        'job_name': ''
    }
    
    # Try different field names for job number
    for field in ['Job', 'JOB', 'JobNo', 'job_number', 'ProjectNo', 'JobNumber', 'Job Number']:
        if field in record and record[field]:
            job_data['job_number'] = str(record[field])
            break
    
    # Try different field names for job name
    for field in ['JobName', 'job_name', 'ProjectName', 'Job Name', 'Description']:
        if field in record and record[field]:
            job_data['job_name'] = str(record[field])
            break
            
    # Clean job number (remove decimal part if present)
    if job_data['job_number'] and '.' in job_data['job_number']:
        job_data['job_number'] = job_data['job_number'].split('.')[0]
    
    return job_data

def process_driving_history(data: List[Dict[str, Any]], date_str: str) -> Dict[str, Dict[str, Any]]:
    """
    Process driving history data
    
    Args:
        data: List of driving history records
        date_str: Date string (YYYY-MM-DD)
        
    Returns:
        dict: Processed driver records keyed by normalized name
    """
    drivers = {}
    
    for record in data:
        # Extract driver name (try different field names)
        driver_name = None
        for field in ['Driver', 'Contact', 'driver_name', 'DriverName', 'DRIVER NAME']:
            if field in record and record[field]:
                driver_name = str(record[field])
                break
        
        if not driver_name:
            continue
        
        # Normalize name for consistent matching
        normalized_name = normalize_driver_name(driver_name)
        
        # Extract event datetime (try different field names)
        event_time = None
        for field in ['EventDateTime', 'Locationx', 'Time', 'timestamp']:
            if field in record and record[field]:
                try:
                    # Try to parse directly
                    event_time = pd.to_datetime(record[field])
                    break
                except:
                    pass
        
        if not event_time:
            continue
        
        # Extract location (try different field names)
        location = None
        for field in ['Location', 'Locationx', 'Address', 'location']:
            if field in record and record[field]:
                location = str(record[field])
                break
        
        # Skip if key fields are missing
        if not normalized_name or not event_time:
            continue
        
        # Initialize driver record if not exists
        if normalized_name not in drivers:
            drivers[normalized_name] = {
                'driver_name': driver_name,
                'normalized_name': normalized_name,
                'events': [],
                'job_number': '',
                'job_name': ''
            }
        
        # Extract job data
        job_data = extract_job_data(record)
        
        # Only update job info if we don't have it yet
        if not drivers[normalized_name]['job_number'] and job_data['job_number']:
            drivers[normalized_name]['job_number'] = job_data['job_number']
        
        if not drivers[normalized_name]['job_name'] and job_data['job_name']:
            drivers[normalized_name]['job_name'] = job_data['job_name']
        
        # Add event to driver's event list
        drivers[normalized_name]['events'].append({
            'time': event_time,
            'location': location,
            'source': 'driving_history'
        })
    
    # Sort events by time and determine start/end times
    for name, driver in drivers.items():
        if driver['events']:
            driver['events'].sort(key=lambda x: x['time'])
            
            # First event time is start time
            driver['start_time'] = driver['events'][0]['time']
            
            # Last event time is end time
            driver['end_time'] = driver['events'][-1]['time']
            
            # Apply attendance classification
            classification = classify_attendance(
                driver['start_time'], 
                driver['end_time'], 
                date_str
            )
            
            # Merge classification into driver record
            driver.update(classification)
            
            # GPS verified since this is GPS data
            driver['gps_verified'] = True
    
    return drivers

def process_time_on_site(data: List[Dict[str, Any]], date_str: str) -> Dict[str, Dict[str, Any]]:
    """
    Process time on site data
    
    Args:
        data: List of time on site records
        date_str: Date string (YYYY-MM-DD)
        
    Returns:
        dict: Processed driver records keyed by normalized name
    """
    drivers = {}
    
    for record in data:
        # Extract driver name (try different field names)
        driver_name = None
        for field in ['Driver', 'Contact', 'driver_name', 'DriverName', 'DRIVER NAME']:
            if field in record and record[field]:
                driver_name = str(record[field])
                break
        
        if not driver_name:
            continue
        
        # Normalize name for consistent matching
        normalized_name = normalize_driver_name(driver_name)
        
        # Extract start time (try different field names)
        start_time_str = None
        for field in ['StartTime', 'Began Day On Site', 'start_time', 'Start Time']:
            if field in record and record[field]:
                start_time_str = str(record[field])
                break
        
        # Extract end time (try different field names)
        end_time_str = None
        for field in ['EndTime', 'Ended Day On Site', 'end_time', 'End Time']:
            if field in record and record[field]:
                end_time_str = str(record[field])
                break
        
        # Parse start and end times
        start_time = parse_date_time(date_str, start_time_str) if start_time_str else None
        end_time = parse_date_time(date_str, end_time_str) if end_time_str else None
        
        # Skip if key fields are missing
        if not normalized_name or not start_time:
            continue
        
        # Extract job data
        job_data = extract_job_data(record)
        
        # Initialize driver record
        drivers[normalized_name] = {
            'driver_name': driver_name,
            'normalized_name': normalized_name,
            'start_time': start_time,
            'end_time': end_time,
            'job_number': job_data['job_number'],
            'job_name': job_data['job_name'],
            'source': 'time_on_site',
            'gps_verified': True
        }
        
        # Apply attendance classification
        classification = classify_attendance(start_time, end_time, date_str)
        
        # Merge classification into driver record
        drivers[normalized_name].update(classification)
    
    return drivers

def process_activity_detail(data: List[Dict[str, Any]], date_str: str) -> Dict[str, Dict[str, Any]]:
    """
    Process activity detail data
    
    Args:
        data: List of activity detail records
        date_str: Date string (YYYY-MM-DD)
        
    Returns:
        dict: Processed driver records keyed by normalized name
    """
    drivers = {}
    
    for record in data:
        # Extract driver name (try different field names)
        driver_name = None
        for field in ['Driver', 'Contact', 'driver_name', 'DriverName', 'DRIVER NAME']:
            if field in record and record[field]:
                driver_name = str(record[field])
                break
        
        if not driver_name:
            continue
        
        # Normalize name for consistent matching
        normalized_name = normalize_driver_name(driver_name)
        
        # Extract event datetime (try different field names)
        event_time = None
        for field in ['EventDateTime', 'Locationx', 'Time', 'timestamp']:
            if field in record and record[field]:
                try:
                    # Try to parse directly
                    event_time = pd.to_datetime(record[field])
                    break
                except:
                    pass
        
        if not event_time:
            continue
        
        # Extract location (try different field names)
        location = None
        for field in ['Location', 'Locationx', 'Address', 'location']:
            if field in record and record[field]:
                location = str(record[field])
                break
        
        # Skip if key fields are missing
        if not normalized_name or not event_time:
            continue
        
        # Initialize driver record if not exists
        if normalized_name not in drivers:
            drivers[normalized_name] = {
                'driver_name': driver_name,
                'normalized_name': normalized_name,
                'events': [],
                'job_number': '',
                'job_name': ''
            }
        
        # Extract job data
        job_data = extract_job_data(record)
        
        # Only update job info if we don't have it yet
        if not drivers[normalized_name]['job_number'] and job_data['job_number']:
            drivers[normalized_name]['job_number'] = job_data['job_number']
        
        if not drivers[normalized_name]['job_name'] and job_data['job_name']:
            drivers[normalized_name]['job_name'] = job_data['job_name']
        
        # Add event to driver's event list
        drivers[normalized_name]['events'].append({
            'time': event_time,
            'location': location,
            'source': 'activity_detail'
        })
    
    # Sort events by time and determine start/end times
    for name, driver in drivers.items():
        if driver['events']:
            driver['events'].sort(key=lambda x: x['time'])
            
            # First event time is start time
            driver['start_time'] = driver['events'][0]['time']
            
            # Last event time is end time
            driver['end_time'] = driver['events'][-1]['time']
            
            # Apply attendance classification
            classification = classify_attendance(
                driver['start_time'], 
                driver['end_time'], 
                date_str
            )
            
            # Merge classification into driver record
            driver.update(classification)
            
            # GPS verified since this is GPS data
            driver['gps_verified'] = True
    
    return drivers

def process_timecard_data(data: List[Dict[str, Any]], date_str: str) -> Dict[str, Dict[str, Any]]:
    """
    Process timecard data
    
    Args:
        data: List of timecard records
        date_str: Date string (YYYY-MM-DD)
        
    Returns:
        dict: Processed driver records keyed by normalized name
    """
    drivers = {}
    
    for record in data:
        # Extract driver name (try different field names)
        driver_name = None
        for field in ['Employee', 'Name', 'employee_name', 'EmployeeName', 'EMPLOYEE NAME']:
            if field in record and record[field]:
                driver_name = str(record[field])
                break
        
        if not driver_name:
            continue
        
        # Normalize name for consistent matching
        normalized_name = normalize_driver_name(driver_name)
        
        # Extract date field (to check if this record matches our target date)
        record_date = None
        for field in ['Date', 'WorkDate', 'work_date', 'TimeCardDate']:
            if field in record and record[field]:
                try:
                    record_date = pd.to_datetime(record[field]).strftime('%Y-%m-%d')
                    break
                except:
                    pass
        
        # Skip if date doesn't match
        if record_date and record_date != date_str:
            continue
        
        # Extract start time (try different field names)
        start_time_str = None
        for field in ['StartTime', 'TimeIn', 'start_time', 'Start Time']:
            if field in record and record[field]:
                start_time_str = str(record[field])
                break
        
        # Extract end time (try different field names)
        end_time_str = None
        for field in ['EndTime', 'TimeOut', 'end_time', 'End Time']:
            if field in record and record[field]:
                end_time_str = str(record[field])
                break
        
        # Parse start and end times
        start_time = parse_date_time(date_str, start_time_str) if start_time_str else None
        end_time = parse_date_time(date_str, end_time_str) if end_time_str else None
        
        # Skip if key fields are missing
        if not normalized_name or not start_time:
            continue
        
        # Extract job data
        job_data = extract_job_data(record)
        
        # Initialize driver record
        drivers[normalized_name] = {
            'driver_name': driver_name,
            'normalized_name': normalized_name,
            'start_time': start_time,
            'end_time': end_time,
            'job_number': job_data['job_number'],
            'job_name': job_data['job_name'],
            'source': 'timecard',
            'gps_verified': False  # Timecard is not GPS verified
        }
        
        # Apply attendance classification
        classification = classify_attendance(start_time, end_time, date_str)
        
        # Merge classification into driver record
        drivers[normalized_name].update(classification)
    
    return drivers

def merge_driver_records(records_sources: List[Dict[str, Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """
    Merge driver records from multiple sources
    
    Args:
        records_sources: List of driver record dictionaries from different sources
        
    Returns:
        dict: Merged driver records with priority given to GPS data
    """
    merged = {}
    
    # Priority order: driving_history > time_on_site > activity_detail > timecard
    source_priority = {
        'driving_history': 0,
        'time_on_site': 1,
        'activity_detail': 2,
        'timecard': 3
    }
    
    # Merge all records
    for records in records_sources:
        for name, record in records.items():
            if name not in merged:
                merged[name] = record
            else:
                # Check source priority - only override if new source has higher priority
                current_priority = source_priority.get(merged[name].get('source', 'unknown'), 999)
                new_priority = source_priority.get(record.get('source', 'unknown'), 999)
                
                if new_priority < current_priority:
                    merged[name] = record
                
                # If same priority, prefer the one with more complete data
                elif new_priority == current_priority:
                    # Prefer record with both start and end times
                    if record.get('end_time') and not merged[name].get('end_time'):
                        merged[name] = record
                    
                    # Prefer record with job data
                    elif (record.get('job_number') and not merged[name].get('job_number')) or \
                         (record.get('job_name') and not merged[name].get('job_name')):
                        # Keep existing times if they're better
                        record['start_time'] = record.get('start_time') or merged[name].get('start_time')
                        record['end_time'] = record.get('end_time') or merged[name].get('end_time')
                        merged[name] = record
    
    return merged

def calculate_summary(driver_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics from driver records
    
    Args:
        driver_records: List of processed driver records
        
    Returns:
        dict: Summary statistics
    """
    total_drivers = len(driver_records)
    
    # Count by classification
    on_time_count = sum(1 for d in driver_records if d.get('classification') == 'on_time')
    late_count = sum(1 for d in driver_records if d.get('classification') == 'late')
    early_end_count = sum(1 for d in driver_records if d.get('classification') == 'early_end')
    not_on_job_count = sum(1 for d in driver_records if d.get('classification') == 'not_on_job')
    
    # Calculate percentages
    on_time_percentage = round((on_time_count / total_drivers * 100) if total_drivers > 0 else 0)
    late_percentage = round((late_count / total_drivers * 100) if total_drivers > 0 else 0)
    early_end_percentage = round((early_end_count / total_drivers * 100) if total_drivers > 0 else 0)
    not_on_job_percentage = round((not_on_job_count / total_drivers * 100) if total_drivers > 0 else 0)
    
    # Calculate average minutes
    late_minutes = [d.get('late_minutes', 0) for d in driver_records if d.get('classification') == 'late']
    early_end_minutes = [d.get('early_end_minutes', 0) for d in driver_records if d.get('classification') == 'early_end']
    
    average_late_minutes = round(sum(late_minutes) / len(late_minutes)) if late_minutes else 0
    average_early_end_minutes = round(sum(early_end_minutes) / len(early_end_minutes)) if early_end_minutes else 0
    
    return {
        'total_drivers': total_drivers,
        'on_time_count': on_time_count,
        'late_count': late_count,
        'early_end_count': early_end_count,
        'not_on_job_count': not_on_job_count,
        'on_time_percentage': on_time_percentage,
        'late_percentage': late_percentage,
        'early_end_percentage': early_end_percentage,
        'not_on_job_percentage': not_on_job_percentage,
        'average_late_minutes': average_late_minutes,
        'average_early_end_minutes': average_early_end_minutes
    }

def process_attendance_data_v2(driving_history_data: List[Dict[str, Any]] = None,
                            time_on_site_data: List[Dict[str, Any]] = None,
                            activity_detail_data: List[Dict[str, Any]] = None,
                            timecard_data: List[Dict[str, Any]] = None,
                            date_str: str = None) -> Dict[str, Any]:
    """
    Main function to process all attendance data sources and generate report
    
    Args:
        driving_history_data: List of driving history records
        time_on_site_data: List of time on site records
        activity_detail_data: List of activity detail records
        timecard_data: List of timecard records
        date_str: Date string (YYYY-MM-DD)
        
    Returns:
        dict: Processed attendance report with driver records and summary
    """
    try:
        # Default to today if date not provided
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Processing attendance data for date: {date_str}")
        
        # Initialize empty lists if not provided
        driving_history_data = driving_history_data or []
        time_on_site_data = time_on_site_data or []
        activity_detail_data = activity_detail_data or []
        timecard_data = timecard_data or []
        
        # Process each data source
        driving_history_records = process_driving_history(driving_history_data, date_str)
        time_on_site_records = process_time_on_site(time_on_site_data, date_str)
        activity_detail_records = process_activity_detail(activity_detail_data, date_str)
        timecard_records = process_timecard_data(timecard_data, date_str)
        
        # Merge records from all sources
        merged_records = merge_driver_records([
            driving_history_records,
            time_on_site_records,
            activity_detail_records,
            timecard_records
        ])
        
        # Convert to list and clean up for output
        driver_records = []
        for name, record in merged_records.items():
            # Format times for output if they're datetime objects
            if isinstance(record.get('start_time'), datetime):
                record['start_time'] = record['start_time'].strftime('%H:%M:%S')
            
            if isinstance(record.get('end_time'), datetime):
                record['end_time'] = record['end_time'].strftime('%H:%M:%S')
            
            # Remove events list and other internal fields
            record.pop('events', None)
            record.pop('normalized_name', None)
            
            driver_records.append(record)
        
        # Calculate summary statistics
        summary = calculate_summary(driver_records)
        
        # Build final report
        attendance_report = {
            'date': date_str,
            'driver_records': driver_records,
            'summary': summary,
            'processed_at': datetime.now().isoformat(),
            'data_sources': {
                'driving_history': len(driving_history_data),
                'time_on_site': len(time_on_site_data),
                'activity_detail': len(activity_detail_data),
                'timecard': len(timecard_data)
            }
        }
        
        return attendance_report
    
    except Exception as e:
        logger.error(f"Error processing attendance data: {str(e)}")
        logger.exception(e)
        return None