"""
TRAXORA Fleet Management System - Simplified Attendance Pipeline

This module provides a streamlined version of the attendance processing logic,
implementing the core classification for on-time, late start, early end, and not on job cases.
"""

import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Define constants for attendance classification
DEFAULT_START_TIME = "07:30:00"  # 7:30 AM cutoff for late
DEFAULT_END_TIME = "16:00:00"    # 4:00 PM cutoff for early end

def normalize_driver_name(name: str) -> str:
    """Normalize driver name for consistent matching"""
    if not name:
        return ""
    
    # Remove extra spaces, convert to lowercase
    name = " ".join(str(name).strip().split()).lower()
    return name

def parse_datetime(date_str: str, time_str: str) -> Optional[datetime]:
    """Parse date and time strings into datetime object"""
    try:
        if not date_str or not time_str:
            return None
            
        # Try to standardize date format
        if '-' in date_str:
            # YYYY-MM-DD
            date_parts = date_str.split('-')
            if len(date_parts) == 3:
                year, month, day = date_parts
            else:
                return None
        elif '/' in date_str:
            # MM/DD/YYYY or DD/MM/YYYY
            date_parts = date_str.split('/')
            if len(date_parts) == 3:
                if len(date_parts[2]) == 4:  # Year is likely the last part
                    month, day, year = date_parts
                else:
                    day, month, year = date_parts
            else:
                return None
        else:
            return None
            
        # Standardize time format
        if ':' in time_str:
            # HH:MM or HH:MM:SS
            time_parts = time_str.split(':')
            if len(time_parts) >= 2:
                hour, minute = time_parts[:2]
                second = time_parts[2] if len(time_parts) > 2 else '00'
            else:
                return None
        else:
            return None
            
        # Construct datetime string and parse
        dt_str = f"{year}-{month.zfill(2)}-{day.zfill(2)} {hour.zfill(2)}:{minute.zfill(2)}:{second.zfill(2)}"
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.error(f"Error parsing datetime: {e}")
        return None

def classify_attendance(start_time: Optional[datetime], end_time: Optional[datetime], date_str: str) -> Dict[str, Any]:
    """Classify driver attendance based on start/end times"""
    # Create expected start and end times
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        expected_start = datetime.strptime(f"{date_str} {DEFAULT_START_TIME}", '%Y-%m-%d %H:%M:%S')
        expected_end = datetime.strptime(f"{date_str} {DEFAULT_END_TIME}", '%Y-%m-%d %H:%M:%S')
        
        # Default classification
        classification = {
            'classification': 'on_time',
            'expected_start': expected_start.strftime('%H:%M'),
            'expected_end': expected_end.strftime('%H:%M'),
            'actual_start': start_time.strftime('%H:%M') if start_time else 'None',
            'actual_end': end_time.strftime('%H:%M') if end_time else 'None',
            'reason': 'On time arrival and departure'
        }
        
        # Not on job (missing both start and end)
        if not start_time and not end_time:
            classification['classification'] = 'not_on_job'
            classification['reason'] = 'No activity detected'
            return classification
            
        # Late start (after expected start time)
        if start_time and start_time > expected_start:
            minutes_late = round((start_time - expected_start).total_seconds() / 60)
            if minutes_late > 0:
                classification['classification'] = 'late'
                classification['reason'] = f"Started {minutes_late} minutes after expected start time"
                
        # Early end (before expected end time)
        if end_time and end_time < expected_end:
            minutes_early = round((expected_end - end_time).total_seconds() / 60)
            if minutes_early > 0:
                # If already classified as late, prioritize late classification
                if classification['classification'] != 'late':
                    classification['classification'] = 'early_end'
                    classification['reason'] = f"Ended {minutes_early} minutes before expected end time"
                else:
                    classification['reason'] += f" and ended {minutes_early} minutes early"
                    
        return classification
        
    except Exception as e:
        logger.error(f"Error classifying attendance: {e}")
        return {
            'classification': 'error',
            'reason': f"Error: {str(e)}"
        }

