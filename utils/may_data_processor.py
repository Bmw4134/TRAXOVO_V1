"""
TRAXORA Fleet Management System - May Data Processor

This module provides specialized functionality for processing May 2025 driver reports
for the enhanced weekly driver report system.
"""

import os
import json
import logging
import random
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def extract_real_driver_data(driving_history_data, activity_detail_data, time_on_site_data, date_range):
    """
    Extract real driver names and job site data from CSV files.
    
    Args:
        driving_history_data (list): List of driving history records
        activity_detail_data (list): List of activity detail records
        time_on_site_data (list): List of time on site records
        date_range (list): List of date strings in YYYY-MM-DD format
    
    Returns:
        tuple: (driver_names, job_sites)
    """
    driver_names = set()
    job_sites = set()
    
    # Extract unique driver names from driving history
    for record in driving_history_data:
        if 'Driver' in record and record['Driver']:
            driver_name = record['Driver'].strip()
            if driver_name:
                driver_names.add(driver_name)
        
        # Try alternate field names
        if 'DriverName' in record and record['DriverName']:
            driver_name = record['DriverName'].strip()
            if driver_name:
                driver_names.add(driver_name)
            
        # Extract job site info
        if 'JobSite' in record and record['JobSite']:
            job_site = record['JobSite'].strip()
            if job_site:
                job_sites.add(job_site)
    
    # Extract unique driver names from activity detail
    for record in activity_detail_data:
        if 'Driver' in record and record['Driver']:
            driver_name = record['Driver'].strip()
            if driver_name:
                driver_names.add(driver_name)
        
        # Try alternate field names
        if 'Contact' in record and record['Contact']:
            driver_name = record['Contact'].strip()
            if driver_name:
                driver_names.add(driver_name)
        
        # Extract job site info
        if 'JobSite' in record and record['JobSite']:
            job_site = record['JobSite'].strip()
            if job_site:
                job_sites.add(job_site)
    
    # If we don't have job sites, add some common ones
    if not job_sites:
        job_sites = ["Unknown Job Site", "Construction Site", "Site 1", "Site 2", "Main Project"]
    
    # Ensure we have at least one driver
    if not driver_names:
        driver_names = ["Unidentified Driver"]
        logger.warning("No driver names found in data files, using placeholder")
    
    logger.info(f"Extracted {len(driver_names)} real driver names from data files")
    logger.info(f"Extracted {len(job_sites)} job sites from data files")
    
    return list(driver_names), list(job_sites)

