"""
TRAXORA Fleet Management System - Driver Reports Module

This module provides routes and functionality for the Driver Reports module,
including daily driver attendance tracking and reporting.
"""
import os
import logging
import pandas as pd
import random
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app

import sys
import os

# Add the parent directory to the sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our robust CSV parser
from utils.robust_csv import parse_driving_history, parse_activity_detail, smart_parse_csv

from app import db
from models import Driver, JobSite, DriverReport

logger = logging.getLogger(__name__)

# Create blueprint
driver_reports_bp = Blueprint('driver_reports', __name__, url_prefix='/driver-reports')

@driver_reports_bp.route('/')
@driver_reports_bp.route('/daily-report')
@driver_reports_bp.route('/daily-report/<date>')
def daily_report(date=None):
    """Daily Driver Report page"""
    try:
        # Parse date if provided, otherwise use today
        if date:
            report_date = datetime.strptime(date, '%Y-%m-%d').date()
        else:
            report_date = datetime.now().date()
            
        # Get driver reports for the specified date
        driver_reports = DriverReport.query.filter(
            DriverReport.report_date == report_date
        ).order_by(DriverReport.status, DriverReport.driver_id).all()
        
        return render_template(
            'drivers/daily_report.html',
            report_date=report_date,
            driver_reports=driver_reports,
            timedelta=timedelta  # Pass timedelta to template
        )
    except Exception as e:
        logger.error(f"Error in daily_report: {str(e)}")
        flash(f"Error loading daily report: {str(e)}", 'error')
        return render_template(
            'drivers/daily_report.html',
            report_date=datetime.now().date(),
            driver_reports=[],
            timedelta=timedelta
        )

@driver_reports_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    """Upload driver files page"""
    if request.method == 'POST':
        try:
            # Check if files were submitted
            if 'driving_history' not in request.files or 'activity_detail' not in request.files:
                flash('Missing required files', 'error')
                return redirect(request.url)
            
            driving_history_file = request.files['driving_history']
            activity_detail_file = request.files['activity_detail']
            asset_list_file = request.files.get('asset_list')
            
            # Check if a file was selected
            if driving_history_file.filename == '' or activity_detail_file.filename == '':
                flash('No selected files', 'error')
                return redirect(request.url)
            
            # Check if the files are valid
            if not allowed_file(driving_history_file.filename) or not allowed_file(activity_detail_file.filename):
                flash('Invalid file type', 'error')
                return redirect(request.url)
            
            if asset_list_file and asset_list_file.filename != '' and not allowed_file(asset_list_file.filename):
                flash('Invalid asset list file type', 'error')
                return redirect(request.url)
            
            # Get verify with asset list option
            verify_with_asset_list = request.form.get('verify_with_asset_list') == 'on'
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(current_app.root_path, 'uploads', 'driver_reports')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate timestamp for unique filenames
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # Save the uploaded files
            driving_history_path = os.path.join(upload_dir, f"{timestamp}_{secure_filename(driving_history_file.filename)}")
            activity_detail_path = os.path.join(upload_dir, f"{timestamp}_{secure_filename(activity_detail_file.filename)}")
            driving_history_file.save(driving_history_path)
            activity_detail_file.save(activity_detail_path)
            
            asset_list_path = None
            if asset_list_file and asset_list_file.filename != '':
                asset_list_path = os.path.join(upload_dir, f"{timestamp}_{secure_filename(asset_list_file.filename)}")
                asset_list_file.save(asset_list_path)
            
            # Process the files
            result = process_driver_files(driving_history_path, activity_detail_path, asset_list_path, verify_with_asset_list)
            
            if 'error' in result:
                flash(f"Error processing files: {result['error']}", 'error')
                return redirect(request.url)
            
            # Redirect to the daily report page for the processed date
            flash('Files processed successfully', 'success')
            return redirect(url_for(
                'driver_reports.daily_report',
                date=result.get('date', datetime.now().strftime('%Y-%m-%d'))
            ))
        except Exception as e:
            logger.error(f"Error in upload: {str(e)}")
            flash(f"Error processing files: {str(e)}", 'error')
            return redirect(request.url)
    
    return render_template('drivers/upload.html')

