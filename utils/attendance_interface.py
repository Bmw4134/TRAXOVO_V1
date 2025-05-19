"""
Attendance Interface Module

This module provides a bridge between the new automated attendance data pipeline
and the existing UI dashboard/reporting system. It translates between the data
structures expected by the UI and the new standardized data format from the pipeline.
"""
import os
import json
import logging
import sqlite3
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

# Constants
ATTENDANCE_DB_PATH = 'data/attendance.db'

# Initialize database if needed
def ensure_attendance_db_setup():
    """
    Ensure the attendance database is properly set up with required tables
    """
    # Create directory if needed
    os.makedirs(os.path.dirname(ATTENDANCE_DB_PATH), exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(ATTENDANCE_DB_PATH)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        driver_name TEXT NOT NULL,
        asset_id TEXT,
        scheduled_start TEXT,
        actual_start TEXT,
        scheduled_end TEXT,
        actual_end TEXT,
        location TEXT,
        job_site TEXT,
        is_late INTEGER DEFAULT 0,
        is_early_end INTEGER DEFAULT 0,
        late_minutes INTEGER DEFAULT 0,
        early_minutes INTEGER DEFAULT 0,
        company TEXT,
        status TEXT,
        region TEXT
    )
    ''')
    
    # Create index on date and driver_name
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date_driver ON attendance_records(date, driver_name)')
    
    # Create audit log table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        file_path TEXT,
        file_type TEXT,
        driver_count INTEGER,
        record_count INTEGER,
        timestamp TEXT,
        status TEXT
    )
    ''')
    
    # Save changes and close connection
    conn.commit()
    conn.close()

# Ensure the database is set up when the module is loaded
ensure_attendance_db_setup()


