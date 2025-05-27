"""
Zone Schedule Manager Routes for TRAXOVO

This module provides routes for processing PM Excel data and managing
zone schedule rules for attendance validation.
"""
import os
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from utils.zone_schedule_processor import ZoneScheduleProcessor

logger = logging.getLogger(__name__)

zone_schedule_bp = Blueprint('zone_schedule', __name__, url_prefix='/zone-schedule')

# Configuration
UPLOAD_FOLDER = 'uploads/pm_data'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def ensure_upload_folder():
    """Ensure upload folder exists"""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@zone_schedule_bp.route('/')
@login_required
def dashboard():
    """Zone schedule management dashboard"""
    processor = ZoneScheduleProcessor()
    zone_rules = processor.load_zone_rules()
    
    return render_template('zone_schedule/dashboard.html',
                         zone_rules=zone_rules,
                         zones_count=len(zone_rules.get('zones', {})),
                         last_updated=zone_rules.get('last_updated', 'Never'))

@zone_schedule_bp.route('/upload-pm-data', methods=['GET', 'POST'])
@login_required
def upload_pm_data():
    """Upload and process PM Excel/CSV data"""
    if request.method == 'POST':
        ensure_upload_folder()
        
        # Check if file was uploaded
        if 'pm_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['pm_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Secure the filename
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # Process the file
            processor = ZoneScheduleProcessor()
            try:
                if filename.lower().endswith('.csv'):
                    zone_rules = processor.process_csv_pm_data(filepath)
                else:
                    # Excel file
                    sheet_name = request.form.get('sheet_name', 'PM')
                    zone_rules = processor.process_excel_pm_data(filepath, sheet_name)
                
                zones_processed = len(zone_rules.get('zones', {}))
                flash(f'Successfully processed {zones_processed} zones from PM data', 'success')
                
                # Clean up uploaded file
                os.remove(filepath)
                
                return redirect(url_for('zone_schedule.dashboard'))
                
            except Exception as e:
                logger.error(f"Error processing PM data: {e}")
                flash(f'Error processing file: {str(e)}', 'error')
                
                # Clean up uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
        else:
            flash('Invalid file type. Please upload Excel (.xlsx, .xls) or CSV files only.', 'error')
    
    return render_template('zone_schedule/upload.html')

@zone_schedule_bp.route('/api/zone-rules')
@login_required
def api_zone_rules():
    """API endpoint to get current zone rules"""
    processor = ZoneScheduleProcessor()
    zone_rules = processor.load_zone_rules()
    return jsonify(zone_rules)

@zone_schedule_bp.route('/api/validate-attendance', methods=['POST'])
@login_required
def api_validate_attendance():
    """API endpoint to validate attendance against zone rules"""
    data = request.get_json()
    
    if not data or 'zone_id' not in data or 'check_time' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        from datetime import datetime
        processor = ZoneScheduleProcessor()
        
        zone_id = data['zone_id']
        check_time = datetime.fromisoformat(data['check_time'])
        gps_coordinates = data.get('gps_coordinates')
        
        result = processor.validate_attendance(zone_id, check_time, gps_coordinates)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error validating attendance: {e}")
        return jsonify({'error': str(e)}), 500

@zone_schedule_bp.route('/zone/<zone_id>')
@login_required
def zone_detail(zone_id):
    """Show details for a specific zone"""
    processor = ZoneScheduleProcessor()
    zone_schedule = processor.get_zone_schedule(zone_id)
    
    if not zone_schedule:
        flash(f'Zone {zone_id} not found', 'error')
        return redirect(url_for('zone_schedule.dashboard'))
    
    return render_template('zone_schedule/zone_detail.html',
                         zone_id=zone_id,
                         zone_schedule=zone_schedule)