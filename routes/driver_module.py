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

def get_drivers():
    """
    Get driver data from the database
    Returns a list of driver dictionaries with attendance metrics
    """
    try:
        # Import driver models
        from models.driver_attendance import DriverAttendance
        
        # Query all drivers from database
        drivers = DriverAttendance.query.all()
        
        # Convert to list of dictionaries for the template
        driver_list = []
        for driver in drivers:
            driver_dict = {
                'id': driver.id,
                'name': driver.full_name,
                'employee_id': driver.employee_id,
                'division': driver.division,
                'attendance_rate': driver.attendance_rate or 0,
                'on_time_rate': driver.on_time_rate or 0,
                'late_count': driver.late_count or 0,
                'total_days': driver.total_days or 0,
                'last_job': driver.last_job_site
            }
            driver_list.append(driver_dict)
            
        return driver_list
    except Exception as e:
        logger.error(f"Error getting drivers: {str(e)}")
        return []

def get_daily_report(date_str=None):
    """
    Get daily report data from the database
    Args:
        date_str: Date string in YYYY-MM-DD format, defaults to today
        
    Returns:
        dict: Daily report data
    """
    try:
        # Get date for report
        if date_str:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            report_date = datetime.now().date()
            
        # Import models
        from models.driver_attendance import AttendanceRecord, DriverAttendance, JobSiteAttendance
        
        # Query attendance records for the date
        records = db.session.query(
            AttendanceRecord, DriverAttendance, JobSiteAttendance
        ).join(
            DriverAttendance, AttendanceRecord.driver_id == DriverAttendance.id
        ).join(
            JobSiteAttendance, AttendanceRecord.assigned_job_id == JobSiteAttendance.id, isouter=True
        ).filter(
            AttendanceRecord.date == report_date
        ).all()
        
        # Process records
        attendance_records = []
        for record, driver, job_site in records:
            # Calculate time difference in minutes
            scheduled_start = record.expected_start_time
            actual_start = record.actual_start_time
            
            minutes_late = 0
            if scheduled_start and actual_start:
                # Convert to datetime for time calculation
                scheduled_dt = datetime.combine(report_date, scheduled_start)
                actual_dt = datetime.combine(report_date, actual_start)
                
                time_diff = actual_dt - scheduled_dt
                minutes_late = time_diff.total_seconds() / 60
            
            # Determine status
            status = "On Time"
            if record.late_start:
                status = "Late Start"
            elif record.early_end:
                status = "Early End"
            elif record.not_on_job:
                status = "Not on Job"
            
            # Create record dictionary
            attendance_records.append({
                'driver_id': driver.id,
                'employee_id': driver.employee_id,
                'name': driver.full_name,
                'division': driver.division,
                'job_site': job_site.name if job_site else 'Unknown',
                'status': status,
                'scheduled_start': scheduled_start.strftime('%H:%M') if scheduled_start else '-',
                'actual_start': actual_start.strftime('%H:%M') if actual_start else '-',
                'minutes_late': int(minutes_late) if minutes_late > 0 else 0,
                'asset_id': record.asset_id,
                'notes': record.notes
            })
        
        # Calculate summary metrics
        total_drivers = len(attendance_records)
        late_drivers = len([r for r in attendance_records if r['status'] == 'Late Start'])
        early_end_drivers = len([r for r in attendance_records if r['status'] == 'Early End'])
        not_on_job_drivers = len([r for r in attendance_records if r['status'] == 'Not on Job'])
        on_time_drivers = total_drivers - late_drivers - early_end_drivers - not_on_job_drivers
        
        on_time_percentage = (on_time_drivers / total_drivers * 100) if total_drivers > 0 else 0
        
        # Group by division
        divisions = {}
        for record in attendance_records:
            division = record['division'] or 'Unknown'
            if division not in divisions:
                divisions[division] = {
                    'total': 0,
                    'on_time': 0,
                    'late': 0,
                    'early_end': 0,
                    'not_on_job': 0
                }
            
            divisions[division]['total'] += 1
            
            if record['status'] == 'On Time':
                divisions[division]['on_time'] += 1
            elif record['status'] == 'Late Start':
                divisions[division]['late'] += 1
            elif record['status'] == 'Early End':
                divisions[division]['early_end'] += 1
            elif record['status'] == 'Not on Job':
                divisions[division]['not_on_job'] += 1
        
        # Calculate percentages for each division
        for division in divisions:
            div_total = divisions[division]['total']
            if div_total > 0:
                divisions[division]['on_time_percentage'] = round(divisions[division]['on_time'] / div_total * 100, 1)
            else:
                divisions[division]['on_time_percentage'] = 0
        
        # Return the report data
        return {
            'date': report_date.strftime('%Y-%m-%d'),
            'formatted_date': report_date.strftime('%B %d, %Y'),
            'records': attendance_records,
            'summary': {
                'total_drivers': total_drivers,
                'on_time_drivers': on_time_drivers,
                'late_drivers': late_drivers,
                'early_end_drivers': early_end_drivers,
                'not_on_job_drivers': not_on_job_drivers,
                'on_time_percentage': round(on_time_percentage, 1)
            },
            'divisions': divisions
        }
    except Exception as e:
        logger.error(f"Error generating daily report: {str(e)}")
        
        # Return empty report structure
        return {
            'date': date_str or datetime.now().strftime('%Y-%m-%d'),
            'formatted_date': datetime.now().strftime('%B %d, %Y'),
            'records': [],
            'summary': {
                'total_drivers': 0,
                'on_time_drivers': 0,
                'late_drivers': 0,
                'early_end_drivers': 0,
                'not_on_job_drivers': 0,
                'on_time_percentage': 0
            },
            'divisions': {}
        }

