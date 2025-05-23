"""
Attendance Pipeline Module

This module provides functions for processing attendance data and generating driver reports
based on GPS tracking data, job site information, and timecard data.
"""

import os
import logging
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

def process_attendance_data(combined_data, date_str, timecard_data=None):
    """
    Process attendance data and generate driver report.
    
    Args:
        combined_data: Combined data from multiple sources
        date_str: Date string in YYYY-MM-DD format
        timecard_data: Optional timecard data for validation
        
    Returns:
        dict: Processed attendance report
    """
    try:
        # Convert date string to datetime
        report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Filter data for the specified date
        daily_data = filter_data_for_date(combined_data, report_date)
        
        if not daily_data:
            logger.warning(f"No data found for date: {date_str}")
            return None
        
        # Extract driver records from daily data
        driver_records = extract_driver_records(daily_data)
        
        # Classify drivers based on attendance rules
        classified_drivers = classify_drivers(driver_records, report_date)
        
        # Add timecard validation if data is available
        if timecard_data:
            classified_drivers = validate_with_timecard(classified_drivers, timecard_data, report_date)
        
        # Generate attendance report
        attendance_report = {
            'date': date_str,
            'generated_at': datetime.now().isoformat(),
            'driver_records': classified_drivers,
            'summary': generate_summary(classified_drivers)
        }
        
        return attendance_report
    
    except Exception as e:
        logger.error(f"Error processing attendance data: {str(e)}")
        return None

def filter_data_for_date(data, target_date):
    """
    Filter data for a specific date.
    
    Args:
        data: Data to filter
        target_date: Target date
        
    Returns:
        list: Filtered data for the target date
    """
    filtered_data = []
    
    for record in data:
        record_date = None
        
        # Try to extract date from various fields
        date_fields = ['date', 'Date', 'timestamp', 'Timestamp', 'event_time', 'EventTime']
        
        for field in date_fields:
            if field in record and record[field]:
                try:
                    # Handle different date formats
                    if isinstance(record[field], datetime):
                        record_date = record[field].date()
                    else:
                        # Try parsing as string
                        date_str = str(record[field])
                        record_date = parse_date(date_str).date()
                    
                    break
                except Exception:
                    continue
        
        # If we couldn't extract a date, skip this record
        if not record_date:
            continue
        
        # Check if the record date matches the target date
        if record_date == target_date:
            filtered_data.append(record)
    
    return filtered_data

def parse_date(date_str):
    """
    Parse date string into datetime object.
    
    Args:
        date_str: Date string
        
    Returns:
        datetime: Parsed datetime object
    """
    formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%Y-%m-%d %H:%M:%S',
        '%m/%d/%Y %H:%M:%S',
        '%d/%m/%Y %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%m/%d/%Y %I:%M:%S %p',
        '%d/%m/%Y %I:%M:%S %p'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # If none of the formats match, try to extract just the date part
    try:
        # Check if date includes time with T separator
        if 'T' in date_str:
            date_part = date_str.split('T')[0]
            return datetime.strptime(date_part, '%Y-%m-%d')
        
        # Check if date includes time with space separator
        if ' ' in date_str:
            date_part = date_str.split(' ')[0]
            
            # Try different formats for the date part
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                try:
                    return datetime.strptime(date_part, fmt)
                except ValueError:
                    continue
    except Exception:
        pass
    
    # As a last resort, raise ValueError
    raise ValueError(f"Could not parse date: {date_str}")

