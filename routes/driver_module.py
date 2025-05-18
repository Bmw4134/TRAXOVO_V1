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

def get_sample_drivers():
    """
    Get sample driver data for demonstration
    In a real application, this would fetch from the database
    """
    return [
        {
            'id': '1001',
            'name': 'John Smith',
            'employee_id': 'E10023',
            'status': 'Active',
            'region': 'DFW',
            'vehicle': 'T-123',
            'job_site': 'NTTA Eastern Extension',
            'attendance_score': 95,
            'late_count': 2,
            'early_end_count': 1,
            'not_on_job_count': 0,
            'last_active': '2025-05-17'
        },
        {
            'id': '1002',
            'name': 'Sarah Johnson',
            'employee_id': 'E10045',
            'status': 'Active',
            'region': 'DFW',
            'vehicle': 'T-156',
            'job_site': 'DFW Connector',
            'attendance_score': 98,
            'late_count': 1,
            'early_end_count': 0,
            'not_on_job_count': 1,
            'last_active': '2025-05-17'
        },
        {
            'id': '1003',
            'name': 'Michael Brown',
            'employee_id': 'E10078',
            'status': 'Inactive',
            'region': 'HOU',
            'vehicle': 'T-204',
            'job_site': 'Harbor Bridge',
            'attendance_score': 82,
            'late_count': 5,
            'early_end_count': 3,
            'not_on_job_count': 2,
            'last_active': '2025-05-15'
        },
        {
            'id': '1004',
            'name': 'Lisa Williams',
            'employee_id': 'E10089',
            'status': 'Active',
            'region': 'WTX',
            'vehicle': 'T-187',
            'job_site': 'Loop 88',
            'attendance_score': 100,
            'late_count': 0,
            'early_end_count': 0,
            'not_on_job_count': 0,
            'last_active': '2025-05-17'
        },
        {
            'id': '1005',
            'name': 'David Martinez',
            'employee_id': 'E10103',
            'status': 'Active',
            'region': 'HOU',
            'vehicle': 'T-239',
            'job_site': 'I-45 Expansion',
            'attendance_score': 91,
            'late_count': 3,
            'early_end_count': 2,
            'not_on_job_count': 0,
            'last_active': '2025-05-16'
        }
    ]

def get_sample_daily_report():
    """
    Get sample daily report data for demonstration
    In a real application, this would be generated from database records
    """
    today = datetime.now().strftime('%Y-%m-%d')
    
    return {
        'date': today,
        'total_drivers': 42,
        'on_time': 35,
        'late_start': 4,
        'early_end': 2,
        'not_on_job': 1,
        'regions': ['DFW', 'HOU', 'WTX'],
        'active_job_sites': 12,
        'late_drivers': [
            {
                'id': '1001',
                'name': 'John Smith',
                'employee_id': 'E10023',
                'region': 'DFW',
                'job_site': 'NTTA Eastern Extension',
                'scheduled_start': '07:00 AM',
                'actual_start': '07:28 AM',
                'minutes_late': 28,
                'vehicle': 'T-123',
                'supervisor': 'James Wilson'
            },
            {
                'id': '1002',
                'name': 'Sarah Johnson',
                'employee_id': 'E10045',
                'region': 'DFW',
                'job_site': 'DFW Connector',
                'scheduled_start': '06:30 AM',
                'actual_start': '06:47 AM',
                'minutes_late': 17,
                'vehicle': 'T-156',
                'supervisor': 'Michael Roberts'
            },
            {
                'id': '1005',
                'name': 'David Martinez',
                'employee_id': 'E10103',
                'region': 'HOU',
                'job_site': 'I-45 Expansion',
                'scheduled_start': '07:00 AM',
                'actual_start': '07:15 AM',
                'minutes_late': 15,
                'vehicle': 'T-239',
                'supervisor': 'Jennifer Lopez'
            },
            {
                'id': '1006',
                'name': 'Robert Taylor',
                'employee_id': 'E10112',
                'region': 'DFW',
                'job_site': 'NTTA Eastern Extension',
                'scheduled_start': '07:00 AM',
                'actual_start': '07:09 AM',
                'minutes_late': 9,
                'vehicle': 'T-174',
                'supervisor': 'James Wilson'
            }
        ],
        'early_end_drivers': [
            {
                'id': '1001',
                'name': 'John Smith',
                'employee_id': 'E10023',
                'region': 'DFW',
                'job_site': 'NTTA Eastern Extension',
                'scheduled_end': '05:30 PM',
                'actual_end': '05:12 PM',
                'minutes_early': 18,
                'vehicle': 'T-123',
                'supervisor': 'James Wilson'
            },
            {
                'id': '1005',
                'name': 'David Martinez',
                'employee_id': 'E10103',
                'region': 'HOU',
                'job_site': 'I-45 Expansion',
                'scheduled_end': '06:00 PM',
                'actual_end': '05:42 PM',
                'minutes_early': 18,
                'vehicle': 'T-239',
                'supervisor': 'Jennifer Lopez'
            }
        ],
        'not_on_job_drivers': [
            {
                'id': '1003',
                'name': 'Michael Brown',
                'employee_id': 'E10078',
                'region': 'HOU',
                'job_site': 'Harbor Bridge',
                'scheduled_start': '07:00 AM',
                'vehicle': 'T-204',
                'supervisor': 'Jennifer Lopez',
                'reason': 'Vehicle located at maintenance facility',
                'notes': 'Driver reported maintenance issues with vehicle T-204'
            }
        ]
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
    log_navigation('driver_module.index')
    
    # Get summary statistics
    driver_count = len(get_sample_drivers())
    active_drivers = len([d for d in get_sample_drivers() if d['status'] == 'Active'])
    
    daily_report = get_sample_daily_report()
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
    log_navigation('driver_module.daily_report')
    
    report_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    report_data = get_sample_daily_report()
    
    return render_template('drivers/daily_report.html', 
                          report=report_data, 
                          selected_date=report_date)

@driver_module_bp.route('/attendance_dashboard')
@login_required
def attendance_dashboard():
    """Attendance dashboard with trends and metrics"""
    log_navigation('driver_module.attendance_dashboard')
    
    stats = get_sample_attendance_stats()
    
    return render_template('drivers/attendance_dashboard.html', stats=stats)

@driver_module_bp.route('/driver_list')
@login_required
def driver_list():
    """List all drivers with filtering options"""
    log_navigation('driver_module.driver_list')
    
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
    log_navigation(f'driver_module.driver_detail.{driver_id}')
    
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
    log_navigation(f'driver_module.job_site_detail.{site_id}')
    
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
    log_navigation(f'driver_module.region_detail.{region_id}')
    
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
    
    # Generate a filename
    date_str = datetime.now().strftime('%Y%m%d')
    filename = f"{report_type}_report_{date_str}.{export_format}"
    
    # In a real application, this would generate the actual report file
    # For demonstration, we'll create a simple text file
    file_path = os.path.join(EXPORTS_FOLDER, filename)
    
    with open(file_path, 'w') as f:
        f.write(f"Example {report_type} report exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Format: {export_format}\n")
        f.write("This is a placeholder for the actual report content.")
    
    # Log the export
    log_report_export(
        report_type=report_type,
        export_format=export_format
    )
    
    # Send the file
    return send_file(file_path, as_attachment=True)

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