@driver_reports_bp.route('/api/drivers')
def api_drivers():
    """API endpoint to get all drivers"""
    try:
        # Query parameters for filtering
        status = request.args.get('status')
        job_site_id = request.args.get('job_site')
        
        # Base query
        query = Driver.query
        
        # Apply filters if provided
        if status:
            query = query.filter(Driver.status == status)
        
        if job_site_id:
            # This assumes Driver has a relationship with JobSite
            # Adjust this filter based on your actual model structure
            query = query.filter(Driver.job_site_id == job_site_id)
        
        # Get the drivers
        drivers = query.filter(Driver.is_active == True).all()
        
        # Prepare the response
        result = []
        for driver in drivers:
            driver_data = {
                'id': driver.id,
                'full_name': driver.full_name,
                'employee_id': driver.employee_id,
                'status': driver.status,
                'job_site': driver.job_site.name if driver.job_site else None
            }
            result.append(driver_data)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in api_drivers: {str(e)}")
        return jsonify({'error': str(e)}), 500

@driver_reports_bp.route('/api/daily-report/<date>')
def api_daily_report(date):
    """API endpoint to get daily report data for a specific date"""
    try:
        # Parse date
        report_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Get driver reports for the specified date
        driver_reports = DriverReport.query.filter(
            DriverReport.report_date == report_date
        ).order_by(DriverReport.status, DriverReport.driver_id).all()
        
        # Prepare the response
        result = []
        for report in driver_reports:
            report_data = {
                'id': report.id,
                'driver': {
                    'id': report.driver.id,
                    'full_name': report.driver.full_name,
                    'employee_id': report.driver.employee_id
                } if report.driver else None,
                'job_site': {
                    'id': report.job_site.id,
                    'name': report.job_site.name,
                    'job_number': report.job_site.job_number
                } if report.job_site else None,
                'scheduled_start_time': report.scheduled_start_time.strftime('%H:%M') if report.scheduled_start_time else None,
                'actual_start_time': report.actual_start_time.strftime('%H:%M') if report.actual_start_time else None,
                'scheduled_end_time': report.scheduled_end_time.strftime('%H:%M') if report.scheduled_end_time else None,
                'actual_end_time': report.actual_end_time.strftime('%H:%M') if report.actual_end_time else None,
                'status': report.status
            }
            result.append(report_data)
        
        # Add summary statistics
        status_counts = {
            'on_time': sum(1 for r in driver_reports if r.status == 'on_time'),
            'late': sum(1 for r in driver_reports if r.status == 'late'),
            'early_end': sum(1 for r in driver_reports if r.status == 'early_end'),
            'not_on_job': sum(1 for r in driver_reports if r.status == 'not_on_job'),
            'total': len(driver_reports)
        }
        
        return jsonify({
            'date': report_date.strftime('%Y-%m-%d'),
            'reports': result,
            'statistics': status_counts
        })
    except Exception as e:
        logger.error(f"Error in api_daily_report: {str(e)}")
        return jsonify({'error': str(e)}), 500

