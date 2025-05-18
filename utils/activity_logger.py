"""
Activity Logger Utility

This module provides a simple interface for logging user activities
throughout the application. It tracks Gauge API pulls, document uploads,
report views/exports, and other key user interactions.
"""
from datetime import datetime
from flask import request, current_app
from flask_login import current_user

from models import ActivityLog, db

# Define event type constants
EVENT_API_PULL = 'api_pull'
EVENT_DOCUMENT_UPLOAD = 'document_upload'
EVENT_REPORT_VIEW = 'report_view'
EVENT_REPORT_EXPORT = 'report_export'
EVENT_ASSET_UPDATE = 'asset_update'
EVENT_USER_LOGIN = 'user_login'
EVENT_USER_LOGOUT = 'user_logout'
EVENT_PM_PROCESS = 'pm_process'

def log_activity(event_type, resource_type=None, resource_id=None, 
                action=None, description=None, details=None, success=True):
    """
    Log a user activity
    
    Args:
        event_type (str): Type of event (api_pull, document_upload, report_view, etc.)
        resource_type (str, optional): Type of resource being accessed
        resource_id (str, optional): ID of the specific resource
        action (str, optional): Action performed (view, create, update, delete)
        description (str, optional): Human-readable description
        details (dict, optional): Additional JSON details
        success (bool, optional): Whether the action succeeded
        
    Returns:
        ActivityLog: The created log entry
    """
    try:
        # Get the current user ID (if authenticated)
        user_id = current_user.id if current_user and current_user.is_authenticated else None
        
        # Get IP address from request
        ip_address = request.remote_addr if request else None
        
        # Create log entry
        log_entry = ActivityLog(
            user_id=user_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            description=description,
            details=details,
            ip_address=ip_address,
            success=success
        )
        
        # Add and commit to database
        db.session.add(log_entry)
        db.session.commit()
        
        return log_entry
    except Exception as e:
        # Log the error but don't interrupt application flow
        current_app.logger.error(f"Error logging activity: {str(e)}")
        try:
            db.session.rollback()
        except:
            pass
        return None


def log_api_pull(api_name, resource_count=None, details=None, success=True):
    """
    Log an API data pull (e.g., Gauge API)
    
    Args:
        api_name (str): Name of the API
        resource_count (int, optional): Number of resources retrieved
        details (dict, optional): Additional details about the API pull
        success (bool): Whether the API pull succeeded
    """
    description = f"Pulled data from {api_name}"
    if resource_count is not None:
        description += f" ({resource_count} items)"
    
    if details is None:
        details = {}
    
    details['timestamp'] = datetime.utcnow().isoformat()
    
    return log_activity(
        event_type=EVENT_API_PULL,
        resource_type='api',
        resource_id=api_name,
        action='pull',
        description=description,
        details=details,
        success=success
    )


def log_document_upload(filename, file_type=None, file_size=None, success=True):
    """
    Log a document upload
    
    Args:
        filename (str): Name of the uploaded file
        file_type (str, optional): Type of file
        file_size (int, optional): Size of file in bytes
        success (bool): Whether the upload succeeded
    """
    description = f"Uploaded document: {filename}"
    
    details = {
        'filename': filename,
        'file_type': file_type,
        'file_size': file_size,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return log_activity(
        event_type=EVENT_DOCUMENT_UPLOAD,
        resource_type='document',
        resource_id=filename,
        action='upload',
        description=description,
        details=details,
        success=success
    )


def log_report_view(report_type, report_id=None, filters=None):
    """
    Log a report view
    
    Args:
        report_type (str): Type of report
        report_id (str, optional): ID of the report
        filters (dict, optional): Filters applied to the report
    """
    description = f"Viewed {report_type} report"
    if report_id:
        description += f" ({report_id})"
    
    details = {
        'report_type': report_type,
        'filters': filters or {},
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return log_activity(
        event_type=EVENT_REPORT_VIEW,
        resource_type='report',
        resource_id=report_id or report_type,
        action='view',
        description=description,
        details=details
    )


def log_report_export(report_type, export_format, report_id=None, filters=None):
    """
    Log a report export
    
    Args:
        report_type (str): Type of report
        export_format (str): Format of the export (pdf, csv, etc.)
        report_id (str, optional): ID of the report
        filters (dict, optional): Filters applied to the report
    """
    description = f"Exported {report_type} report as {export_format.upper()}"
    if report_id:
        description += f" ({report_id})"
    
    details = {
        'report_type': report_type,
        'export_format': export_format,
        'filters': filters or {},
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return log_activity(
        event_type=EVENT_REPORT_EXPORT,
        resource_type='report',
        resource_id=report_id or report_type,
        action='export',
        description=description,
        details=details
    )


def log_pm_process(original_file, updated_file, region=None, changes_count=None, success=True):
    """
    Log a PM allocation processing
    
    Args:
        original_file (str): Name of the original file
        updated_file (str): Name of the updated file
        region (str, optional): Region filter
        changes_count (int, optional): Number of changes detected
        success (bool): Whether the processing succeeded
    """
    description = f"Processed PM allocation files"
    if region:
        description += f" for region {region}"
    
    details = {
        'original_file': original_file,
        'updated_file': updated_file,
        'region': region,
        'changes_count': changes_count,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return log_activity(
        event_type=EVENT_PM_PROCESS,
        resource_type='pm_allocation',
        resource_id=f"{original_file}_{updated_file}",
        action='process',
        description=description,
        details=details,
        success=success
    )