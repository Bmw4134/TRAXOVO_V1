"""
Driver Module Controller

This module provides routes and functionality for the Driver module,
including daily reports, attendance tracking, and driver management.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from models.user_settings import UserSettings
from models.email_configuration import EmailRecipientList
from flask_login import current_user
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

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

# Constants
UPLOAD_FOLDER = os.path.join('uploads', 'driver_files')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

EXPORTS_FOLDER = os.path.join('exports', 'driver_reports')
os.makedirs(EXPORTS_FOLDER, exist_ok=True)

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
    
    # Convert date string to datetime object
    report_date = datetime.strptime(date_str, '%Y-%m-%d')
    formatted_date = report_date.strftime('%A, %B %d, %Y')
    
    # In a real implementation, this would query the database for the specific date
    # For now, we'll return mock data
    report = {
        'date': date_str,
        'formatted_date': formatted_date,
        'total_drivers': 25,
        'total_morning_drivers': 20,
        'on_time_count': 18,
        'late_morning': [
            {
                'id': 1,
                'employee_id': 'E001',
                'name': 'John Doe',
                'region': 'North',
                'job_site': 'Project Alpha',
                'expected_start': '7:00 AM',
                'actual_start': '7:15 AM',
                'minutes_late': 15,
                'vehicle': 'Truck 101'
            },
            {
                'id': 2,
                'employee_id': 'E002',
                'name': 'Jane Smith',
                'region': 'South',
                'job_site': 'Project Beta',
                'expected_start': '7:00 AM',
                'actual_start': '7:25 AM',
                'minutes_late': 25,
                'vehicle': 'Truck 102'
            }
        ],
        'early_departures': [
            {
                'id': 3,
                'employee_id': 'E003',
                'name': 'Bob Johnson',
                'region': 'East',
                'job_site': 'Project Gamma',
                'expected_end': '5:00 PM',
                'actual_end': '4:30 PM',
                'minutes_early': 30,
                'vehicle': 'Truck 103'
            }
        ],
        'not_on_job_drivers': [
            {
                'id': 4,
                'employee_id': 'E004',
                'name': 'Alice Williams',
                'region': 'West',
                'job_site': 'Project Delta',
                'scheduled_start': '7:00 AM',
                'vehicle': 'Truck 104',
                'reason': 'Sick Leave',
                'notes': 'Called in sick at 6:30 AM'
            }
        ],
        'exceptions': [
            {
                'id': 5,
                'employee_id': 'E005',
                'name': 'Charlie Brown',
                'region': 'Central',
                'job_site': 'Project Epsilon',
                'expected_time': '7:00 AM',
                'actual_time': 'No Data',
                'exception_type': 'Missing GPS Data',
                'vehicle': 'Truck 105'
            }
        ]
    }
    
    return report

def get_attendance_stats(days=30):
    """
    Get attendance statistics from the database for dashboard
    
    Args:
        days (int): Number of days to include in statistics
        
    Returns:
        dict: Attendance statistics
    """
    # In a real implementation, this would query the database
    # For now, we'll return mock data
    stats = {
        'attendance_rate': 94.5,
        'on_time_rate': 92.3,
        'late_trend': [-0.5, 0.1, 0.3, -0.2, -0.1, -0.3, -0.4],
        'absence_trend': [1.2, 1.0, 0.8, 1.1, 0.9, 0.7, 0.6],
        'worst_sites': [
            {'name': 'Project Alpha', 'late_rate': 12.5},
            {'name': 'Project Delta', 'late_rate': 10.2},
            {'name': 'Project Zeta', 'late_rate': 9.7}
        ],
        'best_sites': [
            {'name': 'Project Gamma', 'on_time_rate': 98.2},
            {'name': 'Project Beta', 'on_time_rate': 97.5},
            {'name': 'Project Epsilon', 'on_time_rate': 96.8}
        ]
    }
    
    return stats

# Routes
@driver_module_bp.route('/')
@login_required
def index():
    """Driver module home page"""
    log_navigation('Driver Module Home')
    return render_template('drivers/index.html')

@driver_module_bp.route('/daily-report')
@login_required
def daily_report():
    """Daily driver attendance report with email configuration"""
    # Get date parameter, default to today
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Get report data
    report = get_daily_report(date_str)
    
    # Get email configuration for the current user
    email_config = get_user_email_config()
    
    # Check for form submission
    if request.method == 'POST' and request.form.get('action') == 'save_email_config':
        if save_email_config():
            flash('Email configuration saved successfully.', 'success')
        else:
            flash('Failed to save email configuration.', 'danger')
        
        # Redirect to avoid form resubmission
        return redirect(url_for('driver_module.daily_report', date=date_str))
    
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
    """Attendance dashboard with trends and metrics"""
    # Get days parameter, default to 30
    days = int(request.args.get('days', 30))
    
    # Get attendance statistics
    stats = get_attendance_stats(days)
    
    log_navigation('Attendance Dashboard', {'days': days})
    return render_template(
        'drivers/attendance_dashboard.html',
        stats=stats,
        days=days
    )

@driver_module_bp.route('/drivers')
@login_required
def driver_list():
    """List all drivers with filtering options"""
    # Get filter parameters
    region = request.args.get('region')
    job_site = request.args.get('job_site')
    
    # Get drivers
    drivers = get_drivers()
    
    # Apply filters if provided
    if region:
        drivers = [d for d in drivers if d['region'] == region]
    if job_site:
        drivers = [d for d in drivers if d['job_site'] == job_site]
    
    log_navigation('Driver List', {'region': region, 'job_site': job_site})
    return render_template(
        'drivers/driver_list.html',
        drivers=drivers,
        region=region,
        job_site=job_site
    )

@driver_module_bp.route('/driver/<int:driver_id>')
@login_required
def driver_detail(driver_id):
    """Driver detail page with attendance history"""
    # In a real implementation, this would query the database
    # For now, we'll generate mock data based on the ID
    driver = {
        'id': driver_id,
        'name': f'Driver {driver_id}',
        'employee_id': f'E{driver_id:03d}',
        'region': 'North',
        'job_site': 'Project Alpha',
        'attendance_rate': 95,
        'late_count': 2,
        'vehicle': f'Truck {driver_id:03d}',
        'attendance_history': [
            {'date': '2025-05-18', 'status': 'On Time', 'start_time': '6:55 AM', 'end_time': '5:03 PM'},
            {'date': '2025-05-17', 'status': 'Late', 'start_time': '7:15 AM', 'end_time': '5:00 PM'},
            {'date': '2025-05-16', 'status': 'On Time', 'start_time': '6:58 AM', 'end_time': '4:58 PM'},
            {'date': '2025-05-15', 'status': 'On Time', 'start_time': '6:52 AM', 'end_time': '5:05 PM'},
            {'date': '2025-05-14', 'status': 'Absent', 'start_time': 'N/A', 'end_time': 'N/A'},
        ]
    }
    
    log_navigation('Driver Detail', {'driver_id': driver_id})
    return render_template(
        'drivers/driver_detail.html',
        driver=driver
    )

@driver_module_bp.route('/job-site/<int:site_id>')
@login_required
def job_site_detail(site_id):
    """Job site detail page with attendance metrics"""
    # In a real implementation, this would query the database
    # For now, we'll generate mock data based on the ID
    site = {
        'id': site_id,
        'name': f'Project {site_id}',
        'region': 'North',
        'attendance_rate': 93.5,
        'on_time_rate': 91.2,
        'drivers': [
            {'id': 1, 'name': 'John Doe', 'on_time_rate': 95.0},
            {'id': 2, 'name': 'Jane Smith', 'on_time_rate': 98.0},
            {'id': 3, 'name': 'Bob Johnson', 'on_time_rate': 92.0}
        ],
        'attendance_history': [
            {'date': '2025-05-18', 'on_time': 18, 'late': 2, 'absent': 0},
            {'date': '2025-05-17', 'on_time': 17, 'late': 3, 'absent': 0},
            {'date': '2025-05-16', 'on_time': 19, 'late': 0, 'absent': 1},
            {'date': '2025-05-15', 'on_time': 18, 'late': 1, 'absent': 1},
            {'date': '2025-05-14', 'on_time': 16, 'late': 4, 'absent': 0},
        ]
    }
    
    # Set up date ranges for filtering
    current_date = datetime.now()
    
    # Current week
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # Current month
    def get_first_day_of_month(date):
        return date.replace(day=1)
    
    def get_last_day_of_month(date):
        next_month = date.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)
    
    start_of_month = get_first_day_of_month(current_date)
    end_of_month = get_last_day_of_month(current_date)
    
    log_navigation('Job Site Detail', {'site_id': site_id})
    return render_template(
        'drivers/job_site_detail.html',
        site=site,
        date_ranges={
            'week': {
                'start': start_of_week.strftime('%Y-%m-%d'),
                'end': end_of_week.strftime('%Y-%m-%d')
            },
            'month': {
                'start': start_of_month.strftime('%Y-%m-%d'),
                'end': end_of_month.strftime('%Y-%m-%d')
            }
        }
    )

@driver_module_bp.route('/region/<int:region_id>')
@login_required
def region_detail(region_id):
    """Region detail page with attendance metrics"""
    # In a real implementation, this would query the database
    # For now, we'll generate mock data based on the ID
    region = {
        'id': region_id,
        'name': f'Region {region_id}',
        'attendance_rate': 94.8,
        'on_time_rate': 92.5,
        'job_sites': [
            {'id': 1, 'name': 'Project Alpha', 'on_time_rate': 93.5},
            {'id': 2, 'name': 'Project Beta', 'on_time_rate': 97.0},
            {'id': 3, 'name': 'Project Gamma', 'on_time_rate': 91.5}
        ],
        'attendance_history': [
            {'date': '2025-05-18', 'on_time': 48, 'late': 5, 'absent': 2},
            {'date': '2025-05-17', 'on_time': 47, 'late': 6, 'absent': 2},
            {'date': '2025-05-16', 'on_time': 50, 'late': 2, 'absent': 3},
            {'date': '2025-05-15', 'on_time': 49, 'late': 3, 'absent': 3},
            {'date': '2025-05-14', 'on_time': 46, 'late': 7, 'absent': 2},
        ]
    }
    
    log_navigation('Region Detail', {'region_id': region_id})
    return render_template(
        'drivers/region_detail.html',
        region=region
    )

@driver_module_bp.route('/upload-attendance', methods=['GET', 'POST'])
@login_required
def upload_attendance():
    """Upload attendance file for processing"""
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            # Log the upload
            log_document_upload('Attendance File', {'filename': filename})
            
            # Try to process the file
            from utils.attendance_processor import process_attendance_file
            
            # Create import log entry
            from models.attendance import AttendanceImportLog
            import_log = AttendanceImportLog(
                filename=filename,
                file_path=file_path,
                uploaded_by=current_user.id,
                import_date=datetime.now()
            )
            
            try:
                # Process the file
                result = process_attendance_file(file_path)
                
                # Update import log
                import_log.success = True
                import_log.status = f"Processed {result['total_records']} records"
                db.session.add(import_log)
                db.session.commit()
                
                flash(f"Successfully processed {result['total_records']} attendance records", 'success')
            except Exception as e:
                # Log the error
                import_log.success = False
                import_log.status = f"Error: {str(e)}"
                db.session.add(import_log)
                db.session.commit()
                
                flash(f"Error processing file: {str(e)}", 'danger')
            
            return redirect(url_for('driver_module.daily_report'))
    
    # GET request - show upload form
    return render_template('drivers/upload.html')

@driver_module_bp.route('/export-report')
@login_required
def export_report():
    """Redirect to the dedicated export route"""
    report_type = request.args.get('type', 'daily')
    report_format = request.args.get('format', 'pdf')
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Log the export request
    log_report_export(f'{report_type.capitalize()} Driver Report', {'format': report_format, 'date': date})
    
    # Redirect to the appropriate export endpoint
    return redirect(url_for('export_bp.export_driver_report', 
                           type=report_type, 
                           format=report_format, 
                           date=date))

@driver_module_bp.route('/download/<path:filename>')
@login_required
def download_export(filename):
    """Redirect to the dedicated download route"""
    # Log the download request
    log_report_export('Driver Report Download', {'filename': filename})
    
    # Redirect to the downloads blueprint
    return redirect(url_for('downloads_bp.download_file', 
                           folder='driver_reports', 
                           filename=filename))
@driver_module_clean_bp.route('/')
def index():
    """Handler for /"""
    try:
        # Add your route handler logic here
        return render_template('driver_module_clean/index.html')
    except Exception as e:
        logger.error(f"Error in index: {e}")
        return render_template('error.html', error=str(e)), 500

@driver_module_clean_bp.route('/daily-report')
def daily_report():
    """Handler for /daily-report"""
    try:
        # Add your route handler logic here
        return render_template('driver_module_clean/daily_report.html')
    except Exception as e:
        logger.error(f"Error in daily_report: {e}")
        return render_template('error.html', error=str(e)), 500

@driver_module_clean_bp.route('/attendance-dashboard')
def attendance_dashboard():
    """Handler for /attendance-dashboard"""
    try:
        # Add your route handler logic here
        return render_template('driver_module_clean/attendance_dashboard.html')
    except Exception as e:
        logger.error(f"Error in attendance_dashboard: {e}")
        return render_template('error.html', error=str(e)), 500

@driver_module_clean_bp.route('/drivers')
def drivers():
    """Handler for /drivers"""
    try:
        # Add your route handler logic here
        return render_template('driver_module_clean/drivers.html')
    except Exception as e:
        logger.error(f"Error in drivers: {e}")
        return render_template('error.html', error=str(e)), 500

@driver_module_clean_bp.route('/driver/<int:driver_id>')
def driver_<int:driver_id>():
    """Handler for /driver/<int:driver_id>"""
    try:
        # Add your route handler logic here
        return render_template('driver_module_clean/driver_<int:driver_id>.html')
    except Exception as e:
        logger.error(f"Error in driver_<int:driver_id>: {e}")
        return render_template('error.html', error=str(e)), 500

@driver_module_clean_bp.route('/job-site/<int:site_id>')
def job_site_<int:site_id>():
    """Handler for /job-site/<int:site_id>"""
    try:
        # Add your route handler logic here
        return render_template('driver_module_clean/job_site_<int:site_id>.html')
    except Exception as e:
        logger.error(f"Error in job_site_<int:site_id>: {e}")
        return render_template('error.html', error=str(e)), 500

@driver_module_clean_bp.route('/region/<int:region_id>')
def region_<int:region_id>():
    """Handler for /region/<int:region_id>"""
    try:
        # Add your route handler logic here
        return render_template('driver_module_clean/region_<int:region_id>.html')
    except Exception as e:
        logger.error(f"Error in region_<int:region_id>: {e}")
        return render_template('error.html', error=str(e)), 500

@driver_module_clean_bp.route('/upload-attendance')
def upload_attendance():
    """Handler for /upload-attendance"""
    try:
        # Add your route handler logic here
        return render_template('driver_module_clean/upload_attendance.html')
    except Exception as e:
        logger.error(f"Error in upload_attendance: {e}")
        return render_template('error.html', error=str(e)), 500

@driver_module_clean_bp.route('/export-report')
def export_report():
    """Handler for /export-report"""
    try:
        # Add your route handler logic here
        return render_template('driver_module_clean/export_report.html')
    except Exception as e:
        logger.error(f"Error in export_report: {e}")
        return render_template('error.html', error=str(e)), 500

@driver_module_clean_bp.route('/download/<path:filename>')
def download_<path:filename>():
    """Handler for /download/<path:filename>"""
    try:
        # Add your route handler logic here
        return render_template('driver_module_clean/download_<path:filename>.html')
    except Exception as e:
        logger.error(f"Error in download_<path:filename>: {e}")
        return render_template('error.html', error=str(e)), 500
