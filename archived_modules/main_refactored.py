"""
TRAXORA Fleet Management System - Main Application

This module provides the main entry point for the TRAXORA fleet management system.
Refactored for better organization and reduced redundancy.
"""
import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, redirect, url_for, request

from app import app, db
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Setup runtime mode indicator
runtime_mode = os.environ.get('RUNTIME_MODE', 'DEVELOPMENT').upper()
logger.info(f"TRAXORA running in {runtime_mode} mode")

# Load jobsite catalog
try:
    from utils.jobsite_catalog_loader import load_jobsite_catalog
    load_jobsite_catalog()
except Exception as e:
    logger.warning(f"Error loading jobsite catalog: {str(e)}")

# Centralized blueprint registration
# This dictionary tracks registered blueprints to avoid duplicates
registered_blueprints = {}

def register_blueprint(blueprint_name, blueprint_import_path, blueprint_var_name=None):
    """
    Register a blueprint if it hasn't been registered already
    
    Args:
        blueprint_name (str): The name to track for registration status
        blueprint_import_path (str): Import path like 'routes.module_name'
        blueprint_var_name (str, optional): Variable name of the blueprint in the module
                                           Defaults to None (uses blueprint_name + '_bp')
    
    Returns:
        bool: True if registered successfully, False otherwise
    """
    if blueprint_name in registered_blueprints:
        logger.info(f"{blueprint_name} blueprint already registered")
        return False
    
    try:
        # Determine the blueprint variable name if not provided
        if not blueprint_var_name:
            if blueprint_name.endswith('_bp'):
                blueprint_var_name = blueprint_name
            else:
                blueprint_var_name = f"{blueprint_name}_bp"
        
        # Import the module
        module = __import__(blueprint_import_path, fromlist=[blueprint_var_name])
        
        # Get the blueprint from the module
        if hasattr(module, blueprint_var_name):
            blueprint = getattr(module, blueprint_var_name)
            app.register_blueprint(blueprint)
            registered_blueprints[blueprint_name] = blueprint
            logger.info(f"{blueprint_name} blueprint registered successfully")
            return True
        else:
            logger.warning(f"{blueprint_var_name} not found in {blueprint_import_path}")
            return False
    except ImportError:
        logger.warning(f"{blueprint_name} module not found")
        return False
    except Exception as e:
        logger.error(f"Error registering {blueprint_name} blueprint: {str(e)}")
        return False

# Register core blueprints
register_blueprint('driver_reports', 'routes.driver_reports_new')
register_blueprint('asset_map', 'routes.asset_map')
register_blueprint('billing', 'routes.billing')
register_blueprint('system_health', 'routes.system_health')
register_blueprint('map_standalone', 'routes.map_standalone')
register_blueprint('direct_map', 'routes.direct_map_route', 'direct_map')
register_blueprint('mtd_reports', 'routes.mtd_reports_fixed')

# Register modern driver reports dashboard
try:
    from create_driver_reports_route import create_driver_reports_blueprint
    app.register_blueprint(create_driver_reports_blueprint())
    logger.info("Driver reports dashboard (modern UI) registered")
except Exception as e:
    logger.warning(f"Error registering driver reports dashboard: {str(e)}")

# Register all other important modules
register_blueprint('auto_attendance', 'routes.auto_attendance_routes', 'auto_attendance')
register_blueprint('dashboard', 'routes.dashboard')
register_blueprint('file_upload', 'routes.file_upload_new')
register_blueprint('file_processor', 'routes.file_processor')
register_blueprint('upload_api', 'routes.file_upload', 'upload_bp')
register_blueprint('react_upload', 'routes.react_upload')
register_blueprint('attendance_report', 'routes.attendance_report')
register_blueprint('weekly_driver_report', 'routes.weekly_driver_report')
register_blueprint('daily_driver_report', 'routes.daily_driver_report')
register_blueprint('weekly_report', 'routes.weekly_report', 'bp')
register_blueprint('attendance', 'routes.attendance_routes')
register_blueprint('enhanced_weekly_report', 'routes.enhanced_weekly_report')
register_blueprint('system_admin', 'routes.system_admin')
register_blueprint('kaizen_monitor', 'routes.kaizen_monitor')
register_blueprint('kaizen_admin', 'routes.kaizen_admin')
register_blueprint('daily_attendance', 'routes.daily_attendance_routes')
register_blueprint('file_organizer', 'routes.file_organizer_routes', 'file_organizer')

# Standardized redirects
@app.route('/attendance/')
@app.route('/attendance')
def attendance_main():
    """Redirect to enhanced weekly report"""
    return redirect('/enhanced-weekly-report/')