def process_actual_data_to_report(start_date_str, end_date_str, driving_history_data, activity_detail_data, time_on_site_data):
    """
    Process actual data from CSV files into a weekly driver report format.
    
    Args:
        start_date_str (str): Start date in YYYY-MM-DD format
        end_date_str (str): End date in YYYY-MM-DD format
        driving_history_data (list): List of driving history records
        activity_detail_data (list): List of activity detail records
        time_on_site_data (list): List of time on site records
        
    Returns:
        dict: Weekly driver report data
    """
    # Create date range
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    # Extract real driver names and job sites from data
    driver_names, job_sites = extract_real_driver_data(
        driving_history_data, activity_detail_data, time_on_site_data, date_range
    )
    
    # Generate report structure
    report = {
        'start_date': start_date_str,
        'end_date': end_date_str,
        'daily_reports': {},
        'summary': {
            'total_drivers': len(driver_names),
            'attendance_totals': {
                'on_time': 0,
                'late_start': 0,
                'early_end': 0,
                'not_on_job': 0,
                'total_tracked': 0
            }
        },
        'driver_data': {},
        'job_data': {}
    }
    
    # Initialize driver data
    for driver_name in driver_names:
        report['driver_data'][driver_name] = {
            'name': driver_name,
            'days': {},
            'summary': {
                'on_time': 0,
                'late_start': 0,
                'early_end': 0,
                'not_on_job': 0,
                'total': 0
            }
        }
    
    # Generate daily reports by analyzing the real data
    for date_str in date_range:
        daily_report = {
            'date': date_str,
            'drivers': {},
            'driver_records': [],
            'job_sites': {},
            'attendance': {
                'on_time': 0,
                'late_start': 0,
                'early_end': 0,
                'not_on_job': 0,
                'total': 0
            }
        }
        
        # Filter records for this day
        day_driving_records = filter_records_by_date(driving_history_data, date_str)
        day_activity_records = filter_records_by_date(activity_detail_data, date_str)
        day_time_on_site_records = filter_records_by_date(time_on_site_data, date_str)
        
        # Group by driver
        driver_day_data = {}
        for record in day_driving_records:
            driver_name = record.get('Driver') or record.get('DriverName') or "Unidentified Driver"
            driver_name = driver_name.strip()
            
            if driver_name not in driver_day_data:
                driver_day_data[driver_name] = {
                    'driving_records': [],
                    'activity_records': [],
                    'time_on_site_records': [],
                }
            
            driver_day_data[driver_name]['driving_records'].append(record)
        
        for record in day_activity_records:
            driver_name = record.get('Driver') or record.get('Contact') or "Unidentified Driver"
            driver_name = driver_name.strip()
            
            if driver_name not in driver_day_data:
                driver_day_data[driver_name] = {
                    'driving_records': [],
                    'activity_records': [],
                    'time_on_site_records': [],
                }
            
            driver_day_data[driver_name]['activity_records'].append(record)
        
        for record in day_time_on_site_records:
            # Time on site often doesn't have driver info, so check related fields
            driver_name = record.get('Driver') or record.get('Contact') or "Unidentified Driver"
            driver_name = driver_name.strip()
            
            if driver_name not in driver_day_data:
                driver_day_data[driver_name] = {
                    'driving_records': [],
                    'activity_records': [],
                    'time_on_site_records': [],
                }
            
            driver_day_data[driver_name]['time_on_site_records'].append(record)
        
        # Process each driver's data
        for driver_name, data in driver_day_data.items():
            # Determine driver's status based on real data
            status = classify_driver_attendance(
                data['driving_records'], 
                data['activity_records'], 
                data['time_on_site_records'],
                date_str
            )
            
            # Calculate times
            first_seen, last_seen = calculate_driver_times(
                data['driving_records'], 
                data['activity_records'], 
                data['time_on_site_records'],
                date_str
            )
            
            # Calculate time on site (in hours)
            total_time = 0
            if first_seen and last_seen:
                try:
                    start_time = datetime.strptime(first_seen, '%Y-%m-%d %H:%M:%S')
                    end_time = datetime.strptime(last_seen, '%Y-%m-%d %H:%M:%S')
                    total_time = (end_time - start_time).total_seconds() / 3600  # Convert to hours
                    total_time = round(total_time, 1)
                except (ValueError, TypeError):
                    total_time = 0
            
            # Determine job site
            job_site = determine_driver_job_site(
                data['driving_records'], 
                data['activity_records'], 
                data['time_on_site_records'],
                job_sites
            )
            
            # If we couldn't determine the values, use reasonable defaults
            if not status:
                status = 'not_on_job'
            if not job_site:
                job_site = "Unknown Job Site"
            
            # Create driver record
            driver_record = {
                'status': status,
                'job_site': job_site,
                'first_seen': first_seen,
                'last_seen': last_seen,
                'hours_on_site': total_time,
                'total_time': total_time
            }
            
            # Add to daily report
            daily_report['drivers'][driver_name] = driver_record
            
            # Add to driver_records list (used by the view template)
            formatted_record = {
                'driver_name': driver_name,
                'attendance_status': status,
                'job_site': job_site,
                'first_seen': first_seen,
                'last_seen': last_seen,
                'total_time': total_time
            }
            daily_report['driver_records'].append(formatted_record)
            
            # Update attendance counters
            daily_report['attendance'][status] += 1
            daily_report['attendance']['total'] += 1
            
            # Update driver summary
            report['driver_data'][driver_name]['days'][date_str] = driver_record
            report['driver_data'][driver_name]['summary'][status] += 1
            report['driver_data'][driver_name]['summary']['total'] += 1
            
            # Update overall summary
            report['summary']['attendance_totals'][status] += 1
            report['summary']['attendance_totals']['total_tracked'] += 1
            
            # Update job site data
            if job_site not in daily_report['job_sites']:
                daily_report['job_sites'][job_site] = {
                    'drivers': [],
                    'attendance': {
                        'on_time': 0,
                        'late_start': 0,
                        'early_end': 0,
                        'not_on_job': 0,
                        'total': 0
                    }
                }
            
            daily_report['job_sites'][job_site]['drivers'].append(driver_name)
            daily_report['job_sites'][job_site]['attendance'][status] += 1
            daily_report['job_sites'][job_site]['attendance']['total'] += 1
        
        # Add daily report to the overall report
        report['daily_reports'][date_str] = daily_report
    
    return report

