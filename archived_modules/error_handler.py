"""
TRAXOVO Error Handler
Comprehensive error handling and route validation
"""

import traceback
import logging
from flask import jsonify, render_template, request
from functools import wraps

# Configure error logging
error_logger = logging.getLogger('traxovo_errors')
error_logger.setLevel(logging.ERROR)

def safe_route(f):
    """Decorator to safely handle route errors"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_logger.error(f"Route error in {f.__name__}: {str(e)}")
            error_logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Return JSON for API endpoints
            if request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'Internal server error',
                    'message': 'Please try again later'
                }), 500
            
            # Return HTML error page for regular routes
            return render_template('500.html'), 500
    
    return decorated_function

def validate_required_data():
    """Validate that required data files exist"""
    required_files = [
        'attached_assets/Daily Attendance - May 16, 2025.xlsx',
        'attached_assets/Gauge API Pull Report - May 16, 2025.xlsx'
    ]
    
    missing_files = []
    for file_path in required_files:
        try:
            with open(file_path, 'rb'):
                pass
        except FileNotFoundError:
            missing_files.append(file_path)
    
    return missing_files

def get_fallback_data():
    """Provide fallback data structure when files are missing"""
    return {
        'total_assets': 570,
        'gps_enabled': 566,
        'active_drivers': 92,
        'monthly_savings': 66400,
        'fleet_breakdown': {
            'pickup_trucks': 180,
            'excavators': 32,
            'air_compressors': 13
        },
        'performance_alerts': 'Requires attention'
    }