# Root route
@app.route('/')
def dashboard():
    """Homepage shows dashboard"""
    return render_template('dashboard.html',
                          assets_count=get_asset_count(),
                          drivers_count=get_driver_count(),
                          job_sites_count=get_job_site_count(),
                          pm_allocations_count=get_pm_allocation_count(),
                          database_status=check_database_status(),
                          api_status=check_gauge_api_status(),
                          storage_status=check_storage_status(),
                          last_sync_time=get_last_sync_time(),
                          notifications=get_recent_notifications())

# Health check endpoint
@app.route('/system-health')
def system_health():
    """System health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'genius_core': 'CONTINUITY MODE ACTIVE',
        'database': check_database_status(),
        'gauge_api': check_gauge_api_status(),
        'storage': check_storage_status()
    })

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('basic_error.html', 
                          error_code=404,
                          error_message="Page not found",
                          error_details="The requested page does not exist."), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {str(e)}")
    return render_template('basic_error.html',
                          error_code=500,
                          error_message="Internal server error",
                          error_details="An unexpected error occurred on the server."), 500

# Utility functions
def check_gauge_api_status():
    """Check status of the Gauge API connection"""
    try:
        # Check if we have API credentials
        if not os.environ.get('GAUGE_API_URL') or not os.environ.get('GAUGE_API_USERNAME'):
            return 'not_configured'
        
        # In a real implementation, we would check the actual API connection
        # For now, just check for SSL certificate issues based on logs
        if "CERTIFICATE_VERIFY_FAILED" in os.environ.get('GAUGE_API_ERROR', ''):
            return 'warning'
        
        return 'connected'
    except Exception as e:
        logger.error(f"Error checking Gauge API status: {str(e)}")
        return 'error'

def check_database_status():
    """Check status of the database connection"""
    try:
        # Simple query to check if the database is responding
        db.session.execute(text("SELECT 1"))
        return 'connected'
    except Exception as e:
        logger.error(f"Error checking database status: {str(e)}")
        return 'disconnected'

def check_storage_status():
    """Check status of the file storage"""
    try:
        # Check if upload directories exist
        upload_dirs = ['uploads', 'uploads/driver_reports', 'uploads/pm_allocations']
        for directory in upload_dirs:
            os.makedirs(os.path.join(app.root_path, directory), exist_ok=True)
        
        # Check if we can write to the upload directory
        test_file = os.path.join(app.root_path, 'uploads', '.test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        
        return 'connected'
    except Exception as e:
        logger.error(f"Error checking storage status: {str(e)}")
        return 'disconnected'

def get_asset_count():
    """Get the count of active assets"""
    try:
        from models import Asset
        return Asset.query.filter_by(is_active=True).count()
    except Exception as e:
        logger.error(f"Error getting asset count: {str(e)}")
        return 0

def get_driver_count():
    """Get the count of active drivers"""
    try:
        from models import Driver
        return Driver.query.filter_by(is_active=True).count()
    except Exception as e:
        logger.error(f"Error getting driver count: {str(e)}")
        return 0

def get_job_site_count():
    """Get the count of active job sites"""
    try:
        from models import JobSite
        return JobSite.query.filter_by(is_active=True).count()
    except Exception as e:
        logger.error(f"Error getting job site count: {str(e)}")
        return 0

def get_pm_allocation_count():
    """Get the count of PM allocations for the current month"""
    try:
        from models import PMAllocation
        current_month = datetime.now().strftime('%Y-%m')
        return PMAllocation.query.filter_by(month=current_month).count()
    except Exception as e:
        logger.error(f"Error getting PM allocation count: {str(e)}")
        return 0

def get_last_sync_time():
    """Get the last data sync time"""
    try:
        from models import SystemConfiguration
        last_sync = SystemConfiguration.query.filter_by(key='last_sync_time').first()
        if last_sync and last_sync.value:
            return last_sync.value
        return 'Never'
    except Exception as e:
        logger.error(f"Error getting last sync time: {str(e)}")
        return 'Unknown'

def get_recent_notifications():
    """Get recent system notifications"""
    try:
        from models import Notification
        notifications = Notification.query.filter_by(user_id=None).order_by(Notification.created_at.desc()).limit(5).all()
        return [
            {
                'title': notification.title,
                'message': notification.message,
                'type': notification.type,
                'time': notification.created_at.strftime('%Y-%m-%d %H:%M')
            }
            for notification in notifications
        ]
    except Exception as e:
        logger.error(f"Error getting recent notifications: {str(e)}")
        return []

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)