"""
TRAXORA Fleet Management System - Driver Reports Routes

This module provides routes for the driver reporting system, including:
- User-friendly web interface for report generation
- File upload handling for data sources
- GroundWorks timecard comparison
- Report viewing and download
"""
import os
import json
import logging
import traceback
import pandas as pd
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, jsonify, send_file, current_app, abort
)
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest

from driver_pipeline import DriverPipeline
from utils.timecard_processor import process_groundworks_timecards, compare_timecards_with_gps

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
driver_reports_bp = Blueprint('driver_reports', __name__, url_prefix='/driver-reports')

# Constants
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
REPORT_TYPES = ['pdf', 'excel', 'json', 'pmr_late', 'pmr_early_end', 'pmr_not_on_job', 'activity']

def allowed_file(filename):
    """Check if file extension is allowed"""
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_upload_directory():
    """Get upload directory, creating it if needed"""
    upload_dir = os.path.join(current_app.root_path, 'uploads', 'driver_reports')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

def get_data_directory():
    """Get data directory, creating it if needed"""
    data_dir = os.path.join(current_app.root_path, 'data', 'driver_reports')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_reports_directory():
    """Get reports directory, creating it if needed"""
    reports_dir = os.path.join(current_app.root_path, 'reports', 'driver_reports')
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir

def process_uploaded_files(request_files, file_type):
    """Process and save uploaded files
    
    Args:
        request_files: FileStorage object(s) from request
        file_type: Type of files ('driving_history', 'activity_detail', etc.)
    
    Returns:
        list: Paths to saved files
    """
    if file_type not in request_files:
        return []
    
    files = request_files.getlist(file_type)
    if not files or files[0].filename == '':
        return []
    
    saved_files = []
    for file in files:
        if file and allowed_file(file.filename):
            # Make unique filename with type, date and time
            filename = f"{file_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secure_filename(file.filename)}"
            file_path = os.path.join(get_upload_directory(), filename)
            file.save(file_path)
            saved_files.append(file_path)
    
    return saved_files

def get_recent_reports(limit=10):
    """Get recent reports
    
    Args:
        limit: Maximum number of reports to retrieve
    
    Returns:
        list: Report metadata
    """
    reports_dir = get_reports_directory()
    if not os.path.exists(reports_dir):
        return []
    
    reports = []
    for date_dir in sorted(os.listdir(reports_dir), reverse=True):
        # Skip files and non-date directories
        if not os.path.isdir(os.path.join(reports_dir, date_dir)) or not date_dir.strip():
            continue
        
        try:
            # Parse date string
            report_date = datetime.strptime(date_dir, '%Y-%m-%d')
            
            # Get summary file with the classifications count
            summary_file = os.path.join(reports_dir, date_dir, 'summary.json')
            summary = {}
            if os.path.exists(summary_file):
                with open(summary_file, 'r') as f:
                    summary = json.load(f)
            
            reports.append({
                'date': date_dir,
                'display_date': report_date.strftime('%m/%d/%Y'),
                'summary': summary
            })
            
            if len(reports) >= limit:
                break
        except Exception as e:
            logger.error(f"Error processing report directory {date_dir}: {e}")
    
    return reports

def process_job_assignments_file(file_path):
    """Process job assignments from equipment billing file
    
    Args:
        file_path: Path to excel file
    
    Returns:
        dict: Job assignments by driver
    """
    try:
        # For XLSX files
        if file_path.endswith('.xlsx'):
            # Get the "Drivers" sheet
            df = pd.read_excel(file_path, sheet_name='Drivers')
            # Extract driver name and job number
            drivers = {}
            for _, row in df.iterrows():
                driver_name = row.get('Driver', '')
                job_number = row.get('Job #', '')
                if driver_name and job_number:
                    drivers[driver_name] = job_number
            return drivers
        return {}
    except Exception as e:
        logger.error(f"Error processing job assignments file {file_path}: {e}")
        return {}

