"""
CYA (Cover Your Assets) Module

This module provides backup, audit, and reconciliation functionality for the SYSTEMSMITH application.
It logs all data uploads, API pulls, and file modifications to ensure traceability and accountability.
"""

import os
import json
import shutil
import sqlite3
import hashlib
import logging
from datetime import datetime
import pandas as pd

# Setup logging
logger = logging.getLogger(__name__)

# Constants
AUDIT_DB_PATH = os.path.join('data', 'systemsmith_audit.sqlite')
RECONCILE_DIFF_PATH = os.path.join('data', 'reconcile_diff.json')
BACKUP_DIR = 'backups'

# Ensure required directories exist
os.makedirs(os.path.dirname(AUDIT_DB_PATH), exist_ok=True)
os.makedirs(os.path.dirname(RECONCILE_DIFF_PATH), exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# SQLite schema initialization
def init_audit_db():
    """
    Initialize the audit database if it doesn't exist
    """
    conn = sqlite3.connect(AUDIT_DB_PATH)
    cursor = conn.cursor()
    
    # Create action_log table to track all system actions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS action_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        action_type TEXT NOT NULL,
        user_id INTEGER,
        file_path TEXT,
        file_hash TEXT,
        details TEXT,
        status TEXT
    )
    ''')
    
    # Create file_backup table to track file backups
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS file_backup (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_file TEXT NOT NULL,
        backup_path TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        file_hash TEXT NOT NULL,
        file_size INTEGER,
        file_type TEXT,
        user_id INTEGER
    )
    ''')
    
    # Create reconciliation_log table to track differences
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reconciliation_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        file1_path TEXT NOT NULL,
        file2_path TEXT NOT NULL,
        diff_path TEXT,
        diff_count INTEGER,
        status TEXT,
        details TEXT
    )
    ''')
    
    # Create self_score table to track system self-evaluation
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS self_score (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        asset_assignment_accuracy REAL,
        gps_coverage_percent REAL,
        billing_match_rate REAL,
        overall_health_score REAL,
        improvement_suggestions TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    
    logger.info("Audit database initialized successfully")

# Initialize database at module import time
init_audit_db()

def log_action(action_type, user_id=None, file_path=None, details=None, status="success"):
    """
    Log an action in the audit database
    
    Args:
        action_type (str): Type of action (e.g., 'upload', 'api_pull', 'process')
        user_id (int, optional): ID of the user who performed the action
        file_path (str, optional): Path to the file involved in the action
        details (str or dict, optional): Additional details about the action
        status (str, optional): Status of the action ('success', 'error', etc.)
        
    Returns:
        int: ID of the inserted log entry
    """
    try:
        conn = sqlite3.connect(AUDIT_DB_PATH)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        file_hash = None
        
        # Calculate file hash if a file is involved
        if file_path and os.path.exists(file_path):
            file_hash = calculate_file_hash(file_path)
        
        # Convert details to JSON string if it's a dict
        if isinstance(details, dict):
            details = json.dumps(details)
        
        cursor.execute(
            "INSERT INTO action_log (timestamp, action_type, user_id, file_path, file_hash, details, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (timestamp, action_type, user_id, file_path, file_hash, details, status)
        )
        
        log_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Action logged: {action_type} - {status}")
        return log_id
    except Exception as e:
        logger.error(f"Failed to log action: {e}")
        return None

def backup_file(file_path, user_id=None):
    """
    Create a backup of a file and log it in the database
    
    Args:
        file_path (str): Path to the file to backup
        user_id (int, optional): ID of the user who uploaded the file
        
    Returns:
        str: Path to the backup file, or None if backup failed
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"Cannot backup non-existent file: {file_path}")
            return None
        
        # Determine file type
        _, ext = os.path.splitext(file_path)
        file_type = ext.lower().lstrip('.')
        
        # Determine backup directory
        if file_type in ['xlsx', 'xls', 'xlsm']:
            backup_subdir = 'excel'
        elif file_type == 'csv':
            backup_subdir = 'csv'
        elif file_type == 'json':
            backup_subdir = 'json'
        else:
            backup_subdir = 'other'
        
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(BACKUP_DIR, backup_subdir)
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        original_filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{timestamp}_{original_filename}"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copy the file
        shutil.copy2(file_path, backup_path)
        
        # Calculate file hash and size
        file_hash = calculate_file_hash(file_path)
        file_size = os.path.getsize(file_path)
        
        # Log the backup in the database
        conn = sqlite3.connect(AUDIT_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO file_backup (original_file, backup_path, timestamp, file_hash, file_size, file_type, user_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (file_path, backup_path, datetime.now().isoformat(), file_hash, file_size, file_type, user_id)
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"File backed up: {file_path} -> {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to backup file {file_path}: {e}")
        return None

def calculate_file_hash(file_path):
    """
    Calculate the SHA-256 hash of a file
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: Hex digest of the file hash
    """
    try:
        hash_obj = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate hash for {file_path}: {e}")
        return None

def compare_excel_files(file1_path, file2_path, sheet_name=None, diff_output_path=None):
    """
    Compare two Excel files and identify differences
    
    Args:
        file1_path (str): Path to the first Excel file
        file2_path (str): Path to the second Excel file
        sheet_name (str, optional): Name of the sheet to compare. If None, all common sheets are compared.
        diff_output_path (str, optional): Path to save the differences JSON. If None, uses default path.
        
    Returns:
        dict: Dictionary with comparison results
    """
    try:
        if not os.path.exists(file1_path) or not os.path.exists(file2_path):
            return {"error": "One or both files do not exist"}
        
        # Load Excel files
        xls1 = pd.ExcelFile(file1_path)
        xls2 = pd.ExcelFile(file2_path)
        
        # Determine sheets to compare
        if sheet_name:
            if sheet_name in xls1.sheet_names and sheet_name in xls2.sheet_names:
                sheets_to_compare = [sheet_name]
            else:
                return {"error": f"Sheet '{sheet_name}' not found in one or both files"}
        else:
            # Compare all common sheets
            sheets_to_compare = list(set(xls1.sheet_names) & set(xls2.sheet_names))
            if not sheets_to_compare:
                return {"error": "No common sheets found between the files"}
        
        comparison_results = {}
        total_diffs = 0
        
        for sheet in sheets_to_compare:
            df1 = pd.read_excel(file1_path, sheet_name=sheet)
            df2 = pd.read_excel(file2_path, sheet_name=sheet)
            
            # Check for shape differences
            if df1.shape != df2.shape:
                comparison_results[sheet] = {
                    "shape_mismatch": True,
                    "file1_shape": df1.shape,
                    "file2_shape": df2.shape,
                    "details": "Files have different dimensions"
                }
                total_diffs += 1
                continue
            
            # Compare data
            if df1.equals(df2):
                comparison_results[sheet] = {
                    "identical": True,
                    "diff_count": 0
                }
            else:
                # Find differences
                diff_locations = []
                
                # Get common columns
                common_cols = list(set(df1.columns) & set(df2.columns))
                
                for col in common_cols:
                    # Skip comparison for non-numeric columns if they don't match in type
                    if df1[col].dtype != df2[col].dtype and 'object' in [df1[col].dtype, df2[col].dtype]:
                        diff_locations.append({
                            "type": "column_type_mismatch",
                            "column": str(col),
                            "file1_type": str(df1[col].dtype),
                            "file2_type": str(df2[col].dtype)
                        })
                        continue
                        
                    # Compare values
                    for idx in range(len(df1)):
                        if idx >= len(df2):
                            break
                            
                        val1 = df1.iloc[idx][col]
                        val2 = df2.iloc[idx][col]
                        
                        # Handle NaN comparison
                        if pd.isna(val1) and pd.isna(val2):
                            continue
                            
                        # For numeric values, check if they're close enough
                        if pd.api.types.is_numeric_dtype(df1[col].dtype) and pd.api.types.is_numeric_dtype(df2[col].dtype):
                            if not pd.isna(val1) and not pd.isna(val2):
                                if abs(float(val1) - float(val2)) < 0.0001:
                                    continue
                                    
                        # If values don't match
                        if val1 != val2:
                            diff_locations.append({
                                "row": idx,
                                "column": str(col),
                                "file1_value": str(val1),
                                "file2_value": str(val2)
                            })
                
                comparison_results[sheet] = {
                    "identical": False,
                    "diff_count": len(diff_locations),
                    "differences": diff_locations[:100]  # Limit to 100 differences
                }
                
                if len(diff_locations) > 100:
                    comparison_results[sheet]["note"] = f"Showing 100 of {len(diff_locations)} differences"
                
                total_diffs += len(diff_locations)
        
        # Prepare overall result
        result = {
            "timestamp": datetime.now().isoformat(),
            "file1": file1_path,
            "file2": file2_path,
            "total_diff_count": total_diffs,
            "sheets_compared": len(sheets_to_compare),
            "sheets": comparison_results
        }
        
        # Save differences to file
        if diff_output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            diff_output_path = os.path.join('data', f'reconcile_diff_{timestamp}.json')
        
        os.makedirs(os.path.dirname(diff_output_path), exist_ok=True)
        with open(diff_output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Log the reconciliation in the database
        conn = sqlite3.connect(AUDIT_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO reconciliation_log (timestamp, file1_path, file2_path, diff_path, diff_count, status, details) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), file1_path, file2_path, diff_output_path, total_diffs, 
             "differences_found" if total_diffs > 0 else "identical", 
             json.dumps({"sheets_compared": sheets_to_compare}))
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"File comparison completed: {file1_path} vs {file2_path}, {total_diffs} differences found")
        return result
    except Exception as e:
        logger.error(f"Failed to compare files {file1_path} and {file2_path}: {e}")
        return {"error": str(e)}

def update_self_score(asset_assignment_accuracy=None, gps_coverage_percent=None, billing_match_rate=None, 
                     improvement_suggestions=None):
    """
    Update the system's self-evaluation score
    
    Args:
        asset_assignment_accuracy (float, optional): Accuracy score for asset-employee assignments (0-100)
        gps_coverage_percent (float, optional): Percentage of time GPS data is available (0-100)
        billing_match_rate (float, optional): Match rate between billing records and actual assets (0-100)
        improvement_suggestions (list or dict, optional): Suggestions for system improvement
        
    Returns:
        dict: Updated self-score data
    """
    try:
        conn = sqlite3.connect(AUDIT_DB_PATH)
        cursor = conn.cursor()
        
        # Get the latest scores to fill in missing values
        cursor.execute("SELECT * FROM self_score ORDER BY id DESC LIMIT 1")
        latest = cursor.fetchone()
        
        if latest:
            # Use latest values for any missing parameters
            if asset_assignment_accuracy is None:
                asset_assignment_accuracy = latest[2]
            if gps_coverage_percent is None:
                gps_coverage_percent = latest[3]
            if billing_match_rate is None:
                billing_match_rate = latest[4]
            
            if improvement_suggestions is None:
                improvement_suggestions = latest[6]
        
        # Calculate overall health score (weighted average)
        weights = {
            'asset_assignment': 0.4,
            'gps_coverage': 0.3,
            'billing_match': 0.3
        }
        
        scores = [
            (asset_assignment_accuracy or 0) * weights['asset_assignment'],
            (gps_coverage_percent or 0) * weights['gps_coverage'],
            (billing_match_rate or 0) * weights['billing_match']
        ]
        
        # Calculate weighted score, but only for provided values
        provided_weights = sum(weights.values() if s > 0 else 0 for s, weights in zip(
            [asset_assignment_accuracy, gps_coverage_percent, billing_match_rate],
            weights.values()
        ))
        
        if provided_weights > 0:
            overall_health_score = sum(s for s in scores if s > 0) / provided_weights
        else:
            overall_health_score = 0
        
        # Convert improvement suggestions to JSON if needed
        if isinstance(improvement_suggestions, list):
            improvement_suggestions = json.dumps(improvement_suggestions)
        
        # Insert the new score
        cursor.execute(
            "INSERT INTO self_score (timestamp, asset_assignment_accuracy, gps_coverage_percent, billing_match_rate, "
            "overall_health_score, improvement_suggestions) VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), asset_assignment_accuracy, gps_coverage_percent, billing_match_rate,
             overall_health_score, improvement_suggestions)
        )
        
        score_id = cursor.lastrowid
        conn.commit()
        
        # Get the inserted record
        cursor.execute("SELECT * FROM self_score WHERE id = ?", (score_id,))
        record = cursor.fetchone()
        conn.close()
        
        if record:
            result = {
                "id": record[0],
                "timestamp": record[1],
                "asset_assignment_accuracy": record[2],
                "gps_coverage_percent": record[3],
                "billing_match_rate": record[4],
                "overall_health_score": record[5],
                "improvement_suggestions": record[6]
            }
            
            logger.info(f"Self-score updated: overall health score = {overall_health_score:.2f}")
            return result
        else:
            return {"error": "Failed to retrieve updated self-score"}
    except Exception as e:
        logger.error(f"Failed to update self-score: {e}")
        return {"error": str(e)}

def get_audit_history(action_type=None, start_date=None, end_date=None, limit=100):
    """
    Get the audit history from the database
    
    Args:
        action_type (str, optional): Filter by action type
        start_date (str, optional): Filter by start date (ISO format)
        end_date (str, optional): Filter by end date (ISO format)
        limit (int, optional): Maximum number of records to return
        
    Returns:
        list: List of audit records
    """
    try:
        conn = sqlite3.connect(AUDIT_DB_PATH)
        conn.row_factory = sqlite3.Row  # Return results as dictionaries
        cursor = conn.cursor()
        
        query = "SELECT * FROM action_log"
        params = []
        
        # Build WHERE clause
        where_clauses = []
        if action_type:
            where_clauses.append("action_type = ?")
            params.append(action_type)
        
        if start_date:
            where_clauses.append("timestamp >= ?")
            params.append(start_date)
        
        if end_date:
            where_clauses.append("timestamp <= ?")
            params.append(end_date)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return records
    except Exception as e:
        logger.error(f"Failed to get audit history: {e}")
        return []

def get_backup_history(file_path=None, start_date=None, end_date=None, limit=100):
    """
    Get the backup history from the database
    
    Args:
        file_path (str, optional): Filter by original file path
        start_date (str, optional): Filter by start date (ISO format)
        end_date (str, optional): Filter by end date (ISO format)
        limit (int, optional): Maximum number of records to return
        
    Returns:
        list: List of backup records
    """
    try:
        conn = sqlite3.connect(AUDIT_DB_PATH)
        conn.row_factory = sqlite3.Row  # Return results as dictionaries
        cursor = conn.cursor()
        
        query = "SELECT * FROM file_backup"
        params = []
        
        # Build WHERE clause
        where_clauses = []
        if file_path:
            where_clauses.append("original_file LIKE ?")
            params.append(f"%{file_path}%")
        
        if start_date:
            where_clauses.append("timestamp >= ?")
            params.append(start_date)
        
        if end_date:
            where_clauses.append("timestamp <= ?")
            params.append(end_date)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return records
    except Exception as e:
        logger.error(f"Failed to get backup history: {e}")
        return []

def get_reconciliation_history(limit=50):
    """
    Get the reconciliation history from the database
    
    Args:
        limit (int, optional): Maximum number of records to return
        
    Returns:
        list: List of reconciliation records
    """
    try:
        conn = sqlite3.connect(AUDIT_DB_PATH)
        conn.row_factory = sqlite3.Row  # Return results as dictionaries
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM reconciliation_log ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return records
    except Exception as e:
        logger.error(f"Failed to get reconciliation history: {e}")
        return []

def get_self_score_history(limit=30):
    """
    Get the self-score history from the database
    
    Args:
        limit (int, optional): Maximum number of records to return
        
    Returns:
        list: List of self-score records
    """
    try:
        conn = sqlite3.connect(AUDIT_DB_PATH)
        conn.row_factory = sqlite3.Row  # Return results as dictionaries
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM self_score ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return records
    except Exception as e:
        logger.error(f"Failed to get self-score history: {e}")
        return []