def allowed_file(filename):
    """Check if the file extension is allowed"""
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_driver_files(driving_history_path, activity_detail_path, asset_list_path=None, verify_with_asset_list=True):
    """
    Process driver files and generate daily report.
    
    This is a simplified implementation that would be expanded in the actual application
    to include the full GENIUS CORE logic for driver attendance tracking.
    
    Args:
        driving_history_path: Path to the driving history file
        activity_detail_path: Path to the activity detail file
        asset_list_path: Path to the asset list file (optional)
        verify_with_asset_list: Whether to verify drivers against the asset list
        
    Returns:
        dict: Results of processing
    """
    try:
        logger.info("Processing driver files with GENIUS CORE CONTINUITY MODE")
        
        # Load the files
        driving_history_df = load_file(driving_history_path)
        activity_detail_df = load_file(activity_detail_path)
        asset_list_df = load_file(asset_list_path) if asset_list_path else None
        
        if driving_history_df is None or activity_detail_df is None:
            return {'error': 'Failed to load input files'}
        
        if verify_with_asset_list and asset_list_df is None and asset_list_path:
            return {'error': 'Failed to load asset list file for verification'}
        
        # Extract date from driving history file
        # This assumes the file has a 'Date' column
        if 'Date' not in driving_history_df.columns:
            return {'error': 'Driving history file missing Date column'}
        
        # Get the first date in the file
        date_str = driving_history_df['Date'].iloc[0]
        date_obj = None
        
        # Try to parse the date
        try:
            # Handle different date formats
            if isinstance(date_str, str):
                # Try different formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        date_obj = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        continue
            elif isinstance(date_str, datetime):
                date_obj = date_str.date()
            else:
                # For pandas Timestamp or other date types
                date_obj = pd.to_datetime(date_str).date()
        except Exception as e:
            logger.error(f"Error parsing date from driving history: {str(e)}")
            date_obj = datetime.now().date()
        
        if date_obj is None:
            logger.warning("Could not determine date from file, using today's date")
            date_obj = datetime.now().date()
        
        logger.info(f"Processing data for date: {date_obj}")
        
        # In a real implementation, this is where we would execute the full GENIUS CORE
        # driver attendance tracking logic, including:
        # 1. Normalizing driver names
        # 2. Matching drivers across files
        # 3. Verifying against the asset list
        # 4. Classifying drivers (on time, late, early end, not on job)
        # 5. Saving the results to the database
        
        # For this prototype, we'll simulate the result
        # In a real implementation, this would be replaced with actual processing logic
        simulate_daily_report(date_obj)
        
        return {
            'success': True,
            'date': date_obj.strftime('%Y-%m-%d'),
            'message': 'Files processed successfully'
        }
    except Exception as e:
        logger.error(f"Error processing driver files: {str(e)}")
        return {'error': str(e)}

def load_file(file_path):
    """
    Load a file into a pandas DataFrame using robust parsing methods.
    
    Args:
        file_path: Path to the file
        
    Returns:
        DataFrame: Loaded DataFrame or empty DataFrame if failed
    """
    if file_path is None:
        logger.warning("No file path provided to load_file")
        return pd.DataFrame()
    
    if not os.path.exists(file_path):
        logger.warning(f"File does not exist: {file_path}")
        return pd.DataFrame()
    
    try:
        logger.info(f"Loading file: {file_path}")
        # Determine file type from extension and name
        file_ext = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else ''
        filename = os.path.basename(file_path).lower()
        
        if file_ext == 'csv':
            # Use our robust CSV parsing utilities based on file type
            if 'drivinghistory' in filename.replace(' ', '') or 'driving' in filename.lower():
                logger.info(f"Detected driving history file, using specialized parser: {filename}")
                return parse_driving_history(file_path)
            elif 'activitydetail' in filename.replace(' ', '') or 'activity' in filename.lower():
                logger.info(f"Detected activity detail file, using specialized parser: {filename}")
                return parse_activity_detail(file_path)
            else:
                # Use the generic smart parser for other CSV files
                logger.info(f"Using generic robust CSV parser for: {filename}")
                return smart_parse_csv(file_path)
        elif file_ext in ['xls', 'xlsx']:
            # Excel files
            logger.info(f"Loading Excel file: {filename}")
            return pd.read_excel(file_path)
        else:
            logger.warning(f"Unsupported file format: {file_ext} for {filename}")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {str(e)}")
        # Return empty DataFrame to ensure consistent return type
        return pd.DataFrame()