@driver_reports_bp.route('/')
def dashboard():
    """Driver reports dashboard"""
    # Get recent reports
    reports = get_recent_reports()
    
    # Check for timecard comparisons
    timecard_file = os.path.join(get_data_directory(), 'timecard_comparisons.json')
    timecard_comparisons = []
    if os.path.exists(timecard_file):
        try:
            with open(timecard_file, 'r') as f:
                timecard_comparisons = json.load(f)
        except Exception as e:
            logger.error(f"Error loading timecard comparisons: {e}")
    
    # Format timecard data for display
    for comp in timecard_comparisons:
        if 'issues' in comp:
            comp['issues_count'] = len(comp['issues'])
            if comp['issues_count'] > 0:
                comp['status'] = 'warning'
            else:
                comp['status'] = 'success'
    
    # Get today's date for date picker default
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Create default metrics
    metrics = {
        'total': 0,
        'on_time': 0,
        'late': 0,
        'early_end': 0,
        'not_on_job': 0,
        'avg_late': 0,
        'avg_early_end': 0
    }
    
    # If there are any reports, calculate summary metrics
    if reports:
        most_recent = reports[0]
        if 'summary' in most_recent and most_recent['summary']:
            summary = most_recent['summary']
            metrics = {
                'total': summary.get('total', 0),
                'on_time': summary.get('on_time', 0),
                'late': summary.get('late', 0),
                'early_end': summary.get('early_end', 0),
                'not_on_job': summary.get('not_on_job', 0),
                'avg_late': summary.get('avg_late', 0),
                'avg_early_end': summary.get('avg_early_end', 0)
            }
    
    return render_template(
        'driver_reports/dashboard.html', 
        reports=reports,
        today=today,
        timecard_comparisons=timecard_comparisons,
        metrics=metrics
    )

@driver_reports_bp.route('/generate', methods=['POST'])
def generate_report():
    """Generate a driver report"""
    try:
        # Get report date
        report_date = request.form.get('report_date', datetime.now().strftime('%Y-%m-%d'))
        
        # Process Driving History files
        driving_history_files = process_uploaded_files(request.files, 'driving_history')
        if not driving_history_files:
            flash("No Driving History files uploaded", "danger")
            return redirect(url_for('driver_reports.dashboard'))
        
        # Process Activity Detail files
        activity_detail_files = process_uploaded_files(request.files, 'activity_detail')
        if not activity_detail_files:
            flash("No Activity Detail files uploaded", "danger")
            return redirect(url_for('driver_reports.dashboard'))
        
        # Process Assets On Site files (optional)
        assets_on_site_files = process_uploaded_files(request.files, 'assets_on_site')
        
        # Process Equipment Billing file (optional)
        equipment_billing_files = process_uploaded_files(request.files, 'equipment_billing')
        job_assignments = {}
        if equipment_billing_files:
            job_assignments = process_job_assignments_file(equipment_billing_files[0])
        
        # Run the driver pipeline
        pipeline = DriverPipeline(
            date_str=report_date,
            driving_history_files=driving_history_files,
            activity_detail_files=activity_detail_files,
            assets_on_site_files=assets_on_site_files,
            job_assignments=job_assignments
        )
        
        # Generate detailed report
        pipeline.run()
        flash(f"Driver report for {report_date} generated successfully", "success")
        
        return redirect(url_for('driver_reports.dashboard'))
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        logger.error(traceback.format_exc())
        flash(f"Error generating report: {str(e)}", "danger")
        return redirect(url_for('driver_reports.dashboard'))

@driver_reports_bp.route('/upload-timecards', methods=['POST'])
def upload_timecards():
    """Upload and process GroundWorks timecards"""
    try:
        # Get date range
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        # Process uploaded file
        timecard_files = process_uploaded_files(request.files, 'timecard_file')
        if not timecard_files:
            flash("No timecard file uploaded", "danger")
            return redirect(url_for('driver_reports.dashboard'))
        
        # Process the timecards
        timecard_data = process_groundworks_timecards(
            timecard_files[0], 
            start_date=start_date, 
            end_date=end_date
        )
        
        # Load existing driver reports for comparison
        reports_dir = get_reports_directory()
        gps_data = {}
        dates_processed = []
        
        if start_date and end_date:
            # Parse date range
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            date_range = [start + timedelta(days=x) for x in range((end - start).days + 1)]
            for date in date_range:
                date_str = date.strftime('%Y-%m-%d')
                report_dir = os.path.join(reports_dir, date_str)
                if os.path.exists(report_dir):
                    # Find JSON report
                    for filename in os.listdir(report_dir):
                        if filename.endswith('.json') and not filename.startswith('summary'):
                            with open(os.path.join(report_dir, filename), 'r') as f:
                                report_data = json.load(f)
                                gps_data[date_str] = report_data
                                dates_processed.append(date_str)
        
        # Compare timecards with GPS data
        comparisons = []
        for date_str in dates_processed:
            comparison = compare_timecards_with_gps(
                timecard_files[0],
                gps_data,
                target_date=date_str
            )
            comparisons.extend(comparison)
        
        # Save comparison results
        data_dir = get_data_directory()
        with open(os.path.join(data_dir, 'timecard_comparisons.json'), 'w') as f:
            json.dump(comparisons, f, indent=2)
        
        flash(f"Timecard comparison complete: {len(comparisons)} records processed", "success")
        return redirect(url_for('driver_reports.dashboard'))
        
    except Exception as e:
        logger.error(f"Error processing timecards: {e}")
        flash(f"Error processing timecards: {str(e)}", "danger")
        return redirect(url_for('driver_reports.dashboard'))