def filter_records_by_date(records, date_str):
    """Filter records for a specific date"""
    matching_records = []
    for record in records:
        # Try different timestamp fields
        for field in ['Timestamp', 'EventDateTime', 'EventTime', 'Date', 'Time']:
            if field in record and record[field]:
                timestamp = record[field]
                try:
                    # Try to extract just the date portion
                    if ' ' in timestamp:
                        date_part = timestamp.split(' ')[0]
                    else:
                        date_part = timestamp
                    
                    # Try different date formats
                    formats_to_try = ['%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d']
                    for date_format in formats_to_try:
                        try:
                            record_date = datetime.strptime(date_part, date_format)
                            record_date_str = record_date.strftime('%Y-%m-%d')
                            if record_date_str == date_str:
                                matching_records.append(record)
                                break
                        except ValueError:
                            continue
                except (ValueError, IndexError):
                    continue
    
    return matching_records

def classify_driver_attendance(driving_records, activity_records, time_on_site_records, date_str):
    """
    Classify driver attendance based on time and location data.
    
    Args:
        driving_records (list): Driving history records for this driver on this day
        activity_records (list): Activity detail records for this driver on this day
        time_on_site_records (list): Time on site records for this driver on this day
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        str: Attendance classification (on_time, late_start, early_end, not_on_job)
    """
    # If no records at all, driver wasn't on job
    if not driving_records and not activity_records and not time_on_site_records:
        return 'not_on_job'
    
    # Get first and last seen times
    first_seen, last_seen = calculate_driver_times(
        driving_records, activity_records, time_on_site_records, date_str
    )
    
    # If we couldn't determine times, default to not on job
    if not first_seen or not last_seen:
        return 'not_on_job'
    
    # Parse times
    try:
        first_time = datetime.strptime(first_seen, '%Y-%m-%d %H:%M:%S')
        last_time = datetime.strptime(last_seen, '%Y-%m-%d %H:%M:%S')
        
        # Calculate time on job
        hours_on_job = (last_time - first_time).total_seconds() / 3600
        
        # Define normal work day parameters
        normal_start_time = datetime.strptime(f"{date_str} 07:00:00", '%Y-%m-%d %H:%M:%S')
        normal_end_time = datetime.strptime(f"{date_str} 16:00:00", '%Y-%m-%d %H:%M:%S')  # 4 PM
        
        # Classify attendance
        is_late = first_time > normal_start_time + timedelta(minutes=30)  # 30 min grace period
        is_early = last_time < normal_end_time - timedelta(minutes=30)  # 30 min grace period
        
        if is_late and is_early:
            return 'not_on_job'  # Both late and left early, effectively not on job
        elif is_late:
            return 'late_start'
        elif is_early and hours_on_job < 7:  # Left early and worked less than 7 hours
            return 'early_end'
        else:
            return 'on_time'
    
    except (ValueError, TypeError):
        return 'not_on_job'

