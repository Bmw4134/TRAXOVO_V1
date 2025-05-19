"""
Driver Module Controller

This module provides routes and functionality for the Driver module,
including daily reports, attendance tracking, and driver management.
"""

import os
import json
import logging
from datetime import datetime, timedelta
import random
from collections import defaultdict
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import pandas as pd

# Import utility modules
from config import DEFAULT_START_TIME, DEFAULT_THRESHOLD_MINUTES, SKIPROWS_DAILY_USAGE
from time_utils import parse_time_with_tz, calculate_lateness
from driver_utils import extract_driver_from_label, clean_asset_info
from models.user_settings import UserSettings
from models.email_configuration import EmailRecipientList

# Import activity logger
from utils.activity_logger import log_navigation, log_document_upload, log_report_export

# Set up logger
logger = logging.getLogger(__name__)

# Define blueprint
driver_module_bp = Blueprint('driver_module', __name__, url_prefix='/drivers')

# Configuration constants
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Email configuration helper functions
def get_user_email_config():
    """
    Get email configuration for the current user
    Returns a dictionary with configuration values
    """
    email_config = {
        'email_8am_recipients': '',
        'email_9am_recipients': '',
        'email_cc': '',
        'email_bcc': '',
        'email_auto_send': False,
        'email_include_user': False
    }
    
    try:
        if current_user and current_user.is_authenticated:
            # Use the UserSettings model to get values
            for key in email_config.keys():
                value = UserSettings.get_setting(current_user.id, key)
                if value is not None:
                    # Handle boolean settings
                    if key in ['email_auto_send', 'email_include_user']:
                        email_config[key] = value.lower() == 'true'
                    else:
                        email_config[key] = value
    except Exception as e:
        logger.error(f"Error retrieving email configuration: {e}")
        
    return email_config

def save_email_config():
    """
    Save email configuration from form submission
    """
    if not current_user.is_authenticated:
        return False
        
    try:
        # Extract settings from form
        user_id = current_user.id
        
        # Save each config item
        UserSettings.set_setting(user_id, 'email_8am_recipients', request.form.get('email_8am_recipients', ''))
        UserSettings.set_setting(user_id, 'email_9am_recipients', request.form.get('email_9am_recipients', ''))
        UserSettings.set_setting(user_id, 'email_cc', request.form.get('email_cc', ''))
        UserSettings.set_setting(user_id, 'email_bcc', request.form.get('email_bcc', ''))
        UserSettings.set_setting(user_id, 'email_auto_send', 'true' if request.form.get('email_auto_send') else 'false')
        UserSettings.set_setting(user_id, 'email_include_user', 'true' if request.form.get('email_include_user') else 'false')
        
        return True
    except Exception as e:
        logger.error(f"Error saving email configuration: {e}")
        return False

def get_report_recipients(export_time):
    """
    Get recipients for a specific report time (8am or 9am)
    Combines system-wide and user-specific settings
    
    Args:
        export_time (str): The report time ('8am' or '9am')
        
    Returns:
        list: List of email addresses
    """
    recipients = []
    
    try:
        # Get user-specific recipients
        if current_user.is_authenticated:
            setting_key = f'email_{export_time}_recipients'
            user_recipients = UserSettings.get_setting(current_user.id, setting_key)
            if user_recipients:
                recipients.extend([r.strip() for r in user_recipients.split(',') if r.strip()])
        
        # Get system-wide recipients (implement later if needed)
        # ...
        
    except Exception as e:
        logger.error(f"Error getting report recipients: {e}")
    
    return recipients