@driver_reports_bp.route('/download/<date>/<report_type>')
def download_report(date, report_type):
    """Download a specific report"""
    if report_type not in REPORT_TYPES:
        abort(404, f"Invalid report type: {report_type}")
    
    # Get report directory
    report_dir = os.path.join(get_reports_directory(), date)
    if not os.path.exists(report_dir):
        abort(404, f"Report not found for date: {date}")
    
    # Find the requested report file
    if report_type == 'excel':
        for filename in os.listdir(report_dir):
            if filename.endswith('.xlsx'):
                return send_file(os.path.join(report_dir, filename))
    
    elif report_type == 'pdf':
        for filename in os.listdir(report_dir):
            if filename.endswith('.pdf') and 'SUMMARY' in filename:
                return send_file(os.path.join(report_dir, filename))
    
    elif report_type == 'json':
        for filename in os.listdir(report_dir):
            if filename.endswith('.json') and not filename.startswith('summary'):
                return send_file(os.path.join(report_dir, filename))
    
    elif report_type == 'pmr_late':
        for filename in os.listdir(report_dir):
            if filename.startswith('LATE_START_') and filename.endswith('.pdf'):
                return send_file(os.path.join(report_dir, filename))
    
    elif report_type == 'pmr_early_end':
        for filename in os.listdir(report_dir):
            if filename.startswith('EARLY_END_') and filename.endswith('.pdf'):
                return send_file(os.path.join(report_dir, filename))
    
    elif report_type == 'pmr_not_on_job':
        for filename in os.listdir(report_dir):
            if filename.startswith('NOT_ON_JOB_') and filename.endswith('.pdf'):
                return send_file(os.path.join(report_dir, filename))
    
    elif report_type == 'activity':
        for filename in os.listdir(report_dir):
            if filename.startswith('ACTIVITY_DETAIL_SUMMARY_') and filename.endswith('.pdf'):
                return send_file(os.path.join(report_dir, filename))
    
    # If no file found
    abort(404, f"Report file not found for type: {report_type}")

@driver_reports_bp.route('/view-timecard-comparison/<driver_name>')
def view_timecard_comparison(driver_name):
    """View detailed timecard comparison for a specific driver"""
    # Load timecard comparisons
    timecard_file = os.path.join(get_data_directory(), 'timecard_comparisons.json')
    if not os.path.exists(timecard_file):
        abort(404, "Timecard comparison data not found")
    
    try:
        with open(timecard_file, 'r') as f:
            comparisons = json.load(f)
        
        # Filter for specific driver
        driver_data = [c for c in comparisons if c.get('driver_name') == driver_name]
        if not driver_data:
            abort(404, f"No timecard comparison data found for driver: {driver_name}")
        
        return render_template(
            'driver_reports/timecard_comparison.html', 
            driver_name=driver_name,
            timecard_data=driver_data
        )
        
    except Exception as e:
        logger.error(f"Error viewing timecard comparison: {e}")
        abort(500, f"Error viewing timecard comparison: {str(e)}")

@driver_reports_bp.route('/api/report-data/<date>')
def api_report_data(date):
    """API endpoint to get report data for a specific date"""
    # Get report directory
    report_dir = os.path.join(get_reports_directory(), date)
    if not os.path.exists(report_dir):
        return jsonify({"error": f"Report not found for date: {date}"}), 404
    
    # Find report JSON file
    json_file = None
    for filename in os.listdir(report_dir):
        if filename.endswith('.json') and not filename.startswith('summary'):
            json_file = os.path.join(report_dir, filename)
            break
    
    if not json_file:
        return jsonify({"error": f"JSON report not found for date: {date}"}), 404
    
    try:
        with open(json_file, 'r') as f:
            report_data = json.load(f)
        return jsonify(report_data)
    except Exception as e:
        logger.error(f"Error loading report data: {e}")
        return jsonify({"error": f"Error loading report data: {str(e)}"}), 500