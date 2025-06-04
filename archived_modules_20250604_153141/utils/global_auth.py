"""
Global Authentication Enforcer for TRAXOVO Live Field Test

Ensures all dashboard routes require login using the proven secure-attendance pattern.
Safe for live-edit deployment - no breaking changes.
"""
import logging
from functools import wraps
from flask import redirect, url_for, request, session
from flask_login import current_user

logger = logging.getLogger(__name__)

def enforce_global_login(f):
    """
    Global login decorator modeled after secure-attendance auth logic.
    Redirects unauthenticated users to /login by default.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            logger.warning(f"Unauthenticated access attempt to {request.endpoint}")
            # Store the attempted URL for post-login redirect
            session['next_url'] = request.url
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# List of critical dashboard routes that must be protected
PROTECTED_ROUTES = [
    'job_management',
    'attendance_workflow', 
    'asset_map',
    'billing',
    'driver_reports',
    'weekly_report',
    'gps_map',
    'system_health',
    'kaizen_admin',
    'file_processor',
    'upload'
]

def apply_global_auth_to_blueprint(blueprint):
    """
    Apply global authentication to all routes in a blueprint.
    Safe wrapper that doesn't break existing functionality.
    """
    try:
        for endpoint, view_func in blueprint.view_functions.items():
            if not hasattr(view_func, '_login_required'):
                # Mark as protected and wrap with auth
                view_func._login_required = True
                blueprint.view_functions[endpoint] = enforce_global_login(view_func)
                logger.info(f"✅ Global auth applied to {blueprint.name}.{endpoint}")
    except Exception as e:
        logger.warning(f"Auth application skipped for {blueprint.name}: {e}")

def verify_auth_status():
    """
    Verify current authentication status for system health checks.
    """
    return {
        'authenticated': current_user.is_authenticated,
        'user_id': getattr(current_user, 'id', None),
        'username': getattr(current_user, 'username', None),
        'session_active': 'user_id' in session
    }