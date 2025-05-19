"""
Driver Module Controller

This module provides routes and functionality for the Driver module,
including daily reports, attendance tracking, and driver management.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

# Import activity logger
from utils.activity_logger import (
    log_navigation, log_document_upload, log_report_export,
    log_feature_usage, log_search
)

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
        # Import the models
        from models.driver_attendance import DriverAttendance, AttendanceRecord
        from sqlalchemy import func
        
        # Query all active drivers from the database
        drivers = DriverAttendance.query.filter_by(is_active=True).all()
        
        # Start building the result list
        result = []
        
        # Get the current date for "last active" calculation
        current_date = datetime.now().date()
        
        # For each driver, gather attendance statistics
        for driver in drivers:
            # Get attendance records for the last 30 days
            thirty_days_ago = current_date - timedelta(days=30)
            records = AttendanceRecord.query.filter_by(driver_id=driver.id).filter(
                AttendanceRecord.date >= thirty_days_ago,
                AttendanceRecord.date <= current_date
            ).all()
            
            # Calculate attendance metrics
            late_count = sum(1 for r in records if r.late_start)
            early_end_count = sum(1 for r in records if r.early_end)
            not_on_job_count = sum(1 for r in records if r.not_on_job)
            
            # Calculate last active date
            last_record = AttendanceRecord.query.filter_by(driver_id=driver.id).order_by(
                AttendanceRecord.date.desc()
            ).first()
            
            last_active = last_record.date.strftime('%Y-%m-%d') if last_record else "N/A"
            
            # Calculate an attendance score (percentage of days without issues)
            total_records = len(records)
            problem_records = late_count + early_end_count + not_on_job_count
            attendance_score = 100
            if total_records > 0:
                attendance_score = int(round((total_records - problem_records) / total_records * 100))
            
            # Get the most frequent job site
            job_site = "Unknown"
            if records:
                job_sites = {}
                for r in records:
                    if r.assigned_job and r.assigned_job.name:
                        site = r.assigned_job.name
                        job_sites[site] = job_sites.get(site, 0) + 1
                
                if job_sites:
                    job_site = max(job_sites.items(), key=lambda x: x[1])[0]
            
            # Get the most recent vehicle/asset
            vehicle = "None"
            if records:
                vehicles = [r.asset_id for r in records if r.asset_id]
                if vehicles:
                    vehicle = vehicles[0]  # Most recent vehicle
            
            # Add driver to result list
            result.append({
                'id': str(driver.id),
                'name': driver.full_name,
                'employee_id': driver.employee_id,
                'status': 'Active' if driver.is_active else 'Inactive',
                'region': driver.division,
                'vehicle': vehicle,
                'job_site': job_site,
                'attendance_score': attendance_score,
                'late_count': late_count,
                'early_end_count': early_end_count,
                'not_on_job_count': not_on_job_count,
                'last_active': last_active
            })
        
        return result
    except Exception as e:
        # Log the error and return sample data as fallback
        logger.error(f"Error fetching driver data: {str(e)}")
        # Return an empty list if there's an error
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
        # Import models
        from models.driver_attendance import DriverAttendance, AttendanceRecord, JobSiteAttendance
        from sqlalchemy import func
        
        # Parse date or use today
        report_date = datetime.now().date()
        if date_str:
            try:
                report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                logger.error(f"Invalid date format: {date_str}")
        
        # Get all attendance records for the specified date
        records = AttendanceRecord.query.filter(
            AttendanceRecord.date == report_date
        ).all()
        
        # If no records found, return empty report structure
        if not records:
            logger.warning(f"No attendance records found for {report_date}")
            return {
                'date': report_date.strftime('%Y-%m-%d'),
                'total_drivers': 0,
                'on_time': 0,
                'late_start': 0,
                'early_end': 0,
                'not_on_job': 0,
                'regions': [],
                'active_job_sites': 0,
                'late_drivers': [],
                'early_end_drivers': [],
                'not_on_job_drivers': []
            }
        
        # Count metrics
        total_drivers = len(records)
        late_start_count = sum(1 for r in records if r.late_start)
        early_end_count = sum(1 for r in records if r.early_end)
        not_on_job_count = sum(1 for r in records if r.not_on_job)
        on_time_count = total_drivers - (late_start_count + early_end_count + not_on_job_count)
        
        # Get unique regions and job sites
        regions = list(set(d.driver_attendance.division for d in records if d.driver_attendance and d.driver_attendance.division))
        job_sites = set()
        for r in records:
            if r.assigned_job and r.assigned_job.name:
                job_sites.add(r.assigned_job.name)
        
        # Get late drivers
        late_drivers = []
        for record in records:
            if record.late_start and record.driver_attendance:
                driver = record.driver_attendance
                job_site_name = record.assigned_job.name if record.assigned_job else "Unknown"
                
                # Calculate minutes late
                minutes_late = 0
                if record.expected_start_time and record.actual_start_time:
                    time_diff = record.actual_start_time - record.expected_start_time
                    minutes_late = int(time_diff.total_seconds() / 60)
                
                # Format times for display
                scheduled_start = record.expected_start_time.strftime('%I:%M %p') if record.expected_start_time else "Unknown"
                actual_start = record.actual_start_time.strftime('%I:%M %p') if record.actual_start_time else "Unknown"
                
                late_drivers.append({
                    'id': str(driver.id),
                    'name': driver.full_name,
                    'employee_id': driver.employee_id,
                    'region': driver.division,
                    'job_site': job_site_name,
                    'scheduled_start': scheduled_start,
                    'actual_start': actual_start,
                    'minutes_late': minutes_late,
                    'vehicle': record.asset_id or "Unknown",
                    'supervisor': "Not Available"  # Supervisor data not available in current model
                })
        
        # Get early end drivers
        early_end_drivers = []
        for record in records:
            if record.early_end and record.driver_attendance:
                driver = record.driver_attendance
                job_site_name = record.assigned_job.name if record.assigned_job else "Unknown"
                
                # Calculate minutes early
                minutes_early = 0
                if record.expected_end_time and record.actual_end_time:
                    time_diff = record.expected_end_time - record.actual_end_time
                    minutes_early = int(time_diff.total_seconds() / 60)
                
                # Format times for display
                scheduled_end = record.expected_end_time.strftime('%I:%M %p') if record.expected_end_time else "Unknown"
                actual_end = record.actual_end_time.strftime('%I:%M %p') if record.actual_end_time else "Unknown"
                
                early_end_drivers.append({
                    'id': str(driver.id),
                    'name': driver.full_name,
                    'employee_id': driver.employee_id,
                    'region': driver.division,
                    'job_site': job_site_name,
                    'scheduled_end': scheduled_end,
                    'actual_end': actual_end,
                    'minutes_early': minutes_early,
                    'vehicle': record.asset_id or "Unknown",
                    'supervisor': "Not Available"  # Supervisor data not available in current model
                })
        
        # Get not on job drivers
        not_on_job_drivers = []
        for record in records:
            if record.not_on_job and record.driver_attendance:
                driver = record.driver_attendance
                
                # Get assigned and actual job sites
                assigned_site = record.assigned_job.name if record.assigned_job else "Unknown"
                actual_site = record.actual_job.name if record.actual_job else "Unknown"
                
                scheduled_start = record.expected_start_time.strftime('%I:%M %p') if record.expected_start_time else "Unknown"
                
                not_on_job_drivers.append({
                    'id': str(driver.id),
                    'name': driver.full_name,
                    'employee_id': driver.employee_id,
                    'region': driver.division,
                    'job_site': assigned_site,
                    'scheduled_start': scheduled_start,
                    'vehicle': record.asset_id or "Unknown",
                    'supervisor': "Not Available",  # Supervisor data not available in current model
                    'reason': f"Driver at {actual_site} instead of {assigned_site}",
                    'notes': record.notes or "No additional notes"
                })
        
        # Build and return the report
        return {
            'date': report_date.strftime('%Y-%m-%d'),
            'total_drivers': total_drivers,
            'on_time': on_time_count,
            'late_start': late_start_count,
            'early_end': early_end_count,
            'not_on_job': not_on_job_count,
            'regions': regions,
            'active_job_sites': len(job_sites),
            'late_drivers': late_drivers,
            'early_end_drivers': early_end_drivers,
            'not_on_job_drivers': not_on_job_drivers
        }
        
    except Exception as e:
        logger.error(f"Error fetching daily report data: {str(e)}")
        # Return a basic structure in case of error
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_drivers': 0,
            'on_time': 0,
            'late_start': 0,
            'early_end': 0,
            'not_on_job': 0,
            'regions': [],
            'active_job_sites': 0,
            'late_drivers': [],
            'early_end_drivers': [],
            'not_on_job_drivers': []
        }

def get_sample_attendance_stats():
    """
    Get sample attendance statistics for dashboard
    In a real application, this would be calculated from database records
    """
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30, 0, -1)]
    
    return {
        'dates': dates,
        'on_time_percentages': [82, 85, 88, 91, 87, 89, 90, 88, 86, 89, 90, 92, 91, 93, 92, 90, 88, 91, 92, 93, 95, 94, 93, 91, 90, 92, 91, 89, 90, 92],
        'late_start_counts': [7, 6, 5, 3, 5, 4, 4, 5, 6, 4, 4, 3, 4, 3, 3, 4, 5, 4, 3, 3, 2, 2, 3, 4, 4, 3, 4, 4, 4, 3],
        'early_end_counts': [5, 4, 3, 2, 3, 3, 2, 3, 3, 3, 2, 2, 2, 1, 2, 2, 3, 1, 2, 1, 1, 2, 1, 2, 2, 2, 1, 3, 2, 2],
        'not_on_job_counts': [2, 2, 1, 1, 2, 1, 1, 1, 2, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0],
        'job_sites': [
            {'id': '101', 'name': 'NTTA Eastern Extension', 'on_time_percentage': 89, 'driver_count': 12},
            {'id': '102', 'name': 'DFW Connector', 'on_time_percentage': 92, 'driver_count': 8},
            {'id': '103', 'name': 'Harbor Bridge', 'on_time_percentage': 86, 'driver_count': 6},
            {'id': '104', 'name': 'Loop 88', 'on_time_percentage': 95, 'driver_count': 5},
            {'id': '105', 'name': 'I-45 Expansion', 'on_time_percentage': 91, 'driver_count': 11}
        ],
        'regions': [
            {'id': 'DFW', 'name': 'Dallas-Fort Worth', 'on_time_percentage': 91, 'driver_count': 20},
            {'id': 'HOU', 'name': 'Houston', 'on_time_percentage': 88, 'driver_count': 15},
            {'id': 'WTX', 'name': 'West Texas', 'on_time_percentage': 94, 'driver_count': 7}
        ]
    }

# Routes
@driver_module_bp.route('/')
@login_required
def index():
    """Driver module home page"""
    log_navigation(current_user.id, 'driver_module.index')
    
    # Get summary statistics from the database
    drivers = get_drivers()
    driver_count = len(drivers)
    active_drivers = len([d for d in drivers if d['status'] == 'Active'])
    
    # Get daily report data
    daily_report = get_daily_report()
    late_count = len(daily_report['late_drivers'])
    early_end_count = len(daily_report['early_end_drivers'])
    not_on_job_count = len(daily_report['not_on_job_drivers'])
    
    # Calculate attendance score
    total_drivers = daily_report['total_drivers']
    on_time_drivers = daily_report['on_time']
    attendance_score = round((on_time_drivers / total_drivers) * 100) if total_drivers > 0 else 0
    
    return render_template('drivers/index.html',
                           driver_count=driver_count,
                           active_drivers=active_drivers,
                           late_count=late_count,
                           early_end_count=early_end_count,
                           not_on_job_count=not_on_job_count,
                           attendance_score=attendance_score)

@driver_module_bp.route('/daily_report')
@login_required
def daily_report():
    """Daily driver attendance report"""
    log_navigation(current_user.id, 'driver_module.daily_report')
    
    report_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    report_data = get_daily_report(report_date)
    
    return render_template('drivers/daily_report.html', 
                          report=report_data, 
                          selected_date=report_date)

@driver_module_bp.route('/attendance_dashboard')
@login_required
def attendance_dashboard():
    """Attendance dashboard with trends and metrics"""
    log_navigation(current_user.id, 'driver_module.attendance_dashboard')
    
    stats = get_sample_attendance_stats()
    
    return render_template('drivers/attendance_dashboard.html', stats=stats)

@driver_module_bp.route('/driver_list')
@login_required
def driver_list():
    """List all drivers with filtering options"""
    log_navigation(current_user.id, 'driver_module.driver_list')
    
    drivers = get_sample_drivers()
    
    # Handle filtering
    region = request.args.get('region')
    status = request.args.get('status')
    search = request.args.get('search', '').lower()
    
    if region:
        drivers = [d for d in drivers if d['region'] == region]
    
    if status:
        drivers = [d for d in drivers if d['status'] == status]
    
    if search:
        drivers = [d for d in drivers if search in d['name'].lower() or 
                   search in d['employee_id'].lower() or
                   search in d['job_site'].lower()]
        
        # Log search activity
        log_search(search, results_count=len(drivers), 
                  filters={'region': region, 'status': status})
    
    return render_template('drivers/driver_list.html', 
                          drivers=drivers,
                          filter_region=region,
                          filter_status=status,
                          search_query=search)

@driver_module_bp.route('/driver_detail/<driver_id>')
@login_required
def driver_detail(driver_id):
    """Driver detail page with attendance history"""
    log_navigation(current_user.id, f'driver_module.driver_detail.{driver_id}')
    
    # Find the driver in our sample data
    drivers = get_sample_drivers()
    driver = next((d for d in drivers if d['id'] == driver_id), None)
    
    if not driver:
        flash('Driver not found', 'danger')
        return redirect(url_for('driver_module.driver_list'))
    
    # Generate sample attendance history
    today = datetime.now()
    history = []
    
    for i in range(30):
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        
        # Randomize status but weight toward on-time
        import random
        status_weights = {'on_time': 0.85, 'late': 0.10, 'early_end': 0.03, 'not_on_job': 0.02}
        status = random.choices(
            list(status_weights.keys()), 
            weights=list(status_weights.values()), 
            k=1
        )[0]
        
        entry = {
            'date': date_str,
            'status': status,
            'scheduled_start': '07:00 AM',
            'actual_start': '07:00 AM',
            'scheduled_end': '05:30 PM',
            'actual_end': '05:30 PM',
            'job_site': driver['job_site'],
            'vehicle': driver['vehicle']
        }
        
        # Adjust times based on status
        if status == 'late':
            minutes_late = random.randint(5, 45)
            actual_time = (date.replace(hour=7, minute=0) + 
                          timedelta(minutes=minutes_late))
            entry['actual_start'] = actual_time.strftime('%I:%M %p')
            entry['minutes_late'] = minutes_late
            
        elif status == 'early_end':
            minutes_early = random.randint(5, 30)
            actual_time = (date.replace(hour=17, minute=30) - 
                          timedelta(minutes=minutes_early))
            entry['actual_end'] = actual_time.strftime('%I:%M %p')
            entry['minutes_early'] = minutes_early
            
        elif status == 'not_on_job':
            entry['reason'] = random.choice([
                'Vehicle maintenance',
                'Weather conditions',
                'Job site closure',
                'Equipment failure'
            ])
            
        history.append(entry)
    
    return render_template('drivers/driver_detail.html', 
                          driver=driver,
                          attendance_history=history)

@driver_module_bp.route('/job_site_detail/<site_id>')
@login_required
def job_site_detail(site_id):
    """Job site detail page with attendance metrics"""
    log_navigation(current_user.id, f'driver_module.job_site_detail.{site_id}')
    
    # Look up job site from our sample data
    stats = get_sample_attendance_stats()
    site = next((s for s in stats['job_sites'] if s['id'] == site_id), None)
    
    if not site:
        flash('Job site not found', 'danger')
        return redirect(url_for('driver_module.attendance_dashboard'))
    
    # Generate sample drivers for this job site
    drivers = [d for d in get_sample_drivers() if site_id in d['job_site']]
    
    # Generate sample daily metrics for the last 14 days
    today = datetime.now()
    daily_metrics = []
    
    for i in range(14):
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        
        import random
        on_time_pct = random.randint(80, 98)
        driver_count = random.randint(5, 15)
        on_time_count = int((on_time_pct / 100) * driver_count)
        
        daily_metrics.append({
            'date': date_str,
            'driver_count': driver_count,
            'on_time_count': on_time_count,
            'late_count': driver_count - on_time_count,
            'on_time_percentage': on_time_pct
        })
    
    return render_template('drivers/job_site_detail.html',
                          site=site,
                          drivers=drivers,
                          daily_metrics=daily_metrics)

@driver_module_bp.route('/region_detail/<region_id>')
@login_required
def region_detail(region_id):
    """Region detail page with attendance metrics"""
    log_navigation(current_user.id, f'driver_module.region_detail.{region_id}')
    
    # Look up region from our sample data
    stats = get_sample_attendance_stats()
    region = next((r for r in stats['regions'] if r['id'] == region_id), None)
    
    if not region:
        flash('Region not found', 'danger')
        return redirect(url_for('driver_module.attendance_dashboard'))
    
    # Get drivers for this region
    drivers = [d for d in get_sample_drivers() if d['region'] == region_id]
    
    # Get job sites in this region
    job_sites = [s for s in stats['job_sites'] if any(d['job_site'] == s['name'] for d in drivers)]
    
    # Generate sample monthly metrics for the last 6 months
    today = datetime.now()
    monthly_metrics = []
    
    for i in range(6):
        month_date = today.replace(day=1) - timedelta(days=i*30)
        month_str = month_date.strftime('%B %Y')
        
        import random
        on_time_pct = random.randint(80, 95)
        driver_count = random.randint(15, 25)
        on_time_count = int((on_time_pct / 100) * driver_count)
        
        monthly_metrics.append({
            'month': month_str,
            'driver_count': driver_count,
            'on_time_count': on_time_count,
            'late_count': driver_count - on_time_count,
            'on_time_percentage': on_time_pct
        })
    
    return render_template('drivers/region_detail.html',
                          region=region,
                          drivers=drivers,
                          job_sites=job_sites,
                          monthly_metrics=monthly_metrics)

@driver_module_bp.route('/upload_attendance', methods=['GET', 'POST'])
@login_required
def upload_attendance():
    """Upload attendance file for processing"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Log the upload
            log_document_upload(
                filename=filename,
                file_type=filename.rsplit('.', 1)[1].lower(),
                file_size=file_size
            )
            
            # In a real application, this would trigger processing
            # For demonstration, we'll just show success
            flash(f'File {filename} uploaded successfully and queued for processing', 'success')
            return redirect(url_for('driver_module.daily_report'))
        else:
            flash(f'File type not allowed. Please upload {", ".join(ALLOWED_EXTENSIONS)} files.', 'danger')
            
    return render_template('drivers/upload_attendance.html')