def extract_driver_records(data):
    """
    Extract driver records from data.
    
    Args:
        data: Data to extract driver records from
        
    Returns:
        list: List of driver records
    """
    driver_records = []
    
    # Track drivers to avoid duplicates
    driver_map = {}
    
    for record in data:
        # Try to extract driver name
        driver_name = None
        for field in ['driver_name', 'DriverName', 'driver', 'Driver', 'operator', 'Operator']:
            if field in record and record[field]:
                driver_name = record[field]
                break
        
        if not driver_name:
            continue
        
        # Extract job information
        job_number = None
        job_name = None
        
        for field in ['job_number', 'JobNumber', 'job_id', 'JobID']:
            if field in record and record[field]:
                job_number = record[field]
                break
        
        for field in ['job_name', 'JobName', 'job_site', 'JobSite']:
            if field in record and record[field]:
                job_name = record[field]
                break
        
        # Extract timestamps
        start_time = None
        end_time = None
        
        for field in ['start_time', 'StartTime', 'on_time', 'OnTime']:
            if field in record and record[field]:
                start_time = record[field]
                if isinstance(start_time, datetime):
                    start_time = start_time.strftime('%H:%M:%S')
                break
        
        for field in ['end_time', 'EndTime', 'off_time', 'OffTime']:
            if field in record and record[field]:
                end_time = record[field]
                if isinstance(end_time, datetime):
                    end_time = end_time.strftime('%H:%M:%S')
                break
        
        # If we don't have both start and end time, try to extract it from other fields
        if not start_time or not end_time:
            if 'timestamp' in record:
                if isinstance(record['timestamp'], datetime):
                    timestamp = record['timestamp']
                else:
                    timestamp = parse_date(record['timestamp'])
                
                if 'event_type' in record:
                    if record['event_type'] in ['start', 'on']:
                        start_time = timestamp.strftime('%H:%M:%S')
                    elif record['event_type'] in ['end', 'off']:
                        end_time = timestamp.strftime('%H:%M:%S')
        
        # Create or update driver record
        if driver_name in driver_map:
            # Update existing record
            driver_record = driver_map[driver_name]
            
            # Update job info if not already set
            if not driver_record.get('job_number') and job_number:
                driver_record['job_number'] = job_number
            
            if not driver_record.get('job_name') and job_name:
                driver_record['job_name'] = job_name
            
            # Update times if not already set
            if not driver_record.get('start_time') and start_time:
                driver_record['start_time'] = start_time
            
            if not driver_record.get('end_time') and end_time:
                driver_record['end_time'] = end_time
            
            # Add to locations list
            if 'location' in record and record['location']:
                if 'locations' not in driver_record:
                    driver_record['locations'] = []
                
                driver_record['locations'].append(record['location'])
        else:
            # Create new record
            driver_record = {
                'driver_name': driver_name,
                'job_number': job_number,
                'job_name': job_name,
                'start_time': start_time,
                'end_time': end_time,
                'gps_verified': True
            }
            
            # Add locations if available
            if 'location' in record and record['location']:
                driver_record['locations'] = [record['location']]
            
            # Add to driver map
            driver_map[driver_name] = driver_record
    
    # Convert driver map to list
    driver_records = list(driver_map.values())
    
    # Calculate hours for each driver
    for record in driver_records:
        if record.get('start_time') and record.get('end_time'):
            try:
                start = datetime.strptime(record['start_time'], '%H:%M:%S')
                end = datetime.strptime(record['end_time'], '%H:%M:%S')
                
                # Handle if end time is earlier than start time (overnight shift)
                if end < start:
                    end += timedelta(days=1)
                
                # Calculate hours
                hours = (end - start).total_seconds() / 3600
                record['hours'] = round(hours, 1)
            except Exception as e:
                logger.warning(f"Error calculating hours for {record['driver_name']}: {str(e)}")
    
    return driver_records

def classify_drivers(driver_records, report_date):
    """
    Classify drivers based on attendance rules.
    
    Args:
        driver_records: List of driver records
        report_date: Report date
        
    Returns:
        list: Classified driver records
    """
    # Define shift start and end times (these can be configurable)
    default_start_time = datetime.strptime('07:00:00', '%H:%M:%S')
    default_end_time = datetime.strptime('17:00:00', '%H:%M:%S')
    
    # Late threshold in minutes
    late_threshold = 15
    
    # Early end threshold in minutes
    early_end_threshold = 15
    
    for record in driver_records:
        # Default classification is not on job (will be updated if criteria are met)
        record['classification'] = 'not_on_job'
        
        # Skip if no start time or end time
        if not record.get('start_time') or not record.get('end_time'):
            continue
        
        try:
            # Parse start and end times
            start_time = datetime.strptime(record['start_time'], '%H:%M:%S')
            end_time = datetime.strptime(record['end_time'], '%H:%M:%S')
            
            # Check if the driver arrived late
            late_minutes = (start_time - default_start_time).total_seconds() / 60
            
            # Check if the driver left early
            early_end_minutes = (default_end_time - end_time).total_seconds() / 60
            
            # Classify based on rules
            if late_minutes > late_threshold:
                record['classification'] = 'late'
                record['late_minutes'] = int(late_minutes)
            elif early_end_minutes > early_end_threshold:
                record['classification'] = 'early_end'
                record['early_end_minutes'] = int(early_end_minutes)
            else:
                record['classification'] = 'on_time'
            
        except Exception as e:
            logger.warning(f"Error classifying driver {record['driver_name']}: {str(e)}")
    
    return driver_records

