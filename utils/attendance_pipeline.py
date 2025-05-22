"""
TRAXORA GENIUS CORE | Attendance Pipeline

This module provides the comprehensive attendance pipeline that combines multiple data sources,
performs cross-validation and classification for attendance reporting.

Key components:
1. Multi-source integration (TimeOnSite, DrivingHistory, ActivityDetail, Timecard)
2. Driver + Date join keys
3. Advanced classification (On Time, Late, No Show, Early End)
4. Timecard cross-validation
5. Exportable reports (Weekly summary, Daily details)
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, time, timedelta
import pytz

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for attendance classification
STANDARD_START_TIME = time(7, 0)  # 7:00 AM
LATE_THRESHOLD = time(7, 15)      # 7:15 AM
EARLY_END_TIME = time(15, 30)     # 3:30 PM
STANDARD_END_TIME = time(16, 0)   # 4:00 PM
MINIMUM_HOURS = 8.0               # Minimum expected hours

# Central timezone for standardization
CENTRAL_TZ = pytz.timezone('US/Central')

def normalize_name(name: Optional[str]) -> Optional[str]:
    """Normalize driver name for consistent matching"""
    if not name:
        return None
    
    # Convert to string, strip whitespace, and convert to lowercase
    name = str(name).strip().lower()
    
    # Remove common prefixes/suffixes
    name = name.replace('driver:', '').replace('id:', '')
    
    return name

def normalize_time(time_str: Optional[Union[str, time, datetime]]) -> Optional[time]:
    """Normalize time string to time object for consistent comparison"""
    if not time_str or pd.isna(time_str):
        return None
    
    try:
        # Handle various time formats
        if isinstance(time_str, time):
            return time_str
        elif isinstance(time_str, datetime):
            return time_str.time()
        
        # Clean up the string
        time_str = str(time_str).strip().upper()
        
        # Remove timezone info if present
        if " " in time_str and any(tz in time_str for tz in ["CST", "CDT", "CT"]):
            time_str = time_str.split(" ")[0]
        
        # Handle AM/PM format
        if "AM" in time_str or "PM" in time_str:
            # Try direct parsing
            try:
                dt = datetime.strptime(time_str, "%I:%M %p")
                return dt.time()
            except ValueError:
                try:
                    dt = datetime.strptime(time_str, "%I:%M:%S %p")
                    return dt.time()
                except ValueError:
                    try:
                        dt = datetime.strptime(time_str, "%I%p")
                        return dt.time()
                    except ValueError:
                        pass
        
        # Try 24-hour format
        try:
            if ":" in time_str:
                parts = time_str.split(":")
                if len(parts) == 2:
                    return time(int(parts[0]), int(parts[1]))
                elif len(parts) == 3:
                    return time(int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            pass
        
        # Try more specific formats
        for fmt in [
            "%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p", 
            "%I%p", "%H%M", "%I%M%p"
        ]:
            try:
                dt = datetime.strptime(time_str, fmt)
                return dt.time()
            except ValueError:
                continue
        
        logger.warning(f"Could not parse time string: {time_str}")
        return None
    except Exception as e:
        logger.error(f"Error normalizing time '{time_str}': {str(e)}")
        return None

def normalize_date(date_str: Optional[Union[str, datetime]]) -> Optional[str]:
    """Normalize date to YYYY-MM-DD format for consistent comparison"""
    if not date_str or pd.isna(date_str):
        return None
    
    try:
        # Handle datetime objects
        if isinstance(date_str, datetime):
            return date_str.strftime('%Y-%m-%d')
        
        # Clean string
        date_str = str(date_str).strip()
        
        # Remove time component if present
        if "T" in date_str:
            date_str = date_str.split("T")[0]
        elif " " in date_str:
            date_str = date_str.split(" ")[0]
        
        # Try various formats
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%Y/%m/%d"]:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date string: {date_str}")
        return None
    except Exception as e:
        logger.error(f"Error normalizing date '{date_str}': {str(e)}")
        return None

def calculate_hours(time_in: Optional[time], time_out: Optional[time]) -> Optional[float]:
    """Calculate hours between time_in and time_out"""
    if not time_in or not time_out:
        return None
    
    try:
        # Create today's datetime with the given times
        today = datetime.today().date()
        dt_in = datetime.combine(today, time_in)
        dt_out = datetime.combine(today, time_out)
        
        # Handle overnight shifts
        if dt_out < dt_in:
            dt_out = datetime.combine(today + timedelta(days=1), time_out)
        
        # Calculate duration in hours
        duration = (dt_out - dt_in).total_seconds() / 3600
        
        # Cap unreasonable values
        if duration > 24:
            logger.warning(f"Calculated duration ({duration:.2f} hrs) exceeds 24 hours, capping at 12")
            duration = 12.0
        
        return round(duration, 2)
    except Exception as e:
        logger.error(f"Error calculating hours: {str(e)}")
        return None

def classify_attendance(time_in: Optional[time], time_out: Optional[time], 
                       timecard_hours: Optional[float] = None) -> Dict:
    """
    Classify attendance based on time in, time out, and timecard hours.
    
    Returns a dict with:
    - status: on_time, late, no_show, early_end, or unclassified
    - reason: Explanation for the classification
    - flags: List of flags for this record
    """
    result = {
        "status": "unclassified",
        "reason": "Insufficient data to classify",
        "flags": []
    }
    
    # No data case
    if time_in is None and time_out is None and (timecard_hours is None or timecard_hours <= 0):
        result["status"] = "no_show"
        result["reason"] = "No time records found for this date"
        result["flags"].append("missing_time_records")
        return result
    
    # Calculate hours if we have both times
    calculated_hours = None
    if time_in and time_out:
        calculated_hours = calculate_hours(time_in, time_out)
    
    # Handle time in classification
    if time_in:
        if time_in <= STANDARD_START_TIME:
            result["status"] = "on_time"
            result["reason"] = f"Arrived on time (before {STANDARD_START_TIME.strftime('%I:%M %p')})"
        elif time_in <= LATE_THRESHOLD:
            result["status"] = "on_time"
            result["reason"] = f"Arrived within grace period (before {LATE_THRESHOLD.strftime('%I:%M %p')})"
            result["flags"].append("within_grace_period")
        else:
            result["status"] = "late"
            result["reason"] = f"Arrived late (after {LATE_THRESHOLD.strftime('%I:%M %p')})"
            result["flags"].append("late_arrival")
    else:
        # Have time out but no time in
        if time_out:
            result["status"] = "unclassified"
            result["reason"] = "Missing arrival time"
            result["flags"].append("missing_time_in")
        else:
            result["status"] = "no_show"
            result["reason"] = "No time records found"
            result["flags"].append("missing_time_records")
    
    # Check for early end if we have end time
    if time_out and time_in and result["status"] != "no_show":
        if time_out < EARLY_END_TIME:
            result["status"] = "early_end"
            result["reason"] = f"Left early (before {EARLY_END_TIME.strftime('%I:%M %p')})"
            result["flags"].append("early_departure")
        
        # If hours are less than minimum expected
        if calculated_hours and calculated_hours < MINIMUM_HOURS:
            result["flags"].append("insufficient_hours")
            
            # If status is already problematic, don't override
            if result["status"] not in ["late", "early_end", "no_show"]:
                result["status"] = "early_end"
                result["reason"] = f"Insufficient hours: {calculated_hours:.1f} (minimum {MINIMUM_HOURS})"
    
    # Cross-check with timecard hours if available
    if timecard_hours is not None and timecard_hours > 0:
        # If timecard shows sufficient hours but our classification says otherwise
        if timecard_hours >= MINIMUM_HOURS and calculated_hours and calculated_hours < MINIMUM_HOURS:
            result["flags"].append("timecard_mismatch")
            result["flags"].append("timecard_shows_sufficient_hours")
        
        # If timecard shows insufficient hours but our classification is on_time
        if timecard_hours < MINIMUM_HOURS and result["status"] == "on_time" and not "insufficient_hours" in result["flags"]:
            result["flags"].append("timecard_mismatch")
            result["flags"].append("timecard_shows_insufficient_hours")
    
    return result

def combine_attendance_data(time_on_site_data: List[Dict], driving_history_data: List[Dict], 
                           activity_detail_data: Optional[List[Dict]] = None, 
                           timecard_data: Optional[List[Dict]] = None) -> List[Dict]:
    """
    Combine attendance data from multiple sources using driver+date as join keys.
    
    Args:
        time_on_site_data: List of TimeOnSite records
        driving_history_data: List of DrivingHistory records
        activity_detail_data: Optional list of ActivityDetail records
        timecard_data: Optional list of Timecard records
        
    Returns:
        List of combined attendance records with classification
    """
    logger.info("Combining attendance data from multiple sources")
    
    # Convert lists to DataFrames for easier manipulation
    tos_df = pd.DataFrame(time_on_site_data) if time_on_site_data else pd.DataFrame()
    dh_df = pd.DataFrame(driving_history_data) if driving_history_data else pd.DataFrame()
    ad_df = pd.DataFrame(activity_detail_data) if activity_detail_data else pd.DataFrame()
    tc_df = pd.DataFrame(timecard_data) if timecard_data else pd.DataFrame()
    
    # Normalize driver names and dates for consistent joining
    for df in [tos_df, dh_df, ad_df, tc_df]:
        if not df.empty:
            if 'driver_name' in df.columns:
                df['driver_name_norm'] = df['driver_name'].apply(normalize_name)
            elif 'employee_name' in df.columns:
                df['driver_name_norm'] = df['employee_name'].apply(normalize_name)
                df['driver_name'] = df['employee_name']
            
            if 'date' in df.columns:
                df['date_norm'] = df['date'].apply(normalize_date)
    
    # Dictionary to store combined records by driver+date key
    combined_records = {}
    
    # Process all data sources to find all unique driver+date combinations
    for df, source_name in [(tos_df, 'TimeOnSite'), (dh_df, 'DrivingHistory'), 
                           (ad_df, 'ActivityDetail'), (tc_df, 'Timecard')]:
        if df.empty:
            continue
        
        for _, row in df.iterrows():
            driver_name = row.get('driver_name')
            driver_name_norm = row.get('driver_name_norm')
            date = row.get('date')
            date_norm = row.get('date_norm')
            
            if not driver_name_norm or not date_norm:
                continue
            
            # Create key for this driver+date combo
            key = f"{driver_name_norm}_{date_norm}"
            
            # Initialize record if it doesn't exist
            if key not in combined_records:
                combined_records[key] = {
                    'driver_name': driver_name,
                    'driver_name_norm': driver_name_norm,
                    'date': date,
                    'date_norm': date_norm,
                    'sources': [],
                    'time_in': None,
                    'time_out': None,
                    'job_site': None,
                    'asset_id': None,
                    'timecard_hours': None,
                    'timecard_job': None,
                    'calculated_hours': None,
                    'classification': {},
                    'raw_data': {}
                }
            
            # Add source to the list
            if source_name not in combined_records[key]['sources']:
                combined_records[key]['sources'].append(source_name)
            
            # Store the raw data for reference
            combined_records[key]['raw_data'][source_name] = row.to_dict()
    
    # Process data from each source to populate fields
    for key, record in combined_records.items():
        # Process TimeOnSite data (most accurate for time windows)
        if 'TimeOnSite' in record['sources']:
            row = record['raw_data']['TimeOnSite']
            
            time_in = normalize_time(row.get('time_in'))
            time_out = normalize_time(row.get('time_out'))
            
            if time_in:
                record['time_in'] = time_in
                record['time_in_raw'] = row.get('time_in')
            
            if time_out:
                record['time_out'] = time_out
                record['time_out_raw'] = row.get('time_out')
            
            if row.get('job_site'):
                record['job_site'] = row.get('job_site')
            
            if row.get('asset_id'):
                record['asset_id'] = row.get('asset_id')
        
        # Process DrivingHistory data (good for movement windows)
        if 'DrivingHistory' in record['sources']:
            row = record['raw_data']['DrivingHistory']
            
            # Only update if not already set
            if not record['time_in']:
                time_in = normalize_time(row.get('time_in'))
                if time_in:
                    record['time_in'] = time_in
                    record['time_in_raw'] = row.get('time_in')
            
            if not record['time_out']:
                time_out = normalize_time(row.get('time_out'))
                if time_out:
                    record['time_out'] = time_out
                    record['time_out_raw'] = row.get('time_out')
            
            if not record['job_site'] and row.get('job_site'):
                record['job_site'] = row.get('job_site')
            
            if not record['asset_id'] and row.get('asset_id'):
                record['asset_id'] = row.get('asset_id')
        
        # Process ActivityDetail data (good for context)
        if 'ActivityDetail' in record['sources']:
            row = record['raw_data']['ActivityDetail']
            
            # Only update if not already set
            if not record['time_in']:
                time_in = normalize_time(row.get('time_in'))
                if time_in:
                    record['time_in'] = time_in
                    record['time_in_raw'] = row.get('time_in')
            
            if not record['time_out']:
                time_out = normalize_time(row.get('time_out'))
                if time_out:
                    record['time_out'] = time_out
                    record['time_out_raw'] = row.get('time_out')
            
            if not record['job_site'] and row.get('job_site'):
                record['job_site'] = row.get('job_site')
            
            if not record['asset_id'] and row.get('asset_id'):
                record['asset_id'] = row.get('asset_id')
        
        # Process Timecard data (for cross-validation)
        if 'Timecard' in record['sources']:
            row = record['raw_data']['Timecard']
            
            # Extract hours
            if row.get('hours'):
                try:
                    record['timecard_hours'] = float(row.get('hours'))
                except (ValueError, TypeError):
                    pass
            
            # Extract job information
            if row.get('job'):
                record['timecard_job'] = row.get('job')
            
            # Try to get time if no other source provided
            if not record['time_in'] and row.get('time_in'):
                time_in = normalize_time(row.get('time_in'))
                if time_in:
                    record['time_in'] = time_in
                    record['time_in_raw'] = row.get('time_in')
            
            if not record['time_out'] and row.get('time_out'):
                time_out = normalize_time(row.get('time_out'))
                if time_out:
                    record['time_out'] = time_out
                    record['time_out_raw'] = row.get('time_out')
        
        # Calculate hours if we have both times
        if record['time_in'] and record['time_out']:
            record['calculated_hours'] = calculate_hours(record['time_in'], record['time_out'])
        
        # Classify attendance
        record['classification'] = classify_attendance(
            record['time_in'],
            record['time_out'],
            record['timecard_hours']
        )
        
        # Cross-validate job site with timecard
        if record['job_site'] and record['timecard_job']:
            # Normalize for comparison
            js = str(record['job_site']).strip().upper()
            tj = str(record['timecard_job']).strip().upper()
            
            # Check if there's a job number mismatch
            if js != tj and not js in tj and not tj in js:
                record['classification']['flags'].append('job_site_mismatch')
    
    # Convert dictionary to list
    combined_list = list(combined_records.values())
    
    # Remove raw_data to reduce size
    for record in combined_list:
        if 'raw_data' in record:
            del record['raw_data']
    
    logger.info(f"Combined {len(combined_list)} attendance records from multiple sources")
    return combined_list

def generate_weekly_summary(attendance_records: List[Dict]) -> List[Dict]:
    """
    Generate weekly summary by driver from attendance records.
    
    Args:
        attendance_records: List of combined attendance records
        
    Returns:
        List of weekly summary records by driver
    """
    if not attendance_records:
        return []
    
    # Group by driver name
    drivers = {}
    for record in attendance_records:
        driver_name = record['driver_name']
        if driver_name not in drivers:
            drivers[driver_name] = []
        drivers[driver_name].append(record)
    
    # Generate summary for each driver
    weekly_summary = []
    
    for driver_name, records in drivers.items():
        # Sort records by date
        records.sort(key=lambda x: x['date'])
        
        # Calculate date range
        dates = [r['date'] for r in records]
        first_date = min(dates) if dates else None
        last_date = max(dates) if dates else None
        
        # Count statuses
        status_counts = {
            'on_time': 0,
            'late': 0,
            'early_end': 0,
            'no_show': 0,
            'unclassified': 0
        }
        
        for record in records:
            status = record['classification']['status']
            if status in status_counts:
                status_counts[status] += 1
        
        # Compile flag counts
        flag_counts = {}
        for record in records:
            for flag in record['classification'].get('flags', []):
                flag_counts[flag] = flag_counts.get(flag, 0) + 1
        
        # Create summary record
        summary = {
            'driver_name': driver_name,
            'week_start': first_date,
            'week_end': last_date,
            'total_days': len(records),
            'on_time_days': status_counts['on_time'],
            'late_days': status_counts['late'],
            'early_end_days': status_counts['early_end'],
            'no_show_days': status_counts['no_show'],
            'unclassified_days': status_counts['unclassified'],
            'flag_counts': flag_counts,
            'flags': [],
            'daily_records': records
        }
        
        # Set summary flags
        if summary['late_days'] > 0:
            summary['flags'].append('has_late_days')
        if summary['early_end_days'] > 0:
            summary['flags'].append('has_early_end_days')
        if summary['no_show_days'] > 0:
            summary['flags'].append('has_no_show_days')
        
        # Flag attendance patterns
        if summary['late_days'] >= 2:
            summary['flags'].append('multiple_late_days')
        if summary['early_end_days'] >= 2:
            summary['flags'].append('multiple_early_end_days')
        if summary['no_show_days'] >= 1:
            summary['flags'].append('has_absence')
        
        # Flag timecard issues
        if flag_counts.get('timecard_mismatch', 0) > 0:
            summary['flags'].append('timecard_mismatches')
        if flag_counts.get('job_site_mismatch', 0) > 0:
            summary['flags'].append('job_mismatches')
        if flag_counts.get('insufficient_hours', 0) > 0:
            summary['flags'].append('insufficient_hours')
        
        weekly_summary.append(summary)
    
    return weekly_summary

def export_attendance_reports(attendance_records: List[Dict], export_dir: str = "exports") -> Dict[str, str]:
    """
    Generate export files (CSV and JSON) from attendance records.
    
    Args:
        attendance_records: List of combined attendance records
        export_dir: Directory to save export files
        
    Returns:
        Dictionary with paths to export files
    """
    if not attendance_records:
        return {'error': 'No attendance records to export'}
    
    # Ensure export directory exists
    os.makedirs(export_dir, exist_ok=True)
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Generate weekly summary
    weekly_summary = generate_weekly_summary(attendance_records)
    
    # Prepare detailed records for CSV export
    detailed_records = []
    for record in attendance_records:
        # Format times for CSV
        time_in_str = record['time_in'].strftime('%I:%M %p') if record['time_in'] else ''
        time_out_str = record['time_out'].strftime('%I:%M %p') if record['time_out'] else ''
        
        # Flatten the record for CSV export
        flat_record = {
            'driver_name': record['driver_name'],
            'date': record['date'],
            'job_site': record['job_site'] or '',
            'time_in': time_in_str,
            'time_out': time_out_str,
            'status': record['classification']['status'],
            'reason': record['classification']['reason'],
            'flags': ','.join(record['classification']['flags']),
            'sources': ','.join(record['sources']),
            'calculated_hours': record.get('calculated_hours', ''),
            'timecard_hours': record.get('timecard_hours', ''),
            'timecard_job': record.get('timecard_job', '')
        }
        detailed_records.append(flat_record)
    
    # Export detailed records to CSV
    detailed_csv_path = os.path.join(export_dir, f"attendance_detailed_{timestamp}.csv")
    pd.DataFrame(detailed_records).to_csv(detailed_csv_path, index=False)
    
    # Prepare weekly summary for CSV export
    summary_records = []
    for summary in weekly_summary:
        # Create a flattened version without daily records
        flat_summary = {
            'driver_name': summary['driver_name'],
            'week_start': summary['week_start'],
            'week_end': summary['week_end'],
            'total_days': summary['total_days'],
            'on_time_days': summary['on_time_days'],
            'late_days': summary['late_days'],
            'early_end_days': summary['early_end_days'],
            'no_show_days': summary['no_show_days'],
            'unclassified_days': summary['unclassified_days'],
            'flags': ','.join(summary['flags'])
        }
        
        # Add flag counts
        for flag, count in summary['flag_counts'].items():
            flat_summary[f'flag_{flag}'] = count
        
        summary_records.append(flat_summary)
    
    # Export weekly summary to CSV
    summary_csv_path = os.path.join(export_dir, f"attendance_summary_{timestamp}.csv")
    pd.DataFrame(summary_records).to_csv(summary_csv_path, index=False)
    
    # Export full data to JSON with special datetime handling
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (datetime, time)):
                return obj.isoformat()
            return super().default(obj)
    
    # Export detailed records to JSON
    detailed_json_path = os.path.join(export_dir, f"attendance_detailed_{timestamp}.json")
    with open(detailed_json_path, 'w') as f:
        json.dump(attendance_records, f, cls=DateTimeEncoder, indent=2)
    
    # Export weekly summary to JSON
    summary_json_path = os.path.join(export_dir, f"attendance_summary_{timestamp}.json")
    with open(summary_json_path, 'w') as f:
        json.dump(weekly_summary, f, cls=DateTimeEncoder, indent=2)
    
    # Return paths to export files
    return {
        'detailed_csv': detailed_csv_path,
        'summary_csv': summary_csv_path,
        'detailed_json': detailed_json_path,
        'summary_json': summary_json_path
    }

def process_weekly_attendance_report(
    time_on_site_files: List[str], 
    driving_history_files: List[str],
    activity_detail_files: Optional[List[str]] = None,
    timecard_files: Optional[List[str]] = None
) -> Dict:
    """
    Process a complete weekly attendance report from multiple file sources.
    
    Args:
        time_on_site_files: List of paths to TimeOnSite files
        driving_history_files: List of paths to DrivingHistory files
        activity_detail_files: Optional list of paths to ActivityDetail files
        timecard_files: Optional list of paths to Timecard files
        
    Returns:
        Dictionary with processing results including export paths
    """
    from utils.enhanced_data_ingestion import load_csv_file, load_excel_file
    
    logger.info("Starting weekly attendance report processing")
    
    # Load all data files
    time_on_site_data = []
    driving_history_data = []
    activity_detail_data = []
    timecard_data = []
    
    # Process TimeOnSite files
    for file_path in time_on_site_files:
        logger.info(f"Processing TimeOnSite file: {os.path.basename(file_path)}")
        
        # Determine file type
        if file_path.lower().endswith(('.csv', '.txt')):
            records = load_csv_file(file_path)
        elif file_path.lower().endswith(('.xlsx', '.xls')):
            records = load_excel_file(file_path)
        else:
            logger.warning(f"Unsupported file format: {file_path}")
            continue
        
        time_on_site_data.extend(records)
    
    # Process DrivingHistory files
    for file_path in driving_history_files:
        logger.info(f"Processing DrivingHistory file: {os.path.basename(file_path)}")
        
        # Determine file type
        if file_path.lower().endswith(('.csv', '.txt')):
            records = load_csv_file(file_path)
        elif file_path.lower().endswith(('.xlsx', '.xls')):
            records = load_excel_file(file_path)
        else:
            logger.warning(f"Unsupported file format: {file_path}")
            continue
        
        driving_history_data.extend(records)
    
    # Process ActivityDetail files if provided
    if activity_detail_files:
        for file_path in activity_detail_files:
            logger.info(f"Processing ActivityDetail file: {os.path.basename(file_path)}")
            
            # Determine file type
            if file_path.lower().endswith(('.csv', '.txt')):
                records = load_csv_file(file_path)
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                records = load_excel_file(file_path)
            else:
                logger.warning(f"Unsupported file format: {file_path}")
                continue
            
            activity_detail_data.extend(records)
    
    # Process Timecard files if provided
    if timecard_files:
        for file_path in timecard_files:
            logger.info(f"Processing Timecard file: {os.path.basename(file_path)}")
            
            # Determine file type
            if file_path.lower().endswith(('.csv', '.txt')):
                records = load_csv_file(file_path)
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                records = load_excel_file(file_path)
            else:
                logger.warning(f"Unsupported file format: {file_path}")
                continue
            
            timecard_data.extend(records)
    
    # Combine all data sources
    attendance_records = combine_attendance_data(
        time_on_site_data,
        driving_history_data,
        activity_detail_data,
        timecard_data
    )
    
    # Generate weekly summary
    weekly_summary = generate_weekly_summary(attendance_records)
    
    # Export reports
    export_paths = export_attendance_reports(attendance_records)
    
    # Return processing results
    return {
        'time_on_site_count': len(time_on_site_data),
        'driving_history_count': len(driving_history_data),
        'activity_detail_count': len(activity_detail_data),
        'timecard_count': len(timecard_data),
        'attendance_records': len(attendance_records),
        'weekly_summary': len(weekly_summary),
        'export_paths': export_paths,
        'success': True
    }