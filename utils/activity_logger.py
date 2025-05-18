"""
Activity Logger Utility

This module provides functions for logging user activities and system events
to maintain an audit trail of actions within the application.
"""

import logging
from datetime import datetime
from flask import session, request, g
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('utils.activity_logger')

# Constants
LOG_FOLDER = os.path.join(os.getcwd(), 'logs')
ACTIVITY_LOG_FILE = os.path.join(LOG_FOLDER, 'activity.log')

# Create logs directory if it doesn't exist
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

def log_navigation(from_page, to_page, user_id=None, metadata=None):
    """
    Log a page navigation event
    
    Args:
        from_page (str): Page user navigated from
        to_page (str): Page user navigated to
        user_id (str, optional): ID of the user performing the action
        metadata (dict, optional): Additional metadata
        
    Returns:
        bool: Success status
    """
    description = f"Navigation from {from_page} to {to_page}"
    return log_activity('navigation', description, user_id, metadata)

def log_document_upload(document_type, filename, user_id=None, metadata=None):
    """
    Log a document upload event
    
    Args:
        document_type (str): Type of document being uploaded
        filename (str): Name of the uploaded file
        user_id (str, optional): ID of the user performing the action
        metadata (dict, optional): Additional metadata
        
    Returns:
        bool: Success status
    """
    description = f"Uploaded {document_type} document: {filename}"
    return log_activity('document_upload', description, user_id, metadata)

def log_report_export(report_type=None, export_format=None, user_id=None, metadata=None):
    """
    Log a report export event
    
    Args:
        report_type (str, optional): Type of report being exported
        export_format (str, optional): Format of the export (PDF, CSV, etc.)
        user_id (str, optional): ID of the user performing the action
        metadata (dict, optional): Additional metadata
        
    Returns:
        bool: Success status
    """
    report_info = f"{report_type} report" if report_type else "report" 
    format_info = f"in {export_format.upper()} format" if export_format else ""
    description = f"Exported {report_info} {format_info}".strip()
    return log_activity('report_export', description, user_id, metadata)

def log_pm_process(original_file, updated_file, user_id=None, metadata=None):
    """
    Log a PM allocation processing event
    
    Args:
        original_file (str): Name of the original PM allocation file
        updated_file (str): Name of the updated PM allocation file
        user_id (str, optional): ID of the user performing the action
        metadata (dict, optional): Additional metadata
        
    Returns:
        bool: Success status
    """
    description = f"Processed PM allocation files: {original_file} and {updated_file}"
    return log_activity('pm_allocation_process', description, user_id, metadata)

def log_feature_usage(feature_name, action=None, user_id=None, metadata=None):
    """
    Log usage of a specific feature
    
    Args:
        feature_name (str): Name of the feature being used
        action (str, optional): Specific action being performed
        user_id (str, optional): ID of the user performing the action
        metadata (dict, optional): Additional metadata
        
    Returns:
        bool: Success status
    """
    action_info = f" - {action}" if action else ""
    description = f"Used feature: {feature_name}{action_info}"
    return log_activity('feature_usage', description, user_id, metadata)

def log_invoice_generation(invoice_id, amount, client=None, user_id=None, metadata=None):
    """
    Log generation of an invoice
    
    Args:
        invoice_id (str): ID of the generated invoice
        amount (float): Total amount of the invoice
        client (str, optional): Client name or ID
        user_id (str, optional): ID of the user performing the action
        metadata (dict, optional): Additional metadata
        
    Returns:
        bool: Success status
    """
    client_info = f" for {client}" if client else ""
    amount_formatted = f"${amount:,.2f}" if amount else ""
    description = f"Generated invoice #{invoice_id}{client_info} - {amount_formatted}"
    return log_activity('invoice_generation', description, user_id, metadata)

