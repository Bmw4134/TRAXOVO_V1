"""
Driver Module Routes

This module contains routes for the driver module, handling driver attendance reports,
driver lists, and related functionality.
"""

import os
import sys
import json
import logging
import traceback
import pandas as pd
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

# Logger setup
logger = logging.getLogger(__name__)

# Blueprint definition
driver_module_bp = Blueprint('driver_module', __name__, url_prefix='/drivers')

# Create error log directory
os.makedirs('logs', exist_ok=True)
error_log_path = 'logs/errors.log'

# Configure error logging
error_logger = logging.getLogger('error_logger')
if not error_logger.handlers:
    file_handler = logging.FileHandler(error_log_path)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    error_logger.addHandler(file_handler)
    error_logger.setLevel(logging.ERROR)

# Attendance Report Helper Functions
def get_daily_report(date_str=None):
    """Get daily attendance report with verified employee data only"""
    if date_str is None:
        # Default to current date
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Check if report JSON file exists
    json_path = f"exports/daily_reports/daily_report_{date_str}.json"
    
    try:
        # First try to load from existing report file
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                report_data = json.load(f)
            
            if report_data.get('drivers') and len(report_data.get('drivers', [])) > 0:
                logger.info(f"Loaded report data from JSON for date {date_str}")
                
                # Create summary data for display
                summary = {
                    'total_drivers': len(report_data.get('drivers', [])),
                    'total_morning_drivers': len(report_data.get('drivers', [])),
                    'on_time_drivers': sum(1 for d in report_data.get('drivers', []) if d.get('status') == 'On Time'),
                    'late_drivers': sum(1 for d in report_data.get('drivers', []) if d.get('status') == 'Late'),
                    'early_end_drivers': sum(1 for d in report_data.get('drivers', []) if d.get('status') == 'Early Departure'),
                    'not_on_job_drivers': sum(1 for d in report_data.get('drivers', []) if d.get('status') == 'Not On Job'),
                    'exception_drivers': 0,
                    'total_issues': 0,
                    'on_time_percent': 0
                }
                
                # Calculate total issues and on-time percentage
                summary['total_issues'] = (summary['late_drivers'] + 
                                          summary['early_end_drivers'] + 
                                          summary['not_on_job_drivers'])
                
                if summary['total_drivers'] > 0:
                    summary['on_time_percent'] = int((summary['on_time_drivers'] / summary['total_drivers']) * 100)
                
                # Create categorized lists
                late_morning = [d for d in report_data.get('drivers', []) if d.get('status') == 'Late']
                early_departures = [d for d in report_data.get('drivers', []) if d.get('status') == 'Early Departure']
                not_on_job = [d for d in report_data.get('drivers', []) if d.get('status') == 'Not On Job']
                
                # Build the enhanced report structure
                return {
                    'date': date_str,
                    'formatted_date': report_data.get('report_date'),
                    'total_drivers': len(report_data.get('drivers', [])),
                    'total_morning_drivers': len(report_data.get('drivers', [])),
                    'on_time_count': summary['on_time_drivers'],
                    'drivers': report_data.get('drivers', []),
                    'late_morning': late_morning,
                    'early_departures': early_departures,
                    'not_on_job_drivers': not_on_job,
                    'summary': summary
                }
        
        # If we get here, either file doesn't exist or it has no drivers
        # Generate the report with authentic employee data
        logger.info(f"Generating new report with authentic employee data for {date_str}")
        
        # Import here to avoid circular imports
        from reports_processor import process_report_for_date
        
        # Process the report with verified employee data
        if process_report_for_date(date_str):
            # Load the newly generated report
            with open(json_path, 'r') as f:
                report_data = json.load(f)
            
            # Return with the same structure as above
            if report_data.get('drivers'):
                summary = {
                    'total_drivers': len(report_data.get('drivers', [])),
                    'total_morning_drivers': len(report_data.get('drivers', [])),
                    'on_time_drivers': sum(1 for d in report_data.get('drivers', []) if d.get('status') == 'On Time'),
                    'late_drivers': sum(1 for d in report_data.get('drivers', []) if d.get('status') == 'Late'),
                    'early_end_drivers': sum(1 for d in report_data.get('drivers', []) if d.get('status') == 'Early Departure'),
                    'not_on_job_drivers': sum(1 for d in report_data.get('drivers', []) if d.get('status') == 'Not On Job'),
                    'exception_drivers': 0,
                    'total_issues': 0,
                    'on_time_percent': 0
                }
                
                summary['total_issues'] = (summary['late_drivers'] + 
                                          summary['early_end_drivers'] + 
                                          summary['not_on_job_drivers'])
                
                if summary['total_drivers'] > 0:
                    summary['on_time_percent'] = int((summary['on_time_drivers'] / summary['total_drivers']) * 100)
                
                late_morning = [d for d in report_data.get('drivers', []) if d.get('status') == 'Late']
                early_departures = [d for d in report_data.get('drivers', []) if d.get('status') == 'Early Departure']
                not_on_job = [d for d in report_data.get('drivers', []) if d.get('status') == 'Not On Job']
                
                return {
                    'date': date_str,
                    'formatted_date': report_data.get('report_date'),
                    'total_drivers': len(report_data.get('drivers', [])),
                    'total_morning_drivers': len(report_data.get('drivers', [])),
                    'on_time_count': summary['on_time_drivers'],
                    'drivers': report_data.get('drivers', []),
                    'late_morning': late_morning,
                    'early_departures': early_departures,
                    'not_on_job_drivers': not_on_job,
                    'summary': summary
                }
    
    except Exception as e:
        error_msg = f"Error loading or generating report for {date_str}: {str(e)}"
        logger.error(error_msg)
        error_logger.error(error_msg)
        traceback.print_exc()
    
    # If we reach here, return an empty report structure
    # No synthetic data, just empty placeholders
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    formatted_date = date_obj.strftime('%A, %B %d, %Y')
    
    return {
        'date': date_str,
        'formatted_date': formatted_date,
        'total_drivers': 0,
        'total_morning_drivers': 0,
        'on_time_count': 0,
        'drivers': [],
        'late_morning': [],
        'early_departures': [],
        'not_on_job_drivers': [],
        'summary': {
            'total_drivers': 0,
            'total_morning_drivers': 0,
            'on_time_drivers': 0,
            'late_drivers': 0,
            'early_end_drivers': 0,
            'not_on_job_drivers': 0,
            'exception_drivers': 0,
            'total_issues': 0,
            'on_time_percent': 0
        },
        'error': "Could not generate report with authentic employee data"
    }
        
