"""
CYA (Cover Your Assets) Module

This module provides utilities for backup, audit logging, and data integrity verification.
It serves as a comprehensive audit trail and backup system for SYSTEMSMITH.
"""
import os
import json
import sqlite3
import logging
import zipfile
import shutil
import hashlib
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Constants
BASE_BACKUP_DIR = 'backups'
AUDIT_DB_PATH = os.path.join(BASE_BACKUP_DIR, 'audit_trail.db')
MAX_BACKUPS_PER_CATEGORY = 25  # Maximum number of backups to keep per category

# Ensure base backup directories exist
def ensure_directories(dirs: List[str]) -> None:
    """
    Ensure that the given directories exist
    
    Args:
        dirs (List[str]): List of directories to create
    """
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)

# Initialize backup directories
ensure_directories([
    BASE_BACKUP_DIR,
    os.path.join(BASE_BACKUP_DIR, 'api'),
    os.path.join(BASE_BACKUP_DIR, 'files'),
    os.path.join(BASE_BACKUP_DIR, 'reports'),
    os.path.join(BASE_BACKUP_DIR, 'database'),
    'uploads',
    'data',
    'data/processed',
    'data/reports'
])

# Initialize audit database
def _init_audit_db() -> None:
    """Initialize the audit trail database"""
    conn = sqlite3.connect(AUDIT_DB_PATH)
    cursor = conn.cursor()
    
    # Create audit_events table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        event_data TEXT NOT NULL,
        user_id TEXT,
        timestamp TEXT NOT NULL,
        ip_address TEXT,
        user_agent TEXT,
        hash TEXT NOT NULL
    )
    ''')
    
    # Create file_versions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS file_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_path TEXT NOT NULL,
        backup_path TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_hash TEXT NOT NULL,
        size INTEGER NOT NULL,
        user_id TEXT,
        timestamp TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Audit database initialized successfully")

# Initialize the audit database
_init_audit_db()

def log_event(event_type: str, event_data: Dict[str, Any], 
              user_id: Optional[str] = None, 
              ip_address: Optional[str] = None,
              user_agent: Optional[str] = None) -> int:
    """
    Log an event to the audit trail
    
    Args:
        event_type (str): Type of event
        event_data (Dict[str, Any]): Event data
        user_id (Optional[str]): ID of the user who triggered the event
        ip_address (Optional[str]): IP address of the user
        user_agent (Optional[str]): User agent of the user
        
    Returns:
        int: ID of the logged event
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Convert event data to JSON string
    event_data_json = json.dumps(event_data)
    
    # Calculate hash for integrity verification
    hash_content = f"{event_type}|{event_data_json}|{user_id}|{timestamp}|{ip_address}|{user_agent}"
    event_hash = hashlib.sha256(hash_content.encode()).hexdigest()
    
    # Insert into database
    conn = sqlite3.connect(AUDIT_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO audit_events (event_type, event_data, user_id, timestamp, ip_address, user_agent, hash)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (event_type, event_data_json, user_id, timestamp, ip_address, user_agent, event_hash))
    
    event_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    logger.info(f"Audit event logged: {event_type}, ID: {event_id}")
    
    return event_id

def backup_file(file_path: str, category: str = 'files', 
               compress: bool = True, user_id: Optional[str] = None) -> str:
    """
    Create a backup of a file
    
    Args:
        file_path (str): Path to the file to back up
        category (str): Category of the backup (files, api, reports, database)
        compress (bool): Whether to compress the backup
        user_id (Optional[str]): ID of the user who initiated the backup
        
    Returns:
        str: Path to the backup file
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found for backup: {file_path}")
        return ""
    
    # Get file information
    file_size = os.path.getsize(file_path)
    filename = os.path.basename(file_path)
    file_ext = os.path.splitext(filename)[1].lower()
    
    # Calculate file hash for integrity verification
    with open(file_path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"{os.path.splitext(filename)[0]}_{timestamp}{file_ext}"
    
    # Determine category directory
    backup_dir = os.path.join(BASE_BACKUP_DIR, category)
    ensure_directories([backup_dir])
    
    backup_path = os.path.join(backup_dir, backup_filename)
    
    # Create backup
    if compress and file_ext not in ['.zip', '.gz', '.bz2', '.xz']:
        # Use ZIP compression
        backup_path += '.zip'
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(file_path, arcname=filename)
    else:
        # Simple copy
        shutil.copy2(file_path, backup_path)
    
    # Record file version in database
    conn = sqlite3.connect(AUDIT_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO file_versions (original_path, backup_path, file_type, file_hash, size, user_id, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (file_path, backup_path, category, file_hash, file_size, user_id, timestamp))
    
    conn.commit()
    conn.close()
    
    logger.info(f"File backup created: {backup_path}")
    
    # Prune old backups if necessary
    _prune_old_backups(category)
    
    return backup_path

def _prune_old_backups(category: str) -> None:
    """
    Prune old backups to stay within the maximum limit
    
    Args:
        category (str): Category of backups to prune
    """
    conn = sqlite3.connect(AUDIT_DB_PATH)
    cursor = conn.cursor()
    
    # Get count of backups in this category
    cursor.execute('SELECT COUNT(*) FROM file_versions WHERE file_type = ?', (category,))
    count = cursor.fetchone()[0]
    
    if count > MAX_BACKUPS_PER_CATEGORY:
        # Get the oldest backups to delete
        cursor.execute('''
        SELECT id, backup_path FROM file_versions 
        WHERE file_type = ? 
        ORDER BY timestamp ASC 
        LIMIT ?
        ''', (category, count - MAX_BACKUPS_PER_CATEGORY))
        
        to_delete = cursor.fetchall()
        
        for id, backup_path in to_delete:
            # Delete the backup file
            if os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                    logger.info(f"Pruned old backup: {backup_path}")
                except Exception as e:
                    logger.error(f"Error pruning backup {backup_path}: {e}")
            
            # Delete the database entry
            cursor.execute('DELETE FROM file_versions WHERE id = ?', (id,))
    
    conn.commit()
    conn.close()

def backup_api_response(endpoint: str, response_data: Dict[str, Any], user_id: Optional[str] = None) -> str:
    """
    Backup an API response
    
    Args:
        endpoint (str): API endpoint
        response_data (Dict[str, Any]): API response data
        user_id (Optional[str]): ID of the user who made the API request
        
    Returns:
        str: Path to the backup file
    """
    # Create a temporary file with the response data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    endpoint_sanitized = endpoint.replace('/', '_').replace(':', '_')
    temp_file_path = os.path.join('data', 'temp_api_response.json')
    
    with open(temp_file_path, 'w') as f:
        json.dump(response_data, f, indent=2)
    
    # Backup the temporary file
    backup_filename = f"api_{endpoint_sanitized}_{timestamp}.json"
    backup_dir = os.path.join(BASE_BACKUP_DIR, 'api')
    ensure_directories([backup_dir])
    
    backup_path = os.path.join(backup_dir, backup_filename)
    
    # Create backup
    shutil.copy2(temp_file_path, backup_path)
    
    # Remove temporary file
    os.remove(temp_file_path)
    
    # Log event
    log_event('api_backup', {
        'endpoint': endpoint,
        'backup_path': backup_path,
        'size': os.path.getsize(backup_path)
    }, user_id)
    
    return backup_path

def backup_report(report_data: Dict[str, Any], report_type: str, 
                 filename: Optional[str] = None, user_id: Optional[str] = None) -> str:
    """
    Backup a generated report
    
    Args:
        report_data (Dict[str, Any]): Report data
        report_type (str): Type of report
        filename (Optional[str]): Custom filename for the report
        user_id (Optional[str]): ID of the user who generated the report
        
    Returns:
        str: Path to the backup file
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if not filename:
        filename = f"report_{report_type}_{timestamp}.json"
    
    # Ensure the filename has a .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    # Create the report file
    temp_file_path = os.path.join('data', 'reports', filename)
    ensure_directories([os.path.dirname(temp_file_path)])
    
    with open(temp_file_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    # Backup the report file
    backup_path = backup_file(temp_file_path, 'reports', True, user_id)
    
    # Log event
    log_event('report_backup', {
        'report_type': report_type,
        'original_path': temp_file_path,
        'backup_path': backup_path
    }, user_id)
    
    return backup_path

def get_audit_trail(limit: int = 100, event_type: Optional[str] = None, 
                   user_id: Optional[str] = None, 
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get the audit trail
    
    Args:
        limit (int): Maximum number of events to return
        event_type (Optional[str]): Filter by event type
        user_id (Optional[str]): Filter by user ID
        start_date (Optional[str]): Filter by start date (YYYY-MM-DD)
        end_date (Optional[str]): Filter by end date (YYYY-MM-DD)
        
    Returns:
        List[Dict[str, Any]]: Audit trail events
    """
    conn = sqlite3.connect(AUDIT_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = 'SELECT * FROM audit_events WHERE 1=1'
    params = []
    
    if event_type:
        query += ' AND event_type = ?'
        params.append(event_type)
    
    if user_id:
        query += ' AND user_id = ?'
        params.append(user_id)
    
    if start_date:
        query += ' AND timestamp >= ?'
        params.append(f"{start_date} 00:00:00")
    
    if end_date:
        query += ' AND timestamp <= ?'
        params.append(f"{end_date} 23:59:59")
    
    query += ' ORDER BY timestamp DESC LIMIT ?'
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    events = []
    for row in rows:
        event = dict(row)
        # Parse JSON data
        event['event_data'] = json.loads(event['event_data'])
        events.append(event)
    
    conn.close()
    
    return events

def get_file_versions(original_path: Optional[str] = None, 
                     category: Optional[str] = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get file version history
    
    Args:
        original_path (Optional[str]): Filter by original file path
        category (Optional[str]): Filter by file category
        limit (int): Maximum number of versions to return
        
    Returns:
        List[Dict[str, Any]]: File versions
    """
    conn = sqlite3.connect(AUDIT_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = 'SELECT * FROM file_versions WHERE 1=1'
    params = []
    
    if original_path:
        query += ' AND original_path = ?'
        params.append(original_path)
    
    if category:
        query += ' AND file_type = ?'
        params.append(category)
    
    query += ' ORDER BY timestamp DESC LIMIT ?'
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    versions = []
    for row in rows:
        versions.append(dict(row))
    
    conn.close()
    
    return versions

def restore_file_version(backup_path: str, destination_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Restore a file from a backup
    
    Args:
        backup_path (str): Path to the backup file
        destination_path (Optional[str]): Path to restore to (if None, uses original path)
        
    Returns:
        Tuple[bool, str]: Success status and message or path
    """
    if not os.path.exists(backup_path):
        return False, f"Backup file not found: {backup_path}"
    
    # Get original path from database if destination not specified
    if not destination_path:
        conn = sqlite3.connect(AUDIT_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT original_path FROM file_versions WHERE backup_path = ?', (backup_path,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            destination_path = result[0]
        else:
            return False, "Original path not found in database for this backup"
    
    # Create a backup of the current file before restoring
    if os.path.exists(destination_path):
        current_backup = backup_file(destination_path, 'restore_points')
        
        if not current_backup:
            logger.warning(f"Failed to backup current file before restore: {destination_path}")
    
    # Check if backup is compressed (zip)
    if backup_path.endswith('.zip'):
        # Extract from zip
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Get the first file in the archive
                filename = zipf.namelist()[0]
                
                # Create directories if needed
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                
                # Extract to destination
                zipf.extract(filename, os.path.dirname(destination_path))
                
                # Rename if necessary
                extracted_path = os.path.join(os.path.dirname(destination_path), filename)
                if extracted_path != destination_path:
                    shutil.move(extracted_path, destination_path)
                
                return True, destination_path
        except Exception as e:
            return False, f"Error extracting backup: {str(e)}"
    else:
        # Simple copy
        try:
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            shutil.copy2(backup_path, destination_path)
            return True, destination_path
        except Exception as e:
            return False, f"Error copying backup: {str(e)}"

def verify_integrity(file_path: str) -> Tuple[bool, str]:
    """
    Verify the integrity of a file by comparing its hash with the stored hash
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        Tuple[bool, str]: Integrity status and message
    """
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"
    
    # Calculate current hash
    with open(file_path, 'rb') as f:
        current_hash = hashlib.sha256(f.read()).hexdigest()
    
    # Get stored hash from database
    conn = sqlite3.connect(AUDIT_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT file_hash, timestamp FROM file_versions 
    WHERE original_path = ? 
    ORDER BY timestamp DESC LIMIT 1
    ''', (file_path,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return False, "No integrity information found for this file"
    
    stored_hash, timestamp = result
    
    if current_hash == stored_hash:
        return True, f"Integrity verified. File is identical to version from {timestamp}"
    else:
        return False, f"Integrity check failed. File has been modified since {timestamp}"

def reconcile_files(source_dir: str, target_dir: str) -> Dict[str, Any]:
    """
    Reconcile files between two directories
    
    Args:
        source_dir (str): Source directory
        target_dir (str): Target directory
        
    Returns:
        Dict[str, Any]: Reconciliation results
    """
    if not os.path.exists(source_dir) or not os.path.isdir(source_dir):
        return {
            'success': False,
            'message': f"Source directory not found: {source_dir}",
            'results': {}
        }
    
    if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
        return {
            'success': False,
            'message': f"Target directory not found: {target_dir}",
            'results': {}
        }
    
    # Get all files recursively in both directories
    source_files = {}
    target_files = {}
    
    for root, _, files in os.walk(source_dir):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, source_dir)
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            source_files[rel_path] = {
                'path': file_path,
                'hash': file_hash,
                'size': os.path.getsize(file_path)
            }
    
    for root, _, files in os.walk(target_dir):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, target_dir)
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            target_files[rel_path] = {
                'path': file_path,
                'hash': file_hash,
                'size': os.path.getsize(file_path)
            }
    
    # Compare files
    missing_in_target = []
    missing_in_source = []
    different = []
    identical = []
    
    for rel_path, source_info in source_files.items():
        if rel_path in target_files:
            target_info = target_files[rel_path]
            if source_info['hash'] == target_info['hash']:
                identical.append(rel_path)
            else:
                different.append({
                    'path': rel_path,
                    'source_size': source_info['size'],
                    'target_size': target_info['size']
                })
        else:
            missing_in_target.append(rel_path)
    
    for rel_path in target_files:
        if rel_path not in source_files:
            missing_in_source.append(rel_path)
    
    return {
        'success': True,
        'message': "Reconciliation completed",
        'results': {
            'missing_in_target': missing_in_target,
            'missing_in_source': missing_in_source,
            'different': different,
            'identical': identical,
            'source_file_count': len(source_files),
            'target_file_count': len(target_files),
            'identical_count': len(identical),
            'different_count': len(different)
        }
    }