@driver_module_bp.route('/export_report', methods=['GET'])
@login_required
def export_report():
    """Export report in specified format"""
    report_type = request.args.get('type', 'daily')
    export_format = request.args.get('format', 'pdf')
    direct_download = request.args.get('direct', 'false') == 'true'
    
    # Generate a filename with timestamp for uniqueness
    timestamp = datetime.now()
    date_str = timestamp.strftime('%Y%m%d_%H%M%S')
    filename = f"{report_type}_report_{date_str}.{export_format}"
    
    # Create the output file based on requested format
    file_path = os.path.join(EXPORTS_FOLDER, filename)
    
    # Get the sample data that would be in the report
    report_data = get_sample_daily_report()
    
    if export_format == 'csv':
        # Generate CSV file with proper formatting
        import csv
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            writer.writerow(['Driver Report', f'Date: {timestamp.strftime("%m/%d/%Y")}'])
            writer.writerow(['Generated:', timestamp.strftime('%m/%d/%Y %I:%M:%S %p')])
            writer.writerow([])
            
            # Summary data
            writer.writerow(['Summary', ''])
            writer.writerow(['Total Drivers', report_data['total_drivers']])
            writer.writerow(['On Time', report_data['on_time']])
            writer.writerow(['Late Start', report_data['late_start']])
            writer.writerow(['Early End', report_data['early_end']])
            writer.writerow(['Not on Job', report_data['not_on_job']])
            writer.writerow([])
            
            # Late drivers
            writer.writerow(['Late Drivers', ''])
            writer.writerow(['Employee ID', 'Driver Name', 'Region', 'Job Site', 'Scheduled Start', 'Actual Start', 'Minutes Late', 'Vehicle'])
            for driver in report_data['late_drivers']:
                writer.writerow([
                    driver['employee_id'],
                    driver['name'],
                    driver['region'],
                    driver['job_site'],
                    driver['scheduled_start'],
                    driver['actual_start'],
                    driver['minutes_late'],
                    driver['vehicle']
                ])
            writer.writerow([])
            
            # Early end drivers
            writer.writerow(['Early End Drivers', ''])
            writer.writerow(['Employee ID', 'Driver Name', 'Region', 'Job Site', 'Scheduled End', 'Actual End', 'Minutes Early', 'Vehicle'])
            for driver in report_data['early_end_drivers']:
                writer.writerow([
                    driver['employee_id'],
                    driver['name'],
                    driver['region'],
                    driver['job_site'],
                    driver['scheduled_end'],
                    driver['actual_end'],
                    driver['minutes_early'],
                    driver['vehicle']
                ])
            
    elif export_format == 'xlsx':
        # Generate Excel file with formatting
        try:
            import pandas as pd
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill
            
            # Create workbook and sheet
            wb = Workbook()
            ws = wb.active
            ws.title = "Driver Report"
            
            # Add header with formatting
            ws['A1'] = f"Driver Daily Report - {timestamp.strftime('%m/%d/%Y')}"
            ws['A1'].font = Font(bold=True, size=14)
            ws.merge_cells('A1:H1')
            
            ws['A2'] = f"Generated: {timestamp.strftime('%m/%d/%Y %I:%M:%S %p')}"
            ws.merge_cells('A2:H2')
            
            # Summary section
            ws['A4'] = "Summary"
            ws['A4'].font = Font(bold=True)
            
            labels = ["Total Drivers", "On Time", "Late Start", "Early End", "Not on Job"]
            values = [
                report_data['total_drivers'],
                report_data['on_time'],
                report_data['late_start'],
                report_data['early_end'],
                report_data['not_on_job']
            ]
            
            for i, (label, value) in enumerate(zip(labels, values)):
                ws[f'A{i+5}'] = label
                ws[f'B{i+5}'] = value
            
            # Late drivers section
            row = 11
            ws[f'A{row}'] = "Late Drivers"
            ws[f'A{row}'].font = Font(bold=True)
            row += 1
            
            # Header row for late drivers
            headers = ['Employee ID', 'Driver Name', 'Region', 'Job Site', 'Scheduled Start', 'Actual Start', 'Minutes Late', 'Vehicle']
            for col, header in enumerate(headers, start=1):
                ws.cell(row=row, column=col, value=header).font = Font(bold=True)
            row += 1
            
            # Data rows for late drivers
            for driver in report_data['late_drivers']:
                ws.cell(row=row, column=1, value=driver['employee_id'])
                ws.cell(row=row, column=2, value=driver['name'])
                ws.cell(row=row, column=3, value=driver['region'])
                ws.cell(row=row, column=4, value=driver['job_site'])
                ws.cell(row=row, column=5, value=driver['scheduled_start'])
                ws.cell(row=row, column=6, value=driver['actual_start'])
                ws.cell(row=row, column=7, value=driver['minutes_late'])
                ws.cell(row=row, column=8, value=driver['vehicle'])
                row += 1
            
            # Early end drivers section
            row += 2
            ws[f'A{row}'] = "Early End Drivers"
            ws[f'A{row}'].font = Font(bold=True)
            row += 1
            
            # Header row for early end drivers
            headers = ['Employee ID', 'Driver Name', 'Region', 'Job Site', 'Scheduled End', 'Actual End', 'Minutes Early', 'Vehicle']
            for col, header in enumerate(headers, start=1):
                ws.cell(row=row, column=col, value=header).font = Font(bold=True)
            row += 1
            
            # Data rows for early end drivers
            for driver in report_data['early_end_drivers']:
                ws.cell(row=row, column=1, value=driver['employee_id'])
                ws.cell(row=row, column=2, value=driver['name'])
                ws.cell(row=row, column=3, value=driver['region'])
                ws.cell(row=row, column=4, value=driver['job_site'])
                ws.cell(row=row, column=5, value=driver['scheduled_end'])
                ws.cell(row=row, column=6, value=driver['actual_end'])
                ws.cell(row=row, column=7, value=driver['minutes_early'])
                ws.cell(row=row, column=8, value=driver['vehicle'])
                row += 1
            
            # Auto-adjust column widths
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                adjusted_width = (max_length + 2)
                ws.column_dimensions[column].width = adjusted_width
            
            # Save the workbook
            wb.save(file_path)
            
        except Exception as e:
            logging.error(f"Error generating Excel file: {e}")
            # Fallback to simpler file if Excel generation fails
            with open(file_path, 'w') as f:
                f.write(f"Driver Report - {timestamp.strftime('%m/%d/%Y')}\n")
                f.write(f"Generated: {timestamp.strftime('%m/%d/%Y %I:%M:%S %p')}\n\n")
                f.write(f"Total Drivers: {report_data['total_drivers']}\n")
                f.write(f"On Time: {report_data['on_time']}\n")
                f.write(f"Late Start: {report_data['late_start']}\n")
                f.write(f"Early End: {report_data['early_end']}\n")
                f.write(f"Not on Job: {report_data['not_on_job']}\n")
            
    else:  # Default to PDF or text
        # Generate a simple PDF using reportlab if PDF requested
        if export_format == 'pdf':
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib import colors
                
                # Create document
                doc = SimpleDocTemplate(file_path, pagesize=letter)
                styles = getSampleStyleSheet()
                elements = []
                
                # Add title
                title_style = styles['Heading1']
                elements.append(Paragraph(f"Driver Daily Report - {timestamp.strftime('%m/%d/%Y')}", title_style))
                elements.append(Spacer(1, 12))
                elements.append(Paragraph(f"Generated: {timestamp.strftime('%m/%d/%Y %I:%M:%S %p')}", styles['Normal']))
                elements.append(Spacer(1, 24))
                
                # Summary section
                elements.append(Paragraph("Summary", styles['Heading2']))
                
                summary_data = [
                    ["Total Drivers", str(report_data['total_drivers'])],
                    ["On Time", str(report_data['on_time'])],
                    ["Late Start", str(report_data['late_start'])],
                    ["Early End", str(report_data['early_end'])],
                    ["Not on Job", str(report_data['not_on_job'])]
                ]
                
                summary_table = Table(summary_data, colWidths=[200, 100])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(summary_table)
                elements.append(Spacer(1, 24))
                
                # Late drivers section
                elements.append(Paragraph("Late Drivers", styles['Heading2']))
                
                if report_data['late_drivers']:
                    # Create table header
                    late_data = [['Employee ID', 'Driver Name', 'Region', 'Job Site', 'Scheduled', 'Actual', 'Minutes Late']]
                    
                    # Add data rows
                    for driver in report_data['late_drivers']:
                        late_data.append([
                            driver['employee_id'],
                            driver['name'],
                            driver['region'],
                            driver['job_site'],
                            driver['scheduled_start'],
                            driver['actual_start'],
                            str(driver['minutes_late'])
                        ])
                    
                    late_table = Table(late_data, colWidths=[80, 100, 60, 100, 70, 70, 60])
                    late_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(late_table)
                else:
                    elements.append(Paragraph("No late drivers reported today", styles['Normal']))
                
                elements.append(Spacer(1, 24))
                
                # Early end drivers section
                elements.append(Paragraph("Early End Drivers", styles['Heading2']))
                
                if report_data['early_end_drivers']:
                    # Create table header
                    early_data = [['Employee ID', 'Driver Name', 'Region', 'Job Site', 'Scheduled', 'Actual', 'Minutes Early']]
                    
                    # Add data rows
                    for driver in report_data['early_end_drivers']:
                        early_data.append([
                            driver['employee_id'],
                            driver['name'],
                            driver['region'],
                            driver['job_site'],
                            driver['scheduled_end'],
                            driver['actual_end'],
                            str(driver['minutes_early'])
                        ])
                    
                    early_table = Table(early_data, colWidths=[80, 100, 60, 100, 70, 70, 60])
                    early_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(early_table)
                else:
                    elements.append(Paragraph("No early end drivers reported today", styles['Normal']))
                
                # Build the PDF
                doc.build(elements)
                
            except Exception as e:
                logging.error(f"Error generating PDF: {e}")
                # Create a text file as fallback
                with open(file_path, 'w') as f:
                    f.write(f"Driver Report - {timestamp.strftime('%m/%d/%Y')}\n")
                    f.write(f"Generated: {timestamp.strftime('%m/%d/%Y %I:%M:%S %p')}\n\n")
                    f.write(f"Total Drivers: {report_data['total_drivers']}\n")
                    f.write(f"On Time: {report_data['on_time']}\n")
                    f.write(f"Late Start: {report_data['late_start']}\n")
                    f.write(f"Early End: {report_data['early_end']}\n")
                    f.write(f"Not on Job: {report_data['not_on_job']}\n")
        else:
            # Create a text file
            with open(file_path, 'w') as f:
                f.write(f"Driver Report - {timestamp.strftime('%m/%d/%Y')}\n")
                f.write(f"Generated: {timestamp.strftime('%m/%d/%Y %I:%M:%S %p')}\n\n")
                f.write(f"Total Drivers: {report_data['total_drivers']}\n")
                f.write(f"On Time: {report_data['on_time']}\n")
                f.write(f"Late Start: {report_data['late_start']}\n")
                f.write(f"Early End: {report_data['early_end']}\n")
                f.write(f"Not on Job: {report_data['not_on_job']}\n")
    
    # Log the export
    log_report_export(
        report_type=report_type,
        export_format=export_format
    )
    
    # If direct download requested, send the file directly
    if direct_download:
        return send_file(file_path, as_attachment=True)
    
    # Otherwise, show a confirmation page with navigation options
    return render_template(
        'drivers/export_success.html',
        filename=filename,
        report_type=report_type,
        export_format=export_format,
        download_url=url_for('driver_module.download_export', filename=filename),
        now=datetime.now()
    )