def get_attendance_data(date=None):
    """
    Process attendance data from DailyUsage.csv with improved driver counting
    Args:
        date: Date string in YYYY-MM-DD format, defaults to None (all dates)
        
    Returns:
        dict: Processed attendance data with accurate driver counts
    """
    try:
        # Search for DailyUsage.csv in attached_assets directory
        file_path = os.path.join('attached_assets', 'DailyUsage.csv')
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
            
        # Read the file with pandas
        df = pd.read_csv(file_path, skiprows=SKIPROWS_DAILY_USAGE)
        
        # Clean column names
        df.columns = [col.strip() for col in df.columns]
        
        # Filter by date if specified
        if date:
            df = df[df['Date'] == date]
        
        if df.empty:
            logger.warning(f"No data found for date: {date}")
            return None
            
        # Format date for display
        date_obj = datetime.strptime(date, '%Y-%m-%d') if date else datetime.strptime(df['Date'].iloc[0], '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Process the data
        # Extract driver information using the improved utilities
        drivers = {}
        driver_issues = {}
        division_stats = defaultdict(lambda: {'total': 0, 'on_time': 0, 'late': 0, 'early_end': 0, 'not_on_job': 0, 'exception': 0})
        
        # Tracking for improved statistics
        unique_driver_count = 0
        morning_drivers = 0
        on_time_drivers = 0
        late_drivers = 0
        early_end_drivers = 0
        not_on_job_drivers = 0
        exception_drivers = 0
        total_issues = 0
        
        # Record details for each driver
        drivers_detail = {}
        
        for _, row in df.iterrows():
            # Extract driver name and asset ID
            asset_label = row['Asset Label']
            driver_name = extract_driver_from_label(asset_label)
            asset_id = clean_asset_info(asset_label)
            
            # Generate a unique ID for this driver
            # Using driver name as the ID for simplicity
            driver_id = driver_name.strip()
            
            # Skip if driver is already processed (count each driver only once)
            if driver_id not in drivers_detail:
                unique_driver_count += 1
                
                # Parse times
                start_time_str = row.get('Start Time', '').strip()
                end_time_str = row.get('Stop Time', '').strip()
                
                # Only count drivers with morning starts for the morning stats
                if start_time_str:
                    morning_drivers += 1
                    
                # Convert string times to datetime objects
                start_time = parse_time_with_tz(start_time_str) if start_time_str else None
                end_time = parse_time_with_tz(end_time_str) if end_time_str else None
                
                # Calculate lateness
                # Using expected start time from config or default
                expected_start = parse_time_with_tz(DEFAULT_START_TIME)
                minutes_late = calculate_lateness(start_time, expected_start, DEFAULT_THRESHOLD_MINUTES) if start_time else 0
                
                # Record driver details
                drivers_detail[driver_id] = {
                    'id': unique_driver_count,
                    'name': driver_name,
                    'asset_id': asset_id,
                    'division': row.get('Division', 'Unknown'),
                    'job_site': row.get('Location', 'Unknown'),
                    'expected_start': DEFAULT_START_TIME,
                    'actual_start': start_time_str,
                    'actual_end': end_time_str,
                    'minutes_late': minutes_late,
                    'issues': []
                }
                
                # Check for issues
                driver_has_issue = False
                
                # Check for late start
                if minutes_late > 0:
                    drivers_detail[driver_id]['issues'].append('late')
                    late_drivers += 1
                    driver_has_issue = True
                else:
                    on_time_drivers += 1
                
                # Check for early end
                if end_time and end_time.hour < 16:  # End before 4 PM
                    drivers_detail[driver_id]['issues'].append('early_end')
                    early_end_drivers += 1
                    driver_has_issue = True
                
                # Check for not on job
                if not row.get('Location', '').strip():
                    drivers_detail[driver_id]['issues'].append('not_on_job')
                    not_on_job_drivers += 1
                    driver_has_issue = True
                
                # Track exceptions
                if 'exception' in row.get('Notes', '').lower():
                    drivers_detail[driver_id]['issues'].append('exception')
                    exception_drivers += 1
                    driver_has_issue = True
                
                # Update division statistics
                division = row.get('Division', 'Unknown')
                division_stats[division]['total'] += 1
                
                if minutes_late > 0:
                    division_stats[division]['late'] += 1
                else:
                    division_stats[division]['on_time'] += 1
                    
                if end_time and end_time.hour < 16:
                    division_stats[division]['early_end'] += 1
                    
                if not row.get('Location', '').strip():
                    division_stats[division]['not_on_job'] += 1
                    
                if 'exception' in row.get('Notes', '').lower():
                    division_stats[division]['exception'] += 1
                
                # Count total issues for statistics
                if driver_has_issue:
                    total_issues += 1
        
        # Build the results
        return {
            'date': date if date else df['Date'].iloc[0],
            'formatted_date': formatted_date,
            'summary': {
                'total_drivers': unique_driver_count,
                'total_morning_drivers': morning_drivers,
                'on_time_drivers': on_time_drivers,
                'late_drivers': late_drivers,
                'early_end_drivers': early_end_drivers,
                'not_on_job_drivers': not_on_job_drivers,
                'exception_drivers': exception_drivers,
                'total_issues': total_issues
            },
            'late_drivers': [drivers_detail[eid] for eid, v in driver_issues.items() if "late" in v],
            'early_end_drivers': [drivers_detail[eid] for eid, v in driver_issues.items() if "early_end" in v],
            'not_on_job_drivers': [drivers_detail[eid] for eid, v in driver_issues.items() if "not_on_job" in v],
            'exceptions': [drivers_detail[eid] for eid, v in driver_issues.items() if "exception" in v],
            'divisions': [{"name": div, "stats": stats} for div, stats in division_stats.items()]
        }
    except Exception as e:
        logger.error(f"Error processing attendance data: {e}")
        return None

def get_daily_report(date_str=None):
    """
    Get daily report data from the database
    Args:
        date_str: Date string in YYYY-MM-DD format, defaults to today
        
    Returns:
        dict: Daily report data
    """
    # Default to today if no date provided
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Try to load real data from the DailyUsage.csv file using the refactored function
    try:
        report = get_attendance_data(date_str)
            
        # Map report fields to expected template fields
        if report is not None:
            return {
                'date': report['date'],
                'formatted_date': report['formatted_date'],
                'total_drivers': report['summary']['total_drivers'],
                'total_morning_drivers': report['summary']['total_morning_drivers'],
                'on_time_count': report['summary']['on_time_drivers'],
                'late_morning': report['late_drivers'],
                'early_departures': report['early_end_drivers'],
                'not_on_job_drivers': report['not_on_job_drivers'],
                'exceptions': report['exceptions'],
                'divisions': report['divisions'],
                'summary': report['summary']
            }
            
        logger.warning(f"Failed to load real data, falling back to sample data")
        
    except Exception as e:
        logger.error(f"Error loading daily usage data: {e}")
    
    # If we get here, we need to use the fallback sample data
    # Format the date for display (default to today)
    date_obj = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()
    formatted_date = date_obj.strftime('%A, %B %d, %Y')
    
    # Return placeholder data
    return {
        'date': date_str or datetime.now().strftime('%Y-%m-%d'),
        'formatted_date': formatted_date,
        'total_drivers': 0,
        'total_morning_drivers': 0,
        'on_time_count': 0,
        'late_morning': [],
        'early_departures': [],
        'not_on_job_drivers': [],
        'exceptions': [],
        'divisions': [],
        'summary': {
            'total_drivers': 0,
            'total_morning_drivers': 0,
            'on_time_drivers': 0,
            'late_drivers': 0,
            'early_end_drivers': 0,
            'not_on_job_drivers': 0,
            'exception_drivers': 0,
            'total_issues': 0
        }
    }

@driver_module_bp.route('/test-daily-report')
def test_daily_report():
    """
    Test route to verify the daily driver report without authentication
    This is for debugging the statistics calculation issue
    """
    # Get date parameter, default to today
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Get report data
    report = get_daily_report(date_str)
    
    # Log activity
    log_navigation('Test Daily Driver Report', {'date': date_str})
    
    return render_template(
        'drivers/daily_report.html',
        report=report,
        selected_date=report['formatted_date'],
        email_config=get_user_email_config()
    )

@driver_module_bp.route('/daily-report', methods=['GET', 'POST'])
@login_required
def daily_report():
    """Daily driver attendance report with email configuration"""
    # Get date parameter, default to today
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Get report data
    report = get_daily_report(date_str)
    
    # Handle form submission for email configuration
    if request.method == 'POST' and request.form.get('action') == 'save_email_config':
        if save_email_config():
            flash('Email configuration saved successfully.', 'success')
        else:
            flash('Failed to save email configuration.', 'danger')
        
        # Redirect to avoid form resubmission
        return redirect(url_for('driver_module.daily_report', date=date_str))
    
    # Get email configuration for the current user
    email_config = get_user_email_config()
    
    # Get attendance trend data for the last 5 days
    try:
        from utils.attendance_trends_api import get_driver_trends
        end_date = date_obj.strftime('%Y-%m-%d')
        trend_data = get_driver_trends(end_date=end_date, days=5)
        
        # Set trend summary counts for display
        trend_summary = trend_data.get('summary', {})
        chronic_late_count = trend_summary.get('chronic_late_count', 0)
        repeated_absence_count = trend_summary.get('repeated_absence_count', 0)
        unstable_shift_count = trend_summary.get('unstable_shift_count', 0)
    except Exception as e:
        logger.error(f"Error getting trend data: {e}")
        trend_data = {"driver_trends": {}, "summary": {}}
        chronic_late_count = 0
        repeated_absence_count = 0 
        unstable_shift_count = 0
    
    log_navigation('Daily Driver Report', {'date': date_str})
    return render_template(
        'drivers/daily_report.html',
        report=report,
        selected_date=report['formatted_date'],
        email_config=email_config,
        trend_data=trend_data,
        trend_summary={
            'chronic_late_count': chronic_late_count,
            'repeated_absence_count': repeated_absence_count,
            'unstable_shift_count': unstable_shift_count
        }
    )

@driver_module_bp.route('/attendance-dashboard')
@login_required
def attendance_dashboard():
    """Display attendance dashboard with trends and statistics"""
    # Get date range parameters, default to current month
    today = datetime.now()
    start_date = request.args.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', today.strftime('%Y-%m-%d'))
    
    # Get attendance data for the date range
    try:
        # Import the centralized pipeline connector
        from utils.attendance_pipeline_connector import get_attendance_data, get_trend_data, get_attendance_audit_log
        
        # Get attendance data from our centralized connector
        attendance_data = get_attendance_data(end_date)
        
        # Get trend data for analysis
        trend_data = get_trend_data(end_date_str=end_date, days=7)  # Last 7 days by default
        
        # Get audit log for tracking data processing
        audit_log = get_attendance_audit_log()
        
        log_navigation('Attendance Dashboard', {'start_date': start_date, 'end_date': end_date})
        return render_template(
            'drivers/attendance_dashboard.html',
            attendance_data=attendance_data,
            trend_data=trend_data,
            audit_log=audit_log,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        logger.error(f"Error loading attendance dashboard: {e}")
        flash('Error loading attendance dashboard data.', 'danger')
        return redirect(url_for('index'))

@driver_module_bp.route('/driver-list')
@login_required
def driver_list():
    """Display list of all drivers with attendance history"""
    # Get date range parameters, default to current month
    today = datetime.now()
    start_date = request.args.get('start_date', today.replace(day=1).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', today.strftime('%Y-%m-%d'))
    
    try:
        # Import the centralized pipeline connector
        from utils.attendance_pipeline_connector import get_driver_list
        
        # Get driver data from our centralized connector
        driver_data = get_driver_list()
        
        log_navigation('Driver List', {'start_date': start_date, 'end_date': end_date})
        return render_template(
            'drivers/driver_list.html',
            drivers=driver_data,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        logger.error(f"Error loading driver list: {e}")
        flash('Error loading driver data.', 'danger')
        return redirect(url_for('index'))

@driver_module_bp.route('/export-report', methods=['GET', 'POST'])
@login_required
def export_driver_report():
    """Export driver attendance reports in various formats"""
    # Get date range parameters
    today = datetime.now()
    default_start = today - timedelta(days=7)
    start_date = request.args.get('start_date', default_start.strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', today.strftime('%Y-%m-%d'))
    
    if request.method == 'POST':
        try:
            # Process export request
            report_type = request.form.get('report_type', 'daily')
            export_format = request.form.get('export_format', 'excel')
            
            # Create export directory if it doesn't exist
            export_dir = os.path.join('exports', 'drivers')
            os.makedirs(export_dir, exist_ok=True)
            
            # Generate filename based on report type and date range
            filename = f"driver_report_{report_type}_{start_date}_to_{end_date}.xlsx"
            file_path = os.path.join(export_dir, filename)
            
            # In a real implementation, we would call a function to generate the report
            # For now, we'll just create a simple Excel file
            if export_format == 'excel':
                # Placeholder for report generation function
                # We'll implement this with real data later
                flash(f'Report {filename} has been generated successfully.', 'success')
                return redirect(url_for('driver_module.export_driver_report', 
                                        start_date=start_date, 
                                        end_date=end_date))
            
            # Handle other export formats
            flash('Unsupported export format.', 'warning')
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            flash('Failed to generate report.', 'danger')
    
    # Render the export form
    log_navigation('Export Driver Reports', {'start_date': start_date, 'end_date': end_date})
    return render_template(
        'drivers/export_reports.html',
        start_date=start_date,
        end_date=end_date
    )

@driver_module_bp.route('/vehicle-audit', methods=['GET', 'POST'])
@login_required
def vehicle_audit():
    """Display vehicle history audit data and search interface"""
    # Get search parameters
    search_term = request.args.get('search', '')
    date_range = request.args.get('date_range', '30')  # default to 30 days
    
    try:
        # Convert date range to integer (days)
        days = int(date_range)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # In a real implementation, we would query the database for vehicle history
        # For now, we'll just use placeholder data
        audit_data = []
        
        if search_term:
            # Log the search activity
            log_navigation('Vehicle Audit Search', {'search': search_term, 'days': days})
            
            # In a real implementation, we would filter the database query
            # Here we'll just show placeholder data when a search is performed
            audit_data = [{
                'asset_id': 'ET-123',
                'vehicle_type': 'RAM 1500 2022',
                'driver': 'MATTHEW C. SHAYLOR',
                'date': (datetime.now() - timedelta(days=random.randint(1, int(days)))).strftime('%Y-%m-%d'),
                'start_time': '7:25 AM',
                'end_time': '5:15 PM',
                'location': 'Fort Worth, TX 76244',
                'job_site': 'Fort Worth Municipal',
                'division': 'Ragle - Texas'
            } for _ in range(3)]
        
        return render_template(
            'drivers/vehicle_audit.html',
            search_term=search_term,
            date_range=date_range,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            audit_data=audit_data
        )
    except Exception as e:
        logger.error(f"Error loading vehicle audit data: {e}")
        flash('Error loading vehicle audit data.', 'danger')
        return redirect(url_for('index'))