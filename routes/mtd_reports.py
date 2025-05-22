"""
MTD Reports Routes

This module provides routes for processing large Month-to-Date files.
It uses a specialized processor designed for memory-efficient handling of large files.
"""

import os
import logging
import pandas as pd
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app, flash, session

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
mtd_reports_bp = Blueprint('mtd_reports', __name__, url_prefix='/mtd-reports')

# Define allowed file extensions
ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_uploaded_files(files, file_type):
    """Process uploaded files and save them to the upload folder"""
    saved_files = []
    
    if not files:
        return saved_files
        
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(current_app.root_path, 'uploads', 'mtd_reports')
    os.makedirs(upload_dir, exist_ok=True)
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to ensure uniqueness
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            new_filename = f"{file_type}_{timestamp}_{filename}"
            file_path = os.path.join(upload_dir, new_filename)
            file.save(file_path)
            saved_files.append(file_path)
            logger.info(f"Saved {file_type} file: {file_path}")
    
    return saved_files

@mtd_reports_bp.route('/')
def dashboard():
    """MTD Reports Dashboard"""
    return render_template('mtd_reports/dashboard.html')

@mtd_reports_bp.route('/upload', methods=['GET', 'POST'])
def upload_files():
    """Upload MTD files"""
    if request.method == 'POST':
        driving_history_files = request.files.getlist('driving_history')
        activity_detail_files = request.files.getlist('activity_detail')
        report_date = request.form.get('report_date')
        
        # Check if we have the necessary files
        if not driving_history_files or not activity_detail_files:
            flash('Please upload at least one file of each type', 'danger')
            return redirect(url_for('mtd_reports.upload_files'))
            
        # Check if report date was provided
        if not report_date:
            flash('Please select a report date', 'danger')
            return redirect(url_for('mtd_reports.upload_files'))
            
        # Save uploaded files
        driving_history_paths = process_uploaded_files(driving_history_files, 'driving_history')
        activity_detail_paths = process_uploaded_files(activity_detail_files, 'activity_detail')
        
        # If we have successfully saved files, redirect to processing page
        if driving_history_paths and activity_detail_paths:
            # Store file paths and report date in session
            session_data = {
                'driving_history_paths': driving_history_paths,
                'activity_detail_paths': activity_detail_paths,
                'report_date': report_date
            }
            # Save session data to a temporary file
            session_file = os.path.join(current_app.root_path, 'uploads', 'mtd_reports', 'session_data.json')
            import json
            with open(session_file, 'w') as f:
                json.dump(session_data, f)
                
            return redirect(url_for('mtd_reports.process_report'))
            
        flash('Failed to upload files', 'danger')
        return redirect(url_for('mtd_reports.upload_files'))
        
    return render_template('mtd_reports/upload.html')

@mtd_reports_bp.route('/process', methods=['GET'])
def process_report():
    """Process MTD files and generate report"""
    try:
        # Load session data from file
        session_file = os.path.join(current_app.root_path, 'uploads', 'mtd_reports', 'session_data.json')
        import json
        with open(session_file, 'r') as f:
            session_data = json.load(f)
            
        driving_history_paths = session_data.get('driving_history_paths', [])
        activity_detail_paths = session_data.get('activity_detail_paths', [])
        report_date = session_data.get('report_date')
        
        if not driving_history_paths or not activity_detail_paths or not report_date:
            flash('Missing required data for processing', 'danger')
            return redirect(url_for('mtd_reports.upload_files'))
        
        # Process the files
        from process_mtd_files import process_mtd_files
        
        report_data = process_mtd_files(
            driving_history_paths=driving_history_paths,
            activity_detail_paths=activity_detail_paths,
            report_date=report_date
        )
        
        # Save report data to file
        report_file = os.path.join(current_app.root_path, 'uploads', 'mtd_reports', f'report_{report_date}.json')
        with open(report_file, 'w') as f:
            json.dump(report_data, f)
            
        return redirect(url_for('mtd_reports.show_report', date=report_date))
        
    except Exception as e:
        logger.error(f"Error processing report: {str(e)}")
        flash(f'Error processing report: {str(e)}', 'danger')
        return redirect(url_for('mtd_reports.upload_files'))
        
@mtd_reports_bp.route('/report/<date>', methods=['GET'])
def show_report(date):
    """Show MTD report"""
    try:
        # Load report data from file
        report_file = os.path.join(current_app.root_path, 'uploads', 'mtd_reports', f'report_{date}.json')
        import json
        with open(report_file, 'r') as f:
            report_data = json.load(f)
            
        return render_template('mtd_reports/report.html', report=report_data)
        
    except Exception as e:
        logger.error(f"Error showing report: {str(e)}")
        flash(f'Error showing report: {str(e)}', 'danger')
        return redirect(url_for('mtd_reports.dashboard'))
        
@mtd_reports_bp.route('/api/report/<date>', methods=['GET'])
def api_report(date):
    """API endpoint for MTD report data"""
    try:
        # Load report data from file
        report_file = os.path.join(current_app.root_path, 'uploads', 'mtd_reports', f'report_{date}.json')
        import json
        with open(report_file, 'r') as f:
            report_data = json.load(f)
            
        return jsonify(report_data)
        
    except Exception as e:
        logger.error(f"Error retrieving report data: {str(e)}")
        return jsonify({'error': str(e)}), 404