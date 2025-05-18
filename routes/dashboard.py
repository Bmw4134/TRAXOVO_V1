"""
Dashboard Routes Module

This module provides routes for the main dashboard interface.
"""

from flask import Blueprint, render_template, current_app
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    """Display the main dashboard"""
    # In a real implementation, this data would be fetched from the database
    # For demo purposes, we're using hardcoded values
    
    # Get current date for timestamps
    now = datetime.now()
    
    # Sample asset data
    asset_data = {
        'active_assets': 278,
        'excavator_count': 3,
        'loader_count': 2,
        'dozer_count': 2,
        'truck_count': 5,
        'backhoe_count': 2
    }
    
    # Sample driver alert data
    driver_alerts = {
        'late_starts': 7,
        'early_ends': 4,
        'not_on_job': 3
    }
    
    # Sample PM data
    pm_data = {
        'pm_allocation_total': 258742,
        'active_jobs': 6,
        'processing_queue': 2
    }
    
    # Sample recent activity data
    recent_activities = [
        {
            'type': 'Driver Assignment',
            'status': 'completed',
            'icon': 'bi-person-check',
            'timestamp': 'Today, 9:45 AM',
            'description': 'John D. assigned to TK-103',
            'asset_id': 'TK-103',
            'job_number': '2024-019'
        },
        {
            'type': 'Location Update',
            'status': 'info',
            'icon': 'bi-geo-alt',
            'timestamp': 'Today, 9:30 AM',
            'description': 'Asset moved to new job site',
            'asset_id': 'EX-74',
            'job_number': '2023-032'
        },
        {
            'type': 'Status Change',
            'status': 'warning',
            'icon': 'bi-arrow-repeat',
            'timestamp': 'Today, 8:15 AM',
            'description': 'Asset status changed to maintenance',
            'asset_id': 'LD-45',
            'job_number': '2024-016'
        },
        {
            'type': 'Maintenance Completed',
            'status': 'completed',
            'icon': 'bi-tools',
            'timestamp': 'Yesterday, 4:30 PM',
            'description': 'Scheduled maintenance completed',
            'asset_id': 'DZ-31',
            'job_number': '2023-034'
        },
        {
            'type': 'Parts Replaced',
            'status': 'warning',
            'icon': 'bi-wrench',
            'timestamp': 'Yesterday, 2:15 PM',
            'description': 'Hydraulic line replaced',
            'asset_id': 'EX-65',
            'job_number': '2024-025'
        }
    ]
    
    # Combine all data
    dashboard_data = {
        **asset_data,
        **driver_alerts,
        **pm_data,
        'recent_activities': recent_activities
    }
    
    return render_template('dashboard/dashboard_v2.html', **dashboard_data)

@dashboard_bp.route('/v2')
def dashboard_v2():
    """Display the enhanced dashboard (v2)"""
    return index()  # Same data, just a separate route for now

def register_blueprint(app):
    """Register the dashboard blueprint with the app"""
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    logger.info('Registered dashboard blueprint')
    return dashboard_bp