def get_user_email_config():
    """Get user's email configuration"""
    try:
        # Default configuration
        config = {
            'recipients': '',
            'cc': '',
            'bcc': '',
            'auto_send': False,
            'include_user': True
        }
        
        # Get from database if user is authenticated
        if current_user and current_user.is_authenticated:
            from models.user_settings import get_user_setting
            
            try:
                config['recipients'] = get_user_setting(current_user.id, 'email_recipients', '')
            except:
                pass
                
            try:
                config['cc'] = get_user_setting(current_user.id, 'email_cc', '')
            except:
                pass
                
            try:
                config['bcc'] = get_user_setting(current_user.id, 'email_bcc', '')
            except:
                pass
                
            try:
                config['auto_send'] = get_user_setting(current_user.id, 'email_auto_send', 'false').lower() == 'true'
            except:
                pass
                
            try:
                config['include_user'] = get_user_setting(current_user.id, 'email_include_user', 'true').lower() == 'true'
            except:
                pass
            
        return config
    except Exception as e:
        logger.error(f"Error getting user email config: {e}")
        return {
            'recipients': '',
            'cc': '',
            'bcc': '',
            'auto_send': False,
            'include_user': True
        }

def save_user_email_config(config):
    """Save user's email configuration"""
    try:
        if current_user and current_user.is_authenticated:
            from models.user_settings import set_user_setting
            
            set_user_setting(current_user.id, 'email_recipients', config.get('recipients', ''))
            set_user_setting(current_user.id, 'email_cc', config.get('cc', ''))
            set_user_setting(current_user.id, 'email_bcc', config.get('bcc', ''))
            set_user_setting(current_user.id, 'email_auto_send', 'true' if config.get('auto_send', False) else 'false')
            set_user_setting(current_user.id, 'email_include_user', 'true' if config.get('include_user', True) else 'false')
            
            return True
    except Exception as e:
        logger.error(f"Error saving user email config: {e}")
    
    return False

# Activity logging
def log_navigation(action, details=None):
    """Log navigation to activity log"""
    try:
        from utils.activity_logger import log_activity
        log_activity('navigation', f'Viewed {action}', details or {})
    except Exception as e:
        logger.error(f"Error logging navigation: {e}")

# Routes
@driver_module_bp.route('/')
@login_required
def index():
    """Driver module index page"""
    log_navigation('Driver Module')
    return render_template('drivers/index.html')