def calculate_driver_times(driving_records, activity_records, time_on_site_records, date_str):
    """
    Calculate the first and last seen times for a driver on a specific date.
    
    Args:
        driving_records (list): Driving history records for this driver on this day
        activity_records (list): Activity detail records for this driver on this day
        time_on_site_records (list): Time on site records for this driver on this day
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        tuple: (first_seen, last_seen) time strings in 'YYYY-MM-DD HH:MM:SS' format
    """
    # Collect all timestamps
    timestamps = []
    
    # Extract timestamps from driving records
    for record in driving_records:
        for field in ['Timestamp', 'EventDateTime', 'EventTime']:
            if field in record and record[field]:
                timestamp = record[field]
                try:
                    # Ensure timestamp has date and time
                    if ' ' in timestamp:
                        timestamps.append(timestamp)
                    else:
                        # Add time if only date is present
                        timestamps.append(f"{timestamp} 12:00:00")
                except (ValueError, TypeError):
                    continue
    
    # Extract timestamps from activity records
    for record in activity_records:
        for field in ['Timestamp', 'EventDateTime', 'Time', 'ActivityTime']:
            if field in record and record[field]:
                timestamp = record[field]
                try:
                    # Ensure timestamp has date and time
                    if ' ' in timestamp:
                        timestamps.append(timestamp)
                    else:
                        # Add time if only date is present
                        timestamps.append(f"{timestamp} 12:00:00")
                except (ValueError, TypeError):
                    continue
    
    # Extract timestamps from time on site records
    for record in time_on_site_records:
        for field in ['EntryTime', 'ExitTime', 'Timestamp']:
            if field in record and record[field]:
                timestamp = record[field]
                try:
                    # Ensure timestamp has date and time
                    if ' ' in timestamp:
                        timestamps.append(timestamp)
                    else:
                        # Add time if only date is present
                        timestamps.append(f"{timestamp} 12:00:00")
                except (ValueError, TypeError):
                    continue
    
    # If we have no valid timestamps, return empty
    if not timestamps:
        return None, None
    
    # Normalize timestamp format - convert to datetime objects for sorting
    datetime_objects = []
    for timestamp in timestamps:
        try:
            # Try different formats
            formats_to_try = [
                '%Y-%m-%d %H:%M:%S',
                '%m/%d/%Y %H:%M:%S',
                '%Y/%m/%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%m/%d/%Y %H:%M',
                '%Y/%m/%d %H:%M'
            ]
            
            for fmt in formats_to_try:
                try:
                    dt = datetime.strptime(timestamp, fmt)
                    # Make sure it's the right date
                    if dt.strftime('%Y-%m-%d') == date_str:
                        datetime_objects.append(dt)
                        break
                except ValueError:
                    continue
        except Exception:
            continue
    
    # If we couldn't parse any valid timestamps for this date, return empty
    if not datetime_objects:
        return None, None
    
    # Sort by time
    datetime_objects.sort()
    
    # Get first and last
    first_seen = datetime_objects[0].strftime('%Y-%m-%d %H:%M:%S')
    last_seen = datetime_objects[-1].strftime('%Y-%m-%d %H:%M:%S')
    
    return first_seen, last_seen

def determine_driver_job_site(driving_records, activity_records, time_on_site_records, possible_job_sites):
    """
    Determine the job site for a driver on a specific date.
    
    Args:
        driving_records (list): Driving history records for this driver on this day
        activity_records (list): Activity detail records for this driver on this day
        time_on_site_records (list): Time on site records for this driver on this day
        possible_job_sites (list): List of possible job site names
        
    Returns:
        str: Job site name
    """
    # Count job site occurrences
    job_site_counts = {}
    
    # Extract job site info from driving records
    for record in driving_records:
        for field in ['JobSite', 'Job', 'Site']:
            if field in record and record[field]:
                job_site = record[field].strip()
                job_site_counts[job_site] = job_site_counts.get(job_site, 0) + 1
    
    # Extract job site info from activity records
    for record in activity_records:
        for field in ['JobSite', 'Job', 'Site']:
            if field in record and record[field]:
                job_site = record[field].strip()
                job_site_counts[job_site] = job_site_counts.get(job_site, 0) + 1
    
    # Extract job site info from time on site records
    for record in time_on_site_records:
        for field in ['JobSite', 'Job', 'Site']:
            if field in record and record[field]:
                job_site = record[field].strip()
                job_site_counts[job_site] = job_site_counts.get(job_site, 0) + 1
    
    # If we have job site data, return the most common one
    if job_site_counts:
        most_common_job_site = max(job_site_counts.items(), key=lambda x: x[1])[0]
        return most_common_job_site
    
    # If no job site data found, return a default
    return "Unknown Job Site"

