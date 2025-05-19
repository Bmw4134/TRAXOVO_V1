"""
Attendance Pipeline Connector

This module provides a centralized system for connecting the automated data pipeline 
to all UI views, ensuring consistent data flow from ingestion through processing to display.
"""
import os
import sqlite3
import logging
import json
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

# Constants
ATTENDANCE_DB_PATH = 'data/attendance.db'
DEFAULT_TREND_DAYS = 5  # Number of days to analyze for trends

def ensure_data_directory():
    """Ensure the data directory exists"""
    os.makedirs(os.path.dirname(ATTENDANCE_DB_PATH), exist_ok=True)

def get_db_connection():
    """Get a connection to the SQLite database"""
    ensure_data_directory()
    conn = sqlite3.connect(ATTENDANCE_DB_PATH)
    conn.row_factory = sqlite3.Row  # Allow dictionary access to rows
    return conn

def get_attendance_data(date_str=None):
    """
    Get attendance data for a specific date, formatted for the UI dashboard
    
    Args:
        date_str (str, optional): Date string in YYYY-MM-DD format. Defaults to today.
        
    Returns:
        dict: Attendance data formatted for UI display containing:
            - total_records: Total number of attendance records
            - late_starts: Number of late start records
            - early_ends: Number of early end records
            - not_on_job: Number of not on job records
            - on_time: Number of on-time records
            - late_start_records: List of late start record details
            - early_end_records: List of early end record details
            - not_on_job_records: List of not on job record details
            - trend_data: Trend data for analysis
    """
    # Use today's date if not specified
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all attendance records for the date
        cursor.execute(
            "SELECT * FROM attendance_records WHERE date = ?",
            (date_str,)
        )
        records = cursor.fetchall()
        
        # No records found
        if not records:
            logger.warning(f"No attendance records found for date {date_str}")
            # Return empty data structure
            return {
                'total_records': 0,
                'late_starts': 0,
                'early_ends': 0,
                'not_on_job': 0,
                'on_time': 0,
                'late_start_records': [],
                'early_end_records': [],
                'not_on_job_records': [],
                'trend_data': {'driver_trends': {}, 'summary': {}}
            }
        
        # Process records into required data structures
        late_start_records = []
        early_end_records = []
        not_on_job_records = []
        
        for record in records:
            record_dict = dict(record)
            
            # Process late starts
            if record['is_late'] == 1:
                late_start_records.append({
                    'driver_name': record['driver_name'],
                    'asset_id': record['asset_id'],
                    'scheduled_start': record['scheduled_start'],
                    'actual_start': record['actual_start'],
                    'late_minutes': record['late_minutes'],
                    'job_site': record['job_site'],
                    'region': record['region']
                })
            
            # Process early ends
            if record['is_early_end'] == 1:
                early_end_records.append({
                    'driver_name': record['driver_name'],
                    'asset_id': record['asset_id'],
                    'scheduled_end': record['scheduled_end'],
                    'actual_end': record['actual_end'],
                    'early_minutes': record['early_minutes'],
                    'job_site': record['job_site'],
                    'region': record['region']
                })
            
            # Process not on job (missing records)
            if record['status'] == 'NOT_ON_JOB':
                not_on_job_records.append({
                    'driver_name': record['driver_name'],
                    'asset_id': record['asset_id'],
                    'job_site': record['job_site'],
                    'region': record['region']
                })
        
        # Get trend data for the past days
        trend_data = get_trend_data(date_str)
        
        # Calculate summary counts
        total_records = len(records)
        late_starts = len(late_start_records)
        early_ends = len(early_end_records)
        not_on_job = len(not_on_job_records)
        on_time = total_records - late_starts - early_ends - not_on_job
        
        conn.close()
        
        # Return data in the format expected by the UI
        return {
            'total_records': total_records,
            'late_starts': late_starts,
            'early_ends': early_ends,
            'not_on_job': not_on_job,
            'on_time': on_time,
            'late_start_records': late_start_records,
            'early_end_records': early_end_records,
            'not_on_job_records': not_on_job_records,
            'trend_data': trend_data
        }
        
    except Exception as e:
        logger.error(f"Error retrieving attendance data: {e}")
        # Return empty data structure in case of error
        return {
            'total_records': 0,
            'late_starts': 0,
            'early_ends': 0,
            'not_on_job': 0,
            'on_time': 0,
            'late_start_records': [],
            'early_end_records': [],
            'not_on_job_records': [],
            'trend_data': {'driver_trends': {}, 'summary': {}}
        }

