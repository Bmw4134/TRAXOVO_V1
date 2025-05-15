"""
SYSTEMSMITH CYA (Cover Your Assets) Module

This module handles backup, auditing, and data integrity functions:
1. Backing up data files and API responses
2. Maintaining an audit trail
3. Storing generated reports with timestamps
4. Reconciling uploaded vs. generated files
"""

import os
import json
import time
import shutil
import sqlite3
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import difflib

# Configure logging
logger = logging.getLogger(__name__)

# Constants
BACKUP_DIR = "backups"
RECONCILE_DIR = "reconcile"
AUDIT_DB_PATH = "data/audit.db"

def ensure_directories():
    """Ensure all required directories exist"""
    today = datetime.now().strftime("%Y-%m-%d")
    directories = [
        BACKUP_DIR,
        f"{BACKUP_DIR}/{today}",
        f"{BACKUP_DIR}/{today}/api",
        f"{BACKUP_DIR}/{today}/uploads",
        f"{BACKUP_DIR}/{today}/reports",
        RECONCILE_DIR
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        
    logger.info(f"CYA directories initialized for {today}")
    return directories

def initialize_audit_db():
    """Initialize the audit database if it doesn't exist"""
    os.makedirs(os.path.dirname(AUDIT_DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(AUDIT_DB_PATH)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_trail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            user_id INTEGER,
            description TEXT,
            data_path TEXT,
            metadata TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            hash TEXT NOT NULL,
            user_id INTEGER,
            operation TEXT NOT NULL,
            backup_path TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    
    logger.info("Audit database initialized")

def log_event(event_type, description, user_id=None, data_path=None, metadata=None):
    """
    Log an event to the audit trail
    
    Args:
        event_type (str): Type of event (API_PULL, FILE_UPLOAD, REPORT_GENERATED, etc.)
        description (str): Description of the event
        user_id (int, optional): ID of the user who triggered the event
        data_path (str, optional): Path to related data file
        metadata (dict, optional): Additional metadata as a dictionary
    """
    try:
        timestamp = datetime.now().isoformat()
        metadata_json = json.dumps(metadata) if metadata else None
        
        conn = sqlite3.connect(AUDIT_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO audit_trail (timestamp, event_type, user_id, description, data_path, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (timestamp, event_type, user_id, description, data_path, metadata_json)
        )
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Logged event: {event_type} - {description}")
        return True
    except Exception as e:
        logger.error(f"Error logging event: {e}")
        return False

def backup_file(file_path, category="uploads", user_id=None, operation="UPLOAD"):
    """
    Create a backup of a file
    
    Args:
        file_path (str): Path to the file to backup
        category (str): Category of the file (uploads, api, reports)
        user_id (int, optional): ID of the user who triggered the backup
        operation (str): Operation that triggered the backup (UPLOAD, DOWNLOAD, GENERATE)
        
    Returns:
        str: Path to the backup file or None if backup failed
    """
    try:
        # Ensure file exists
        if not os.path.exists(file_path):
            logger.error(f"Cannot backup nonexistent file: {file_path}")
            return None
        
        # Create destination directory
        today = datetime.now().strftime("%Y-%m-%d")
        backup_dir = f"{BACKUP_DIR}/{today}/{category}"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create a unique filename with timestamp
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        backup_filename = f"{name}_{timestamp}{ext}"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copy the file
        shutil.copy2(file_path, backup_path)
        
        # Calculate file hash
        file_hash = calculate_file_hash(file_path)
        
        # Log to database
        conn = sqlite3.connect(AUDIT_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO file_versions (file_path, timestamp, hash, user_id, operation, backup_path) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (file_path, datetime.now().isoformat(), file_hash, user_id, operation, backup_path)
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Backed up {file_path} to {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Error backing up file {file_path}: {e}")
        return None

def backup_api_response(api_data, endpoint, params=None):
    """
    Backup API response data
    
    Args:
        api_data (dict): API response data
        endpoint (str): API endpoint
        params (dict, optional): Request parameters
        
    Returns:
        str: Path to the backup file
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        backup_dir = f"{BACKUP_DIR}/{today}/api"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        endpoint_safe = endpoint.replace("/", "_").replace(":", "_")
        backup_filename = f"{endpoint_safe}_{timestamp}.json"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Add metadata
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "params": params,
            "response": api_data
        }
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        # Log event
        log_event(
            "API_RESPONSE",
            f"Backed up API response from {endpoint}",
            data_path=backup_path,
            metadata={"endpoint": endpoint, "params": params}
        )
        
        logger.info(f"Backed up API response to {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Error backing up API response: {e}")
        return None

def backup_report(report_data, report_type, format="json"):
    """
    Backup a generated report
    
    Args:
        report_data: Report data (dict or other format)
        report_type (str): Type of report
        format (str): Format of the report (json, csv, xlsx)
        
    Returns:
        str: Path to the backup file
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        backup_dir = f"{BACKUP_DIR}/{today}/reports"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{report_type}_{timestamp}.{format}"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        if format == "json":
            with open(backup_path, 'w') as f:
                json.dump(report_data, f, indent=2)
        elif format in ["csv", "txt"]:
            with open(backup_path, 'w') as f:
                f.write(report_data)
        elif format in ["xlsx", "xls", "pdf"]:
            # Binary files should be passed as file objects or file paths
            if isinstance(report_data, str) and os.path.exists(report_data):
                shutil.copy2(report_data, backup_path)
            else:
                with open(backup_path, 'wb') as f:
                    f.write(report_data)
        
        # Log event
        log_event(
            "REPORT_GENERATED",
            f"Generated and backed up {report_type} report",
            data_path=backup_path,
            metadata={"report_type": report_type, "format": format}
        )
        
        logger.info(f"Backed up {report_type} report to {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Error backing up report: {e}")
        return None

def reconcile_files(generated_file, uploaded_file, output_name=None):
    """
    Compare generated and uploaded files and store differences
    
    Args:
        generated_file (str): Path to the generated file
        uploaded_file (str): Path to the uploaded file
        output_name (str, optional): Name for the diff file
        
    Returns:
        str: Path to the diff file
    """
    try:
        if not os.path.exists(generated_file) or not os.path.exists(uploaded_file):
            logger.error(f"Cannot reconcile - files don't exist: {generated_file}, {uploaded_file}")
            return None
        
        # Create output name if not provided
        if not output_name:
            gen_name = os.path.basename(generated_file)
            upl_name = os.path.basename(uploaded_file)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"diff_{gen_name}_vs_{upl_name}_{timestamp}.txt"
        
        diff_path = os.path.join(RECONCILE_DIR, output_name)
        
        # Read files
        with open(generated_file, 'r') as f1:
            gen_lines = f1.readlines()
        
        with open(uploaded_file, 'r') as f2:
            upl_lines = f2.readlines()
        
        # Generate diff
        diff = difflib.unified_diff(
            gen_lines, 
            upl_lines,
            fromfile=f"Generated: {os.path.basename(generated_file)}",
            tofile=f"Uploaded: {os.path.basename(uploaded_file)}",
            n=3
        )
        
        # Write diff
        with open(diff_path, 'w') as f:
            f.write("".join(diff))
        
        # Log event
        log_event(
            "FILE_RECONCILIATION",
            f"Reconciled generated and uploaded files",
            data_path=diff_path,
            metadata={
                "generated_file": generated_file,
                "uploaded_file": uploaded_file,
                "diff_file": diff_path
            }
        )
        
        logger.info(f"Reconciled files and saved diff to {diff_path}")
        return diff_path
    except Exception as e:
        logger.error(f"Error reconciling files: {e}")
        return None

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of a file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def get_audit_trail(event_type=None, from_date=None, to_date=None, limit=100):
    """
    Get audit trail entries
    
    Args:
        event_type (str, optional): Filter by event type
        from_date (datetime, optional): Start date for filtering
        to_date (datetime, optional): End date for filtering
        limit (int): Maximum number of entries to return
        
    Returns:
        list: List of audit trail entries as dictionaries
    """
    try:
        conn = sqlite3.connect(AUDIT_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM audit_trail"
        params = []
        
        # Build WHERE clause
        where_clauses = []
        if event_type:
            where_clauses.append("event_type = ?")
            params.append(event_type)
        
        if from_date:
            where_clauses.append("timestamp >= ?")
            params.append(from_date.isoformat())
        
        if to_date:
            where_clauses.append("timestamp <= ?")
            params.append(to_date.isoformat())
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        # Add order and limit
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dictionaries
        results = []
        for row in rows:
            event = dict(row)
            # Parse JSON metadata
            if event['metadata']:
                event['metadata'] = json.loads(event['metadata'])
            results.append(event)
        
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Error getting audit trail: {e}")
        return []

def get_file_versions(file_path, limit=10):
    """
    Get version history for a file
    
    Args:
        file_path (str): Path to the file
        limit (int): Maximum number of versions to return
        
    Returns:
        list: List of file versions as dictionaries
    """
    try:
        conn = sqlite3.connect(AUDIT_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM file_versions WHERE file_path = ? ORDER BY timestamp DESC LIMIT ?",
            (file_path, limit)
        )
        
        rows = cursor.fetchall()
        versions = [dict(row) for row in rows]
        
        conn.close()
        return versions
    except Exception as e:
        logger.error(f"Error getting file versions: {e}")
        return []

def init():
    """Initialize the CYA module"""
    ensure_directories()
    initialize_audit_db()
    logger.info("CYA module initialized")