"""
SYSTEMSMITH Kaizen Module

This module focuses on continuous improvement through self-evaluation:
1. Assessing data completeness
2. Evaluating file match rates
3. Analyzing asset assignment accuracy
4. Generating improvement suggestions
5. Tracking system health metrics
"""

import os
import json
import logging
import re
from datetime import datetime
from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

# Constants
SELF_SCORE_PATH = "data/self_score.json"
KAIZEN_DB_PATH = "data/kaizen.db"
AUDIT_DB_PATH = "data/audit.db"

def initialize_kaizen_db():
    """Initialize the Kaizen database if it doesn't exist"""
    os.makedirs(os.path.dirname(KAIZEN_DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(KAIZEN_DB_PATH)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            data_completeness REAL,
            file_match_rate REAL,
            asset_assignment_accuracy REAL,
            overall_health_score REAL,
            metric_details TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS improvement_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            category TEXT NOT NULL,
            priority INTEGER NOT NULL,
            description TEXT NOT NULL,
            implemented BOOLEAN DEFAULT 0,
            implemented_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asset_employee_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_identifier TEXT NOT NULL,
            employee_name TEXT NOT NULL,
            employee_id TEXT,
            confidence_score REAL NOT NULL,
            detection_method TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            match_count INTEGER DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()
    
    logger.info("Kaizen database initialized")

def calculate_data_completeness(assets):
    """
    Calculate data completeness score based on asset data
    
    Args:
        assets (list): List of asset dictionaries
    
    Returns:
        dict: Data completeness metrics
    """
    if not assets:
        return {"score": 0, "total_fields": 0, "empty_fields": 0, "details": {}}
    
    # Define critical fields that should be present
    critical_fields = [
        "asset_identifier", "asset_category", "active", 
        "latitude", "longitude", "engine_hours", "odometer"
    ]
    
    total_fields = len(assets) * len(critical_fields)
    empty_fields = 0
    field_stats = defaultdict(int)
    
    for asset in assets:
        for field in critical_fields:
            if field not in asset or asset[field] is None or asset[field] == "":
                empty_fields += 1
                field_stats[field] += 1
    
    # Calculate completeness score (0-100)
    completeness_score = round(100 * (1 - (empty_fields / total_fields)), 2) if total_fields > 0 else 0
    
    # Calculate per-field completeness
    field_completeness = {}
    for field in critical_fields:
        missing = field_stats[field]
        field_completeness[field] = round(100 * (1 - (missing / len(assets))), 2)
    
    return {
        "score": completeness_score,
        "total_fields": total_fields,
        "empty_fields": empty_fields,
        "total_assets": len(assets),
        "details": field_completeness
    }

def analyze_file_match_rates(audit_db_path=AUDIT_DB_PATH):
    """
    Analyze match rates between uploaded and generated files
    
    Returns:
        dict: File match rate metrics
    """
    try:
        conn = sqlite3.connect(audit_db_path)
        cursor = conn.cursor()
        
        # Get reconciliation events from the last 30 days
        cursor.execute(
            "SELECT * FROM audit_trail WHERE event_type = 'FILE_RECONCILIATION' "
            "AND timestamp >= datetime('now', '-30 day') ORDER BY timestamp DESC"
        )
        
        reconciliations = cursor.fetchall()
        conn.close()
        
        if not reconciliations:
            return {
                "score": 0,
                "total_reconciliations": 0,
                "details": {}
            }
        
        # Analyze reconciliation diffs
        match_rates = []
        details = []
        
        for rec in reconciliations:
            metadata = json.loads(rec[6]) if rec[6] else {}
            diff_file = metadata.get('diff_file')
            
            if diff_file and os.path.exists(diff_file):
                with open(diff_file, 'r') as f:
                    diff_content = f.read()
                
                # Count the number of differences (lines starting with + or -)
                diff_lines = diff_content.split('\n')
                diff_count = sum(1 for line in diff_lines if line.startswith('+') or line.startswith('-'))
                
                # Estimate total lines from the diff header
                total_lines = 0
                for line in diff_lines[:20]:  # Check first few lines for header info
                    if line.startswith('@@'):
                        parts = line.split()
                        if len(parts) > 2:
                            match = re.search(r'-\d+,(\d+)', parts[1])
                            if match:
                                total_lines = int(match.group(1))
                                break
                
                if total_lines > 0:
                    match_rate = max(0, min(100, 100 * (1 - (diff_count / (2 * total_lines)))))
                else:
                    match_rate = 0 if diff_count > 0 else 100
                
                match_rates.append(match_rate)
                details.append({
                    "timestamp": rec[1],
                    "diff_file": diff_file,
                    "diff_count": diff_count,
                    "match_rate": match_rate
                })
        
        # Calculate overall match rate
        overall_match_rate = sum(match_rates) / len(match_rates) if match_rates else 0
        
        return {
            "score": round(overall_match_rate, 2),
            "total_reconciliations": len(reconciliations),
            "details": details
        }
    except Exception as e:
        logger.error(f"Error analyzing file match rates: {e}")
        return {
            "score": 0,
            "total_reconciliations": 0,
            "error": str(e),
            "details": {}
        }

def evaluate_asset_assignment_accuracy():
    """
    Evaluate the accuracy of asset-employee assignments
    
    Returns:
        dict: Asset assignment accuracy metrics
    """
    try:
        conn = sqlite3.connect(KAIZEN_DB_PATH)
        cursor = conn.cursor()
        
        # Get asset-employee mappings
        cursor.execute(
            "SELECT * FROM asset_employee_mappings ORDER BY confidence_score DESC"
        )
        
        mappings = cursor.fetchall()
        conn.close()
        
        if not mappings:
            return {
                "score": 0,
                "total_mappings": 0,
                "details": {}
            }
        
        # Calculate accuracy stats
        total_mappings = len(mappings)
        confidence_scores = [mapping[4] for mapping in mappings]  # confidence_score column
        avg_confidence = sum(confidence_scores) / total_mappings
        
        # Count mappings by confidence level
        high_confidence = sum(1 for score in confidence_scores if score >= 0.8)
        medium_confidence = sum(1 for score in confidence_scores if 0.5 <= score < 0.8)
        low_confidence = sum(1 for score in confidence_scores if score < 0.5)
        
        # Calculate overall score (0-100)
        overall_score = round(avg_confidence * 100, 2)
        
        return {
            "score": overall_score,
            "total_mappings": total_mappings,
            "average_confidence": round(avg_confidence, 2),
            "details": {
                "high_confidence": high_confidence,
                "medium_confidence": medium_confidence,
                "low_confidence": low_confidence,
                "high_confidence_percent": round(100 * high_confidence / total_mappings, 2)
            }
        }
    except Exception as e:
        logger.error(f"Error evaluating asset assignment accuracy: {e}")
        return {
            "score": 0,
            "total_mappings": 0,
            "error": str(e),
            "details": {}
        }

def calculate_system_health(assets=None):
    """
    Calculate overall system health score and metrics
    
    Args:
        assets (list, optional): List of asset dictionaries
        
    Returns:
        dict: System health metrics
    """
    try:
        # If assets not provided, try to load them
        if not assets:
            from utils import load_data
            assets = load_data()
        
        # Calculate individual metrics
        data_completeness = calculate_data_completeness(assets)
        file_match_rate = analyze_file_match_rates()
        asset_assignment = evaluate_asset_assignment_accuracy()
        
        # Calculate weighted overall score
        weights = {
            "data_completeness": 0.4,
            "file_match_rate": 0.3,
            "asset_assignment": 0.3
        }
        
        overall_score = (
            data_completeness["score"] * weights["data_completeness"] +
            file_match_rate["score"] * weights["file_match_rate"] +
            asset_assignment["score"] * weights["asset_assignment"]
        )
        
        # Prepare full metrics report
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "overall_health_score": round(overall_score, 2),
            "data_completeness": data_completeness,
            "file_match_rate": file_match_rate,
            "asset_assignment_accuracy": asset_assignment,
            "weights": weights
        }
        
        # Store in database
        conn = sqlite3.connect(KAIZEN_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO system_metrics (timestamp, data_completeness, file_match_rate, "
            "asset_assignment_accuracy, overall_health_score, metric_details) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                metrics["timestamp"],
                data_completeness["score"],
                file_match_rate["score"],
                asset_assignment["score"],
                metrics["overall_health_score"],
                json.dumps(metrics)
            )
        )
        
        conn.commit()
        conn.close()
        
        # Save to self_score.json
        with open(SELF_SCORE_PATH, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Generate improvement suggestions
        generate_improvement_suggestions(metrics)
        
        logger.info(f"System health score: {overall_score:.2f}")
        return metrics
    except Exception as e:
        logger.error(f"Error calculating system health: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_health_score": 0,
            "error": str(e)
        }

def generate_improvement_suggestions(metrics):
    """
    Generate improvement suggestions based on system metrics
    
    Args:
        metrics (dict): System health metrics
        
    Returns:
        list: Improvement suggestions
    """
    try:
        suggestions = []
        
        # Check data completeness
        data_completeness = metrics["data_completeness"]
        if data_completeness["score"] < 90:
            # Find fields with lowest completeness
            details = data_completeness["details"]
            problem_fields = [
                (field, score) for field, score in details.items() 
                if score < 90
            ]
            problem_fields.sort(key=lambda x: x[1])
            
            # Generate suggestions for each problem field
            for field, score in problem_fields:
                priority = 1 if score < 70 else 2 if score < 85 else 3
                suggestion = {
                    "category": "DATA_COMPLETENESS",
                    "priority": priority,
                    "description": f"Improve data collection for '{field}' field (currently {score:.1f}% complete)"
                }
                suggestions.append(suggestion)
        
        # Check file match rate
        file_match_rate = metrics["file_match_rate"]
        if file_match_rate["score"] < 85:
            priority = 1 if file_match_rate["score"] < 60 else 2 if file_match_rate["score"] < 75 else 3
            suggestion = {
                "category": "FILE_MATCHING",
                "priority": priority,
                "description": f"Improve file matching algorithms (current match rate: {file_match_rate['score']:.1f}%)"
            }
            suggestions.append(suggestion)
        
        # Check asset assignment accuracy
        asset_assignment = metrics["asset_assignment_accuracy"]
        if asset_assignment["score"] < 85:
            priority = 1 if asset_assignment["score"] < 60 else 2 if asset_assignment["score"] < 75 else 3
            suggestion = {
                "category": "ASSET_ASSIGNMENT",
                "priority": priority,
                "description": f"Enhance asset-employee matching logic (current accuracy: {asset_assignment['score']:.1f}%)"
            }
            suggestions.append(suggestion)
            
            # If low confidence mappings are high
            details = asset_assignment["details"]
            if details.get("low_confidence", 0) > 0.2 * asset_assignment["total_mappings"]:
                suggestion = {
                    "category": "ASSET_ASSIGNMENT",
                    "priority": 2,
                    "description": f"Review and correct {details.get('low_confidence', 0)} low-confidence asset-employee mappings"
                }
                suggestions.append(suggestion)
        
        # Store suggestions in database
        if suggestions:
            conn = sqlite3.connect(KAIZEN_DB_PATH)
            cursor = conn.cursor()
            
            for suggestion in suggestions:
                cursor.execute(
                    "INSERT INTO improvement_suggestions (timestamp, category, priority, description) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        datetime.now().isoformat(),
                        suggestion["category"],
                        suggestion["priority"],
                        suggestion["description"]
                    )
                )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Generated {len(suggestions)} improvement suggestions")
        
        return suggestions
    except Exception as e:
        logger.error(f"Error generating improvement suggestions: {e}")
        return []

def get_latest_health_score():
    """
    Get the latest system health score
    
    Returns:
        dict: Latest system health metrics
    """
    try:
        if os.path.exists(SELF_SCORE_PATH):
            with open(SELF_SCORE_PATH, 'r') as f:
                return json.load(f)
        else:
            return calculate_system_health()
    except Exception as e:
        logger.error(f"Error getting latest health score: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_health_score": 0,
            "error": str(e)
        }

def get_improvement_suggestions(limit=10, implemented=False):
    """
    Get improvement suggestions
    
    Args:
        limit (int): Maximum number of suggestions to return
        implemented (bool): Whether to return implemented or non-implemented suggestions
        
    Returns:
        list: Improvement suggestions
    """
    try:
        conn = sqlite3.connect(KAIZEN_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM improvement_suggestions WHERE implemented = ? "
            "ORDER BY priority, timestamp DESC LIMIT ?",
            (1 if implemented else 0, limit)
        )
        
        rows = cursor.fetchall()
        suggestions = [dict(row) for row in rows]
        
        conn.close()
        return suggestions
    except Exception as e:
        logger.error(f"Error getting improvement suggestions: {e}")
        return []

def update_employee_asset_mapping(asset_identifier, employee_name, confidence_score, detection_method):
    """
    Update or create an asset-employee mapping
    
    Args:
        asset_identifier (str): Asset identifier
        employee_name (str): Employee name
        confidence_score (float): Confidence score (0-1)
        detection_method (str): Method used for detection
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(KAIZEN_DB_PATH)
        cursor = conn.cursor()
        
        # Check if mapping exists
        cursor.execute(
            "SELECT * FROM asset_employee_mappings WHERE asset_identifier = ? AND employee_name = ?",
            (asset_identifier, employee_name)
        )
        
        existing = cursor.fetchone()
        now = datetime.now().isoformat()
        
        if existing:
            # Update existing mapping
            cursor.execute(
                "UPDATE asset_employee_mappings SET confidence_score = ?, "
                "detection_method = ?, last_seen = ?, match_count = match_count + 1 "
                "WHERE asset_identifier = ? AND employee_name = ?",
                (
                    max(existing[4], confidence_score),  # Keep highest confidence
                    detection_method,
                    now,
                    asset_identifier,
                    employee_name
                )
            )
        else:
            # Create new mapping
            cursor.execute(
                "INSERT INTO asset_employee_mappings "
                "(asset_identifier, employee_name, confidence_score, detection_method, created_at, last_seen) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    asset_identifier,
                    employee_name,
                    confidence_score,
                    detection_method,
                    now,
                    now
                )
            )
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Updated asset-employee mapping: {asset_identifier} -> {employee_name}")
        return True
    except Exception as e:
        logger.error(f"Error updating asset-employee mapping: {e}")
        return False

def extract_employee_from_asset(asset_identifier):
    """
    Extract employee name from asset identifier using various patterns
    
    Args:
        asset_identifier (str): Asset identifier string
        
    Returns:
        tuple: (employee_name, confidence_score, detection_method) or (None, 0, None)
    """
    if not asset_identifier or not isinstance(asset_identifier, str):
        return None, 0, None
    
    try:
        # Pattern 1: "PT-277 (Said Garcia)" - name in parentheses
        pattern1 = r'.*\((.*?)\).*'
        match1 = re.match(pattern1, asset_identifier)
        if match1:
            name = match1.group(1).strip()
            # Check if it looks like a name (not "OPEN", "SOLD", etc.)
            if len(name) > 3 and not name.isupper():
                return name, 0.9, "parentheses_pattern"
            elif name.isupper() and "OPEN" in name:
                return None, 0, None
        
        # Pattern 2: "#210003 - AMMAR I. ELHAMAD" - after dash
        pattern2 = r'#\d+\s*-\s*(.*)'
        match2 = re.match(pattern2, asset_identifier)
        if match2:
            name = match2.group(1).strip()
            return name, 0.95, "id_dash_pattern"
        
        # Pattern 3: "ET-41 (Hampton, Justin D)" - name in parentheses with comma
        pattern3 = r'.*\((.*?,.*?)\).*'
        match3 = re.match(pattern3, asset_identifier)
        if match3:
            name = match3.group(1).strip()
            return name, 0.95, "parentheses_comma_pattern"
        
        return None, 0, None
    except Exception as e:
        logger.error(f"Error extracting employee from asset: {e}")
        return None, 0, None

def process_asset_identifiers(assets):
    """
    Process all asset identifiers to extract and map employees
    
    Args:
        assets (list): List of asset dictionaries
        
    Returns:
        int: Number of mappings created or updated
    """
    count = 0
    for asset in assets:
        identifier = asset.get('asset_identifier')
        if identifier:
            employee, confidence, method = extract_employee_from_asset(identifier)
            if employee and confidence > 0.5:
                if update_employee_asset_mapping(identifier, employee, confidence, method):
                    count += 1
    
    logger.info(f"Processed {len(assets)} assets, updated {count} employee mappings")
    return count

def init():
    """Initialize the Kaizen module"""
    initialize_kaizen_db()
    logger.info("Kaizen module initialized")