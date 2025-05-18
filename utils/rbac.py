"""
Role-Based Access Control (RBAC) Utilities

This module provides utilities for implementing role-based access control
throughout the application, including decorators for protecting routes.
"""

from functools import wraps
from flask import current_app, flash, redirect, url_for
from flask_login import current_user

def permission_required(permission):
    """
    Decorator for views that require a specific permission.
    
    Args:
        permission (str): The permission to check. Should match a method name
                         on the User model (e.g., 'can_view_reports').
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            
            # Check if the permission check method exists
            if not hasattr(current_user, permission):
                current_app.logger.error(f"Permission check method '{permission}' not found")
                flash('Access denied due to an error. Please contact administrator.', 'danger')
                return redirect(url_for('index'))
            
            # Call the permission check method
            check_method = getattr(current_user, permission)
            if callable(check_method) and check_method():
                return f(*args, **kwargs)
            else:
                flash('You do not have permission to access this resource.', 'warning')
                return redirect(url_for('index'))
        
        return decorated_function
    return decorator

# Specific permission decorators for common use cases
def view_reports_required(f):
    """Decorator for views that require permission to view reports."""
    return permission_required('can_view_reports')(f)

def export_reports_required(f):
    """Decorator for views that require permission to export reports."""
    return permission_required('can_export_reports')(f)

def manage_assets_required(f):
    """Decorator for views that require permission to manage assets."""
    return permission_required('can_manage_assets')(f)

def manage_drivers_required(f):
    """Decorator for views that require permission to manage drivers."""
    return permission_required('can_manage_drivers')(f)

def process_pm_required(f):
    """Decorator for views that require permission to process PM allocations."""
    return permission_required('can_process_pm')(f)

def admin_required(f):
    """Decorator for views that require admin privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        if not current_user.is_admin:
            flash('Administrator privileges required.', 'warning')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    
    return decorated_function