"""
MTD Reports Routes - Fixed Version

This module provides the routes for the Month-to-Date reports section
with improved error handling and simplified user interface.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, session

# Import MTD data processor
from utils.mtd_data_processor import process_mtd_files

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
mtd_reports_bp = Blueprint('mtd_reports', __name__, url_prefix='/mtd-reports')

# Utility functions
def allowed_file(filename):
    """Check if file has an allowed extension"""
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_uploaded_files(files, file_type):
    """Process uploaded files and save them to the upload folder"""
    saved_files = []
    
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

# Routes
@mtd_reports_bp.route('/')
@mtd_reports_bp.route('/dashboard')
def dashboard():
    """MTD Reports Dashboard - Simple Version"""
    try:
        # Create necessary directories if they don't exist
        upload_dir = os.path.join(current_app.root_path, 'uploads', 'mtd_reports')
        os.makedirs(upload_dir, exist_ok=True)
        
        return render_template('mtd_reports/simple_dashboard.html')
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash(f'Error loading MTD Reports dashboard: {str(e)}', 'danger')
        return redirect(url_for('index'))

@mtd_reports_bp.route('/simple-upload', methods=['GET', 'POST'])
def simple_upload_files():
    """Simple Upload MTD Files"""
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'driving_history_files' not in request.files and 'activity_detail_files' not in request.files:
            flash('Please select at least one file to upload', 'danger')
            return redirect(request.url)
            
        driving_history_files = request.files.getlist('driving_history_files')
        activity_detail_files = request.files.getlist('activity_detail_files')
        report_date = request.form.get('report_date')
        
        if not driving_history_files[0].filename and not activity_detail_files[0].filename:
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if not report_date:
            flash('Please select a target report date', 'danger')
            return redirect(request.url)
            
        # Create directories if they don't exist
        upload_dir = os.path.join(current_app.root_path, 'uploads', 'mtd_reports')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save and track uploaded files
        driving_history_paths = []
        activity_detail_paths = []
        
        # Save driving history files
        for file in driving_history_files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                new_filename = f"driving_history_{timestamp}_{filename}"
                file_path = os.path.join(upload_dir, new_filename)
                file.save(file_path)
                driving_history_paths.append(file_path)
                logger.info(f"Saved driving history file: {file_path}")
        
        # Save activity detail files
        for file in activity_detail_files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                new_filename = f"activity_detail_{timestamp}_{filename}"
                file_path = os.path.join(upload_dir, new_filename)
                file.save(file_path)
                activity_detail_paths.append(file_path)
                logger.info(f"Saved activity detail file: {file_path}")
        
        # Process the files if we have both types
        if driving_history_paths and activity_detail_paths:
            try:
                # Process the data and generate a report
                report_data = process_mtd_files(driving_history_paths, activity_detail_paths, report_date)
                
                # Save the report data to a JSON file
                report_file = os.path.join(upload_dir, f'report_{report_date}.json')
                with open(report_file, 'w') as f:
                    json.dump(report_data, f)
                
                flash(f'Successfully processed data for {report_date}', 'success')
                return redirect(url_for('mtd_reports.show_report', date=report_date))
            except Exception as e:
                logger.error(f"Error processing MTD files: {str(e)}")
                flash(f'Error processing files: {str(e)}', 'danger')
                return redirect(url_for('mtd_reports.simple_reports'))
        else:
            flash('Please upload both driving history and activity detail files', 'warning')
            return redirect(request.url)
        
    return render_template('mtd_reports/simple_upload.html')

@mtd_reports_bp.route('/simple-reports')
def simple_reports():
    """Display a simplified reports list"""
    try:
        # For demonstration, create a basic list of sample reports
        # In a real implementation, this would be loaded from the database or files
        reports = [
            {
                'date': '2025-05-20',
                'driver_count': 42,
                'job_site_count': 15,
                'created_at': '2025-05-20 14:32:45'
            },
            {
                'date': '2025-05-19',
                'driver_count': 38,
                'job_site_count': 12,
                'created_at': '2025-05-19 16:20:10'
            },
            {
                'date': '2025-05-18',
                'driver_count': 44,
                'job_site_count': 14,
                'created_at': '2025-05-18 15:45:22'
            }
        ]
        return render_template('mtd_reports/simple_reports.html', reports=reports)
    except Exception as e:
        logger.error(f"Error loading reports list: {str(e)}")
        flash(f'Error loading reports list: {str(e)}', 'danger')
        return redirect(url_for('mtd_reports.dashboard'))

@mtd_reports_bp.route('/report/<date>')
def show_report(date):
    """Show MTD report with improved error handling"""
    try:
        # Load report data from the saved JSON file
        upload_dir = os.path.join(current_app.root_path, 'uploads', 'mtd_reports')
        report_file = os.path.join(upload_dir, f'report_{date}.json')
        
        # Check if the report file exists
        if os.path.exists(report_file):
            # Load the JSON data
            with open(report_file, 'r') as f:
                report_data = json.load(f)
                
            # Return the enhanced report view with the real data
            return render_template('mtd_reports/enhanced_report.html', 
                                  report=report_data,
                                  date=date)
        else:
            # If no report file exists, check if we need to generate one
            # Look for available Driving History and Activity Detail files
            files = os.listdir(upload_dir)
            driving_history_files = [os.path.join(upload_dir, f) for f in files if f.startswith('driving_history_')]
            activity_detail_files = [os.path.join(upload_dir, f) for f in files if f.startswith('activity_detail_')]
            
            if driving_history_files and activity_detail_files:
                # We have files available, try to generate a report
                try:
                    # Process the data and generate a report
                    report_data = process_mtd_files(driving_history_files, activity_detail_files, date)
                    
                    # Save the report data to a JSON file
                    with open(report_file, 'w') as f:
                        json.dump(report_data, f)
                    
                    # Return the enhanced report view
                    flash('Generated new report from available files', 'success')
                    return render_template('mtd_reports/enhanced_report.html', 
                                          report=report_data,
                                          date=date)
                except Exception as e:
                    logger.error(f"Error generating report on-demand: {str(e)}")
                    flash(f'Error generating report: {str(e)}', 'danger')
                    return redirect(url_for('mtd_reports.simple_reports'))
            else:
                # No files available, show a placeholder
                logger.info(f"No report file or source files available for date: {date}")
                flash('No report available for this date. Please upload files first.', 'warning')
                return redirect(url_for('mtd_reports.simple_upload_files'))
                              
    except Exception as e:
        logger.error(f"Error showing report: {str(e)}")
        flash(f'Error showing report: {str(e)}', 'danger')
        return redirect(url_for('mtd_reports.simple_reports'))

@mtd_reports_bp.route('/job-site/<date>/<job_site_id>')
def job_site_detail(date, job_site_id):
    """Show job site detail for a specific date"""
    try:
        # Create placeholder data for demonstration
        job_site_data = {
            'id': job_site_id,
            'name': 'Sample Job Site',
            'location': '123 Main St, Cityville',
            'foreman': 'John Smith',
            'project_number': 'PRJ-2024-001',
            'drivers': [
                {
                    'id': 1,
                    'name': 'John Smith',
                    'status': 'on_time',
                    'start_time': '07:15:00',
                    'end_time': '16:30:00'
                },
                {
                    'id': 2,
                    'name': 'Maria Garcia',
                    'status': 'late',
                    'start_time': '08:45:00',
                    'end_time': '17:00:00'
                }
            ]
        }
        
        return render_template('mtd_reports/job_site_detail.html',
                             job_site=job_site_data,
                             date=date)
                             
    except Exception as e:
        logger.error(f"Error showing job site detail: {str(e)}")
        flash(f'Error showing job site detail: {str(e)}', 'danger')
        return redirect(url_for('mtd_reports.show_report', date=date))

@mtd_reports_bp.route('/driver/<date>/<driver_id>')
def driver_detail(date, driver_id):
    """Show driver detail for a specific date"""
    try:
        # Create placeholder data for demonstration
        driver_data = {
            'id': driver_id,
            'name': 'Sample Driver',
            'employee_id': 'EMP-1234',
            'status': 'on_time',
            'start_time': '07:15:00',
            'end_time': '16:30:00',
            'job_site': 'Midtown Project',
            'driving_history': [
                {
                    'time': '07:05:00',
                    'event': 'Start',
                    'location': '123 Main St'
                },
                {
                    'time': '07:15:00',
                    'event': 'Arrival',
                    'location': 'Midtown Project'
                },
                {
                    'time': '12:00:00',
                    'event': 'Lunch Break',
                    'location': 'Midtown Project'
                },
                {
                    'time': '16:30:00',
                    'event': 'Departure',
                    'location': 'Midtown Project'
                }
            ]
        }
        
        return render_template('mtd_reports/driver_detail.html',
                             driver=driver_data,
                             date=date)
                             
    except Exception as e:
        logger.error(f"Error showing driver detail: {str(e)}")
        flash(f'Error showing driver detail: {str(e)}', 'danger')
        return redirect(url_for('mtd_reports.show_report', date=date))

# API endpoints
@mtd_reports_bp.route('/api/report/<date>')
def api_report(date):
    """API endpoint for MTD report data"""
    try:
        # Create placeholder data for demonstration
        report_data = {
            'date': date,
            'total_drivers': 42,
            'on_time_count': 35,
            'late_count': 7,
            'early_end_count': 5,
            'not_on_job_count': 3,
            'on_time_percent': 83,
            'late_percent': 17,
            'early_end_percent': 12,
            'not_on_job_percent': 7
        }
        
        return jsonify(report_data)
                              
    except Exception as e:
        logger.error(f"Error in API endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500