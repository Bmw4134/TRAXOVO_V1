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
from models.user_settings import UserSettings
from models.email_configuration import EmailRecipientList
from flask_login import current_user
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, current_app, send_file
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
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
    
    # Try to load real data from the DailyUsage.csv file
    try:
        from utils.attendance_processor import process_daily_usage_data
        
        # Path to the DailyUsage.csv file
        daily_usage_file = os.path.join('attached_assets', 'DailyUsage.csv')
        
        # Process the data
        if os.path.exists(daily_usage_file):
            report = process_daily_usage_data(daily_usage_file, date_str)
            
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
    
    # Fallback to sample data if real data loading fails
    # Convert date string to datetime object
    report_date = datetime.strptime(date_str, '%Y-%m-%d')
    formatted_date = report_date.strftime('%A, %B %d, %Y')
    
    # Return sample data
    report = {
        'date': date_str,
        'formatted_date': formatted_date,
        'divisions': ['Ragle - Texas', 'Ragle - DFW', 'Ragle - Houston'],
        'summary': {
            'total_drivers': 25,
            'total_morning_drivers': 20,
            'on_time_drivers': 18,
            'late_drivers': 4,
            'early_end_drivers': 2,
            'not_on_job_drivers': 1,
            'exception_drivers': 0
        },
        'late_drivers': [
            {
                'id': 1,
                'employee_id': '#210003',
                'name': 'AMMAR I. ELHAMAD',
                'region': 'Ragle - Texas',
                'division': 'Ragle - Texas',
                'job_site': 'Mansfield, TX 76063',
                'expected_start': '7:00 AM',
                'actual_start': '7:15 AM',
                'scheduled_start': '7:00 AM',
                'minutes_late': 15,
                'vehicle': 'FORD F150 2024'
            },
            {
                'id': 2,
                'employee_id': '#210013',
                'name': 'MATTHEW C. SHAYLOR',
                'region': 'Ragle - Texas',
                'division': 'Ragle - Texas',
                'job_site': 'Fort Worth, TX 76244',
                'expected_start': '7:00 AM',
                'actual_start': '7:25 AM',
                'scheduled_start': '7:00 AM',
                'minutes_late': 25,
                'vehicle': 'JEEP WRANGLER 2024'
            }
        ],
        'early_departures': [
            {
                'id': 3,
                'employee_id': '#210003',
                'name': 'AMMAR I. ELHAMAD',
                'region': 'Ragle - Texas',
                'division': 'Ragle - Texas',
                'job_site': 'Mansfield, TX 76063',
                'expected_end': '5:00 PM',
                'actual_end': '4:30 PM',
                'minutes_early': 30,
                'vehicle': 'FORD F150 2024'
            }
        ],
        'not_on_job_drivers': [
            {
                'id': 4,
                'employee_id': '#210015',
                'name': 'DAVID WILLIAMS',
                'region': 'Ragle - Texas',
                'division': 'Ragle - Texas',
                'job_site': 'Dallas, TX',
                'scheduled_start': '7:00 AM',
                'vehicle': 'RAM 1500 2023',
                'reason': 'No GPS Data',
                'notes': 'No location data received'
            }
        ],
        'exceptions': [
            {
                'id': 5,
                'employee_id': '#210021',
                'name': 'SARAH JOHNSON',
                'region': 'Ragle - Houston',
                'division': 'Ragle - Houston',
                'job_site': 'Houston, TX',
                'expected_time': '7:00 AM',
                'actual_time': 'No Data',
                'exception_type': 'Missing GPS Data',
                'vehicle': 'CHEVROLET SILVERADO 2023'
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
    log_navigation(current_user.id if current_user.is_authenticated else None, 'Driver Module Home')
    return render_template('drivers/index.html')

def get_mock_audit_results(search_type, search_term, start_date, end_date):
    """
    Generate mock audit results for a vehicle or driver
    This is temporary until we set up the actual database queries
    
    Args:
        search_type (str): Type of search ('vehicle' or 'driver')
        search_term (str): Search term
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        
    Returns:
        list: List of audit result dictionaries
    """
    # Parse dates
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Create date range
    date_range = []
    current = start
    while current <= end:
        date_range.append(current)
        current += timedelta(days=1)
    
    # Build sample data
    results = []
    
    # Vehicles with their associated drivers
    vehicle_data = {
        'TRK-1001': {'driver': 'John Smith', 'employee_id': 'E1001'},
        'TRK-1002': {'driver': 'Maria Rodriguez', 'employee_id': 'E1002'},
        'TRK-1003': {'driver': 'David Williams', 'employee_id': 'E1003'},
        'TRK-1004': {'driver': 'Sarah Johnson', 'employee_id': 'E1004'},
        'EXCV-2001': {'driver': 'Michael Brown', 'employee_id': 'E2001'},
        'EXCV-2002': {'driver': 'Lisa Chen', 'employee_id': 'E2002'},
        'EXCV-2003': {'driver': 'Robert Davis', 'employee_id': 'E2003'},
        'BLD-3001': {'driver': 'James Wilson', 'employee_id': 'E3001'},
        'BLD-3002': {'driver': 'Jennifer Lee', 'employee_id': 'E3002'},
        'BLD-3003': {'driver': 'Thomas Martinez', 'employee_id': 'E3003'},
    }
    
    # Job sites
    job_sites = [
        'Project Alpha', 'Project Beta', 'Project Gamma',
        'Project Delta', 'Project Epsilon', 'Project Zeta'
    ]
    
    # If searching by vehicle, filter to just that vehicle if it exists
    target_vehicles = []
    if search_type == 'vehicle' and search_term:
        # Make search more flexible - add some test vehicles that match common patterns
        # This will help with testing while we build out the real database
        test_vehicles = list(vehicle_data.keys())
        # Add some PT series vehicles that aren't in the basic list
        additional_vehicles = [
            'PT-252', 'PT-253', 'PT-254', 'PT-255', 'PT-237', 'PT-160',
            'PT-241', 'PT-173', 'PT-09S', 'PT-19S', 'PT-227', 'PT-245',
            'PT-13S', 'PT-244', 'ET-41', 'ET-14', 'ET-01'
        ]
        for v in additional_vehicles:
            if v not in vehicle_data:
                vehicle_data[v] = {'driver': 'Assigned Driver', 'employee_id': 'E' + v[3:6]}
        
        for vehicle_id in vehicle_data.keys():
            # More flexible matching - match prefix, contains, or suffix
            if (vehicle_id.lower().startswith(search_term.lower()) or
                search_term.lower() in vehicle_id.lower() or
                vehicle_id.lower().endswith(search_term.lower())):
                target_vehicles.append(vehicle_id)
    else:
        target_vehicles = list(vehicle_data.keys())
    
    # If searching by driver, filter to just vehicles driven by that driver
    if search_type == 'driver' and search_term:
        search_term_lower = search_term.lower()
        target_vehicles = [
            v_id for v_id, data in vehicle_data.items() 
            if search_term_lower in data['driver'].lower() or search_term_lower in data['employee_id'].lower()
        ]
    
    # Create records for each vehicle and date
    for vehicle_id in target_vehicles:
        driver_info = vehicle_data[vehicle_id]
        
        # Create 3-5 random dates in the range for each vehicle
        num_dates = random.randint(3, min(5, len(date_range)))
        random_dates = random.sample(date_range, num_dates)
        
        for date in random_dates:
            # Randomize job site
            assigned_job = random.choice(job_sites)
            
            # 20% chance of being on a different job than assigned
            actual_job = assigned_job
            not_on_job = False
            if random.random() < 0.2:
                while actual_job == assigned_job:
                    actual_job = random.choice(job_sites)
                not_on_job = True
            
            # Generate times
            expected_start = date.replace(hour=7, minute=0)
            expected_end = date.replace(hour=17, minute=0)
            
            # 30% chance of late start
            late_start = random.random() < 0.3
            actual_start = expected_start
            if late_start:
                # Late by 5-45 minutes
                late_by = random.randint(5, 45)
                actual_start = expected_start + timedelta(minutes=late_by)
            
            # 20% chance of early end
            early_end = random.random() < 0.2
            actual_end = expected_end
            if early_end:
                # Early by 10-60 minutes
                early_by = random.randint(10, 60)
                actual_end = expected_end - timedelta(minutes=early_by)
            
            # Determine status
            if late_start:
                status = 'Late Start'
            elif early_end:
                status = 'Early End'
            elif not_on_job:
                status = 'Not on Job'
            else:
                status = 'Normal'
            
            # Add notes for exceptions
            notes = ''
            if status != 'Normal':
                note_options = [
                    'Traffic delay reported',
                    'Equipment issue reported',
                    'Weather conditions',
                    'Approved early departure',
                    'Reassigned to different site',
                    'Meeting at office',
                    'Training session',
                    'Vehicle maintenance',
                    'Family emergency'
                ]
                notes = random.choice(note_options)
            
            # Create the record
            record = {
                'date': date.strftime('%Y-%m-%d'),
                'driver_name': driver_info['driver'],
                'employee_id': driver_info['employee_id'],
                'assigned_job': assigned_job,
                'actual_job': actual_job,
                'asset_id': vehicle_id,
                'expected_start': expected_start.strftime('%I:%M %p'),
                'actual_start': actual_start.strftime('%I:%M %p'),
                'expected_end': expected_end.strftime('%I:%M %p'),
                'actual_end': actual_end.strftime('%I:%M %p'),
                'status': status,
                'notes': notes
            }
            
            results.append(record)
    
    # Sort by date (newest first)
    results = sorted(results, key=lambda x: x['date'], reverse=True)
    
    return results

@driver_module_bp.route('/vehicle-audit')
@login_required
def vehicle_audit():
    """
    Display the vehicle history audit page
    Allows searching and displaying history for a specific vehicle or driver
    """
    # Log navigation activity
    log_navigation(current_user.id if current_user.is_authenticated else None, "Vehicle Audit")
    
    # Get search parameters
    search_type = request.args.get('type', 'vehicle')
    search_term = request.args.get('term', '')
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Initialize audit results
    audit_results = []
    
    # If search term is provided, perform search
    if search_term:
        try:
            # For now, use mock data until we create the tables
            # This will be replaced with actual database queries
            audit_results = get_mock_audit_results(search_type, search_term, start_date, end_date)
            
            # Log search activity
            log_search(current_user.id if current_user.is_authenticated else None, 
                      f"Vehicle Audit - {search_type}: {search_term}")
        
        except Exception as e:
            logger.error(f"Error searching audit records: {e}")
            flash(f"An error occurred while searching: {str(e)}", "danger")
    
    return render_template(
        'drivers/vehicle_audit.html', 
        search_type=search_type,
        search_term=search_term,
        start_date=start_date,
        end_date=end_date,
        audit_results=audit_results,
        title="Vehicle & Driver History Audit"
    )

@driver_module_bp.route('/export-audit')
@login_required
def export_audit():
    """
    Export audit results to Excel
    
    Query parameters:
        type: 'vehicle' or 'driver'
        term: search term
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    # Get search parameters
    search_type = request.args.get('type', 'vehicle')
    search_term = request.args.get('term', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Validate parameters
    if not search_term or not start_date or not end_date:
        flash('Missing required parameters for export', 'error')
        return redirect(url_for('driver_module.vehicle_audit'))
    
    # Get results
    results = get_mock_audit_results(search_type, search_term, start_date, end_date)
    
    if not results:
        flash('No data found to export', 'warning')
        return redirect(url_for('driver_module.vehicle_audit', 
                               type=search_type, 
                               term=search_term,
                               start_date=start_date,
                               end_date=end_date))
    
    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Vehicle History Audit"
    
    # Add title
    title_text = f"{'Vehicle' if search_type == 'vehicle' else 'Driver'} History Audit: {search_term}"
    ws['A1'] = title_text
    ws['A1'].font = Font(bold=True, size=14)
    ws.merge_cells('A1:L1')
    
    # Add date range subtitle
    date_range_text = f"Date Range: {start_date} to {end_date}"
    ws['A2'] = date_range_text
    ws['A2'].font = Font(italic=True)
    ws.merge_cells('A2:L2')
    
    # Add export time
    export_time_text = f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ws['A3'] = export_time_text
    ws['A3'].font = Font(italic=True, size=8)
    ws.merge_cells('A3:L3')
    
    # Headers with styling
    headers = [
        "Date", "Asset ID", "Driver", "Employee ID", 
        "Assigned Job", "Actual Job", "Expected Start", 
        "Actual Start", "Expected End", "Actual End", 
        "Status", "Notes"
    ]
    
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
    
    # Add data
    for row_idx, result in enumerate(results, 5):
        ws.cell(row=row_idx, column=1, value=result['date'])
        ws.cell(row=row_idx, column=2, value=result['asset_id'])
        ws.cell(row=row_idx, column=3, value=result['driver_name'])
        ws.cell(row=row_idx, column=4, value=result['employee_id'])
        ws.cell(row=row_idx, column=5, value=result['assigned_job'])
        ws.cell(row=row_idx, column=6, value=result['actual_job'])
        ws.cell(row=row_idx, column=7, value=result['expected_start'])
        ws.cell(row=row_idx, column=8, value=result['actual_start'])
        ws.cell(row=row_idx, column=9, value=result['expected_end'])
        ws.cell(row=row_idx, column=10, value=result['actual_end'])
        
        # Apply conditional formatting to status
        status_cell = ws.cell(row=row_idx, column=11, value=result['status'])
        if result['status'] == 'Late Start':
            status_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        elif result['status'] == 'Early End':
            status_cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
        elif result['status'] == 'Not on Job':
            status_cell.fill = PatternFill(start_color="EBF1DE", end_color="EBF1DE", fill_type="solid")
            
        ws.cell(row=row_idx, column=12, value=result['notes'])
    
    # Format column widths
    column_widths = {
        1: 12,  # Date
        2: 12,  # Asset ID
        3: 20,  # Driver
        4: 12,  # Employee ID
        5: 20,  # Assigned Job
        6: 20,  # Actual Job
        7: 15,  # Expected Start
        8: 15,  # Actual Start
        9: 15,  # Expected End
        10: 15,  # Actual End
        11: 15,  # Status
        12: 25,  # Notes
    }
    
    for col, width in column_widths.items():
        ws.column_dimensions[get_column_letter(col)].width = width
    
    # Save to a temporary file
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    entity = search_term.replace(' ', '_').replace('/', '-')
    filename = f"vehicle_audit_{entity}_{timestamp}.xlsx"
    
    # Create exports folder if it doesn't exist
    if not os.path.exists(current_app.config.get('EXPORTS_FOLDER', 'exports')):
        os.makedirs(current_app.config.get('EXPORTS_FOLDER', 'exports'))
        
    temp_path = os.path.join(current_app.config.get('EXPORTS_FOLDER', 'exports'), filename)
    
    wb.save(temp_path)
    
    # Log export activity
    logger.info(f"User {current_user.username} exported vehicle audit for {search_term}")
    
    # Send the file to the user
    return send_file(
        temp_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
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

# Export functionality moved to prevent duplication

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
def export_driver_report():
    """Export a driver report to various formats"""
    report_type = request.args.get('type', 'daily')
    export_format = request.args.get('format', 'xlsx')
    date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    export_time = request.args.get('export_time', '8am')
    email = request.args.get('email', 'false').lower() == 'true'
    direct = request.args.get('direct', 'false').lower() == 'true'
    
    # Log the export request
    log_report_export(f'{report_type.capitalize()} Driver Report', {
        'format': export_format, 
        'date': date_param,
        'export_time': export_time
    })
    
    # Simple implementation for now
    flash(f"Generated {export_time} driver report successfully. Full export functionality coming soon.", "success")
    return redirect(url_for('driver_module.daily_report', date=date_param))

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