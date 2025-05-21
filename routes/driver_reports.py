"""
TRAXORA Fleet Management System - Driver Reports Module

This module provides the routes and functionality for the Driver Reports module,
which is responsible for processing driver attendance and activity data.
"""
import os
import logging
import pandas as pd
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename

from app import db
from models import Driver, Asset, AttendanceRecord, JobSite, ActivityLog

logger = logging.getLogger(__name__)

# Create blueprint
driver_reports_bp = Blueprint('driver_reports', __name__, url_prefix='/drivers')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_csv(file_path):
    """Load a CSV file into a pandas DataFrame"""
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Error loading CSV file {file_path}: {str(e)}")
        return None

def derive_driver_reports(driving_history_df, activity_detail_df):
    """
    Derive driver reports from driving history and activity detail data
    
    This function implements the core logic of the Driver Reports module:
    1. Process driving history and activity detail data
    2. Derive Start Time, End Time, and Job fields from event timestamps
    3. Generate structured report records
    """
    if driving_history_df is None or activity_detail_df is None:
        return pd.DataFrame()
    
    # Normalize driver names
    driving_history_df['NormalizedDriver'] = driving_history_df['Driver'].apply(normalize_name)
    activity_detail_df['NormalizedDriver'] = activity_detail_df['Driver'].apply(normalize_name)
    
    # Process driving history to extract start and end times
    driving_history_grouped = driving_history_df.groupby(['NormalizedDriver', 'Date'])
    
    # Create a new DataFrame to store the results
    driver_reports = []
    
    for (driver_name, date), group in driving_history_grouped:
        # Extract earliest and latest timestamps for each driver on each date
        start_time = group['StartTime'].min() if 'StartTime' in group.columns else None
        end_time = group['EndTime'].max() if 'EndTime' in group.columns else None
        
        # Extract job information from activity detail
        job_info = activity_detail_df[
            (activity_detail_df['NormalizedDriver'] == driver_name) & 
            (activity_detail_df['Date'] == date)
        ]
        
        job_site = job_info['JobSite'].iloc[0] if not job_info.empty and 'JobSite' in job_info.columns else None
        
        # Create a report record
        driver_reports.append({
            'DriverName': driver_name,
            'Date': date,
            'StartTime': start_time,
            'EndTime': end_time,
            'JobSite': job_site,
            'Source': 'driving_history'
        })
    
    # Convert to DataFrame
    return pd.DataFrame(driver_reports)

def cross_verify_with_asset_list(driver_reports, asset_list_df):
    """
    Cross-verify driver reports with the Asset List
    
    This function ensures that all drivers in the reports are present in the Asset List,
    which is the source of truth for driver-asset mappings.
    """
    if driver_reports.empty or asset_list_df is None:
        return driver_reports
    
    # Normalize driver names in the asset list
    asset_list_df['NormalizedDriver'] = asset_list_df['Driver'].apply(normalize_name)
    
    # Filter driver reports to include only drivers in the asset list
    verified_driver_reports = driver_reports[driver_reports['DriverName'].isin(asset_list_df['NormalizedDriver'])]
    
    # Add asset information from the asset list
    verified_driver_reports = verified_driver_reports.merge(
        asset_list_df[['NormalizedDriver', 'Asset', 'AssetType']],
        left_on='DriverName',
        right_on='NormalizedDriver',
        how='left'
    )
    
    return verified_driver_reports

def normalize_name(name):
    """Normalize driver name for consistent matching"""
    if name is None:
        return ""
    
    # Convert to lowercase and remove extra spaces
    normalized = str(name).lower().strip()
    
    # Handle common name formats (last, first -> first last)
    if ',' in normalized:
        parts = normalized.split(',')
        if len(parts) >= 2:
            normalized = f"{parts[1].strip()} {parts[0].strip()}"
    
    return normalized

