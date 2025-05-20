"""
Attendance Audit Module

This module provides functions for auditing and tracking attendance data processing,
including source file tracking, error logging, and report generation status.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

# Constants
AUDIT_DIR = Path('logs/attendance')
AUDIT_DIR.mkdir(exist_ok=True, parents=True)

def create_audit_record(date_str, status="processing"):
    """
    Create or update an audit record for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        status (str): Status of processing (processing, completed, error)
        
    Returns:
        dict: Audit record
    """
    audit_file = AUDIT_DIR / f"{date_str}_audit.json"
    
    # Initialize or load existing audit record
    if os.path.exists(audit_file):
        try:
            with open(audit_file, 'r') as f:
                audit_record = json.load(f)
        except Exception as e:
            logger.error(f"Error loading audit record: {e}")
            audit_record = {}
    else:
        audit_record = {}
    
    # Update audit record
    audit_record.update({
        'date': date_str,
        'status': status,
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    })
    
    # Initialize sections if they don't exist
    if 'sources' not in audit_record:
        audit_record['sources'] = []
    
    if 'stats' not in audit_record:
        audit_record['stats'] = {
            'total_drivers': 0,
            'matched_drivers': 0,
            'unmatched_drivers': 0,
            'late_drivers': 0,
            'early_end_drivers': 0,
            'not_on_job_drivers': 0
        }
    
    if 'errors' not in audit_record:
        audit_record['errors'] = []
    
    # Save audit record
    try:
        with open(audit_file, 'w') as f:
            json.dump(audit_record, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving audit record: {e}")
    
    return audit_record

def add_source_file(date_str, file_path, file_type):
    """
    Add a source file to the audit record
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        file_path (str): Path to the source file
        file_type (str): Type of source file (e.g., driving_history, activity_detail)
        
    Returns:
        dict: Updated audit record
    """
    audit_record = create_audit_record(date_str)
    
    # Add source file if not already present
    source_files = audit_record.get('sources', [])
    file_entry = {
        'path': file_path,
        'type': file_type,
        'added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
    }
    
    # Check if file already exists
    for existing in source_files:
        if existing.get('path') == file_path and existing.get('type') == file_type:
            # Update existing entry
            existing.update(file_entry)
            break
    else:
        # Add new entry
        source_files.append(file_entry)
    
    audit_record['sources'] = source_files
    
    # Save updated audit record
    audit_file = AUDIT_DIR / f"{date_str}_audit.json"
    try:
        with open(audit_file, 'w') as f:
            json.dump(audit_record, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving audit record: {e}")
    
    return audit_record

def update_stats(date_str, stats):
    """
    Update statistics in the audit record
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        stats (dict): Statistics to update
        
    Returns:
        dict: Updated audit record
    """
    audit_record = create_audit_record(date_str)
    
    # Update statistics
    audit_record['stats'].update(stats)
    
    # Save updated audit record
    audit_file = AUDIT_DIR / f"{date_str}_audit.json"
    try:
        with open(audit_file, 'w') as f:
            json.dump(audit_record, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving audit record: {e}")
    
    return audit_record

def log_error(date_str, error_message, error_source=None):
    """
    Log an error in the audit record
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        error_message (str): Error message
        error_source (str): Source of the error (e.g., file path, function name)
        
    Returns:
        dict: Updated audit record
    """
    audit_record = create_audit_record(date_str, status="error")
    
    # Add error
    errors = audit_record.get('errors', [])
    error_entry = {
        'message': error_message,
        'source': error_source,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    errors.append(error_entry)
    audit_record['errors'] = errors
    
    # Save updated audit record
    audit_file = AUDIT_DIR / f"{date_str}_audit.json"
    try:
        with open(audit_file, 'w') as f:
            json.dump(audit_record, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving audit record: {e}")
    
    return audit_record

def complete_audit(date_str, success=True):
    """
    Mark audit record as completed
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        success (bool): Whether processing was successful
        
    Returns:
        dict: Updated audit record
    """
    status = "completed" if success else "error"
    audit_record = create_audit_record(date_str, status=status)
    
    # Add completion timestamp
    audit_record['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Save updated audit record
    audit_file = AUDIT_DIR / f"{date_str}_audit.json"
    try:
        with open(audit_file, 'w') as f:
            json.dump(audit_record, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving audit record: {e}")
    
    return audit_record

def get_audit_record(date_str):
    """
    Get audit record for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        dict: Audit record or None if not found
    """
    audit_file = AUDIT_DIR / f"{date_str}_audit.json"
    
    if os.path.exists(audit_file):
        try:
            with open(audit_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading audit record: {e}")
    
    return None

def list_audit_records():
    """
    List all audit records
    
    Returns:
        list: List of audit records
    """
    audit_files = list(AUDIT_DIR.glob('*_audit.json'))
    
    records = []
    for audit_file in audit_files:
        try:
            with open(audit_file, 'r') as f:
                record = json.load(f)
                records.append(record)
        except Exception as e:
            logger.error(f"Error loading audit record {audit_file}: {e}")
    
    # Sort by date
    records.sort(key=lambda x: x.get('date', ''))
    
    return records