def process_attendance_data(date_str: str, 
                          driving_history_df: Optional[pd.DataFrame] = None,
                          activity_detail_df: Optional[pd.DataFrame] = None,
                          time_on_site_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """Process attendance data from multiple sources"""
    try:
        if not date_str:
            logger.error("Date string is required")
            return {"error": "Date string is required"}
            
        # Initialize data structures
        driver_records = {}
        data_sources = []
        
        # Process driving history data if available
        if driving_history_df is not None and not driving_history_df.empty:
            data_sources.append("driving_history")
            
            for _, row in driving_history_df.iterrows():
                driver_name = normalize_driver_name(row.get('driver_name') or row.get('Driver Name'))
                if not driver_name:
                    continue
                    
                # Extract timestamps
                start_time = None
                end_time = None
                
                # Look for start time
                if 'first_start' in row and pd.notna(row['first_start']):
                    start_date = row.get('date') or date_str
                    start_time = parse_datetime(start_date, str(row['first_start']))
                    
                # Look for end time
                if 'last_end' in row and pd.notna(row['last_end']):
                    end_date = row.get('date') or date_str
                    end_time = parse_datetime(end_date, str(row['last_end']))
                
                # Create or update driver record
                if driver_name not in driver_records:
                    driver_records[driver_name] = {
                        'name': driver_name,
                        'start_time': start_time,
                        'end_time': end_time,
                        'job_site': row.get('job_site') or row.get('Job Site') or 'Unknown',
                        'sources': ["driving_history"]
                    }
                else:
                    # Update with priority given to earliest start and latest end
                    if start_time and (not driver_records[driver_name]['start_time'] or 
                                      start_time < driver_records[driver_name]['start_time']):
                        driver_records[driver_name]['start_time'] = start_time
                        
                    if end_time and (not driver_records[driver_name]['end_time'] or 
                                    end_time > driver_records[driver_name]['end_time']):
                        driver_records[driver_name]['end_time'] = end_time
                        
                    if "driving_history" not in driver_records[driver_name]['sources']:
                        driver_records[driver_name]['sources'].append("driving_history")
        
        # Process time on site data if available
        if time_on_site_df is not None and not time_on_site_df.empty:
            data_sources.append("time_on_site")
            
            for _, row in time_on_site_df.iterrows():
                driver_name = normalize_driver_name(row.get('driver_name') or row.get('Driver Name'))
                if not driver_name:
                    continue
                    
                # Extract timestamps
                start_time = None
                end_time = None
                
                # Look for start time
                if 'time_in' in row and pd.notna(row['time_in']):
                    start_date = row.get('date') or date_str
                    start_time = parse_datetime(start_date, str(row['time_in']))
                    
                # Look for end time
                if 'time_out' in row and pd.notna(row['time_out']):
                    end_date = row.get('date') or date_str
                    end_time = parse_datetime(end_date, str(row['time_out']))
                
                # Create or update driver record
                if driver_name not in driver_records:
                    driver_records[driver_name] = {
                        'name': driver_name,
                        'start_time': start_time,
                        'end_time': end_time,
                        'job_site': row.get('job_site') or row.get('Job Site') or 'Unknown',
                        'sources': ["time_on_site"]
                    }
                else:
                    # Update with priority given to earliest start and latest end
                    if start_time and (not driver_records[driver_name]['start_time'] or 
                                      start_time < driver_records[driver_name]['start_time']):
                        driver_records[driver_name]['start_time'] = start_time
                        
                    if end_time and (not driver_records[driver_name]['end_time'] or 
                                    end_time > driver_records[driver_name]['end_time']):
                        driver_records[driver_name]['end_time'] = end_time
                        
                    if "time_on_site" not in driver_records[driver_name]['sources']:
                        driver_records[driver_name]['sources'].append("time_on_site")
        
        # Process activity detail data if available
        if activity_detail_df is not None and not activity_detail_df.empty:
            data_sources.append("activity_detail")
            
            for _, row in activity_detail_df.iterrows():
                driver_name = normalize_driver_name(row.get('driver_name') or row.get('Driver Name'))
                if not driver_name:
                    continue
                    
                # Extract timestamps
                start_time = None
                end_time = None
                
                # Look for start time
                if 'start_time' in row and pd.notna(row['start_time']):
                    start_date = row.get('date') or date_str
                    start_time = parse_datetime(start_date, str(row['start_time']))
                    
                # Look for end time
                if 'end_time' in row and pd.notna(row['end_time']):
                    end_date = row.get('date') or date_str
                    end_time = parse_datetime(end_date, str(row['end_time']))
                
                # Create or update driver record
                if driver_name not in driver_records:
                    driver_records[driver_name] = {
                        'name': driver_name,
                        'start_time': start_time,
                        'end_time': end_time,
                        'job_site': row.get('job_site') or row.get('Job Site') or 'Unknown',
                        'sources': ["activity_detail"]
                    }
                else:
                    # Update with priority given to earliest start and latest end
                    if start_time and (not driver_records[driver_name]['start_time'] or 
                                      start_time < driver_records[driver_name]['start_time']):
                        driver_records[driver_name]['start_time'] = start_time
                        
                    if end_time and (not driver_records[driver_name]['end_time'] or 
                                    end_time > driver_records[driver_name]['end_time']):
                        driver_records[driver_name]['end_time'] = end_time
                        
                    if "activity_detail" not in driver_records[driver_name]['sources']:
                        driver_records[driver_name]['sources'].append("activity_detail")
        
        # Classify attendance for each driver
        for name, record in driver_records.items():
            classification = classify_attendance(record['start_time'], record['end_time'], date_str)
            record.update(classification)
            
        # Calculate summary statistics
        summary = {
            'total_drivers': len(driver_records),
            'on_time': sum(1 for r in driver_records.values() if r.get('classification') == 'on_time'),
            'late': sum(1 for r in driver_records.values() if r.get('classification') == 'late'),
            'early_end': sum(1 for r in driver_records.values() if r.get('classification') == 'early_end'),
            'not_on_job': sum(1 for r in driver_records.values() if r.get('classification') == 'not_on_job')
        }
        
        # Build the final report
        report = {
            'date': date_str,
            'driver_records': list(driver_records.values()),
            'summary': summary,
            'data_sources': data_sources
        }
        
        # Add metrics
        report['metrics'] = {
            'on_time_percentage': round(summary.get('on_time', 0) / max(summary.get('total_drivers', 1), 1) * 100, 1),
            'late_percentage': round(summary.get('late', 0) / max(summary.get('total_drivers', 1), 1) * 100, 1),
            'early_end_percentage': round(summary.get('early_end', 0) / max(summary.get('total_drivers', 1), 1) * 100, 1),
            'not_on_job_percentage': round(summary.get('not_on_job', 0) / max(summary.get('total_drivers', 1), 1) * 100, 1)
        }
        
        return report
        
    except Exception as e:
        logger.error(f"Error processing attendance data: {e}")
        return {
            'error': str(e),
            'date': date_str,
            'driver_records': [],
            'summary': {
                'total_drivers': 0,
                'on_time': 0,
                'late': 0,
                'early_end': 0,
                'not_on_job': 0
            },
            'metrics': {
                'on_time_percentage': 0,
                'late_percentage': 0,
                'early_end_percentage': 0,
                'not_on_job_percentage': 0
            },
            'data_sources': data_sources if 'data_sources' in locals() else []
        }

def generate_attendance_report(attendance_data: Dict[str, Any], format: str = 'json') -> Dict[str, Any]:
    """Generate attendance report"""
    try:
        # For simplicity, just return the attendance data
        return attendance_data
    except Exception as e:
        logger.error(f"Error generating attendance report: {e}")
        return {
            'error': str(e),
            'date': attendance_data.get('date', 'Unknown'),
            'format': format
        }

def process_attendance_data_v2(driving_history_data=None, time_on_site_data=None, 
                           activity_detail_data=None, timecard_data=None, date_str=None):
    """Compatibility function for the old v2 API"""
    try:
        # Convert data to DataFrames if needed
        driving_history_df = pd.DataFrame(driving_history_data) if driving_history_data else None
        time_on_site_df = pd.DataFrame(time_on_site_data) if time_on_site_data else None
        activity_detail_df = pd.DataFrame(activity_detail_data) if activity_detail_data else None
        
        # Process the attendance data
        return process_attendance_data(
            date_str=date_str,
            driving_history_df=driving_history_df,
            activity_detail_df=activity_detail_df,
            time_on_site_df=time_on_site_df
        )
    except Exception as e:
        logger.error(f"Error in process_attendance_data_v2: {e}")
        return {
            'error': str(e),
            'date': date_str,
            'driver_records': [],
            'summary': {
                'total_drivers': 0,
                'on_time': 0,
                'late': 0,
                'early_end': 0,
                'not_on_job': 0
            }
        }