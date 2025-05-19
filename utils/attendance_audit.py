"""
Attendance Audit Module

This module provides audit logging and reporting capabilities for the attendance data pipeline,
tracking which files were processed for each date and how many drivers were included.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define path constants
DATA_DIR = Path("data")
AUDIT_DIR = DATA_DIR / "audit"
ATTENDANCE_DB = DATA_DIR / "attendance.db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
AUDIT_DIR.mkdir(exist_ok=True)

def setup_audit_database():
    """Create audit database tables if they don't exist"""
    conn = sqlite3.connect(ATTENDANCE_DB)
    cursor = conn.cursor()
    
    # Create attendance_audit table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        timestamp TEXT,
        file_path TEXT,
        file_type TEXT,
        driver_count INTEGER,
        records_added INTEGER,
        status TEXT,
        error_message TEXT
    )
    ''')
    
    # Create attendance_summary table for quick access to processed data completeness
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_summary (
        date TEXT PRIMARY KEY,
        last_updated TEXT,
        total_drivers INTEGER,
        total_files_processed INTEGER,
        file_types TEXT,
        completeness_score REAL,
        status TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Audit database setup complete")

def log_file_processing(date, file_path, file_type, driver_count, records_added, status="success", error_message=None):
    """
    Log the processing of a file for a specific date
    
    Args:
        date (str): Date in YYYY-MM-DD format
        file_path (str): Path to the processed file
        file_type (str): Type of file (e.g., 'daily_usage', 'timecard', 'activity_detail')
        driver_count (int): Number of drivers in the file
        records_added (int): Number of records successfully added to the database
        status (str): Processing status ('success', 'partial', 'failed')
        error_message (str): Error message if processing failed
    """
    timestamp = datetime.now().isoformat()
    
    conn = sqlite3.connect(ATTENDANCE_DB)
    cursor = conn.cursor()
    
    # Add to audit log
    cursor.execute('''
    INSERT INTO attendance_audit
    (date, timestamp, file_path, file_type, driver_count, records_added, status, error_message)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        date,
        timestamp,
        str(file_path),
        file_type,
        driver_count,
        records_added,
        status,
        error_message
    ))
    
    # Update summary for this date
    cursor.execute('''
    SELECT * FROM attendance_summary WHERE date = ?
    ''', (date,))
    
    existing_summary = cursor.fetchone()
    
    if existing_summary:
        # Update existing summary
        cursor.execute('''
        SELECT SUM(driver_count), SUM(records_added), COUNT(*), GROUP_CONCAT(DISTINCT file_type)
        FROM attendance_audit
        WHERE date = ?
        ''', (date,))
        
        total_drivers, total_records, total_files, file_types = cursor.fetchone()
        
        # Calculate completeness score (simplified version)
        completeness_score = min(1.0, total_records / max(1, total_drivers))
        
        cursor.execute('''
        UPDATE attendance_summary
        SET last_updated = ?, total_drivers = ?, total_files_processed = ?,
            file_types = ?, completeness_score = ?, status = ?
        WHERE date = ?
        ''', (
            timestamp,
            total_drivers,
            total_files,
            file_types,
            completeness_score,
            'complete' if completeness_score >= 0.9 else 'partial',
            date
        ))
    else:
        # Create new summary
        cursor.execute('''
        INSERT INTO attendance_summary
        (date, last_updated, total_drivers, total_files_processed, file_types, completeness_score, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            date,
            timestamp,
            driver_count,
            1,
            file_type,
            records_added / max(1, driver_count),
            'complete' if driver_count > 0 and records_added >= driver_count * 0.9 else 'partial'
        ))
    
    conn.commit()
    conn.close()

def get_processed_dates(min_completeness=0.0):
    """
    Get a list of all processed dates and their completeness status
    
    Args:
        min_completeness (float): Minimum completeness score (0.0-1.0) to include
        
    Returns:
        list: List of dictionaries with date info
    """
    conn = sqlite3.connect(ATTENDANCE_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM attendance_summary
    WHERE completeness_score >= ?
    ORDER BY date DESC
    ''', (min_completeness,))
    
    rows = cursor.fetchall()
    date_info = []
    
    for row in rows:
        date_info.append(dict(row))
    
    conn.close()
    return date_info

def get_date_audit_details(date):
    """
    Get detailed audit information for a specific date
    
    Args:
        date (str): Date in YYYY-MM-DD format
        
    Returns:
        dict: Dictionary with detailed audit information
    """
    conn = sqlite3.connect(ATTENDANCE_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get summary
    cursor.execute('''
    SELECT * FROM attendance_summary WHERE date = ?
    ''', (date,))
    
    summary = cursor.fetchone()
    
    if not summary:
        conn.close()
        return {"error": f"No data available for date {date}"}
    
    # Get file processing details
    cursor.execute('''
    SELECT * FROM attendance_audit WHERE date = ? ORDER BY timestamp
    ''', (date,))
    
    audit_rows = cursor.fetchall()
    file_details = [dict(row) for row in audit_rows]
    
    # Get driver counts
    cursor.execute('''
    SELECT COUNT(DISTINCT driver_name) FROM daily_attendance WHERE date = ?
    ''', (date,))
    
    unique_drivers_count = cursor.fetchone()[0]
    
    # Get status breakdown 
    cursor.execute('''
    SELECT 
        SUM(CASE WHEN is_late = 1 THEN 1 ELSE 0 END) as late_count,
        SUM(CASE WHEN is_early_end = 1 THEN 1 ELSE 0 END) as early_count,
        COUNT(*) as total_count
    FROM daily_attendance WHERE date = ?
    ''', (date,))
    
    status_counts = cursor.fetchone()
    late_count = status_counts[0] or 0
    early_count = status_counts[1] or 0
    total_count = status_counts[2] or 0
    
    conn.close()
    
    return {
        "date": date,
        "summary": dict(summary),
        "file_details": file_details,
        "driver_stats": {
            "unique_drivers": unique_drivers_count,
            "late_count": late_count,
            "early_count": early_count,
            "total_records": total_count
        }
    }

def generate_audit_report(output_path=None):
    """
    Generate a comprehensive audit report for all processed dates
    
    Args:
        output_path (str): Path to save the JSON report
        
    Returns:
        dict: Audit report data
    """
    # Get all processed dates
    all_dates = get_processed_dates()
    
    # Get detailed information for each date
    date_details = {}
    for date_info in all_dates:
        date = date_info['date']
        date_details[date] = get_date_audit_details(date)
    
    # Create report structure
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_dates_processed": len(all_dates),
        "dates_by_completeness": {
            "complete": sum(1 for d in all_dates if d['status'] == 'complete'),
            "partial": sum(1 for d in all_dates if d['status'] == 'partial')
        },
        "date_details": date_details
    }
    
    # Save report if output_path is provided
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
    
    return report