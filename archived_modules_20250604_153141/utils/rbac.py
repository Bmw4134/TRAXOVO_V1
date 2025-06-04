"""
Role-Based Access Control (RBAC) Utilities

This module provides decorators and utilities for implementing role-based access control
throughout the application.
"""
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """Decorator that checks if the current user is an admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'warning')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    
    return decorated_function


def permission_required(permission_name):
    """
    Decorator factory that creates a decorator to check if a user has a specific permission
    
    Args:
        permission_name (str): Name of the permission method to check (e.g., 'can_view_reports')
    
    Returns:
        function: Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            
            # Check if user is an admin (admins have all permissions)
            if current_user.is_admin:
                return f(*args, **kwargs)
            
            # Check if user has the required permission
            if hasattr(current_user, permission_name) and callable(getattr(current_user, permission_name)):
                permission_check = getattr(current_user, permission_name)
                if permission_check():
                    return f(*args, **kwargs)
            
            # If no permission, redirect
            flash('You do not have permission to access this page.', 'warning')
            return redirect(url_for('index'))
        
        return decorated_function
    
    return decorator