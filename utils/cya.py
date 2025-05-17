"""
CYA Module - Cover Your Assets

This module provides silent backup and audit logging functionality
for all file uploads, report generations, and system actions.
"""

import os
import json
import hashlib
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from flask import request, session, current_app

# Ensure CYA directories exist
def ensure_directories():
    """Create necessary directories for CYA module"""
    base_dir = Path('./backups')
    file_backups = base_dir / 'files'
    report_backups = base_dir / 'reports'
    audit_logs = base_dir / 'logs'
    
    for directory in [base_dir, file_backups, report_backups, audit_logs]:
        directory.mkdir(exist_ok=True)
    
    return {
        'base': base_dir,
        'files': file_backups,
        'reports': report_backups,
        'logs': audit_logs
    }

# Initialize SQLite audit database
def init_audit_db():
    """Initialize the SQLite audit database"""
    db_path = Path('./backups/audit.db')
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create audit trail table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_trail (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        user_id INTEGER,
        username TEXT,
        file_name TEXT,
        file_path TEXT,
        file_hash TEXT,
        organization_id INTEGER,
        ip_address TEXT,
        user_agent TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        details TEXT
    )
    ''')
    
    # Create file backups table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS file_backups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_path TEXT NOT NULL,
        backup_path TEXT NOT NULL,
        file_hash TEXT NOT NULL,
        file_size INTEGER,
        mime_type TEXT,
        created_by INTEGER,
        organization_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

# Create file hash
def get_file_hash(file_path):
    """Calculate SHA-256 hash of a file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

# Log audit event
def log_audit_event(action_type, file_name=None, file_path=None, file_hash=None, details=None):
    """Log an audit event to the SQLite database"""
    try:
        db_path = Path('./backups/audit.db')
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get user information
        user_id = session.get('user_id') if session else None
        username = session.get('username') if session else None
        organization_id = session.get('organization_id') if session else None
        
        # Get request information
        ip_address = request.remote_addr if request else None
        user_agent = request.user_agent.string if request and request.user_agent else None
        
        # Prepare JSON details if provided
        if details and isinstance(details, dict):
            details_json = json.dumps(details)
        else:
            details_json = details
        
        # Insert audit record
        cursor.execute('''
        INSERT INTO audit_trail 
        (action_type, user_id, username, file_name, file_path, file_hash, 
         organization_id, ip_address, user_agent, timestamp, details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            action_type, user_id, username, file_name, file_path, file_hash,
            organization_id, ip_address, user_agent, datetime.now().isoformat(), details_json
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        # Silent failure - don't disrupt regular operations
        current_app.logger.error(f"Failed to log audit event: {str(e)}")
        return False

# Backup a file
def backup_file(file_path, user_id=None, organization_id=None):
    """Create a backup of a file"""
    try:
        # Ensure we have a Path object
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        # Skip if file doesn't exist
        if not file_path.exists():
            return False
        
        # Create backup directories
        dirs = ensure_directories()
        
        # Generate backup path with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = file_path.name
        backup_dir = dirs['files'] / timestamp
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / filename
        
        # Copy the file
        shutil.copy2(file_path, backup_path)
        
        # Calculate file hash
        file_hash = get_file_hash(file_path)
        
        # Record the backup in database
        db_path = Path('./backups/audit.db')
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO file_backups 
        (original_path, backup_path, file_hash, file_size, created_by, organization_id)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            str(file_path), str(backup_path), file_hash, 
            file_path.stat().st_size, user_id, organization_id
        ))
        
        conn.commit()
        conn.close()
        
        # Log the backup action
        log_audit_event(
            'file_backup', 
            file_name=filename,
            file_path=str(file_path),
            file_hash=file_hash,
            details={'backup_path': str(backup_path)}
        )
        
        return True
    except Exception as e:
        # Silent failure - don't disrupt regular operations
        current_app.logger.error(f"Failed to backup file: {str(e)}")
        return False

# Backup a report or generated file
def backup_report(report_path, report_type=None, user_id=None, organization_id=None):
    """Create a backup of a generated report"""
    try:
        # Ensure we have a Path object
        if isinstance(report_path, str):
            report_path = Path(report_path)
        
        # Skip if file doesn't exist
        if not report_path.exists():
            return False
        
        # Create backup directories
        dirs = ensure_directories()
        
        # Generate backup path with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = report_path.name
        
        # Organize by report type if provided
        if report_type:
            backup_dir = dirs['reports'] / report_type / timestamp
        else:
            backup_dir = dirs['reports'] / timestamp
            
        backup_dir.mkdir(exist_ok=True, parents=True)
        backup_path = backup_dir / filename
        
        # Copy the file
        shutil.copy2(report_path, backup_path)
        
        # Calculate file hash
        file_hash = get_file_hash(report_path)
        
        # Log the backup action
        log_audit_event(
            'report_backup', 
            file_name=filename,
            file_path=str(report_path),
            file_hash=file_hash,
            details={
                'backup_path': str(backup_path),
                'report_type': report_type
            }
        )
        
        return True
    except Exception as e:
        # Silent failure - don't disrupt regular operations
        current_app.logger.error(f"Failed to backup report: {str(e)}")
        return False

# Export audit logs to JSON
def export_audit_logs(start_date=None, end_date=None, action_type=None, user_id=None):
    """Export audit logs to a JSON file"""
    try:
        # Create query conditions
        conditions = []
        params = []
        
        if start_date:
            conditions.append("timestamp >= ?")
            params.append(start_date)
        
        if end_date:
            conditions.append("timestamp <= ?")
            params.append(end_date)
        
        if action_type:
            conditions.append("action_type = ?")
            params.append(action_type)
        
        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
        
        # Build query
        query = "SELECT * FROM audit_trail"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY timestamp DESC"
        
        # Execute query
        db_path = Path('./backups/audit.db')
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dictionary list
        audit_logs = []
        for row in rows:
            audit_logs.append({key: row[key] for key in row.keys()})
        
        conn.close()
        
        # Generate output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dirs = ensure_directories()
        output_file = dirs['logs'] / f"audit_export_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(audit_logs, f, indent=2)
        
        return str(output_file)
    except Exception as e:
        current_app.logger.error(f"Failed to export audit logs: {str(e)}")
        return None

# Initialize the CYA module
def init_cya_module():
    """Initialize the CYA module"""
    ensure_directories()
    init_audit_db()
    
    # Log initialization event
    log_audit_event('system', details="CYA module initialized")
    
    return True