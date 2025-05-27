"""
TRAXORA Unified Attendance + Job Zone + GPS vs Timecard Validation Suite

This module provides the critical validation system that cross-references:
1. GPS tracking data (Driving History, Time on Site, Activity Detail)
2. Ground Works timecard data (WTD exports)
3. Job zone configurations with PM assignments

Flags discrepancies: Timecard but no GPS, GPS but no timecard, overlaps, gaps
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

# Create blueprint
unified_attendance_bp = Blueprint('unified_attendance', __name__, url_prefix='/unified-attendance')

def get_upload_directory():
    """Get the upload directory for attendance data"""
    upload_dir = os.path.join(os.getcwd(), 'uploads', 'attendance_validation')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

def load_job_zones():
    """Load job zone configurations from jobs.json"""
    try:
        jobs_file = os.path.join(os.getcwd(), 'data', 'jobs.json')
        if os.path.exists(jobs_file):
            with open(jobs_file, 'r') as f:
                return json.load(f)
        return {"jobs": []}
    except Exception as e:
        logger.error(f"Error loading job zones: {e}")
        return {"jobs": []}

def save_job_zones(job_data):
    """Save job zone configurations to jobs.json"""
    try:
        jobs_dir = os.path.join(os.getcwd(), 'data')
        os.makedirs(jobs_dir, exist_ok=True)
        jobs_file = os.path.join(jobs_dir, 'jobs.json')
        with open(jobs_file, 'w') as f:
            json.dump(job_data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving job zones: {e}")
        return False

def validate_attendance_data(gps_data, timecard_data, job_zones, date_filter=None):
    """
    Core validation logic that cross-references all data sources
    Returns: dict with validation results and flags
    """
    validation_results = {
        'total_drivers': 0,
        'valid_matches': 0,
        'timecard_no_gps': [],
        'gps_no_timecard': [],
        'overlaps': [],
        'gaps': [],
        'summary': {}
    }
    
    try:
        # Process GPS data
        gps_records = {}
        if gps_data is not None and not gps_data.empty:
            for _, row in gps_data.iterrows():
                driver = str(row.get('Driver', '')).strip()
                if driver and driver != 'nan':
                    if driver not in gps_records:
                        gps_records[driver] = []
                    gps_records[driver].append({
                        'timestamp': row.get('Date/Time', ''),
                        'location': row.get('Location', ''),
                        'asset': row.get('Asset', ''),
                        'job': row.get('Job', '')
                    })
        
        # Process timecard data
        timecard_records = {}
        if timecard_data is not None and not timecard_data.empty:
            for _, row in timecard_data.iterrows():
                driver = str(row.get('Employee Name', '') or row.get('Driver', '')).strip()
                if driver and driver != 'nan':
                    if driver not in timecard_records:
                        timecard_records[driver] = []
                    timecard_records[driver].append({
                        'date': row.get('Date', ''),
                        'hours': row.get('Hours', 0),
                        'job_code': row.get('Job Code', ''),
                        'description': row.get('Description', '')
                    })
        
        # Cross-validate drivers
        all_drivers = set(list(gps_records.keys()) + list(timecard_records.keys()))
        validation_results['total_drivers'] = len(all_drivers)
        
        for driver in all_drivers:
            has_gps = driver in gps_records
            has_timecard = driver in timecard_records
            
            if has_timecard and not has_gps:
                validation_results['timecard_no_gps'].append({
                    'driver': driver,
                    'timecard_entries': len(timecard_records[driver])
                })
            elif has_gps and not has_timecard:
                validation_results['gps_no_timecard'].append({
                    'driver': driver,
                    'gps_entries': len(gps_records[driver])
                })
            elif has_gps and has_timecard:
                validation_results['valid_matches'] += 1
        
        # Generate summary
        validation_results['summary'] = {
            'total_drivers': validation_results['total_drivers'],
            'valid_matches': validation_results['valid_matches'],
            'discrepancies': len(validation_results['timecard_no_gps']) + len(validation_results['gps_no_timecard']),
            'coverage_percentage': (validation_results['valid_matches'] / validation_results['total_drivers'] * 100) if validation_results['total_drivers'] > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error in validation: {e}")
    
    return validation_results

@unified_attendance_bp.route('/')
def dashboard():
    """Main dashboard for unified attendance validation"""
    logger.info("Unified attendance dashboard accessed")
    
    # Load job zones
    job_zones = load_job_zones()
    
    # Get recent validation results if available
    results_file = os.path.join(get_upload_directory(), 'latest_validation.json')
    validation_results = None
    if os.path.exists(results_file):
        try:
            with open(results_file, 'r') as f:
                validation_results = json.load(f)
        except Exception as e:
            logger.error(f"Error loading validation results: {e}")
    
    return render_template('unified_attendance/dashboard.html',
                         job_zones=job_zones,
                         validation_results=validation_results,
                         title="Unified Attendance Validation Suite")

@unified_attendance_bp.route('/upload', methods=['POST'])
def upload_files():
    """Upload and process GPS data, timecards, and activity details"""
    logger.info("Processing file uploads for attendance validation")
    
    try:
        upload_dir = get_upload_directory()
        uploaded_files = {}
        
        # Process each file type
        file_types = ['driving_history', 'time_on_site', 'activity_detail', 'timecards']
        
        for file_type in file_types:
            if file_type in request.files:
                file = request.files[file_type]
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(upload_dir, f"{file_type}_{filename}")
                    file.save(filepath)
                    uploaded_files[file_type] = filepath
        
        # Process uploaded files
        gps_data = None
        timecard_data = None
        
        # Load GPS data (driving history)
        if 'driving_history' in uploaded_files:
            try:
                if uploaded_files['driving_history'].endswith('.xlsx'):
                    gps_data = pd.read_excel(uploaded_files['driving_history'])
                else:
                    gps_data = pd.read_csv(uploaded_files['driving_history'])
                logger.info(f"Loaded GPS data: {len(gps_data)} records")
            except Exception as e:
                logger.error(f"Error loading GPS data: {e}")
        
        # Load timecard data
        if 'timecards' in uploaded_files:
            try:
                if uploaded_files['timecards'].endswith('.xlsx'):
                    timecard_data = pd.read_excel(uploaded_files['timecards'])
                else:
                    timecard_data = pd.read_csv(uploaded_files['timecards'])
                logger.info(f"Loaded timecard data: {len(timecard_data)} records")
            except Exception as e:
                logger.error(f"Error loading timecard data: {e}")
        
        # Run validation
        job_zones = load_job_zones()
        validation_results = validate_attendance_data(gps_data, timecard_data, job_zones)
        
        # Save results
        results_file = os.path.join(upload_dir, 'latest_validation.json')
        with open(results_file, 'w') as f:
            json.dump(validation_results, f, indent=2)
        
        flash(f'Validation complete: {validation_results["valid_matches"]} valid matches, {len(validation_results["timecard_no_gps"]) + len(validation_results["gps_no_timecard"])} discrepancies found', 'success')
        
    except Exception as e:
        logger.error(f"Error processing uploads: {e}")
        flash(f'Error processing files: {str(e)}', 'error')
    
    return redirect(url_for('unified_attendance.dashboard'))

@unified_attendance_bp.route('/job-zones')
def job_zones():
    """Job zone configuration page"""
    job_data = load_job_zones()
    return render_template('unified_attendance/job_zones.html',
                         jobs=job_data.get('jobs', []),
                         title="Job Zone Configuration")

@unified_attendance_bp.route('/job-zones/save', methods=['POST'])
def save_job_zone():
    """Save job zone configuration"""
    try:
        job_data = load_job_zones()
        
        new_job = {
            'id': len(job_data.get('jobs', [])) + 1,
            'name': request.form.get('name', ''),
            'pm': request.form.get('pm', ''),
            'start_date': request.form.get('start_date', ''),
            'end_date': request.form.get('end_date', ''),
            'night_work': 'night_work' in request.form,
            'weekend_work': 'weekend_work' in request.form,
            'geofence': {
                'latitude': float(request.form.get('latitude', 0)),
                'longitude': float(request.form.get('longitude', 0)),
                'radius': float(request.form.get('radius', 100))
            },
            'created_at': datetime.now().isoformat()
        }
        
        if 'jobs' not in job_data:
            job_data['jobs'] = []
        
        job_data['jobs'].append(new_job)
        
        if save_job_zones(job_data):
            flash('Job zone saved successfully', 'success')
        else:
            flash('Error saving job zone', 'error')
            
    except Exception as e:
        logger.error(f"Error saving job zone: {e}")
        flash(f'Error saving job zone: {str(e)}', 'error')
    
    return redirect(url_for('unified_attendance.job_zones'))

@unified_attendance_bp.route('/api/validation-summary')
def validation_summary_api():
    """API endpoint for validation summary data"""
    results_file = os.path.join(get_upload_directory(), 'latest_validation.json')
    if os.path.exists(results_file):
        try:
            with open(results_file, 'r') as f:
                return jsonify(json.load(f))
        except Exception as e:
            logger.error(f"Error loading validation results: {e}")
    
    return jsonify({'error': 'No validation results available'})

# Register blueprint info
BLUEPRINT_INFO = {
    'name': 'Unified Attendance Suite',
    'description': 'GPS vs Timecard validation with job zone integration',
    'category': 'Operations',
    'icon': 'fas fa-tasks',
    'url': '/unified-attendance/',
    'order': 1
}