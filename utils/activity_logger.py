"""
Activity Logger Module

This module provides functions for logging user activities
to help with auditing and troubleshooting.
"""

import logging
import json
from datetime import datetime
from flask import current_app, request, session
from flask_login import current_user

# Configure logger
logger = logging.getLogger(__name__)

def _get_user_info():
    """
    Get user information for logging
    
    Returns:
        dict: User information
    """
    user_info = {
        'user_id': None,
        'username': 'anonymous',
        'ip_address': request.remote_addr,
        'user_agent': request.user_agent.string if request.user_agent else 'unknown'
    }
    
    try:
        if current_user and current_user.is_authenticated:
            user_info['user_id'] = current_user.id
            user_info['username'] = current_user.username
    except:
        pass
        
    return user_info

def log_activity(activity_type, description, details=None):
    """
    Log a user activity
    
    Args:
        activity_type (str): Type of activity (e.g., 'login', 'export', 'search')
        description (str): Brief description of the activity
        details (dict): Additional details about the activity
    """
    try:
        user_info = _get_user_info()
        
        activity_data = {
            'timestamp': datetime.now().isoformat(),
            'activity_type': activity_type,
            'description': description,
            'details': details or {},
            'user_info': user_info,
            'session_id': session.get('_id', None)
        }
        
        # Log in JSON format for easier parsing
        logger.info(f"ACTIVITY: {json.dumps(activity_data)}")
        
        # In a more advanced implementation, we would also store in database
        
    except Exception as e:
        logger.warning(f"Failed to log activity: {e}")

def log_navigation(page_name, params=None):
    """
    Log a page navigation event
    
    Args:
        page_name (str): Name of the page being viewed
        params (dict): URL parameters or other context
    """
    log_activity('navigation', f"Viewed {page_name}", params)

def log_login(success, username, reason=None):
    """
    Log a login attempt
    
    Args:
        success (bool): Whether the login was successful
        username (str): Username attempting to log in
        reason (str): Reason for failure if not successful
    """
    details = {'username': username, 'success': success}
    if reason:
        details['reason'] = reason
        
    log_activity('login', 
                 f"{'Successful' if success else 'Failed'} login for {username}", 
                 details)

def log_document_upload(file_name, file_size, file_type, module):
    """
    Log a document upload
    
    Args:
        file_name (str): Name of the uploaded file
        file_size (int): Size of the file in bytes
        file_type (str): MIME type or extension of the file
        module (str): Module where the file was uploaded
    """
    log_activity('upload', 
                 f"Uploaded {file_name} to {module}", 
                 {
                     'file_name': file_name,
                     'file_size': file_size,
                     'file_type': file_type,
                     'module': module
                 })

def log_report_export(report_type, format_type, filters=None):
    """
    Log a report export
    
    Args:
        report_type (str): Type of report exported
        format_type (str): Format of the export (e.g., 'excel', 'pdf')
        filters (dict): Filters applied to the report
    """
    log_activity('export', 
                 f"Exported {report_type} report in {format_type} format", 
                 {
                     'report_type': report_type,
                     'format': format_type,
                     'filters': filters or {}
                 })

def log_data_change(entity_type, entity_id, change_type, old_values=None, new_values=None):
    """
    Log a data change event
    
    Args:
        entity_type (str): Type of entity being changed (e.g., 'driver', 'asset')
        entity_id (str): ID of the entity
        change_type (str): Type of change ('create', 'update', 'delete')
        old_values (dict): Previous values for the entity's fields
        new_values (dict): New values for the entity's fields
    """
    log_activity('data_change', 
                 f"{change_type.capitalize()} {entity_type} {entity_id}", 
                 {
                     'entity_type': entity_type,
                     'entity_id': entity_id,
                     'change_type': change_type,
                     'old_values': old_values or {},
                     'new_values': new_values or {}
                 })

def log_error(error_type, message, context=None):
    """
    Log an application error
    
    Args:
        error_type (str): Type of error
        message (str): Error message
        context (dict): Contextual information about the error
    """
    user_info = _get_user_info()
    
    error_data = {
        'timestamp': datetime.now().isoformat(),
        'error_type': error_type,
        'message': message,
        'context': context or {},
        'user_info': user_info,
        'url': request.url if request else None,
        'method': request.method if request else None,
        'session_id': session.get('_id', None)
    }
    
    # Log error details
    logger.error(f"APPLICATION ERROR: {json.dumps(error_data)}")

def log_pm_process(process_type, file_name, result_stats=None):
    """
    Log a PM allocation processing event
    
    Args:
        process_type (str): Type of process ('import', 'export', 'reconcile')
        file_name (str): Name of the file being processed
        result_stats (dict): Statistics about the processing result
    """
    log_activity('pm_process', 
                 f"{process_type.capitalize()} PM allocation file: {file_name}", 
                 {
                     'process_type': process_type,
                     'file_name': file_name,
                     'stats': result_stats or {}
                 })

def log_invoice_generation(invoice_type, invoice_number, amount, details=None):
    """
    Log an invoice generation event
    
    Args:
        invoice_type (str): Type of invoice ('monthly', 'corrected', 'supplemental')
        invoice_number (str): Invoice reference number
        amount (float): Total amount of the invoice
        details (dict): Additional details about the invoice
    """
    log_activity('invoice_generation', 
                 f"Generated {invoice_type} invoice #{invoice_number} for ${amount:.2f}", 
                 {
                     'invoice_type': invoice_type,
                     'invoice_number': invoice_number,
                     'amount': amount,
                     'details': details or {}
                 })
                 
def log_payment_record(payment_type, amount, reference_number, details=None):
    """
    Log a payment record event
    
    Args:
        payment_type (str): Type of payment ('check', 'credit', 'wire', 'cash')
        amount (float): Amount of the payment
        reference_number (str): Reference or transaction number
        details (dict): Additional details about the payment
    """
    log_activity('payment_record', 
                 f"Recorded {payment_type} payment of ${amount:.2f} (Ref: {reference_number})", 
                 {
                     'payment_type': payment_type,
                     'amount': amount,
                     'reference_number': reference_number,
                     'details': details or {}
                 })