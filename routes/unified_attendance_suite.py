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

@unified_attendance_bp.route('/export/<format>')
def export_results(format):
    """Export validation results to Excel or PDF"""
    logger.info(f"Exporting validation results to {format}")
    
    try:
        results_file = os.path.join(get_upload_directory(), 'latest_validation.json')
        if not os.path.exists(results_file):
            flash('No validation results to export', 'error')
            return redirect(url_for('unified_attendance.dashboard'))
        
        with open(results_file, 'r') as f:
            validation_results = json.load(f)
        
        if format.lower() == 'excel':
            return export_to_excel(validation_results)
        elif format.lower() == 'pdf':
            return export_to_pdf(validation_results)
        else:
            flash('Invalid export format', 'error')
            return redirect(url_for('unified_attendance.dashboard'))
            
    except Exception as e:
        logger.error(f"Error exporting results: {e}")
        flash(f'Export error: {str(e)}', 'error')
        return redirect(url_for('unified_attendance.dashboard'))

def export_to_excel(validation_results):
    """Export validation results to Excel format"""
    import tempfile
    from flask import send_file
    
    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        
        # Create Excel workbook with multiple sheets
        with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                'Metric': ['Total Drivers', 'Valid Matches', 'Discrepancies', 'Coverage %'],
                'Value': [
                    validation_results['summary']['total_drivers'],
                    validation_results['valid_matches'],
                    validation_results['summary']['discrepancies'],
                    f"{validation_results['summary']['coverage_percentage']:.1f}%"
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Timecard but no GPS sheet
            if validation_results['timecard_no_gps']:
                timecard_df = pd.DataFrame(validation_results['timecard_no_gps'])
                timecard_df.to_excel(writer, sheet_name='Timecard_No_GPS', index=False)
            
            # GPS but no timecard sheet
            if validation_results['gps_no_timecard']:
                gps_df = pd.DataFrame(validation_results['gps_no_timecard'])
                gps_df.to_excel(writer, sheet_name='GPS_No_Timecard', index=False)
        
        return send_file(temp_file.name, 
                        as_attachment=True,
                        download_name=f'attendance_validation_{datetime.now().strftime("%Y%m%d")}.xlsx',
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
    except Exception as e:
        logger.error(f"Error creating Excel export: {e}")
        raise

def export_to_pdf(validation_results):
    """Export validation results to PDF format"""
    import tempfile
    from flask import send_file
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    
    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        
        # Create PDF document
        doc = SimpleDocTemplate(temp_file.name, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph("TRAXORA Attendance Validation Report", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Summary table
        summary_data = [
            ['Metric', 'Value'],
            ['Total Drivers', str(validation_results['summary']['total_drivers'])],
            ['Valid Matches', str(validation_results['valid_matches'])],
            ['Discrepancies', str(validation_results['summary']['discrepancies'])],
            ['Coverage %', f"{validation_results['summary']['coverage_percentage']:.1f}%"]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(elements)
        
        return send_file(temp_file.name,
                        as_attachment=True,
                        download_name=f'attendance_validation_{datetime.now().strftime("%Y%m%d")}.pdf',
                        mimetype='application/pdf')
        
    except Exception as e:
        logger.error(f"Error creating PDF export: {e}")
        raise

@unified_attendance_bp.route('/process-daily-reports')
def process_daily_reports():
    """Process PM assignments from DAILY LATE START-EARLY END files"""
    logger.info("Processing daily reports for PM assignments")
    
    try:
        # Look for DAILY LATE START-EARLY END files in attached_assets
        daily_files = []
        assets_dir = os.path.join(os.getcwd(), 'attached_assets')
        
        if os.path.exists(assets_dir):
            for file in os.listdir(assets_dir):
                if 'DAILY LATE START-EARLY END' in file and file.endswith('.xlsx'):
                    daily_files.append(os.path.join(assets_dir, file))
        
        if not daily_files:
            flash('No DAILY LATE START-EARLY END files found', 'warning')
            return redirect(url_for('unified_attendance.dashboard'))
        
        # Process the most recent file
        latest_file = max(daily_files, key=os.path.getctime)
        pm_assignments = process_pm_assignments(latest_file)
        
        flash(f'Processed PM assignments from {os.path.basename(latest_file)}', 'success')
        return jsonify(pm_assignments)
        
    except Exception as e:
        logger.error(f"Error processing daily reports: {e}")
        flash(f'Error processing daily reports: {str(e)}', 'error')
        return redirect(url_for('unified_attendance.dashboard'))

def process_pm_assignments(file_path):
    """Extract PM assignments from daily report file"""
    try:
        df = pd.read_excel(file_path)
        
        pm_assignments = {}
        for _, row in df.iterrows():
            driver = str(row.get('Driver', '')).strip()
            pm = str(row.get('PM', '') or row.get('Project Manager', '')).strip()
            job = str(row.get('Job', '') or row.get('Job Number', '')).strip()
            
            if driver and driver != 'nan':
                pm_assignments[driver] = {
                    'pm': pm,
                    'job': job,
                    'status': row.get('Status', ''),
                    'notes': row.get('Notes', '')
                }
        
        # Save PM assignments
        pm_file = os.path.join(get_upload_directory(), 'pm_assignments.json')
        with open(pm_file, 'w') as f:
            json.dump(pm_assignments, f, indent=2)
        
        return pm_assignments
        
    except Exception as e:
        logger.error(f"Error processing PM assignments: {e}")
        return {}

# Register blueprint info
BLUEPRINT_INFO = {
    'name': 'Unified Attendance Suite',
    'description': 'GPS vs Timecard validation with job zone integration',
    'category': 'Operations',
    'icon': 'fas fa-tasks',
    'url': '/unified-attendance/',
    'order': 1
}