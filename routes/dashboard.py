"""
TRAXORA | Dashboard Routes

This module provides routes for the main dashboard and system overview.
"""
from flask import Blueprint, render_template, jsonify
import logging

# Configure logging
logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')

@dashboard_bp.route('/')
def index():
    """Application main dashboard"""
    try:
        # Get system health data - in production these would be actual DB queries
        # Sample data for demonstration
        system_data = {
            'assets_count': 718,
            'drivers_count': 143,
            'job_sites_count': 42,
            'pm_allocations_count': 86,
            'api_status': 'connected',
            'database_status': 'connected',
            'storage_status': 'connected',
            'last_sync_time': '2025-05-22 14:30:21'
        }
        
        # Sample notifications
        notifications = [
            {
                'type': 'info',
                'title': 'Daily Driver Report Updated',
                'message': 'West Texas Division report completed with 143 entries.',
                'time': '10 minutes ago'
            },
            {
                'type': 'warning',
                'title': 'Late Driver Alert',
                'message': '3 drivers arrived late to job site #2024-016.',
                'time': '1 hour ago'
            },
            {
                'type': 'info',
                'title': 'PM Allocation Processed',
                'message': 'Successfully processed April 2025 allocations.',
                'time': '3 hours ago'
            }
        ]
        
        return render_template('dashboard_new.html', 
                              **system_data, 
                              notifications=notifications)
    except Exception as e:
        logger.error(f"Error rendering dashboard: {str(e)}")
        return render_template('dashboard_new.html', 
                              api_status='error',
                              database_status='error',
                              storage_status='error',
                              notifications=[])

@dashboard_bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})