def get_attendance_records_for_date(date_str):
    """
    Get attendance records for a specific date from the new pipeline database
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        list: List of attendance records for the date
    """
    records = []
    
    try:
        # Connect to the attendance database
        conn = sqlite3.connect(ATTENDANCE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query attendance records for the date
        cursor.execute("""
            SELECT * FROM attendance_records 
            WHERE date = ? 
            ORDER BY driver_name
        """, (date_str,))
        
        # Convert to list of dictionaries
        for row in cursor.fetchall():
            record = dict(row)
            records.append(record)
            
        conn.close()
        
    except Exception as e:
        logger.error(f"Error retrieving attendance records: {e}")
    
    return records


def get_attendance_data(date_str):
    """
    Get attendance data formatted for the UI dashboard
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        dict: Formatted attendance data for the dashboard
    """
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    try:
        # Get records from the database
        records = get_attendance_records_for_date(date_str)
        
        if not records:
            logger.warning(f"No attendance records found for date {date_str}")
            return None
        
        # Convert date string to datetime object for formatting
        report_date = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = report_date.strftime('%A, %B %d, %Y')
        
        # Initialize counters and lists
        total_drivers = len(set([r['driver_name'] for r in records]))
        total_morning_drivers = total_drivers  # All are considered morning drivers in this system
        
        late_drivers = []
        early_end_drivers = []
        not_on_job_drivers = []
        on_time_drivers = 0
        
        # Process each record
        for record in records:
            driver_info = {
                'id': record.get('id', 0),
                'employee_id': f"E{hash(record['driver_name']) % 1000:03d}",
                'name': record['driver_name'],
                'region': record.get('region', 'Unknown'),
                'job_site': record.get('job_site', 'Unknown'),
                'expected_start': record.get('scheduled_start', '07:00:00').replace(':', ':')[:5] + ' AM',
                'expected_end': record.get('scheduled_end', '16:00:00').replace(':', ':')[:5] + ' PM',
                'vehicle': record.get('asset_id', 'Unknown')
            }
            
            # Check for lateness
            if record.get('is_late', 0) == 1:
                actual_start = record.get('actual_start', '')
                if actual_start:
                    # Convert from 24h to 12h format for display
                    time_obj = datetime.strptime(actual_start, '%H:%M:%S')
                    display_time = time_obj.strftime('%I:%M %p')
                    driver_info['actual_start'] = display_time
                    driver_info['minutes_late'] = record.get('late_minutes', 0)
                late_drivers.append(driver_info)
            else:
                on_time_drivers += 1
            
            # Check for early end
            if record.get('is_early_end', 0) == 1:
                actual_end = record.get('actual_end', '')
                if actual_end:
                    # Convert from 24h to 12h format for display
                    time_obj = datetime.strptime(actual_end, '%H:%M:%S')
                    display_time = time_obj.strftime('%I:%M %p')
                    driver_info['actual_end'] = display_time
                    driver_info['minutes_early'] = record.get('early_minutes', 0)
                early_end_drivers.append(driver_info)
            
            # For now, we don't have "not on job" in the new system
            # This would need to be calculated based on other data sources
        
        # Group data by division/region
        divisions = {}
        for record in records:
            region = record.get('region', 'Unknown')
            if region not in divisions:
                divisions[region] = {
                    'name': region,
                    'total_drivers': 0,
                    'late_count': 0,
                    'early_end_count': 0,
                    'not_on_job_count': 0
                }
            
            divisions[region]['total_drivers'] += 1
            if record.get('is_late', 0) == 1:
                divisions[region]['late_count'] += 1
            if record.get('is_early_end', 0) == 1:
                divisions[region]['early_end_count'] += 1
        
        # Format into expected structure
        return {
            'date': date_str,
            'formatted_date': formatted_date,
            'summary': {
                'total_drivers': total_drivers,
                'total_morning_drivers': total_morning_drivers,
                'on_time_drivers': on_time_drivers,
                'late_count': len(late_drivers),
                'early_end_count': len(early_end_drivers),
                'not_on_job_count': len(not_on_job_drivers)
            },
            'late_drivers': late_drivers,
            'early_end_drivers': early_end_drivers,
            'not_on_job_drivers': not_on_job_drivers,
            'exceptions': [],  # Not implemented in new system yet
            'divisions': list(divisions.values())
        }
        
    except Exception as e:
        logger.error(f"Error formatting attendance data: {e}")
        return None


def get_trend_data(end_date=None, days=5):
    """
    Get trend data for the dashboard
    
    Args:
        end_date: End date string in YYYY-MM-DD format
        days: Number of days to include in the trend
        
    Returns:
        dict: Trend data for dashboard
    """
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    start_date_obj = end_date_obj - timedelta(days=days-1)
    start_date = start_date_obj.strftime('%Y-%m-%d')
    
    try:
        # Connect to the attendance database
        conn = sqlite3.connect(ATTENDANCE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query attendance records for the date range
        cursor.execute("""
            SELECT * FROM attendance_records 
            WHERE date BETWEEN ? AND ?
            ORDER BY driver_name, date
        """, (start_date, end_date))
        
        # Convert to list of dictionaries
        records = [dict(row) for row in cursor.fetchall()]
        
        # Load trend analysis results if available
        trend_file = f'trend_report_{end_date}.json'
        trend_data = None
        if os.path.exists(trend_file):
            try:
                with open(trend_file, 'r') as f:
                    trend_data = json.load(f)
            except:
                pass
        
        if not trend_data:
            # If trend report not found, create a basic version from raw data
            driver_records = {}
            for record in records:
                driver = record['driver_name']
                if driver not in driver_records:
                    driver_records[driver] = []
                driver_records[driver].append(record)
            
            # Calculate simple trend metrics
            chronic_late = []
            repeated_absence = []
            unstable_shift = []
            
            for driver, driver_data in driver_records.items():
                # Simplified trend detection
                late_days = sum(1 for r in driver_data if r.get('is_late', 0) == 1)
                if late_days >= 3:
                    chronic_late.append(driver)
                
                # For now, we don't detect absences from this data
                
                # Simplified unstable shift detection
                if len(driver_data) >= 2:
                    start_times = []
                    for r in driver_data:
                        if r.get('actual_start'):
                            try:
                                time_obj = datetime.strptime(r['actual_start'], '%H:%M:%S')
                                start_times.append(time_obj.hour * 60 + time_obj.minute)
                            except:
                                pass
                    
                    if start_times and max(start_times) - min(start_times) > 180:  # 3 hours variance
                        unstable_shift.append(driver)
            
            trend_data = {
                'driver_trends': {},
                'summary': {
                    'chronic_late_count': len(chronic_late),
                    'repeated_absence_count': len(repeated_absence),
                    'unstable_shift_count': len(unstable_shift)
                }
            }
            
            # Add basic trend flags
            for driver in chronic_late:
                if driver not in trend_data['driver_trends']:
                    trend_data['driver_trends'][driver] = []
                trend_data['driver_trends'][driver].append('CHRONIC_LATE')
                
            for driver in unstable_shift:
                if driver not in trend_data['driver_trends']:
                    trend_data['driver_trends'][driver] = []
                trend_data['driver_trends'][driver].append('UNSTABLE_SHIFT')
        
        return trend_data
        
    except Exception as e:
        logger.error(f"Error retrieving trend data: {e}")
        return {
            'driver_trends': {},
            'summary': {
                'chronic_late_count': 0,
                'repeated_absence_count': 0,
                'unstable_shift_count': 0
            }
        }
