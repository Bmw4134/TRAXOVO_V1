"""
TRAXORA Fleet Management System - System Health Module

This module provides routes for monitoring system health, resource usage,
and connection status to external services.
"""

import os
import platform
import psutil
import datetime
import logging
from flask import Blueprint, render_template, current_app, jsonify, request, flash
import requests
import importlib

# Try to import gauge_api, but handle it gracefully if not found
try:
    from utils.gauge_api import test_gauge_api_connection
    gauge_api_imported = True
except ImportError:
    gauge_api_imported = False

# Create logger
logger = logging.getLogger(__name__)

# Create blueprint
system_health_bp = Blueprint('system_health', __name__, url_prefix='/system-health')

@system_health_bp.route('/')
def dashboard():
    """System health dashboard"""
    try:
        # Get system information
        system_info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': round(psutil.virtual_memory().total / (1024 * 1024 * 1024), 2),  # GB
            'uptime': get_uptime()
        }
        
        # Get resource usage
        resource_usage = {
            'cpu_percent': psutil.cpu_percent(interval=0.5),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
        
        # Check database connection
        db_status = check_database_connection()
        
        # Check external services
        external_services = check_external_services()
        
        # Get recent logs
        logs = get_recent_logs(20)
        
        # Current time for update timestamp
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return render_template(
            'system_health/dashboard.html',
            system_info=system_info,
            resource_usage=resource_usage,
            db_status=db_status,
            external_services=external_services,
            logs=logs,
            now=now
        )
    
    except Exception as e:
        logger.error(f"Error displaying system health dashboard: {str(e)}")
        flash(f"Error displaying system health: {str(e)}", "danger")
        return render_template('error.html', error=str(e))

@system_health_bp.route('/api/status')
def api_status():
    """API endpoint for system status"""
    try:
        # Get resource usage
        resource_usage = {
            'cpu_percent': psutil.cpu_percent(interval=0.5),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
        
        # Check database connection
        db_status = check_database_connection()
        
        # Check external services
        external_services = check_external_services()
        
        return jsonify({
            'status': 'success',
            'resource_usage': resource_usage,
            'db_status': db_status,
            'external_services': external_services
        })
    
    except Exception as e:
        logger.error(f"Error in API status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

def get_uptime():
    """Get system uptime in days, hours, minutes"""
    try:
        uptime_seconds = psutil.boot_time()
        uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(uptime_seconds)
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        return f"{days}d {hours}h {minutes}m"
    except:
        return "Unknown"

def check_database_connection():
    """Check database connection status"""
    try:
        from app import db
        from sqlalchemy import text
        # Try a simple query with SQLAlchemy text
        db.session.execute(text("SELECT 1"))
        return {'status': 'connected', 'message': 'Database is connected'}
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return {'status': 'error', 'message': f'Database connection error: {str(e)}'}

def check_external_services():
    """Check external service connections"""
    services = []
    
    # Check Gauge API
    if gauge_api_imported:
        try:
            # Import the function dynamically to avoid potential circular imports
            from utils.gauge_api import test_gauge_api_connection
            gauge_api_status = test_gauge_api_connection()
            services.append({
                'name': 'Gauge API',
                'status': 'connected' if gauge_api_status else 'error',
                'message': 'Successfully connected to Gauge API' if gauge_api_status else 'Failed to connect to Gauge API'
            })
        except Exception as e:
            services.append({
                'name': 'Gauge API',
                'status': 'error',
                'message': f'Error checking Gauge API: {str(e)}'
            })
    else:
        services.append({
            'name': 'Gauge API',
            'status': 'error',
            'message': 'Gauge API module not found'
        })
    
    # Add Database status
    try:
        db_status = check_database_connection()
        services.append({
            'name': 'Database',
            'status': 'connected' if db_status.get('status') == 'connected' else 'error',
            'message': db_status.get('message', 'Unknown status')
        })
    except Exception as e:
        services.append({
            'name': 'Database',
            'status': 'error',
            'message': f'Error checking database: {str(e)}'
        })
    
    return services

def get_recent_logs(count=20):
    """Get recent application logs"""
    logs = []
    
    try:
        # Look for log file in common locations
        log_paths = [
            os.path.join(current_app.root_path, 'logs', 'app.log'),
            os.path.join(current_app.root_path, '..', 'logs', 'app.log'),
            '/var/log/traxora/app.log',
        ]
        
        log_file = None
        for path in log_paths:
            if os.path.exists(path):
                log_file = path
                break
        
        if log_file:
            with open(log_file, 'r') as f:
                # Get last N lines
                lines = f.readlines()
                logs = lines[-count:] if len(lines) > count else lines
        
        return logs
    
    except Exception as e:
        logger.error(f"Error getting logs: {str(e)}")
        return [f"Error getting logs: {str(e)}"]