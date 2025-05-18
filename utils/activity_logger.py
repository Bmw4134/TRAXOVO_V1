"""
Activity Logger Module

This module provides logging functions for user activities throughout the system,
helping track important operations for analysis and auditing.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from flask import g, session, current_app
from flask_login import current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)
ACTIVITY_LOG_FILE = LOGS_DIR / "activity_log.jsonl"

def _get_user_info():
    """
    Get current user information for logging
    
    Returns:
        dict: User information
    """
    user_info = {
        "user_id": "anonymous",
        "username": "anonymous"
    }
    
    try:
        if current_user and current_user.is_authenticated:
            user_info = {
                "user_id": getattr(current_user, 'id', 'unknown'),
                "username": getattr(current_user, 'username', 'unknown')
            }
    except:
        # If there's any error getting user info, use the default
        pass
    
    # Add org info if available
    try:
        user_info["organization_id"] = session.get("current_organization_id")
    except:
        pass
    
    return user_info

def _log_activity(activity_type, details=None, success=True, error=None):
    """
    Generic activity logging function
    
    Args:
        activity_type (str): Type of activity
        details (dict): Additional details to log
        success (bool): Whether the activity was successful
        error (str): Error message if activity failed
    """
    try:
        # Get current time in ISO format
        timestamp = datetime.now().isoformat()
        
        # Get user info
        user_info = _get_user_info()
        
        # Create log entry
        log_entry = {
            "timestamp": timestamp,
            "activity_type": activity_type,
            "user_id": user_info["user_id"],
            "username": user_info["username"],
            "success": success
        }
        
        # Add organization if available
        if "organization_id" in user_info:
            log_entry["organization_id"] = user_info["organization_id"]
        
        # Add additional details if provided
        if details:
            log_entry.update(details)
        
        # Add error if provided
        if error:
            log_entry["error"] = error
        
        # Write to JSONL file
        with open(ACTIVITY_LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Also log to regular logger for console/application logs
        if success:
            logger.info(f"ACTIVITY: {activity_type} by {user_info['username']}")
        else:
            logger.error(f"ACTIVITY ERROR: {activity_type} by {user_info['username']} - {error}")
            
        return True
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")
        return False

# Specific activity logging functions

def log_api_pull(api_name, endpoint=None, params=None, record_count=None, success=True, error=None):
    """
    Log API pull activity
    
    Args:
        api_name (str): Name of the API
        endpoint (str): API endpoint
        params (dict): Request parameters
        record_count (int): Number of records returned
        success (bool): Whether the API call was successful
        error (str): Error message if API call failed
    """
    details = {
        "api_name": api_name,
        "request_time": datetime.now().isoformat()
    }
    
    if endpoint:
        details["endpoint"] = endpoint
    
    if params:
        details["params"] = params
    
    if record_count is not None:
        details["record_count"] = record_count
    
    return _log_activity("api_pull", details, success, error)

def log_document_upload(filename, file_type=None, file_size=None, success=True, error=None):
    """
    Log document upload activity
    
    Args:
        filename (str): Name of the uploaded file
        file_type (str): Type/extension of the file
        file_size (int): Size of the file in bytes
        success (bool): Whether the upload was successful
        error (str): Error message if upload failed
    """
    details = {
        "filename": filename,
        "upload_time": datetime.now().isoformat()
    }
    
    if file_type:
        details["file_type"] = file_type
    
    if file_size:
        details["file_size"] = file_size
    
    return _log_activity("document_upload", details, success, error)

def log_report_export(report_type, export_format=None, report_id=None, filters=None, success=True, error=None):
    """
    Log report export activity
    
    Args:
        report_type (str): Type of report
        export_format (str): Format of the export (PDF, CSV, etc.)
        report_id (str): ID of the exported report if applicable
        filters (dict): Filters used for the report
        success (bool): Whether the export was successful
        error (str): Error message if export failed
    """
    details = {
        "report_type": report_type,
        "export_time": datetime.now().isoformat()
    }
    
    if export_format:
        details["export_format"] = export_format
    
    if report_id:
        details["report_id"] = report_id
    
    if filters:
        details["filters"] = filters
    
    return _log_activity("report_export", details, success, error)

def log_pm_process(original_file=None, updated_file=None, region=None, changes_count=None, success=True, error=None):
    """
    Log PM allocation processing activity
    
    Args:
        original_file (str): Name of the original file
        updated_file (str): Name of the updated file
        region (str): Region being processed
        changes_count (int): Number of changes found
        success (bool): Whether the processing was successful
        error (str): Error message if processing failed
    """
    details = {
        "process_time": datetime.now().isoformat()
    }
    
    if original_file:
        details["original_file"] = original_file
    
    if updated_file:
        details["updated_file"] = updated_file
    
    if region:
        details["region"] = region
    
    if changes_count is not None:
        details["changes_count"] = changes_count
    
    return _log_activity("pm_process", details, success, error)

def log_invoice_generation(invoice_number, job_number=None, amount=None, success=True, error=None):
    """
    Log invoice generation activity
    
    Args:
        invoice_number (str): Number of the invoice
        job_number (str): Related job number
        amount (float): Invoice amount
        success (bool): Whether the generation was successful
        error (str): Error message if generation failed
    """
    details = {
        "invoice_number": invoice_number,
        "generation_time": datetime.now().isoformat()
    }
    
    if job_number:
        details["job_number"] = job_number
    
    if amount:
        details["amount"] = amount
    
    return _log_activity("invoice_generation", details, success, error)

def log_payment_record(invoice_id, payment_amount, payment_method=None, success=True, error=None):
    """
    Log payment recording activity
    
    Args:
        invoice_id (str): ID of the invoice
        payment_amount (float): Amount of the payment
        payment_method (str): Payment method used
        success (bool): Whether the recording was successful
        error (str): Error message if recording failed
    """
    details = {
        "invoice_id": invoice_id,
        "payment_amount": payment_amount,
        "record_time": datetime.now().isoformat()
    }
    
    if payment_method:
        details["payment_method"] = payment_method
    
    return _log_activity("payment_record", details, success, error)

def log_login(success=True, error=None):
    """
    Log user login activity
    
    Args:
        success (bool): Whether the login was successful
        error (str): Error message if login failed
    """
    details = {
        "login_time": datetime.now().isoformat(),
        "ip_address": getattr(g, 'ip_address', 'unknown')
    }
    
    # Get user agent if available
    user_agent = getattr(g, 'user_agent', None)
    if user_agent:
        details["user_agent"] = user_agent
    
    return _log_activity("login", details, success, error)

def log_logout():
    """
    Log user logout activity
    """
    details = {
        "logout_time": datetime.now().isoformat()
    }
    
    return _log_activity("logout", details)

def log_navigation(page, source_page=None):
    """
    Log user navigation activity
    
    Args:
        page (str): Page being navigated to
        source_page (str): Page being navigated from
    """
    details = {
        "page": page,
        "navigation_time": datetime.now().isoformat()
    }
    
    if source_page:
        details["source_page"] = source_page
    
    return _log_activity("navigation", details)

def log_feature_usage(feature_name, usage_details=None):
    """
    Log feature usage activity
    
    Args:
        feature_name (str): Name of the feature being used
        usage_details (dict): Additional details about the usage
    """
    details = {
        "feature_name": feature_name,
        "usage_time": datetime.now().isoformat()
    }
    
    if usage_details:
        details["usage_details"] = usage_details
    
    return _log_activity("feature_usage", details)

def log_search(query, results_count=None, filters=None):
    """
    Log search activity
    
    Args:
        query (str): Search query
        results_count (int): Number of results returned
        filters (dict): Filters applied to the search
    """
    details = {
        "query": query,
        "search_time": datetime.now().isoformat()
    }
    
    if results_count is not None:
        details["results_count"] = results_count
    
    if filters:
        details["filters"] = filters
    
    return _log_activity("search", details)

def log_system_event(event_type, description=None, severity="info"):
    """
    Log system event
    
    Args:
        event_type (str): Type of system event
        description (str): Description of the event
        severity (str): Severity of the event (info, warning, error, critical)
    """
    details = {
        "event_type": event_type,
        "event_time": datetime.now().isoformat(),
        "severity": severity
    }
    
    if description:
        details["description"] = description
    
    return _log_activity("system_event", details)

def get_recent_activities(limit=50, activity_type=None, user_id=None):
    """
    Get recent activity logs
    
    Args:
        limit (int): Maximum number of logs to return
        activity_type (str): Filter by activity type
        user_id (str): Filter by user ID
        
    Returns:
        list: Recent activity logs
    """
    try:
        if not os.path.exists(ACTIVITY_LOG_FILE):
            return []
        
        # Read logs from file
        with open(ACTIVITY_LOG_FILE, "r") as f:
            logs = [json.loads(line) for line in f]
        
        # Filter logs if needed
        if activity_type:
            logs = [log for log in logs if log.get("activity_type") == activity_type]
        
        if user_id:
            logs = [log for log in logs if log.get("user_id") == user_id]
        
        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Limit results
        return logs[:limit]
    except Exception as e:
        logger.error(f"Failed to get recent activities: {e}")
        return []

def get_user_activity_stats(user_id=None, days=30):
    """
    Get statistics on user activities
    
    Args:
        user_id (str): Filter by user ID (None for all users)
        days (int): Number of days to include
        
    Returns:
        dict: Activity statistics
    """
    try:
        if not os.path.exists(ACTIVITY_LOG_FILE):
            return {}
        
        # Read logs from file
        with open(ACTIVITY_LOG_FILE, "r") as f:
            logs = [json.loads(line) for line in f]
        
        # Filter logs by user if needed
        if user_id:
            logs = [log for log in logs if log.get("user_id") == user_id]
        
        # Filter by date range
        cutoff_date = datetime.now() - datetime.timedelta(days=days)
        logs = [log for log in logs if datetime.fromisoformat(log.get("timestamp", "")) >= cutoff_date]
        
        # Count activities by type
        activity_counts = {}
        for log in logs:
            activity_type = log.get("activity_type")
            activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1
        
        # Get top users if not filtering by user
        top_users = {}
        if not user_id:
            for log in logs:
                user = log.get("user_id")
                if user:
                    top_users[user] = top_users.get(user, 0) + 1
        
        # Get success rate
        success_count = sum(1 for log in logs if log.get("success", True))
        
        return {
            "total_activities": len(logs),
            "activity_counts": activity_counts,
            "top_users": top_users,
            "success_rate": success_count / len(logs) if logs else 0
        }
    except Exception as e:
        logger.error(f"Failed to get user activity stats: {e}")
        return {}