def get_trend_data(end_date_str=None, days=DEFAULT_TREND_DAYS):
    """
    Get trend data for analysis
    
    Args:
        end_date_str (str, optional): End date string in YYYY-MM-DD format. Defaults to today.
        days (int, optional): Number of days to include. Defaults to 5.
        
    Returns:
        dict: Trend data with driver_trends and summary statistics
    """
    # Use today's date if not specified
    if not end_date_str:
        end_date_str = datetime.now().strftime('%Y-%m-%d')
    
    try:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all attendance records for the date range
        cursor.execute(
            "SELECT * FROM attendance_records WHERE date BETWEEN ? AND ? ORDER BY date",
            (start_date_str, end_date_str)
        )
        records = cursor.fetchall()
        
        # No records found
        if not records:
            logger.warning(f"No attendance records found for trend analysis period {start_date_str} to {end_date_str}")
            return {'driver_trends': {}, 'summary': {}}
        
        # Process records for trend analysis
        driver_trends = {}
        
        for record in records:
            driver_name = record['driver_name']
            record_date = record['date']
            
            # Initialize driver data if not exists
            if driver_name not in driver_trends:
                driver_trends[driver_name] = {
                    'dates': [],
                    'late_count': 0,
                    'early_count': 0,
                    'absence_count': 0,
                    'total_late_minutes': 0,
                    'total_early_minutes': 0,
                    'asset_id': record['asset_id'],
                    'job_site': record['job_site'],
                    'region': record['region'],
                    'flag_chronic_late': False,
                    'flag_repeated_absence': False,
                    'flag_unstable_shift': False
                }
            
            # Add date to track which days we have data for
            if record_date not in driver_trends[driver_name]['dates']:
                driver_trends[driver_name]['dates'].append(record_date)
            
            # Process late starts
            if record['is_late'] == 1:
                driver_trends[driver_name]['late_count'] += 1
                driver_trends[driver_name]['total_late_minutes'] += record['late_minutes']
            
            # Process early ends
            if record['is_early_end'] == 1:
                driver_trends[driver_name]['early_count'] += 1
                driver_trends[driver_name]['total_early_minutes'] += record['early_minutes']
            
            # Process not on job
            if record['status'] == 'NOT_ON_JOB':
                driver_trends[driver_name]['absence_count'] += 1
        
        # Calculate trend flags
        for driver, data in driver_trends.items():
            # Flag: CHRONIC_LATE - 3+ times late in analysis period
            if data['late_count'] >= 3:
                data['flag_chronic_late'] = True
            
            # Flag: REPEATED_ABSENCE - 2+ absences in analysis period
            if data['absence_count'] >= 2:
                data['flag_repeated_absence'] = True
            
            # Flag: UNSTABLE_SHIFT - Check for variance in shift times (simplified version)
            if data['late_count'] + data['early_count'] >= 3:
                data['flag_unstable_shift'] = True
        
        # Calculate summary statistics
        chronic_late_count = sum(1 for d in driver_trends.values() if d['flag_chronic_late'])
        repeated_absence_count = sum(1 for d in driver_trends.values() if d['flag_repeated_absence'])
        unstable_shift_count = sum(1 for d in driver_trends.values() if d['flag_unstable_shift'])
        
        summary = {
            'chronic_late_count': chronic_late_count,
            'repeated_absence_count': repeated_absence_count,
            'unstable_shift_count': unstable_shift_count,
            'analysis_period': f"{start_date_str} to {end_date_str}",
            'drivers_analyzed': len(driver_trends)
        }
        
        conn.close()
        
        return {
            'driver_trends': driver_trends,
            'summary': summary
        }
        
    except Exception as e:
        logger.error(f"Error generating trend data: {e}")
        return {'driver_trends': {}, 'summary': {}}

