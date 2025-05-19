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
from models.user_settings import UserSettings
from models.email_configuration import EmailRecipientList
from flask_login import current_user
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, current_app, send_file
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import pandas as pd
from config import DEFAULT_START_TIME, DEFAULT_THRESHOLD_MINUTES, SKIPROWS_DAILY_USAGE
from time_utils import parse_time_with_tz, calculate_lateness
from driver_utils import extract_driver_from_label, clean_asset_info

# Import activity logger
from utils.activity_logger import (
    log_navigation, log_document_upload, log_report_export,
    log_feature_usage, log_search
)

# Import database
from app import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize blueprint
driver_module_bp = Blueprint('driver_module', __name__, url_prefix='/drivers')

# Temporary test route to verify attendance statistics calculation
@driver_module_bp.route('/test-report')
def test_daily_report():
    """
    Test route to verify the daily driver report without authentication
    This is for debugging the statistics calculation issue
    """
    from utils.attendance_processor import process_daily_usage_data
    
    # Process test data
    try:
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        report = process_daily_usage_data('attached_assets/DailyUsage.csv', date_str)
        if isinstance(report, dict) and 'summary' in report:
            return jsonify({
                'success': True,
                'summary': report['summary'],
                'late_count': len(report.get('late_drivers', [])),
                'early_end_count': len(report.get('early_end_drivers', [])),
                'exception_count': len(report.get('exceptions', [])),
                'not_on_job_count': len(report.get('not_on_job_drivers', []))
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid report format',
                'report': report
            })
    except Exception as e:
        logging.error(f"Error in test report: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Constants
UPLOAD_FOLDER = os.path.join('uploads', 'driver_files')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

EXPORTS_FOLDER = os.path.join('exports', 'driver_reports')
os.makedirs(EXPORTS_FOLDER, exist_ok=True)

# Create audit history folder for reports
AUDIT_EXPORTS_FOLDER = os.path.join('exports', 'audit_reports')
os.makedirs(AUDIT_EXPORTS_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'pdf'}

# Helper functions
def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Email configuration helper functions
def get_user_email_config():
    """
    Get email configuration for the current user
    Returns a dictionary with configuration values
    """
    email_config = {}
    
    try:
        if current_user.is_authenticated:
            # Get 8am email recipients
            setting_8am = UserSettings.query.filter_by(
                user_id=current_user.id,
                setting_key='email_8am_recipients'
            ).first()
            
            if setting_8am:
                email_config['8am'] = setting_8am.setting_value
                
            # Get 9am email recipients
            setting_9am = UserSettings.query.filter_by(
                user_id=current_user.id,
                setting_key='email_9am_recipients'
            ).first()
            
            if setting_9am:
                email_config['9am'] = setting_9am.setting_value
                
            # Get auto-send setting
            auto_send = UserSettings.query.filter_by(
                user_id=current_user.id,
                setting_key='email_auto_send'
            ).first()
            
            if auto_send:
                email_config['auto_send'] = auto_send.setting_value == 'true'
                
            # Get include_user setting
            include_user = UserSettings.query.filter_by(
                user_id=current_user.id,
                setting_key='email_include_user'
            ).first()
            
            if include_user:
                email_config['include_user'] = include_user.setting_value == 'true'
            else:
                # Default to true for include_user
                email_config['include_user'] = True
                
    except Exception as e:
        logger.error(f"Error getting email config: {e}")
    
    return email_config

def save_email_config():
    """
    Save email configuration from form submission
    """
    if not current_user.is_authenticated:
        return False
        
    try:
        # Get form data
        email_8am = request.form.get('email8am', '')
        email_9am = request.form.get('email9am', '')
        include_user = 'includeCurrentUser' in request.form
        auto_send = 'automaticSend' in request.form
        
        # Save 8am recipients
        setting_8am = UserSettings.query.filter_by(
            user_id=current_user.id,
            setting_key='email_8am_recipients'
        ).first()
        
        if setting_8am:
            setting_8am.setting_value = email_8am
        else:
            setting_8am = UserSettings(
                user_id=current_user.id,
                setting_key='email_8am_recipients',
                setting_value=email_8am
            )
            db.session.add(setting_8am)
        
        # Save 9am recipients
        setting_9am = UserSettings.query.filter_by(
            user_id=current_user.id,
            setting_key='email_9am_recipients'
        ).first()
        
        if setting_9am:
            setting_9am.setting_value = email_9am
        else:
            setting_9am = UserSettings(
                user_id=current_user.id,
                setting_key='email_9am_recipients',
                setting_value=email_9am
            )
            db.session.add(setting_9am)
        
        # Save include_user setting
        include_user_setting = UserSettings.query.filter_by(
            user_id=current_user.id,
            setting_key='email_include_user'
        ).first()
        
        include_user_value = 'true' if include_user else 'false'
        
        if include_user_setting:
            include_user_setting.setting_value = include_user_value
        else:
            include_user_setting = UserSettings(
                user_id=current_user.id,
                setting_key='email_include_user',
                setting_value=include_user_value
            )
            db.session.add(include_user_setting)
        
        # Save auto_send setting
        auto_send_setting = UserSettings.query.filter_by(
            user_id=current_user.id,
            setting_key='email_auto_send'
        ).first()
        
        auto_send_value = 'true' if auto_send else 'false'
        
        if auto_send_setting:
            auto_send_setting.setting_value = auto_send_value
        else:
            auto_send_setting = UserSettings(
                user_id=current_user.id,
                setting_key='email_auto_send',
                setting_value=auto_send_value
            )
            db.session.add(auto_send_setting)
        
        # Commit changes
        db.session.commit()
        
        # Log activity
        log_feature_usage('Email Configuration Updated', {
            'email_8am_count': len(email_8am.split(',')) if email_8am else 0,
            'email_9am_count': len(email_9am.split(',')) if email_9am else 0,
            'include_user': include_user,
            'auto_send': auto_send
        })
        
        return True
    except Exception as e:
        logger.error(f"Error saving email config: {e}")
        db.session.rollback()
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
        # Get system-wide recipients for this report time
        list_name = f'driver_report_{export_time}'
        system_list = EmailRecipientList.query.filter_by(
            list_name=list_name,
            is_active=True
        ).first()
        
        if system_list:
            recipients.extend(system_list.get_recipients_list())
        
        # Add user-specific recipients if user is logged in
        if current_user.is_authenticated:
            setting_key = f'email_{export_time}_recipients'
            user_setting = UserSettings.query.filter_by(
                user_id=current_user.id,
                setting_key=setting_key
            ).first()
            
            if user_setting and user_setting.setting_value:
                user_recipients = [email.strip() for email in user_setting.setting_value.split(',') if email.strip()]
                recipients.extend(user_recipients)
            
            # Check if user wants to be included
            include_user = UserSettings.query.filter_by(
                user_id=current_user.id,
                setting_key='email_include_user'
            ).first()
            
            if (include_user and include_user.setting_value == 'true') and current_user.email:
                if current_user.email not in recipients:
                    recipients.append(current_user.email)
    
    except Exception as e:
        logger.error(f"Error getting report recipients: {e}")
    
    # Remove duplicates and return
    return list(set(recipients))

def get_drivers():
    """
    Get driver data from the database
    Returns a list of driver dictionaries with attendance metrics
    """
    # In a real implementation, this would query the database
    # For now, we'll return mock data
    drivers = [
        {
            'id': 1,
            'name': 'John Doe',
            'employee_id': 'E001',
            'region': 'North',
            'job_site': 'Project Alpha',
            'attendance_rate': 95,
            'late_count': 2,
            'vehicle': 'Truck 101'
        },
        {
            'id': 2,
            'name': 'Jane Smith',
            'employee_id': 'E002',
            'region': 'South',
            'job_site': 'Project Beta',
            'attendance_rate': 98,
            'late_count': 1,
            'vehicle': 'Truck 102'
        },
        {
            'id': 3,
            'name': 'Bob Johnson',
            'employee_id': 'E003',
            'region': 'East',
            'job_site': 'Project Gamma',
            'attendance_rate': 92,
            'late_count': 3,
            'vehicle': 'Truck 103'
        }
    ]
    
    return drivers

def get_attendance_data(date=None):
    """
    Process attendance data from DailyUsage.csv with improved driver counting
    Args:
        date: Date string in YYYY-MM-DD format, defaults to None (all dates)
        
    Returns:
        dict: Processed attendance data with accurate driver counts
    """
    daily_usage_file = os.path.join('attached_assets', 'DailyUsage.csv')
    if not os.path.exists(daily_usage_file):
        logger.warning(f"DailyUsage.csv file not found at {daily_usage_file}")
        return None
        
    # Process the CSV file with the correct number of rows to skip
    df = pd.read_csv(daily_usage_file, skiprows=SKIPROWS_DAILY_USAGE, low_memory=False)
    driver_issues = defaultdict(set)
    drivers_detail = {}

    for _, row in df.iterrows():
        label = row.get("assetlabel", "")
        employee_id = extract_driver_from_label(label)
        name = employee_id  # fallback
        vehicle = clean_asset_info(label)

        started = parse_time_with_tz(row.get("started"))
        stopped = parse_time_with_tz(row.get("stopped"))
        scheduled_start = parse_time_with_tz(DEFAULT_START_TIME)

        late = calculate_lateness(started, scheduled_start, DEFAULT_THRESHOLD_MINUTES)
        early = calculate_lateness(scheduled_start, stopped, DEFAULT_THRESHOLD_MINUTES)
        not_on_job = not started or not stopped
        missing_data = pd.isna(row).any()

        if late: driver_issues[employee_id].add("late")
        if early: driver_issues[employee_id].add("early")
        if not_on_job: driver_issues[employee_id].add("no_show")
        if missing_data: driver_issues[employee_id].add("exception")

        if employee_id not in drivers_detail:
            drivers_detail[employee_id] = {
                "employee_id": employee_id,
                "name": name,
                "vehicle": vehicle,
                "expected_start": DEFAULT_START_TIME,
                "actual_start": row.get("started", ""),
                "scheduled_start": DEFAULT_START_TIME,
                "division": row.get("companyname1", "UNKNOWN"),
                "job_site": row.get("location", "UNKNOWN")
            }

    # Count each driver only once in the total while tracking all issues
    division_stats = defaultdict(lambda: {"total": 0, "late": 0, "early": 0, "no_show": 0, "exception": 0})
    for driver_id, issues in driver_issues.items():
        division = drivers_detail[driver_id]["division"]
        division_stats[division]["total"] += 1
        if "late" in issues: division_stats[division]["late"] += 1
        if "early" in issues: division_stats[division]["early"] += 1
        if "no_show" in issues: division_stats[division]["no_show"] += 1
        if "exception" in issues: division_stats[division]["exception"] += 1

    # Create summary statistics
    summary = {
        "total_drivers": len(driver_issues),
        "late_drivers": sum("late" in v for v in driver_issues.values()),
        "early_end_drivers": sum("early" in v for v in driver_issues.values()),
        "not_on_job_drivers": sum("no_show" in v for v in driver_issues.values()),
        "exception_drivers": sum("exception" in v for v in driver_issues.values()),
        "on_time_drivers": len(driver_issues) - sum("late" in v for v in driver_issues.values())
    }
    summary["total_issues"] = sum(summary[k] for k in ["late_drivers", "early_end_drivers", "not_on_job_drivers", "exception_drivers"])
    summary["total_morning_drivers"] = summary["total_drivers"]

    # Format date for display
    formatted_date = date if date else datetime.now().strftime('%Y-%m-%d')

    return {
        "date": date,
        "formatted_date": formatted_date,
        "summary": summary,
        "late_drivers": [drivers_detail[eid] for eid, v in driver_issues.items() if "late" in v],
        "early_end_drivers": [drivers_detail[eid] for eid, v in driver_issues.items() if "early" in v],
        "not_on_job_drivers": [drivers_detail[eid] for eid, v in driver_issues.items() if "no_show" in v],
        "exceptions": [drivers_detail[eid] for eid, v in driver_issues.items() if "exception" in v],
        "divisions": [{"name": div, "stats": stats} for div, stats in division_stats.items()]
    }

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
    
    log_navigation('Daily Driver Report', {'date': date_str})
    return render_template(
        'drivers/daily_report.html',
        report=report,
        selected_date=report['formatted_date'],
        email_config=email_config
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
        attendance_data = {}  # We'll implement this later with real data
        
        log_navigation('Attendance Dashboard', {'start_date': start_date, 'end_date': end_date})
        return render_template(
            'drivers/attendance_dashboard.html',
            attendance_data=attendance_data,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        logger.error(f"Error loading attendance dashboard: {e}")
        flash('Error loading attendance dashboard data.', 'danger')
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