def log_payment_record(invoice_id, amount, payment_method=None, user_id=None, metadata=None):
    """
    Log recording of a payment
    
    Args:
        invoice_id (str): ID of the invoice being paid
        amount (float): Amount of the payment
        payment_method (str, optional): Method of payment
        user_id (str, optional): ID of the user performing the action
        metadata (dict, optional): Additional metadata
        
    Returns:
        bool: Success status
    """
    method_info = f" via {payment_method}" if payment_method else ""
    amount_formatted = f"${amount:,.2f}" if amount else ""
    description = f"Recorded payment of {amount_formatted}{method_info} for invoice #{invoice_id}"
    return log_activity('payment_record', description, user_id, metadata)

def log_search(query, results_count=None, module=None, user_id=None, metadata=None):
    """
    Log a search operation
    
    Args:
        query (str): Search query
        results_count (int, optional): Number of results found
        module (str, optional): Module where search was performed
        user_id (str, optional): ID of the user performing the action
        metadata (dict, optional): Additional metadata
        
    Returns:
        bool: Success status
    """
    count_info = f" - {results_count} results" if results_count is not None else ""
    module_info = f" in {module}" if module else ""
    description = f"Searched{module_info}: '{query}'{count_info}"
    return log_activity('search', description, user_id, metadata)

def get_recent_activities(limit=20):
    """
    Get recent activities from the activity log
    
    Args:
        limit (int): Maximum number of activities to return
        
    Returns:
        list: List of activity dictionaries
    """
    try:
        # Get database connection
        from app import db
        from models import ActivityLog
        
        # Query recent activities ordered by timestamp (newest first)
        activities = (ActivityLog.query
                     .order_by(ActivityLog.timestamp.desc())
                     .limit(limit)
                     .all())
        
        # Convert to dictionaries for template rendering
        return [activity.to_dict() for activity in activities]
    except Exception as e:
        print(f"Error getting recent activities: {e}")
        return []

def log_activity(activity_type, description=None, user_id=None, metadata=None):
    """
    Log a user activity or system event
    
    Args:
        activity_type (str): Type of activity (e.g., 'login', 'report_generation')
        description (str, optional): Description of the activity
        user_id (str, optional): ID of the user performing the activity
        metadata (dict, optional): Additional metadata about the activity
        
    Returns:
        bool: Success status
    """
    try:
        # Get current user from session if available
        if user_id is None:
            if hasattr(g, 'user') and g.user:
                user_id = g.user.id
            elif session.get('user_id'):
                user_id = session.get('user_id')
            else:
                user_id = 'admin'  # Default for system events or anonymous users
        
        # Create activity record
        activity = {
            'timestamp': datetime.now().isoformat(),
            'activity_type': activity_type,
            'description': description,
            'user_id': user_id,
            'ip_address': request.remote_addr if request else None,
            'user_agent': request.user_agent.string if request and request.user_agent else None,
            'endpoint': request.endpoint if request else None,
            'metadata': metadata or {}
        }
        
        # Log to application logger
        logger.info(f"ACTIVITY: {activity_type} by {user_id}")
        
        # Write to activity log file
        with open(ACTIVITY_LOG_FILE, 'a') as log_file:
            log_file.write(f"{json.dumps(activity)}\n")
            
        return True
    except Exception as e:
        logger.error(f"Error logging activity: {str(e)}")
        return False

def get_recent_activities(limit=100, activity_type=None, user_id=None):
    """
    Get recent activity logs
    
    Args:
        limit (int): Maximum number of activities to return
        activity_type (str, optional): Filter by activity type
        user_id (str, optional): Filter by user ID
        
    Returns:
        list: List of activity records
    """
    try:
        if not os.path.exists(ACTIVITY_LOG_FILE):
            return []
            
        activities = []
        with open(ACTIVITY_LOG_FILE, 'r') as log_file:
            # Start from the end and read the file backwards to get the most recent entries
            lines = log_file.readlines()
            for line in reversed(lines):
                try:
                    activity = json.loads(line.strip())
                    
                    # Apply filters
                    if activity_type and activity['activity_type'] != activity_type:
                        continue
                        
                    if user_id and activity['user_id'] != user_id:
                        continue
                        
                    activities.append(activity)
                    
                    if len(activities) >= limit:
                        break
                except json.JSONDecodeError:
                    continue
                    
        return activities
    except Exception as e:
        logger.error(f"Error getting recent activities: {str(e)}")
        return []