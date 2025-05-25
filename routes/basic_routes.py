"""
Basic Routes Module

This module provides the basic routes and navigation structure for the TRAXORA application.
It serves as a centralized place for core navigation functionality.
"""
import logging
from flask import Blueprint, render_template, redirect, url_for, jsonify
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Create a blueprint for basic routes
basic_routes_bp = Blueprint('basic_routes', __name__)

def register_basic_routes(app):
    """
    Register basic routes with the application
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(basic_routes_bp)
    
    # Register redirect routes
    register_redirects(app)
    
    logger.info("Basic routes registered")

def register_redirects(app):
    """
    Register redirect routes to standardize navigation
    
    Args:
        app: Flask application instance
    """
    # Map legacy URLs to new standardized structure
    redirect_map = {
        '/attendance/': '/enhanced-weekly-report/',
        '/attendance': '/enhanced-weekly-report/',
        '/driver-reports/': '/daily-driver-report/',
        '/driver-reports': '/daily-driver-report/',
        '/drivers/': '/driver-management/',
        '/drivers': '/driver-management/',
        '/assets/': '/asset-management/',
        '/assets': '/asset-management/',
    }
    
    # Register each redirect
    for old_path, new_path in redirect_map.items():
        app.add_url_rule(old_path, f'redirect_{old_path.replace("/", "_")}', 
                         lambda p=new_path: redirect(p))
    
    logger.info("Redirect routes registered")

@basic_routes_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring systems"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'app': 'TRAXORA Fleet Management System'
    })

@basic_routes_bp.route('/navigation')
def navigation_data():
    """Provide navigation structure as JSON for dynamic menus"""
    navigation = [
        {
            'id': 'dashboard',
            'title': 'Dashboard',
            'icon': 'fas fa-tachometer-alt',
            'url': '/',
            'active_paths': ['/']
        },
        {
            'id': 'daily_driver_report',
            'title': 'Daily Driver Report',
            'icon': 'fas fa-calendar-day',
            'url': '/daily-driver-report/',
            'active_paths': ['/daily-driver-report/', '/daily-driver-report']
        },
        {
            'id': 'enhanced_weekly_report',
            'title': 'Weekly Driver Report',
            'icon': 'fas fa-calendar-week',
            'url': '/enhanced-weekly-report/',
            'active_paths': ['/enhanced-weekly-report/', '/enhanced-weekly-report']
        },
        {
            'id': 'daily_attendance',
            'title': 'Daily Attendance',
            'icon': 'fas fa-clipboard-check',
            'url': '/daily_attendance/',
            'active_paths': ['/daily_attendance/', '/daily_attendance']
        },
        {
            'id': 'file_organizer',
            'title': 'File Organizer',
            'icon': 'fas fa-folder-open',
            'url': '/file-organizer/',
            'active_paths': ['/file-organizer/', '/file-organizer']
        },
        {
            'id': 'asset_map',
            'title': 'Asset Map',
            'icon': 'fas fa-map-marked-alt',
            'url': '/asset-map/',
            'active_paths': ['/asset-map/', '/asset-map']
        },
        {
            'id': 'system_admin',
            'title': 'System Admin',
            'icon': 'fas fa-cogs',
            'url': '/system-admin/',
            'active_paths': ['/system-admin/', '/system-admin']
        }
    ]
    
    return jsonify(navigation)

@basic_routes_bp.context_processor
def inject_navigation():
    """Inject navigation data into all templates"""
    def get_navigation():
        return [
            {
                'id': 'dashboard',
                'title': 'Dashboard',
                'icon': 'fas fa-tachometer-alt',
                'url': '/',
                'active_paths': ['/']
            },
            {
                'id': 'daily_driver_report',
                'title': 'Daily Driver Report',
                'icon': 'fas fa-calendar-day',
                'url': '/daily-driver-report/',
                'active_paths': ['/daily-driver-report/', '/daily-driver-report']
            },
            {
                'id': 'enhanced_weekly_report',
                'title': 'Weekly Driver Report',
                'icon': 'fas fa-calendar-week',
                'url': '/enhanced-weekly-report/',
                'active_paths': ['/enhanced-weekly-report/', '/enhanced-weekly-report']
            },
            {
                'id': 'daily_attendance',
                'title': 'Daily Attendance',
                'icon': 'fas fa-clipboard-check',
                'url': '/daily_attendance/',
                'active_paths': ['/daily_attendance/', '/daily_attendance']
            },
            {
                'id': 'file_organizer',
                'title': 'File Organizer',
                'icon': 'fas fa-folder-open',
                'url': '/file-organizer/',
                'active_paths': ['/file-organizer/', '/file-organizer']
            },
            {
                'id': 'asset_map',
                'title': 'Asset Map',
                'icon': 'fas fa-map-marked-alt',
                'url': '/asset-map/',
                'active_paths': ['/asset-map/', '/asset-map']
            },
            {
                'id': 'system_admin',
                'title': 'System Admin',
                'icon': 'fas fa-cogs',
                'url': '/system-admin/',
                'active_paths': ['/system-admin/', '/system-admin']
            }
        ]
    
    return {'navigation': get_navigation()}