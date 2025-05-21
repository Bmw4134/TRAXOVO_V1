"""
Driver Reports Module

This module provides routes for displaying driver-related reports including:
- Enhanced daily driver report with attendance tracking
- Late start/early end report
- Job site efficiency analysis
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from datetime import datetime, timedelta
import logging
import json
import random

logger = logging.getLogger(__name__)

# Create blueprint
driver_reports_bp = Blueprint('driver_reports', __name__, url_prefix='/driver-reports')

@driver_reports_bp.route('/')
def index():
    """Display the driver reports dashboard"""
    return render_template('driver_reports/index.html')

@driver_reports_bp.route('/enhanced-daily')
def enhanced_daily():
    """Display the enhanced daily driver report"""
    # Get report date (default to today)
    report_date_str = request.args.get('date')
    if report_date_str:
        try:
            report_date = datetime.strptime(report_date_str, '%Y-%m-%d')
        except ValueError:
            report_date = datetime.now()
    else:
        report_date = datetime.now()
    
    formatted_date = report_date.strftime('%A, %B %d, %Y')
    today_date = report_date.strftime('%Y-%m-%d')
    
    # In a real implementation, we would fetch this data from the database
    # For demo purposes, we're using sample data
    
    # Sample driver activity data
    driver_activities = [
        {
            'driver_name': 'John Smith',
            'status': 'Late Start',
            'status_class': 'late-start',
            'icon_class': 'late',
            'icon': 'bi-clock-history',
            'badge_class': 'danger',
            'details': 'Arrived at 8:45 AM (45 minutes late)',
            'job_number': '2023-032',
            'job_color': '#4e73df',
            'timestamp': '8:45 AM'
        },
        {
            'driver_name': 'Michael Johnson',
            'status': 'On Time',
            'status_class': 'on-time',
            'icon_class': 'on-time',
            'icon': 'bi-check-circle',
            'badge_class': 'success',
            'details': 'Arrived at 8:00 AM',
            'job_number': '2023-034',
            'job_color': '#1cc88a',
            'timestamp': '8:00 AM'
        },
        {
            'driver_name': 'Robert Williams',
            'status': 'Early End',
            'status_class': 'early-end',
            'icon_class': 'early',
            'icon': 'bi-clock',
            'badge_class': 'warning',
            'details': 'Left at 3:30 PM (30 minutes early)',
            'job_number': '2024-016',
            'job_color': '#36b9cc',
            'timestamp': '3:30 PM'
        },
        {
            'driver_name': 'William Davis',
            'status': 'Not On Job',
            'status_class': 'not-on-job',
            'icon_class': 'not-on-job',
            'icon': 'bi-geo-alt',
            'badge_class': 'secondary',
            'details': 'Located 5 miles from assigned job site',
            'job_number': '2024-019',
            'job_color': '#f6c23e',
            'timestamp': '10:15 AM'
        },
        {
            'driver_name': 'David Brown',
            'status': 'On Time',
            'status_class': 'on-time',
            'icon_class': 'on-time',
            'icon': 'bi-check-circle',
            'badge_class': 'success',
            'details': 'Arrived at 7:55 AM',
            'job_number': '2024-025',
            'job_color': '#e74a3b',
            'timestamp': '7:55 AM'
        },
        {
            'driver_name': 'Richard Miller',
            'status': 'Late Start',
            'status_class': 'late-start',
            'icon_class': 'late',
            'icon': 'bi-clock-history',
            'badge_class': 'danger',
            'details': 'Arrived at 8:20 AM (20 minutes late)',
            'job_number': '2023-032',
            'job_color': '#4e73df',
            'timestamp': '8:20 AM'
        },
        {
            'driver_name': 'Joseph Wilson',
            'status': 'On Time',
            'status_class': 'on-time',
            'icon_class': 'on-time',
            'icon': 'bi-check-circle',
            'badge_class': 'success',
            'details': 'Arrived at 8:05 AM',
            'job_number': '2024-025',
            'job_color': '#e74a3b',
            'timestamp': '8:05 AM'
        },
        {
            'driver_name': 'Thomas Moore',
            'status': 'Early End',
            'status_class': 'early-end',
            'icon_class': 'early',
            'icon': 'bi-clock',
            'badge_class': 'warning',
            'details': 'Left at 3:45 PM (15 minutes early)',
            'job_number': '2024-019',
            'job_color': '#f6c23e',
            'timestamp': '3:45 PM'
        }
    ]
    
    # Count of each status
    late_starts = sum(1 for activity in driver_activities if activity['status'] == 'Late Start')
    early_ends = sum(1 for activity in driver_activities if activity['status'] == 'Early End')
    not_on_job = sum(1 for activity in driver_activities if activity['status'] == 'Not On Job')
    on_time = sum(1 for activity in driver_activities if activity['status'] == 'On Time')
    
    report_data = {
        'report_date': formatted_date,
        'today_date': today_date,
        'late_starts': late_starts,
        'early_ends': early_ends,
        'not_on_job': not_on_job,
        'on_time': on_time,
        'driver_activities': driver_activities
    }
    
    return render_template('driver_reports/enhanced_daily.html', **report_data)

@driver_reports_bp.route('/api/driver-locations')
def driver_locations():
    """API endpoint to get driver locations for the map"""
    # In a real implementation, we would fetch this data from the database
    # For demo purposes, we're using sample data
    driver_locations = [
        {'name': 'John Smith', 'status': 'late', 'lat': 32.7516, 'lng': -96.8339, 'job': '2023-032'},
        {'name': 'Michael Johnson', 'status': 'on-time', 'lat': 32.7641, 'lng': -96.7596, 'job': '2023-034'},
        {'name': 'Robert Williams', 'status': 'early', 'lat': 32.8075, 'lng': -96.8148, 'job': '2024-016'},
        {'name': 'William Davis', 'status': 'not-on-job', 'lat': 32.7865, 'lng': -96.7986, 'job': '2024-019'},
        {'name': 'David Brown', 'status': 'on-time', 'lat': 32.7972, 'lng': -96.8192, 'job': '2024-025'}
    ]
    return jsonify(driver_locations)

def register_blueprint(app):
    """Register the driver reports blueprint with the app"""
    app.register_blueprint(driver_reports_bp)
    logger.info('Registered Driver Reports blueprint')
    return driver_reports_bp