def validate_with_timecard(driver_records, timecard_data, report_date):
    """
    Validate driver records with timecard data.
    
    Args:
        driver_records: List of driver records
        timecard_data: Timecard data
        report_date: Report date
        
    Returns:
        list: Validated driver records
    """
    # Create mapping of driver names to timecard records
    timecard_map = {}
    
    for record in timecard_data:
        # Skip records for different dates
        record_date = None
        
        if 'date' in record and record['date']:
            if isinstance(record['date'], datetime):
                record_date = record['date'].date()
            else:
                try:
                    record_date = parse_date(str(record['date'])).date()
                except Exception:
                    continue
        
        if record_date and record_date != report_date:
            continue
        
        # Get driver name
        driver_name = None
        for field in ['driver_name', 'DriverName', 'employee', 'Employee', 'name', 'Name']:
            if field in record and record[field]:
                driver_name = record[field]
                break
        
        if not driver_name:
            continue
        
        # Get reported hours
        hours = None
        for field in ['hours', 'Hours', 'reported_hours', 'ReportedHours', 'timecard_hours', 'TimecardHours']:
            if field in record and record[field] is not None:
                try:
                    hours = float(record[field])
                    break
                except (ValueError, TypeError):
                    continue
        
        if hours is None:
            continue
        
        # Add to timecard map
        timecard_map[driver_name] = {
            'timecard_hours': hours,
            'job_number': record.get('job_number'),
            'job_name': record.get('job_name')
        }
    
    # Validate driver records with timecard data
    for record in driver_records:
        driver_name = record['driver_name']
        
        if driver_name in timecard_map:
            timecard = timecard_map[driver_name]
            
            # Add timecard hours
            record['timecard_hours'] = timecard['timecard_hours']
            
            # Calculate hours difference
            if 'hours' in record:
                record['hours_difference'] = round(record['hours'] - timecard['timecard_hours'], 1)
            
            # Check job match if both have job information
            if (record.get('job_number') and timecard.get('job_number') and 
                record['job_number'] != timecard['job_number']):
                record['job_mismatch'] = True
    
    return driver_records

def generate_summary(driver_records):
    """
    Generate summary of driver records.
    
    Args:
        driver_records: List of driver records
        
    Returns:
        dict: Summary data
    """
    summary = {
        'total_drivers': len(driver_records),
        'on_time_count': 0,
        'late_count': 0,
        'early_end_count': 0,
        'not_on_job_count': 0,
        'average_late_minutes': 0,
        'average_early_end_minutes': 0
    }
    
    # Count by classification
    late_minutes = []
    early_end_minutes = []
    
    for record in driver_records:
        classification = record.get('classification')
        
        if classification == 'on_time':
            summary['on_time_count'] += 1
        elif classification == 'late':
            summary['late_count'] += 1
            if 'late_minutes' in record:
                late_minutes.append(record['late_minutes'])
        elif classification == 'early_end':
            summary['early_end_count'] += 1
            if 'early_end_minutes' in record:
                early_end_minutes.append(record['early_end_minutes'])
        elif classification == 'not_on_job':
            summary['not_on_job_count'] += 1
    
    # Calculate averages
    if late_minutes:
        summary['average_late_minutes'] = round(sum(late_minutes) / len(late_minutes), 1)
    
    if early_end_minutes:
        summary['average_early_end_minutes'] = round(sum(early_end_minutes) / len(early_end_minutes), 1)
    
    # Calculate percentages
    total = summary['total_drivers']
    
    if total > 0:
        summary['on_time_percentage'] = round((summary['on_time_count'] / total) * 100, 1)
        summary['late_percentage'] = round((summary['late_count'] / total) * 100, 1)
        summary['early_end_percentage'] = round((summary['early_end_count'] / total) * 100, 1)
        summary['not_on_job_percentage'] = round((summary['not_on_job_count'] / total) * 100, 1)
    else:
        summary['on_time_percentage'] = 0
        summary['late_percentage'] = 0
        summary['early_end_percentage'] = 0
        summary['not_on_job_percentage'] = 0
    
    return summary