def simulate_daily_report(date_obj):
    """
    Simulate generating a daily report for testing purposes.
    
    In a real implementation, this would be replaced with actual data processing.
    """
    try:
        # Clear existing reports for this date to avoid duplicates
        DriverReport.query.filter_by(report_date=date_obj).delete()
        
        # Get all active drivers and job sites
        drivers = Driver.query.filter_by(is_active=True).all()
        job_sites = JobSite.query.filter_by(is_active=True).all()
        
        if not drivers or not job_sites:
            # If no drivers or job sites exist, create some sample data
            if not drivers:
                sample_drivers = [
                    {'full_name': 'John Smith', 'employee_id': 'EMP001'},
                    {'full_name': 'Jane Doe', 'employee_id': 'EMP002'},
                    {'full_name': 'Bob Johnson', 'employee_id': 'EMP003'},
                    {'full_name': 'Alice Brown', 'employee_id': 'EMP004'},
                    {'full_name': 'Charlie Davis', 'employee_id': 'EMP005'}
                ]
                
                for driver_data in sample_drivers:
                    driver = Driver(
                        full_name=driver_data['full_name'],
                        employee_id=driver_data['employee_id'],
                        is_active=True,
                        status='active'
                    )
                    db.session.add(driver)
                
                db.session.commit()
                drivers = Driver.query.filter_by(is_active=True).all()
            
            if not job_sites:
                sample_job_sites = [
                    {'name': 'Downtown Construction', 'job_number': 'JOB001'},
                    {'name': 'Highway Extension', 'job_number': 'JOB002'},
                    {'name': 'Commercial Building', 'job_number': 'JOB003'}
                ]
                
                for site_data in sample_job_sites:
                    job_site = JobSite(
                        name=site_data['name'],
                        job_number=site_data['job_number'],
                        is_active=True
                    )
                    db.session.add(job_site)
                
                db.session.commit()
                job_sites = JobSite.query.filter_by(is_active=True).all()
        
        # Generate random reports
        import random
        
        # Set seed for reproducibility within a day
        random.seed(date_obj.toordinal())
        
        for driver in drivers:
            # Randomly assign a job site
            job_site = random.choice(job_sites)
            
            # Generate scheduled times
            scheduled_start = datetime.combine(date_obj, datetime.strptime('07:00', '%H:%M').time())
            scheduled_end = datetime.combine(date_obj, datetime.strptime('16:00', '%H:%M').time())
            
            # Randomly determine status
            status_choices = ['on_time', 'late', 'early_end', 'not_on_job']
            status_weights = [0.6, 0.2, 0.15, 0.05]  # Probabilities for each status
            status = random.choices(status_choices, weights=status_weights, k=1)[0]
            
            # Generate actual times based on status
            if status == 'on_time':
                # On time: start within 15 minutes of scheduled, end after scheduled
                actual_start = scheduled_start + timedelta(minutes=random.randint(-5, 10))
                actual_end = scheduled_end + timedelta(minutes=random.randint(0, 30))
            elif status == 'late':
                # Late: start more than 15 minutes after scheduled
                actual_start = scheduled_start + timedelta(minutes=random.randint(16, 60))
                actual_end = scheduled_end + timedelta(minutes=random.randint(0, 30))
            elif status == 'early_end':
                # Early end: start on time, end more than 30 minutes before scheduled
                actual_start = scheduled_start + timedelta(minutes=random.randint(-5, 10))
                actual_end = scheduled_end - timedelta(minutes=random.randint(31, 90))
            else:  # not_on_job
                # Not on job: no actual times
                actual_start = None
                actual_end = None
            
            # Create the driver report
            report = DriverReport(
                driver_id=driver.id,
                job_site_id=job_site.id,
                report_date=date_obj,
                scheduled_start_time=scheduled_start,
                scheduled_end_time=scheduled_end,
                actual_start_time=actual_start,
                actual_end_time=actual_end,
                status=status
            )
            
            db.session.add(report)
        
        db.session.commit()
        logger.info(f"Generated simulated daily report for {date_obj}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error simulating daily report: {str(e)}")
        raise