@driver_module_bp.route('/download_export/<filename>')
@login_required
def download_export(filename):
    """Download a previously exported file"""
    file_path = os.path.join(EXPORTS_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    flash('Export file not found.', 'danger')
    return redirect(url_for('driver_module.daily_report'))

# API endpoints for AJAX requests
@driver_module_bp.route('/api/attendance_chart_data')
@login_required
def attendance_chart_data():
    """Get attendance data for charts"""
    stats = get_sample_attendance_stats()
    
    # Log feature usage
    log_feature_usage('attendance_chart_data')
    
    return jsonify(stats)

@driver_module_bp.route('/api/driver_search')
@login_required
def driver_search():
    """Search for drivers"""
    query = request.args.get('q', '').lower()
    drivers = get_sample_drivers()
    
    if query:
        drivers = [d for d in drivers if 
                   query in d['name'].lower() or 
                   query in d['employee_id'].lower() or
                   query in d['job_site'].lower()]
        
        # Log search
        log_search(query, results_count=len(drivers))
    
    return jsonify({'results': drivers})

@driver_module_bp.route('/api/get_driver/<driver_id>')
@login_required
def get_driver(driver_id):
    """Get driver by ID"""
    drivers = get_sample_drivers()
    driver = next((d for d in drivers if d['id'] == driver_id), None)
    
    if not driver:
        return jsonify({'error': 'Driver not found'}), 404
    
    return jsonify(driver)