def get_attendance_audit_log():
    """
    Get the audit log for attendance data processing
    
    Returns:
        list: List of audit log entries
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM attendance_audit ORDER BY id DESC LIMIT 50")
        audit_records = [dict(record) for record in cursor.fetchall()]
        
        conn.close()
        return audit_records
    except Exception as e:
        logger.error(f"Error retrieving audit log: {e}")
        return []

def record_attendance_processing(date_str, file_path, file_type, driver_count, status="COMPLETE"):
    """
    Record a data processing event in the audit log
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        file_path (str): Path to the processed file
        file_type (str): Type of file (daily_usage, timecard, etc.)
        driver_count (int): Number of drivers in the processed data
        status (str, optional): Processing status. Defaults to "COMPLETE".
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO attendance_audit (
            date, file_path, file_type, driver_count, timestamp, status
        ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            date_str,
            file_path,
            file_type,
            driver_count,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            status
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Recorded processing of {file_type} file for {date_str}")
    except Exception as e:
        logger.error(f"Error recording attendance processing: {e}")

def get_data_source_mapping():
    """
    Get a mapping of data sources to UI views
    
    Returns:
        dict: Mapping of data sources to UI views
    """
    return {
        'data_sources': [
            {
                'name': 'DailyUsage.csv',
                'description': 'Driver daily activity data from Gauge API',
                'type': 'daily_usage',
                'feeds_views': [
                    'Daily Driver Report (/daily_report)',
                    'Attendance Dashboard (/attendance_dashboard)',
                    'Driver Detail View (/driver_detail/<id>)'
                ],
                'processor': 'attendance_data_processor.py',
                'database_table': 'attendance_records',
                'sample_fields': [
                    'driver_name', 'asset_id', 'scheduled_start', 'actual_start', 
                    'scheduled_end', 'actual_end', 'is_late', 'is_early_end'
                ]
            },
            {
                'name': 'Timecards.xlsx',
                'description': 'Weekly timecard data with driver hours',
                'type': 'timecard',
                'feeds_views': [
                    'Attendance Dashboard (/attendance_dashboard)',
                    'Timecard Analysis (/timecard_analysis)'
                ],
                'processor': 'attendance_data_processor.py',
                'database_table': 'attendance_records',
                'sample_fields': [
                    'driver_name', 'hours_worked', 'job_code', 'job_site'
                ]
            },
            {
                'name': 'ActivityDetail.csv',
                'description': 'Detailed activity logs from Gauge API',
                'type': 'activity_detail',
                'feeds_views': [
                    'Vehicle History Audit (/vehicle_audit)',
                    'Job Site Analysis (/job_site_detail/<id>)'
                ],
                'processor': 'attendance_data_processor.py',
                'database_table': 'attendance_records',
                'sample_fields': [
                    'driver_name', 'asset_id', 'location', 'activity_type', 'timestamp'
                ]
            }
        ],
        'ui_views': [
            {
                'name': 'Daily Driver Report',
                'route': '/daily_report',
                'description': 'Shows daily summary of driver attendance issues',
                'data_sources': ['DailyUsage.csv', 'Timecards.xlsx'],
                'controller': 'main.py:daily_report()',
                'required_fields': [
                    'driver_name', 'asset_id', 'scheduled_start', 'actual_start', 
                    'scheduled_end', 'actual_end', 'is_late', 'is_early_end'
                ]
            },
            {
                'name': 'Attendance Dashboard',
                'route': '/attendance_dashboard',
                'description': 'Interactive dashboard showing attendance trends',
                'data_sources': ['DailyUsage.csv', 'Timecards.xlsx'],
                'controller': 'attendance_dashboard.py:attendance_dashboard()',
                'required_fields': [
                    'driver_name', 'date', 'is_late', 'is_early_end', 'late_minutes', 'early_minutes'
                ]
            },
            {
                'name': 'Driver Detail View',
                'route': '/driver_detail/<id>',
                'description': 'Detailed view of a single driver\'s attendance history',
                'data_sources': ['DailyUsage.csv', 'ActivityDetail.csv', 'Timecards.xlsx'],
                'controller': 'attendance_dashboard.py:driver_detail()',
                'required_fields': [
                    'driver_name', 'asset_id', 'date', 'is_late', 'is_early_end', 'late_minutes', 'early_minutes'
                ]
            }
        ]
    }

# Initialize database tables on module import
def init_database():
    """Initialize the database tables if they don't exist"""
    # Ensure data directory exists
    ensure_data_directory()
    
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
        timestamp TEXT,
        status TEXT
    )
    ''')
    
    # Create index on date for audit log
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_date ON attendance_audit(date)')
    
    # Save changes and close connection
    conn.commit()
    conn.close()
    
    logger.info("Attendance database initialized")

# Initialize database on module load
init_database()