def classify_driver_status(row):
    """
    Classify driver status based on scheduled and actual times
    
    Classification rules:
    - On Time: Within 15 minutes of scheduled start time
    - Late: More than 15 minutes after scheduled start time
    - Early End: More than 30 minutes before scheduled end time
    - Not On Job: Not present in driving history
    """
    if pd.isna(row['StartTime']):
        return 'not_on_job'
    
    scheduled_start = row['ScheduledStartTime']
    scheduled_end = row['ScheduledEndTime']
    actual_start = row['StartTime']
    actual_end = row['EndTime']
    
    # Convert to datetime if they are strings
    if isinstance(scheduled_start, str):
        scheduled_start = pd.to_datetime(scheduled_start)
    if isinstance(scheduled_end, str):
        scheduled_end = pd.to_datetime(scheduled_end)
    if isinstance(actual_start, str):
        actual_start = pd.to_datetime(actual_start)
    if isinstance(actual_end, str):
        actual_end = pd.to_datetime(actual_end)
    
    # If any of the required fields are missing, return 'unknown'
    if pd.isna(scheduled_start) or pd.isna(actual_start):
        return 'unknown'
    
    # Calculate time differences
    start_diff = (actual_start - scheduled_start).total_seconds() / 60  # in minutes
    
    if start_diff > 15:
        return 'late'
    
    # Check for early end if both scheduled and actual end times are available
    if not pd.isna(scheduled_end) and not pd.isna(actual_end):
        end_diff = (scheduled_end - actual_end).total_seconds() / 60  # in minutes
        if end_diff > 30:
            return 'early_end'
    
    return 'on_time'

@driver_reports_bp.route('/')
def index():
    """Driver Reports main page"""
    return render_template('drivers/index.html')

@driver_reports_bp.route('/daily-report')
def daily_report():
    """Daily Driver Report page"""
    # Get the date parameter, default to today
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    try:
        # Convert to datetime
        report_date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Get driver report for the specified date
        driver_reports = AttendanceRecord.query.filter(
            AttendanceRecord.date == report_date
        ).all()
        
        return render_template(
            'drivers/daily_report.html',
            report_date=report_date,
            driver_reports=driver_reports
        )
    except ValueError:
        flash(f"Invalid date format: {date_str}", 'error')
        return redirect(url_for('driver_reports.daily_report'))
    except Exception as e:
        flash(f"Error retrieving driver report: {str(e)}", 'error')
        return redirect(url_for('driver_reports.daily_report'))

@driver_reports_bp.route('/upload', methods=['GET', 'POST'])
def upload_files():
    """Upload driving history and activity detail files"""
    if request.method == 'POST':
        # Check if files were submitted
        if 'driving_history' not in request.files or 'activity_detail' not in request.files:
            flash('Missing required files', 'error')
            return redirect(request.url)
        
        driving_history_file = request.files['driving_history']
        activity_detail_file = request.files['activity_detail']
        
        # Validate file extensions
        if not allowed_file(driving_history_file.filename) or not allowed_file(activity_detail_file.filename):
            flash('Invalid file format. Only CSV and Excel files are allowed.', 'error')
            return redirect(request.url)
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the uploaded files
        driving_history_path = os.path.join(upload_dir, secure_filename(driving_history_file.filename))
        activity_detail_path = os.path.join(upload_dir, secure_filename(activity_detail_file.filename))
        
        driving_history_file.save(driving_history_path)
        activity_detail_file.save(activity_detail_path)
        
        # Process the files
        try:
            # Load the uploaded files
            driving_history_df = load_csv(driving_history_path)
            activity_detail_df = load_csv(activity_detail_path)
            
            # Derive driver reports
            driver_reports = derive_driver_reports(driving_history_df, activity_detail_df)
            
            # Process and store the results
            # (In a real implementation, we would save these to the database)
            
            flash('Files uploaded and processed successfully', 'success')
            return redirect(url_for('driver_reports.daily_report'))
        except Exception as e:
            flash(f"Error processing files: {str(e)}", 'error')
            return redirect(request.url)
    
    return render_template('drivers/upload.html')

@driver_reports_bp.route('/api/daily-report/<date_str>')
def api_daily_report(date_str):
    """API endpoint for daily driver report data"""
    try:
        # Convert to datetime
        report_date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Get driver report for the specified date
        driver_reports = AttendanceRecord.query.filter(
            AttendanceRecord.date == report_date
        ).all()
        
        # Convert to JSON
        result = []
        for report in driver_reports:
            result.append({
                'id': report.id,
                'driver_name': report.driver.full_name if report.driver else 'Unknown',
                'job_site': report.job_site.name if report.job_site else 'Unknown',
                'scheduled_start': report.scheduled_start_time.strftime('%H:%M') if report.scheduled_start_time else None,
                'scheduled_end': report.scheduled_end_time.strftime('%H:%M') if report.scheduled_end_time else None,
                'actual_start': report.actual_start_time.strftime('%H:%M') if report.actual_start_time else None,
                'actual_end': report.actual_end_time.strftime('%H:%M') if report.actual_end_time else None,
                'status': report.status
            })
        
        return jsonify(result)
    except ValueError:
        return jsonify({'error': f"Invalid date format: {date_str}"}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500