def get_attendance_stats(days=30):
    """
    Get attendance statistics from the database for dashboard
    
    Args:
        days (int): Number of days to include in statistics
        
    Returns:
        dict: Attendance statistics
    """
    try:
        # Import models
        from models.driver_attendance import AttendanceRecord, DriverAttendance
        from sqlalchemy import func, and_, distinct
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get total drivers
        total_drivers = db.session.query(func.count(distinct(DriverAttendance.id))).scalar() or 0
        
        # Get total attendance records in period
        total_records = db.session.query(func.count(AttendanceRecord.id))\
            .filter(AttendanceRecord.date.between(start_date, end_date))\
            .scalar() or 0
        
        # Get late start counts
        late_count = db.session.query(func.count(AttendanceRecord.id))\
            .filter(
                AttendanceRecord.date.between(start_date, end_date),
                AttendanceRecord.late_start == True
            )\
            .scalar() or 0
        
        # Get early end counts
        early_end_count = db.session.query(func.count(AttendanceRecord.id))\
            .filter(
                AttendanceRecord.date.between(start_date, end_date),
                AttendanceRecord.early_end == True
            )\
            .scalar() or 0
        
        # Get not on job counts
        not_on_job_count = db.session.query(func.count(AttendanceRecord.id))\
            .filter(
                AttendanceRecord.date.between(start_date, end_date),
                AttendanceRecord.not_on_job == True
            )\
            .scalar() or 0
        
        # Calculate on time count
        on_time_count = total_records - late_count - early_end_count - not_on_job_count
        
        # Calculate percentages
        on_time_percentage = (on_time_count / total_records * 100) if total_records > 0 else 0
        late_percentage = (late_count / total_records * 100) if total_records > 0 else 0
        early_end_percentage = (early_end_count / total_records * 100) if total_records > 0 else 0
        not_on_job_percentage = (not_on_job_count / total_records * 100) if total_records > 0 else 0
        
        # Get daily trend data
        daily_stats = []
        current_date = start_date
        while current_date <= end_date:
            # Count records for this day
            day_records = db.session.query(func.count(AttendanceRecord.id))\
                .filter(AttendanceRecord.date == current_date)\
                .scalar() or 0
            
            # Count late starts for this day
            day_late = db.session.query(func.count(AttendanceRecord.id))\
                .filter(
                    AttendanceRecord.date == current_date,
                    AttendanceRecord.late_start == True
                )\
                .scalar() or 0
            
            # Calculate on time percentage
            day_on_time_pct = ((day_records - day_late) / day_records * 100) if day_records > 0 else 0
            
            daily_stats.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'formatted_date': current_date.strftime('%m/%d'),
                'total': day_records,
                'on_time': day_records - day_late,
                'late': day_late,
                'on_time_percentage': round(day_on_time_pct, 1)
            })
            
            current_date += timedelta(days=1)
        
        return {
            'total_drivers': total_drivers,
            'total_records': total_records,
            'on_time_count': on_time_count,
            'late_count': late_count,
            'early_end_count': early_end_count,
            'not_on_job_count': not_on_job_count,
            'on_time_percentage': round(on_time_percentage, 1),
            'late_percentage': round(late_percentage, 1),
            'early_end_percentage': round(early_end_percentage, 1),
            'not_on_job_percentage': round(not_on_job_percentage, 1),
            'daily_stats': daily_stats,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
    except Exception as e:
        logger.error(f"Error getting attendance stats: {str(e)}")
        return {
            'total_drivers': 0,
            'total_records': 0,
            'on_time_count': 0,
            'late_count': 0,
            'early_end_count': 0,
            'not_on_job_count': 0,
            'on_time_percentage': 0,
            'late_percentage': 0,
            'early_end_percentage': 0,
            'not_on_job_percentage': 0,
            'daily_stats': [],
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }

# Routes
@driver_module_bp.route('/')
@login_required
def index():
    """Driver module home page"""
    # Log navigation
    log_navigation('driver_module.index', 'Visited Driver Module Home')
    
    # Get attendance stats for dashboard
    stats = get_attendance_stats(days=30)
    
    return render_template('drivers/index.html', stats=stats)

@driver_module_bp.route('/daily_report', methods=['GET', 'POST'])
@login_required
def daily_report():
    """Daily driver attendance report with email configuration"""
    # Handle email configuration POST request
    if request.method == 'POST' and request.form.get('action') == 'save_email_config':
        return save_email_config()
    
    # Get date parameter, default to today
    date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Log navigation
    log_navigation('driver_module.daily_report', f'Viewed Daily Report for {date_param}')
    
    # Get the report data
    report_data = get_daily_report(date_param)
    
    # Get previous/next day for navigation
    report_date = datetime.strptime(date_param, '%Y-%m-%d').date()
    prev_day = (report_date - timedelta(days=1)).strftime('%Y-%m-%d')
    next_day = (report_date + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Get email configuration for the current user
    email_config = get_user_email_config()
    
    return render_template('drivers/daily_report.html', 
                          report=report_data, 
                          prev_day=prev_day,
                          next_day=next_day,
                          email_config=email_config)

@driver_module_bp.route('/attendance_dashboard')
@login_required
def attendance_dashboard():
    """Attendance dashboard with trends and metrics"""
    # Get days parameter (30, 60, 90)
    days = int(request.args.get('days', 30))
    
    # Log navigation
    log_navigation('driver_module.attendance_dashboard', f'Viewed Attendance Dashboard ({days} days)')
    
    # Get attendance stats
    stats = get_attendance_stats(days=days)
    
    return render_template('drivers/attendance_dashboard.html', stats=stats, selected_days=days)

@driver_module_bp.route('/driver_list')
@login_required
def driver_list():
    """List all drivers with filtering options"""
    # Log navigation
    log_navigation('driver_module.driver_list', 'Viewed Driver List')
    
    # Get drivers from database
    drivers = get_drivers()
    
    return render_template('drivers/driver_list.html', drivers=drivers)

@driver_module_bp.route('/driver/<driver_id>')
@login_required
def driver_detail(driver_id):
    """Driver detail page with attendance history"""
    # Log navigation
    log_navigation('driver_module.driver_detail', f'Viewed Driver Detail for {driver_id}')
    
    try:
        # Import models
        from models.driver_attendance import DriverAttendance, AttendanceRecord, JobSiteAttendance
        
        # Get driver data
        driver = DriverAttendance.query.get(driver_id)
        
        if not driver:
            flash("Driver not found", "danger")
            return redirect(url_for('driver_module.driver_list'))
        
        # Get attendance history
        records = db.session.query(
            AttendanceRecord, JobSiteAttendance
        ).outerjoin(
            JobSiteAttendance, AttendanceRecord.assigned_job_id == JobSiteAttendance.id
        ).filter(
            AttendanceRecord.driver_id == driver_id
        ).order_by(
            AttendanceRecord.date.desc()
        ).limit(30).all()
        
        # Process records
        attendance_history = []
        for record, job_site in records:
            # Determine status
            status = "On Time"
            if record.late_start:
                status = "Late Start"
            elif record.early_end:
                status = "Early End"
            elif record.not_on_job:
                status = "Not on Job"
            
            attendance_history.append({
                'date': record.date,
                'job_site': job_site.name if job_site else 'Unknown',
                'status': status,
                'expected_start': record.expected_start_time,
                'actual_start': record.actual_start_time,
                'expected_end': record.expected_end_time,
                'actual_end': record.actual_end_time,
                'asset_id': record.asset_id,
                'notes': record.notes
            })
        
        # Calculate attendance metrics
        total_records = len(attendance_history)
        late_count = len([r for r in attendance_history if r['status'] == 'Late Start'])
        early_end_count = len([r for r in attendance_history if r['status'] == 'Early End'])
        not_on_job_count = len([r for r in attendance_history if r['status'] == 'Not on Job'])
        on_time_count = total_records - late_count - early_end_count - not_on_job_count
        
        attendance_rate = (total_records / 30 * 100) if total_records > 0 else 0
        on_time_rate = (on_time_count / total_records * 100) if total_records > 0 else 0
        
        attendance_metrics = {
            'total_records': total_records,
            'on_time_count': on_time_count,
            'late_count': late_count,
            'early_end_count': early_end_count,
            'not_on_job_count': not_on_job_count,
            'attendance_rate': round(attendance_rate, 1),
            'on_time_rate': round(on_time_rate, 1)
        }
        
        return render_template('drivers/driver_detail.html', 
                              driver=driver, 
                              history=attendance_history,
                              metrics=attendance_metrics)
    
    except Exception as e:
        logger.error(f"Error in driver_detail route: {str(e)}")
        flash(f"Error retrieving driver details: {str(e)}", "danger")
        return redirect(url_for('driver_module.driver_list'))

@driver_module_bp.route('/job_site/<site_id>')
@login_required
def job_site_detail(site_id):
    """Job site detail page with attendance metrics"""
    # Log navigation
    log_navigation('driver_module.job_site_detail', f'Viewed Job Site Detail for {site_id}')
    
    try:
        # Import models
        from models.driver_attendance import JobSiteAttendance, AttendanceRecord, DriverAttendance
        
        # Get job site data
        job_site = JobSiteAttendance.query.get(site_id)
        
        if not job_site:
            flash("Job site not found", "danger")
            return redirect(url_for('driver_module.index'))
        
        # Get attendance records for this job site
        records = db.session.query(
            AttendanceRecord, DriverAttendance
        ).join(
            DriverAttendance, AttendanceRecord.driver_id == DriverAttendance.id
        ).filter(
            AttendanceRecord.assigned_job_id == site_id
        ).order_by(
            AttendanceRecord.date.desc()
        ).limit(50).all()
        
        # Process records
        attendance_records = []
        for record, driver in records:
            # Determine status
            status = "On Time"
            if record.late_start:
                status = "Late Start"
            elif record.early_end:
                status = "Early End"
            elif record.not_on_job:
                status = "Not on Job"
            
            attendance_records.append({
                'date': record.date,
                'driver_id': driver.id,
                'driver_name': driver.full_name,
                'employee_id': driver.employee_id,
                'division': driver.division,
                'status': status,
                'expected_start': record.expected_start_time,
                'actual_start': record.actual_start_time,
                'expected_end': record.expected_end_time,
                'actual_end': record.actual_end_time,
                'asset_id': record.asset_id,
                'notes': record.notes
            })
        
        # Calculate attendance metrics
        total_records = len(attendance_records)
        late_count = len([r for r in attendance_records if r['status'] == 'Late Start'])
        early_end_count = len([r for r in attendance_records if r['status'] == 'Early End'])
        not_on_job_count = len([r for r in attendance_records if r['status'] == 'Not on Job'])
        on_time_count = total_records - late_count - early_end_count - not_on_job_count
        
        on_time_rate = (on_time_count / total_records * 100) if total_records > 0 else 0
        
        # Group by division
        divisions = {}
        for record in attendance_records:
            division = record['division'] or 'Unknown'
            if division not in divisions:
                divisions[division] = {
                    'total': 0,
                    'on_time': 0,
                    'late': 0,
                    'early_end': 0,
                    'not_on_job': 0
                }
            
            divisions[division]['total'] += 1
            
            if record['status'] == 'On Time':
                divisions[division]['on_time'] += 1
            elif record['status'] == 'Late Start':
                divisions[division]['late'] += 1
            elif record['status'] == 'Early End':
                divisions[division]['early_end'] += 1
            elif record['status'] == 'Not on Job':
                divisions[division]['not_on_job'] += 1
        
        # Calculate percentages for each division
        for division in divisions:
            div_total = divisions[division]['total']
            if div_total > 0:
                divisions[division]['on_time_percentage'] = round(divisions[division]['on_time'] / div_total * 100, 1)
            else:
                divisions[division]['on_time_percentage'] = 0
        
        attendance_metrics = {
            'total_records': total_records,
            'on_time_count': on_time_count,
            'late_count': late_count,
            'early_end_count': early_end_count,
            'not_on_job_count': not_on_job_count,
            'on_time_rate': round(on_time_rate, 1),
            'divisions': divisions
        }
        
        return render_template('drivers/job_site_detail.html', 
                              job_site=job_site, 
                              records=attendance_records,
                              metrics=attendance_metrics)
    
    except Exception as e:
        logger.error(f"Error in job_site_detail route: {str(e)}")
        flash(f"Error retrieving job site details: {str(e)}", "danger")
        return redirect(url_for('driver_module.index'))

@driver_module_bp.route('/region/<region_id>')
@login_required
def region_detail(region_id):
    """Region detail page with attendance metrics"""
    # Log navigation
    log_navigation('driver_module.region_detail', f'Viewed Region Detail for {region_id}')
    
    try:
        # Import models
        from models.driver_attendance import AttendanceRecord, DriverAttendance, JobSiteAttendance
        from models.organization import Region, JobSite
        
        # Parse date range parameters
        today = datetime.now().date()
        
        # Helper functions for date parameters
        def get_first_day_of_month(date):
            return date.replace(day=1)
        
        def get_last_day_of_month(date):
            next_month = date.replace(day=28) + timedelta(days=4)
            return next_month - timedelta(days=next_month.day)
        
        # Default to current month
        start_date = get_first_day_of_month(today)
        end_date = get_last_day_of_month(today)
        
        # Use custom date range if provided
        if request.args.get('start_date') and request.args.get('end_date'):
            try:
                start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
                end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
            except ValueError:
                # Ignore invalid date formats
                pass
        
        # Get region data
        region = Region.query.filter_by(id=region_id).first()
        
        if not region:
            # Just use the provided region_id as the name
            region = {'id': region_id, 'name': region_id}
        
        # Get attendance records for this region
        records = db.session.query(
            AttendanceRecord, DriverAttendance, JobSiteAttendance
        ).join(
            DriverAttendance, AttendanceRecord.driver_id == DriverAttendance.id
        ).outerjoin(
            JobSiteAttendance, AttendanceRecord.assigned_job_id == JobSiteAttendance.id
        ).filter(
            DriverAttendance.division == region_id,
            AttendanceRecord.date.between(start_date, end_date)
        ).order_by(
            AttendanceRecord.date.desc()
        ).all()
        
        # Process records
        attendance_records = []
        for record, driver, job_site in records:
            # Determine status
            status = "On Time"
            if record.late_start:
                status = "Late Start"
            elif record.early_end:
                status = "Early End"
            elif record.not_on_job:
                status = "Not on Job"
            
            attendance_records.append({
                'date': record.date,
                'driver_id': driver.id,
                'driver_name': driver.full_name,
                'employee_id': driver.employee_id,
                'job_site_id': job_site.id if job_site else None,
                'job_site': job_site.name if job_site else 'Unknown',
                'status': status,
                'expected_start': record.expected_start_time,
                'actual_start': record.actual_start_time,
                'expected_end': record.expected_end_time,
                'actual_end': record.actual_end_time,
                'asset_id': record.asset_id,
                'notes': record.notes
            })
        
        # Calculate attendance metrics
        total_records = len(attendance_records)
        late_count = len([r for r in attendance_records if r['status'] == 'Late Start'])
        early_end_count = len([r for r in attendance_records if r['status'] == 'Early End'])
        not_on_job_count = len([r for r in attendance_records if r['status'] == 'Not on Job'])
        on_time_count = total_records - late_count - early_end_count - not_on_job_count
        
        on_time_rate = (on_time_count / total_records * 100) if total_records > 0 else 0
        
        # Group by job site
        job_sites = {}
        for record in attendance_records:
            job_site = record['job_site']
            if job_site not in job_sites:
                job_sites[job_site] = {
                    'id': record['job_site_id'],
                    'total': 0,
                    'on_time': 0,
                    'late': 0,
                    'early_end': 0,
                    'not_on_job': 0
                }
            
            job_sites[job_site]['total'] += 1
            
            if record['status'] == 'On Time':
                job_sites[job_site]['on_time'] += 1
            elif record['status'] == 'Late Start':
                job_sites[job_site]['late'] += 1
            elif record['status'] == 'Early End':
                job_sites[job_site]['early_end'] += 1
            elif record['status'] == 'Not on Job':
                job_sites[job_site]['not_on_job'] += 1
        
        # Calculate percentages for each job site
        for job_site in job_sites:
            site_total = job_sites[job_site]['total']
            if site_total > 0:
                job_sites[job_site]['on_time_percentage'] = round(job_sites[job_site]['on_time'] / site_total * 100, 1)
            else:
                job_sites[job_site]['on_time_percentage'] = 0
        
        # Get daily trend data
        daily_stats = []
        current_date = start_date
        while current_date <= end_date:
            # Filter records for this day
            day_records = [r for r in attendance_records if r['date'] == current_date]
            day_total = len(day_records)
            day_late = len([r for r in day_records if r['status'] == 'Late Start'])
            day_early_end = len([r for r in day_records if r['status'] == 'Early End'])
            day_not_on_job = len([r for r in day_records if r['status'] == 'Not on Job'])
            day_on_time = day_total - day_late - day_early_end - day_not_on_job
            
            # Calculate on time percentage
            day_on_time_pct = (day_on_time / day_total * 100) if day_total > 0 else 0
            
            daily_stats.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'formatted_date': current_date.strftime('%m/%d'),
                'total': day_total,
                'on_time': day_on_time,
                'late': day_late,
                'early_end': day_early_end,
                'not_on_job': day_not_on_job,
                'on_time_percentage': round(day_on_time_pct, 1)
            })
            
            current_date += timedelta(days=1)
        
        attendance_metrics = {
            'total_records': total_records,
            'on_time_count': on_time_count,
            'late_count': late_count,
            'early_end_count': early_end_count,
            'not_on_job_count': not_on_job_count,
            'on_time_rate': round(on_time_rate, 1),
            'job_sites': job_sites,
            'daily_stats': daily_stats
        }
        
        return render_template('drivers/region_detail.html', 
                              region=region, 
                              records=attendance_records,
                              metrics=attendance_metrics,
                              start_date=start_date.strftime('%Y-%m-%d'),
                              end_date=end_date.strftime('%Y-%m-%d'))
    
    except Exception as e:
        logger.error(f"Error in region_detail route: {str(e)}")
        flash(f"Error retrieving region details: {str(e)}", "danger")
        return redirect(url_for('driver_module.index'))