@driver_module_bp.route('/daily-report', methods=['GET', 'POST'])
@login_required
def daily_report():
    """Daily driver attendance report with email configuration"""
    # Get date parameter with safe fallback
    try:
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    except Exception as e:
        error_msg = f"Error getting date parameter: {e}"
        logger.error(error_msg)
        error_logger.error(error_msg)
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Create fallback report structure
    fallback_report = {
        'date': date_str,
        'formatted_date': datetime.strptime(date_str, '%Y-%m-%d').strftime('%A, %B %d, %Y'),
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
            'total_issues': 0,
            'on_time_percent': 0
        }
    }
    
    # Initialize report with fallback
    report = fallback_report.copy()
    
    # Process form submission if applicable
    if request.method == 'POST' and request.form.get('action') == 'update_email':
        try:
            # Update email settings
            config = {
                'recipients': request.form.get('recipients', ''),
                'cc': request.form.get('cc', ''),
                'bcc': request.form.get('bcc', ''),
                'auto_send': request.form.get('auto_send') == 'on',
                'include_user': request.form.get('include_user') == 'on'
            }
            
            if save_user_email_config(config):
                flash('Email configuration updated successfully', 'success')
            else:
                flash('Failed to update email configuration', 'error')
                
            # Redirect to avoid form resubmission
            return redirect(url_for('driver_module.daily_report', date=date_str))
        except Exception as e:
            error_msg = f"Error processing form: {e}"
            logger.error(error_msg)
            error_logger.error(error_msg)
            flash('An error occurred while updating email configuration', 'error')
    
    # Get email configuration for the current user
    try:
        email_config = get_user_email_config()
    except Exception as e:
        logger.warning(f"Error loading email config: {e}")
        email_config = {
            'recipients': '',
            'cc': '',
            'bcc': '',
            'auto_send': False,
            'include_user': True
        }
    
    # Import attendance pipeline connector for modern data processing
    try:
        from utils.attendance_pipeline_connector import get_attendance_data as get_pipeline_attendance_data
        
        # Get data from the pipeline with error handling
        attendance_data = None
        try:
            attendance_data = get_pipeline_attendance_data(date_str, force_refresh=False)
        except Exception as pipeline_error:
            error_msg = f"Error getting pipeline data: {pipeline_error}"
            logger.error(error_msg)
            error_logger.error(error_msg)
        
        # Process data if we got it successfully
        if attendance_data and attendance_data.get('date') == date_str:
            # Successfully retrieved data from the pipeline
            logger.info(f"Using data from attendance pipeline for {date_str}")
            
            # Map pipeline fields to report format with safe gets
            try:
                report = {
                    'date': attendance_data.get('date', date_str),
                    'formatted_date': datetime.strptime(attendance_data.get('date', date_str), '%Y-%m-%d').strftime('%A, %B %d, %Y'),
                    'total_drivers': attendance_data.get('total_drivers', 0),
                    'total_morning_drivers': attendance_data.get('total_drivers', 0),
                    'on_time_count': max(0, attendance_data.get('total_drivers', 0) - attendance_data.get('late_count', 0) - attendance_data.get('missing_count', 0)),
                    'late_morning': attendance_data.get('late_start_records', []),
                    'early_departures': attendance_data.get('early_end_records', []),
                    'not_on_job_drivers': attendance_data.get('not_on_job_records', []),
                    'exceptions': [],
                    'divisions': [],
                    'summary': {
                        'total_drivers': attendance_data.get('total_drivers', 0),
                        'total_morning_drivers': attendance_data.get('total_drivers', 0),
                        'on_time_drivers': max(0, attendance_data.get('total_drivers', 0) - attendance_data.get('late_count', 0) - attendance_data.get('missing_count', 0)),
                        'late_drivers': attendance_data.get('late_count', 0),
                        'early_end_drivers': attendance_data.get('early_count', 0),
                        'not_on_job_drivers': attendance_data.get('missing_count', 0),
                        'exception_drivers': 0,
                        'total_issues': attendance_data.get('late_count', 0) + attendance_data.get('early_count', 0) + attendance_data.get('missing_count', 0),
                        'on_time_percent': attendance_data.get('on_time_percent', 0)
                    }
                }
            except Exception as mapping_error:
                error_msg = f"Error mapping attendance data: {mapping_error}"
                logger.error(error_msg)
                error_logger.error(error_msg)
                report = fallback_report.copy()
        else:
            # Fall back to legacy method
            logger.warning(f"No data from attendance pipeline for {date_str}, using legacy method")
            try:
                report = get_daily_report(date_str)
            except Exception as legacy_error:
                error_msg = f"Legacy data retrieval failed: {legacy_error}"
                logger.error(error_msg)
                error_logger.error(error_msg)
                report = fallback_report.copy()
    except Exception as e:
        error_msg = f"Critical error in daily report processing: {e}"
        logger.error(error_msg)
        error_logger.error(error_msg)
        report = fallback_report.copy()
    
    # Get attendance trend data for the last 5 days
    try:
        from utils.attendance_trends_api import get_driver_trends
        # Parse date string into date_obj
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
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
        chronic_late_count=chronic_late_count,
        repeated_absence_count=repeated_absence_count,
        unstable_shift_count=unstable_shift_count
    )