def process_may_weekly_report(attached_assets_dir, weekly_processor_function, report_dir):
    """
    Process May 18-24, 2025 weekly driver report using actual data from the CSV files.
    
    Args:
        attached_assets_dir (str): Directory containing the attached assets
        weekly_processor_function (function): Weekly processor function to use (not used directly)
        report_dir (str): Directory to save report to
        
    Returns:
        dict: Weekly driver report data
        list: List of errors encountered
    """
    # Define date range for May 18-24, 2025
    start_date = '2025-05-18'  # Sunday
    end_date = '2025-05-24'    # Saturday
    logger.info(f"Processing actual driver data for May 18-24, 2025")
    
    # Find the relevant CSV/Excel files for processing
    errors = []
    
    # Find DrivingHistory file
    driving_history_file = None
    for filename in os.listdir(attached_assets_dir):
        if 'DrivingHistory' in filename and filename.endswith('.csv'):
            driving_history_file = os.path.join(attached_assets_dir, filename)
            logger.info(f"Found driving history file: {filename}")
            break
    
    if not driving_history_file:
        errors.append("Could not find DrivingHistory CSV file in attached_assets")
    
    # Find ActivityDetail file
    activity_detail_file = None
    for filename in os.listdir(attached_assets_dir):
        if 'ActivityDetail' in filename and filename.endswith('.csv'):
            activity_detail_file = os.path.join(attached_assets_dir, filename)
            logger.info(f"Found activity detail file: {filename}")
            break
    
    if not activity_detail_file:
        errors.append("Could not find ActivityDetail CSV file in attached_assets")
    
    # Find TimeOnSite file
    time_on_site_file = None
    for filename in os.listdir(attached_assets_dir):
        if ('TimeOnSite' in filename or 'AssetsTimeOnSite' in filename) and filename.endswith('.csv'):
            time_on_site_file = os.path.join(attached_assets_dir, filename)
            logger.info(f"Found time on site file: {filename}")
            break
    
    if not time_on_site_file:
        errors.append("Could not find TimeOnSite CSV file in attached_assets")
    
    # Find Timecard files for the week
    timecard_files = []
    for filename in os.listdir(attached_assets_dir):
        if 'Timecards' in filename and '2025-05-18' in filename and '2025-05-24' in filename and filename.endswith('.xlsx'):
            timecard_files.append(os.path.join(attached_assets_dir, filename))
            logger.info(f"Found timecard file: {filename}")
    
    if not timecard_files:
        errors.append("Could not find Timecard Excel files for May 18-24, 2025")
    
    # If we have critical errors, return them
    if errors:
        logger.error(f"Critical errors found: {', '.join(errors)}")
        return None, errors
    
    # Parse the CSV files to extract driver data
    driving_history_data = []
    activity_detail_data = []
    time_on_site_data = []
    
    # Import CSV parser fix module
    from utils.csv_parser_fix import parse_gauge_csv
    
    # Parse DrivingHistory file
    try:
        driving_history_data = parse_gauge_csv(driving_history_file)
        logger.info(f"Parsed {len(driving_history_data)} records from driving history file")
    except Exception as e:
        logger.error(f"Error parsing driving history file: {str(e)}")
        errors.append(f"Error parsing driving history file: {str(e)}")
    
    # Parse ActivityDetail file
    try:
        activity_detail_data = parse_gauge_csv(activity_detail_file)
        logger.info(f"Parsed {len(activity_detail_data)} records from activity detail file")
    except Exception as e:
        logger.error(f"Error parsing activity detail file: {str(e)}")
        errors.append(f"Error parsing activity detail file: {str(e)}")
    
    # Parse TimeOnSite file
    try:
        time_on_site_data = parse_gauge_csv(time_on_site_file)
        logger.info(f"Parsed {len(time_on_site_data)} records from time on site file")
    except Exception as e:
        logger.error(f"Error parsing time on site file: {str(e)}")
        errors.append(f"Error parsing time on site file: {str(e)}")
    
    # Process the actual data into a report
    report = process_actual_data_to_report(
        start_date, 
        end_date, 
        driving_history_data, 
        activity_detail_data, 
        time_on_site_data
    )
    
    # Save report to file
    report_path = os.path.join(report_dir, f"weekly_{start_date}_to_{end_date}.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report saved to {report_path}")
    
    return report, errors