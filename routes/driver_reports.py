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
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_upload_directory():
    """Get upload directory, creating it if needed"""
    upload_dir = os.path.join(current_app.root_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

def get_data_directory():
    """Get data directory, creating it if needed"""
    data_dir = os.path.join(current_app.root_path, 'data')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_reports_directory():
    """Get reports directory, creating it if needed"""
    reports_dir = os.path.join(current_app.root_path, 'reports')
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
    # Create directory for this file type
    base_dir = get_data_directory()
    type_dir = os.path.join(base_dir, file_type)
    os.makedirs(type_dir, exist_ok=True)
    
    # Get file or files
    files = request_files.getlist(file_type) if hasattr(request_files, 'getlist') else [request_files]
    
    # Save files
    saved_paths = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(type_dir, filename)
            file.save(path)
            saved_paths.append(path)
    
    return saved_paths

def get_recent_reports(limit=10):
    """Get recent reports
    
    Args:
        limit: Maximum number of reports to retrieve
    
    Returns:
        list: Report metadata
    """
    reports_dir = get_reports_directory()
    reports = []
    
    # Get subdirectories (dates)
    if os.path.exists(reports_dir):
        date_dirs = sorted(os.listdir(reports_dir), reverse=True)
        
        for date_dir in date_dirs[:limit]:
            dir_path = os.path.join(reports_dir, date_dir)
            if os.path.isdir(dir_path):
                # Look for summary file
                summary_path = os.path.join(dir_path, 'report_summary.json')
                if os.path.exists(summary_path):
                    try:
                        with open(summary_path, 'r') as f:
                            summary = json.load(f)
                            reports.append(summary)
                    except Exception as e:
                        logger.error(f"Error reading summary file {summary_path}: {e}")
                else:
                    # Create basic report info from directory
                    basic_info = {
                        'date': date_dir,
                        'generated_at': datetime.fromtimestamp(os.path.getctime(dir_path)).isoformat(),
                        'pdf_url': url_for('driver_reports.download_report', date=date_dir, report_type='pdf'),
                        'excel_url': url_for('driver_reports.download_report', date=date_dir, report_type='excel'),
                        'metrics': {
                            'on_time': 0,
                            'late': 0,
                            'early_end': 0,
                            'not_on_job': 0
                        }
                    }
                    reports.append(basic_info)
    
    return reports

def process_job_assignments_file(file_path):
    """Process job assignments from equipment billing file
    
    Args:
        file_path: Path to excel file
    
    Returns:
        dict: Job assignments by driver
    """
    try:
        # Read file
        df = pd.read_excel(file_path)
        
        # Extract driver and job number columns
        # This is simplified and should be adjusted based on actual file format
        driver_col = None
        job_col = None
        
        for col in df.columns:
            if 'driver' in col.lower():
                driver_col = col
            elif 'job' in col.lower() and 'number' in col.lower():
                job_col = col
        
        if not driver_col or not job_col:
            logger.warning(f"Could not find driver or job columns in {file_path}")
            return {}
        
        # Create assignments dictionary
        assignments = {}
        for _, row in df.iterrows():
            driver = str(row[driver_col]).strip().lower()
            job = str(row[job_col]).strip()
            
            if driver and job and driver != 'nan' and job != 'nan':
                assignments[driver] = job
        
        return assignments
        
    except Exception as e:
        logger.error(f"Error processing job assignments file {file_path}: {e}")
        return {}

@driver_reports_bp.route('/')
def dashboard():
    """Driver reports dashboard"""
    # Get recent reports
    reports = get_recent_reports()
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get timecard comparisons if available
    timecard_comparisons = []
    timecard_file = os.path.join(get_data_directory(), 'timecard_comparisons.json')
    if os.path.exists(timecard_file):
        try:
            with open(timecard_file, 'r') as f:
                timecard_comparisons = json.load(f)
        except Exception as e:
            logger.error(f"Error reading timecard comparisons: {e}")
    
    # Get metrics from most recent report
    metrics = {
        'on_time': 0,
        'late': 0,
        'early_end': 0,
        'not_on_job': 0,
        'avg_late': 0,
        'avg_early': 0
    }
    
    if reports:
        latest_report = reports[0]
        if 'metrics' in latest_report:
            metrics = latest_report['metrics']
    
    return render_template(
        'driver_reports/dashboard.html',
        reports=reports,
        metrics=metrics,
        today=today,
        timecard_comparisons=timecard_comparisons
    )

@driver_reports_bp.route('/generate', methods=['POST'])
def generate_report():
    """Generate a driver report"""
    try:
        # Get report date
        report_date = request.form.get('report_date', datetime.now().strftime('%Y-%m-%d'))
        
        # Process uploaded files
        driving_history_paths = process_uploaded_files(request.files, 'driving_history')
        activity_detail_paths = process_uploaded_files(request.files, 'activity_detail')
        asset_time_paths = process_uploaded_files(request.files, 'asset_time')
        
        # Process job assignments if provided
        job_assignments = {}
        if 'job_assignments' in request.files and request.files['job_assignments'].filename:
            job_file = request.files['job_assignments']
            if allowed_file(job_file.filename):
                # Save job assignments file
                filename = secure_filename(job_file.filename)
                upload_dir = get_upload_directory()
                job_path = os.path.join(upload_dir, filename)
                job_file.save(job_path)
                
                # Process job assignments
                job_assignments = process_job_assignments_file(job_path)
        
        # Check if we have data files
        if not driving_history_paths and not activity_detail_paths:
            flash("Please upload at least one data file", "danger")
            return redirect(url_for('driver_reports.dashboard'))
        
        # Configure pipeline
        config = {
            'date_str': report_date,
            'job_assignments': job_assignments,
            'output_dir': os.path.join(get_reports_directory(), report_date)
        }
        
        # If specific files were uploaded, use them
        if driving_history_paths:
            config['driving_history_path'] = os.path.dirname(driving_history_paths[0])
        if activity_detail_paths:
            config['activity_detail_path'] = os.path.dirname(activity_detail_paths[0])
        if asset_time_paths:
            config['asset_time_path'] = os.path.dirname(asset_time_paths[0])
        
        # Run pipeline
        pipeline = DriverPipeline(config)
        results = pipeline.run()
        
        # Check for timecard comparison
        include_timecards = 'include_timecards' in request.form
        if include_timecards:
            # Compare with timecards
            timecard_file = os.path.join(get_data_directory(), 'groundworks_timecards.xlsx')
            if os.path.exists(timecard_file):
                # Process comparison
                comparisons = compare_timecards_with_gps(
                    timecard_file, 
                    results.get('classification_results', {}),
                    report_date
                )
                
                # Save comparison results
                comparison_path = os.path.join(config['output_dir'], 'timecard_comparison.json')
                with open(comparison_path, 'w') as f:
                    json.dump(comparisons, f, indent=2)
                
                # Include in report files
                results['report_files']['timecard_comparison'] = comparison_path
        
        # Create summary for easy access
        summary = {
            'date': report_date,
            'generated_at': datetime.now().isoformat(),
            'pdf_url': url_for('driver_reports.download_report', date=report_date, report_type='pdf'),
            'excel_url': url_for('driver_reports.download_report', date=report_date, report_type='excel'),
            'metrics': {}
        }
        
        # Add metrics if available
        if 'status_counts' in results:
            summary['metrics'] = {
                'on_time': results['status_counts'].get('on_time', 0),
                'late': results['status_counts'].get('late', 0),
                'early_end': results['status_counts'].get('early_end', 0),
                'not_on_job': results['status_counts'].get('not_on_job', 0)
            }
        
        # Add time statistics if available
        if 'time_stats' in results:
            summary['metrics']['avg_late'] = round(results['time_stats'].get('avg_minutes_late', 0), 1)
            summary['metrics']['avg_early'] = round(results['time_stats'].get('avg_minutes_early_end', 0), 1)
        
        # Save summary
        summary_path = os.path.join(config['output_dir'], 'report_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Show success message
        flash(f"Report for {report_date} generated successfully", "success")
        
        # Redirect to dashboard
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
        if 'timecard_file' not in request.files or not request.files['timecard_file'].filename:
            flash("Please upload a timecard file", "danger")
            return redirect(url_for('driver_reports.dashboard'))
        
        timecard_file = request.files['timecard_file']
        if not allowed_file(timecard_file.filename):
            flash("Invalid file format. Please upload a CSV or Excel file", "danger")
            return redirect(url_for('driver_reports.dashboard'))
        
        # Save timecard file
        filename = secure_filename(timecard_file.filename)
        data_dir = get_data_directory()
        timecard_path = os.path.join(data_dir, 'groundworks_timecards.xlsx')
        timecard_file.save(timecard_path)
        
        # Process timecards
        processed_data = process_groundworks_timecards(timecard_path, start_date, end_date)
        
        # Get GPS data for comparison
        # First, get recent reports
        reports = get_recent_reports(limit=14)  # Last two weeks
        
        # Collect all driver classifications
        all_classifications = {}
        for report in reports:
            report_date = report.get('date')
            report_dir = os.path.join(get_reports_directory(), report_date)
            
            # Look for classification results
            results_path = os.path.join(report_dir, 'classification_results.json')
            if os.path.exists(results_path):
                try:
                    with open(results_path, 'r') as f:
                        classifications = json.load(f)
                        all_classifications[report_date] = classifications
                except Exception as e:
                    logger.error(f"Error reading classifications from {results_path}: {e}")
        
        # Compare timecards with GPS data
        comparisons = compare_timecards_with_gps(timecard_path, all_classifications)
        
        # Save comparison results
        comparison_path = os.path.join(data_dir, 'timecard_comparisons.json')
        with open(comparison_path, 'w') as f:
            json.dump(comparisons, f, indent=2)
        
        # Show success message
        flash(f"Timecard data processed successfully. Found {len(comparisons)} comparisons.", "success")
        
        # Redirect to dashboard
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
    
    # Find report file
    if report_type == 'pdf':
        for filename in os.listdir(report_dir):
            if filename.endswith('.pdf') and not filename.startswith('PMR_'):
                return send_file(os.path.join(report_dir, filename))
    
    elif report_type == 'excel':
        for filename in os.listdir(report_dir):
            if filename.endswith('.xlsx') and 'comprehensive' in filename:
                return send_file(os.path.join(report_dir, filename))
    
    elif report_type == 'json':
        for filename in os.listdir(report_dir):
            if filename.endswith('.json') and filename != 'report_summary.json' and filename != 'genius_core_log.json':
                return send_file(os.path.join(report_dir, filename))
    
    elif report_type == 'pmr_late':
        for filename in os.listdir(report_dir):
            if filename.startswith('PMR_LATE_') and filename.endswith('.pdf'):
                return send_file(os.path.join(report_dir, filename))
    
    elif report_type == 'pmr_early_end':
        for filename in os.listdir(report_dir):
            if filename.startswith('PMR_EARLY_END_') and filename.endswith('.pdf'):
                return send_file(os.path.join(report_dir, filename))
    
    elif report_type == 'pmr_not_on_job':
        for filename in os.listdir(report_dir):
            if filename.startswith('PMR_NOT_ON_JOB_') and filename.endswith('.pdf'):
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
        
        # Find driver comparisons
        driver_comparisons = []
        for comp in comparisons:
            if comp.get('driver_name', '').lower() == driver_name.lower():
                driver_comparisons.append(comp)
        
        if not driver_comparisons:
            abort(404, f"No timecard comparisons found for driver: {driver_name}")
        
        return render_template(
            'driver_reports/timecard_comparison.html',
            driver_name=driver_name,
            comparisons=driver_comparisons
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
        if filename.endswith('.json') and filename != 'report_summary.json' and filename != 'genius_core_log.json':
            json_file = os.path.join(report_dir, filename)
            break
    
    if not json_file:
        return jsonify({"error": "Report data not found"}), 404
    
    try:
        with open(json_file, 'r') as f:
            report_data = json.load(f)
        
        return jsonify(report_data)
        
    except Exception as e:
        logger.error(f"Error reading report data: {e}")
        return jsonify({"error": f"Error reading report data: {str(e)}"}), 500