@driver_module_bp.route('/upload_attendance', methods=['GET', 'POST'])
@login_required
def upload_attendance():
    """Upload attendance file for processing"""
    if request.method == 'POST':
        try:
            # Check if a file was uploaded
            if 'file' not in request.files:
                flash('No file uploaded', 'danger')
                return redirect(request.url)
                
            file = request.files['file']
            
            # Check if file is empty
            if file.filename == '':
                flash('No file selected', 'danger')
                return redirect(request.url)
                
            # Check file extension
            if not allowed_file(file.filename):
                flash('File type not supported. Please upload CSV or Excel files only.', 'danger')
                return redirect(request.url)
                
            # Secure the filename
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            
            # Save the file
            file.save(file_path)
            
            # Log the upload
            log_document_upload(filename, 'driver_attendance', current_user.id if current_user.is_authenticated else None)
            
            # Create import log record
            from models.driver_attendance import AttendanceImportLog
            import_log = AttendanceImportLog(
                filename=filename,
                file_type=filename.rsplit('.', 1)[1].lower(),
                file_size=os.path.getsize(file_path),
                import_date=datetime.now(),
                user_id=current_user.id if current_user.is_authenticated else None,
                status='pending'
            )
            db.session.add(import_log)
            db.session.commit()
            
            # Process the file
            from utils.attendance_import import process_attendance_file
            result = process_attendance_file(file_path, import_log.id)
            
            if result['success']:
                # Update import log
                import_log.record_count = result['record_count']
                import_log.success = True
                import_log.status = 'completed'
                db.session.commit()
                
                flash(f"File processed successfully. {result['record_count']} records imported.", 'success')
                return redirect(url_for('driver_module.attendance_dashboard'))
            else:
                # Update import log with error
                import_log.success = False
                import_log.error_message = result['error']
                import_log.status = 'failed'
                db.session.commit()
                
                flash(f"Error processing file: {result['error']}", 'danger')
                return redirect(request.url)
        
        except Exception as e:
            logger.error(f"Error in upload_attendance route: {str(e)}")
            flash(f"An unexpected error occurred: {str(e)}", "danger")
            return redirect(url_for('driver_module.index'))

@driver_module_bp.route('/export_report', methods=['GET'])
@login_required
def export_report():
    """Redirect to the dedicated export route"""
    # Simply redirect to the dedicated exports blueprint
    return redirect(url_for('driver_exports.export_report', 
                          type=request.args.get('type', 'daily'),
                          format=request.args.get('format', 'xlsx'),
                          date=request.args.get('date'),
                          region=request.args.get('region'),
                          direct=request.args.get('direct', 'false')))


@driver_module_bp.route('/download_export/<filename>', methods=['GET'])
@login_required
def download_export(filename):
    """Redirect to the dedicated download route"""
    return redirect(url_for('driver_exports.download_export', filename=filename))