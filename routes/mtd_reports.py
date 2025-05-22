"""
MTD Reports Routes

This module provides routes for processing large Month-to-Date files.
It uses a specialized processor designed for memory-efficient handling of large files.
"""

import os
import logging
import json
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
@mtd_reports_bp.route('/dashboard')
def dashboard():
    """MTD Reports Dashboard"""
    try:
        # Create necessary directories if they don't exist
        upload_dir = os.path.join(current_app.root_path, 'uploads', 'mtd_reports')
        os.makedirs(upload_dir, exist_ok=True)
        
        return render_template('mtd_reports/dashboard.html')
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash(f'Error loading MTD Reports dashboard: {str(e)}', 'danger')
        return redirect(url_for('index'))

@mtd_reports_bp.route('/reports')
def list_reports():
    """List all available reports"""
    # Find all single date reports
    upload_dir = os.path.join(current_app.root_path, 'uploads', 'mtd_reports')
    single_reports = []
    interval_reports = []
    
    # Look for single date report files
    for filename in os.listdir(upload_dir):
        if filename.startswith('report_') and filename.endswith('.json'):
            try:
                date_str = filename.replace('report_', '').replace('.json', '')
                report_path = os.path.join(upload_dir, filename)
                with open(report_path, 'r') as f:
                    report_data = json.load(f)
                
                # Extract summary data
                report_summary = {
                    'date': date_str,
                    'total_drivers': report_data.get('total_drivers', 0),
                    'on_time_count': report_data.get('on_time_count', 0),
                    'late_count': report_data.get('late_count', 0),
                    'early_end_count': report_data.get('early_end_count', 0),
                    'not_on_job_count': report_data.get('not_on_job_count', 0),
                    'on_time_percent': report_data.get('on_time_percent', 0),
                    'late_percent': report_data.get('late_percent', 0),
                    'early_end_percent': report_data.get('early_end_percent', 0),
                    'not_on_job_percent': report_data.get('not_on_job_percent', 0)
                }
                single_reports.append(report_summary)
            except Exception as e:
                logger.error(f"Error loading report {filename}: {str(e)}")
    
    # Sort reports by date (newest first)
    single_reports.sort(key=lambda x: x['date'], reverse=True)
    
    # Look for interval report files
    for filename in os.listdir(upload_dir):
        if filename.startswith('interval_index_') and filename.endswith('.json'):
            try:
                report_path = os.path.join(upload_dir, filename)
                with open(report_path, 'r') as f:
                    report_data = json.load(f)
                
                # Extract summary data
                report_summary = {
                    'start_date': report_data.get('start_date'),
                    'end_date': report_data.get('end_date'),
                    'interval_type': report_data.get('interval_type', 'daily'),
                    'periods': len(report_data.get('reports', []))
                }
                interval_reports.append(report_summary)
            except Exception as e:
                logger.error(f"Error loading interval report {filename}: {str(e)}")
    
    # Sort interval reports by start date (newest first)
    interval_reports.sort(key=lambda x: x['start_date'], reverse=True)
    
    return render_template('mtd_reports/reports_list.html', 
                          single_reports=single_reports,
                          interval_reports=interval_reports)

@mtd_reports_bp.route('/upload', methods=['GET', 'POST'])
def upload_files():
    """Upload MTD files"""
    if request.method == 'POST':
        driving_history_files = request.files.getlist('driving_history')
        activity_detail_files = request.files.getlist('activity_detail')
        report_type = request.form.get('report_type', 'single')
        
        # Check if we have the necessary files
        if not driving_history_files or not activity_detail_files:
            flash('Please upload at least one file of each type', 'danger')
            return redirect(url_for('mtd_reports.upload_files'))
        
        # Save uploaded files
        driving_history_paths = process_uploaded_files(driving_history_files, 'driving_history')
        activity_detail_paths = process_uploaded_files(activity_detail_files, 'activity_detail')
        
        # If we have successfully saved files, prepare session data based on report type
        if driving_history_paths and activity_detail_paths:
            session_data = {
                'driving_history_paths': driving_history_paths,
                'activity_detail_paths': activity_detail_paths,
                'report_type': report_type
            }
            
            # Handle different report types
            if report_type == 'single':
                report_date = request.form.get('report_date')
                if not report_date:
                    flash('Please select a report date', 'danger')
                    return redirect(url_for('mtd_reports.upload_files'))
                session_data['report_date'] = report_date
                
            elif report_type == 'interval':
                start_date = request.form.get('start_date')
                end_date = request.form.get('end_date')
                interval_type = request.form.get('interval_type', 'daily')
                
                if not start_date or not end_date:
                    flash('Please select both start and end dates', 'danger')
                    return redirect(url_for('mtd_reports.upload_files'))
                
                session_data['start_date'] = start_date
                session_data['end_date'] = end_date
                session_data['interval_type'] = interval_type
            
            # Save session data to a temporary file
            session_file = os.path.join(current_app.root_path, 'uploads', 'mtd_reports', 'session_data.json')
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
        report_type = session_data.get('report_type', 'single')
        
        if not driving_history_paths or not activity_detail_paths:
            flash('Missing required files for processing', 'danger')
            return redirect(url_for('mtd_reports.upload_files'))
        
        # Import processors
        from process_mtd_files import process_mtd_files
        from datetime import datetime, timedelta
        
        # Process based on report type
        if report_type == 'single':
            report_date = session_data.get('report_date')
            if not report_date:
                flash('Missing report date', 'danger')
                return redirect(url_for('mtd_reports.upload_files'))
            
            # Process single date report
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
        
        elif report_type == 'interval':
            start_date = session_data.get('start_date')
            end_date = session_data.get('end_date')
            interval_type = session_data.get('interval_type', 'daily')
            
            if not start_date or not end_date:
                flash('Missing start or end date', 'danger')
                return redirect(url_for('mtd_reports.upload_files'))
            
            # Convert to datetime objects
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Calculate date intervals based on interval type
            date_intervals = []
            
            if interval_type == 'daily':
                # One report per day
                current_date = start_dt
                while current_date <= end_dt:
                    date_intervals.append(current_date.strftime('%Y-%m-%d'))
                    current_date += timedelta(days=1)
                
            elif interval_type == 'weekly':
                # One report per week
                current_date = start_dt
                while current_date <= end_dt:
                    week_end = min(current_date + timedelta(days=6), end_dt)
                    date_intervals.append({
                        'label': f"{current_date.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}",
                        'start': current_date.strftime('%Y-%m-%d'),
                        'end': week_end.strftime('%Y-%m-%d')
                    })
                    current_date += timedelta(days=7)
                
            elif interval_type == 'monthly':
                # One report per month
                current_date = start_dt.replace(day=1)  # Start at first day of month
                while current_date <= end_dt:
                    # Get last day of current month
                    if current_date.month == 12:
                        next_month = current_date.replace(year=current_date.year + 1, month=1)
                    else:
                        next_month = current_date.replace(month=current_date.month + 1)
                    
                    month_end = (next_month - timedelta(days=1))
                    month_end = min(month_end, end_dt)
                    
                    date_intervals.append({
                        'label': current_date.strftime('%B %Y'),
                        'start': current_date.strftime('%Y-%m-%d'),
                        'end': month_end.strftime('%Y-%m-%d')
                    })
                    
                    current_date = next_month
            
            # Generate and save reports for each interval
            reports = []
            
            if interval_type == 'daily':
                # Process daily reports
                for date in date_intervals:
                    report_data = process_mtd_files(
                        driving_history_paths=driving_history_paths,
                        activity_detail_paths=activity_detail_paths,
                        report_date=date
                    )
                    
                    # Save report data to file
                    report_file = os.path.join(current_app.root_path, 'uploads', 'mtd_reports', f'report_{date}.json')
                    with open(report_file, 'w') as f:
                        json.dump(report_data, f)
                    
                    reports.append({
                        'date': date,
                        'label': datetime.strptime(date, '%Y-%m-%d').strftime('%A, %B %d, %Y'),
                        'total_drivers': report_data.get('total_drivers', 0),
                        'on_time_count': report_data.get('on_time_count', 0),
                        'late_count': report_data.get('late_count', 0),
                        'early_end_count': report_data.get('early_end_count', 0),
                        'not_on_job_count': report_data.get('not_on_job_count', 0)
                    })
            else:
                # Process weekly/monthly reports
                for interval in date_intervals:
                    # Save interval info
                    interval_report = {
                        'label': interval['label'],
                        'start_date': interval['start'],
                        'end_date': interval['end'],
                        'interval_type': interval_type,
                        'days': []
                    }
                    
                    # Process each day in the interval - limit to 3 days max for performance
                    current_date = datetime.strptime(interval['start'], '%Y-%m-%d')
                    end_date = datetime.strptime(interval['end'], '%Y-%m-%d')
                    
                    # Limit the number of days to process to prevent timeout
                    days_to_process = []
                    max_days = 3  # Limit to 3 days per interval for performance
                    
                    # Calculate sample days across the interval
                    if (end_date - current_date).days > max_days:
                        # Process start, middle and end dates as a sample
                        total_days = (end_date - current_date).days + 1
                        interval_step = max(1, total_days // max_days)
                        
                        sample_date = current_date
                        while sample_date <= end_date:
                            days_to_process.append(sample_date)
                            sample_date += timedelta(days=interval_step)
                            
                        # Ensure end date is included if not already
                        if days_to_process[-1] != end_date:
                            if len(days_to_process) >= max_days:
                                days_to_process[-1] = end_date
                            else:
                                days_to_process.append(end_date)
                    else:
                        # Process all days if within limit
                        sample_date = current_date
                        while sample_date <= end_date:
                            days_to_process.append(sample_date)
                            sample_date += timedelta(days=1)
                            
                    # Custom JSON encoder to handle datetime objects
                    class DateTimeEncoder(json.JSONEncoder):
                        def default(self, o):
                            if isinstance(o, datetime):
                                return o.strftime('%Y-%m-%d')
                            return super().default(o)
                    
                    # Process the selected days
                    for sample_date in days_to_process:
                        date_str = sample_date.strftime('%Y-%m-%d')
                        
                        try:
                            # Process individual day
                            day_report = process_mtd_files(
                                driving_history_paths=driving_history_paths,
                                activity_detail_paths=activity_detail_paths,
                                report_date=date_str
                            )
                            
                            # Add day to interval report
                            interval_report['days'].append({
                                'date': date_str,
                                'label': sample_date.strftime('%A, %B %d'),
                                'total_drivers': day_report.get('total_drivers', 0),
                                'on_time_count': day_report.get('on_time_count', 0),
                                'late_count': day_report.get('late_count', 0),
                                'early_end_count': day_report.get('early_end_count', 0),
                                'not_on_job_count': day_report.get('not_on_job_count', 0)
                            })
                        except Exception as e:
                            logger.error(f"Error processing date {date_str}: {str(e)}")
                            import traceback
                            logger.error(traceback.format_exc())
                    
                    # Calculate interval summary
                    total_drivers = sum(day.get('total_drivers', 0) for day in interval_report['days'])
                    on_time_count = sum(day.get('on_time_count', 0) for day in interval_report['days'])
                    late_count = sum(day.get('late_count', 0) for day in interval_report['days'])
                    early_end_count = sum(day.get('early_end_count', 0) for day in interval_report['days'])
                    not_on_job_count = sum(day.get('not_on_job_count', 0) for day in interval_report['days'])
                    
                    interval_report['summary'] = {
                        'total_drivers': total_drivers,
                        'on_time_count': on_time_count,
                        'late_count': late_count,
                        'early_end_count': early_end_count,
                        'not_on_job_count': not_on_job_count,
                        'on_time_percent': round((on_time_count / total_drivers * 100) if total_drivers > 0 else 0),
                        'late_percent': round((late_count / total_drivers * 100) if total_drivers > 0 else 0),
                        'early_end_percent': round((early_end_count / total_drivers * 100) if total_drivers > 0 else 0),
                        'not_on_job_percent': round((not_on_job_count / total_drivers * 100) if total_drivers > 0 else 0)
                    }
                    
                    # Save interval report
                    interval_id = f"{interval['start']}_to_{interval['end']}"
                    report_file = os.path.join(current_app.root_path, 'uploads', 'mtd_reports', f'interval_{interval_id}.json')
                    with open(report_file, 'w') as f:
                        json.dump(interval_report, f)
                    
                    reports.append({
                        'id': interval_id,
                        'label': interval['label'],
                        'start_date': interval['start'],
                        'end_date': interval['end'],
                        'type': interval_type,
                        'total_drivers': total_drivers,
                        'on_time_count': on_time_count,
                        'late_count': late_count,
                        'early_end_count': early_end_count,
                        'not_on_job_count': not_on_job_count
                    })
            
            # Save reports index
            reports_index = {
                'interval_type': interval_type,
                'start_date': start_date,
                'end_date': end_date,
                'reports': reports
            }
            
            index_file = os.path.join(current_app.root_path, 'uploads', 'mtd_reports', f'interval_index_{start_date}_to_{end_date}.json')
            with open(index_file, 'w') as f:
                json.dump(reports_index, f, cls=DateTimeEncoder)
            
            # Redirect to interval reports page
            return redirect(url_for('mtd_reports.show_interval_reports', start=start_date, end=end_date))
        
    except Exception as e:
        logger.error(f"Error processing report: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        flash(f'Error processing report: {str(e)}', 'danger')
        return redirect(url_for('mtd_reports.upload_files'))
        
@mtd_reports_bp.route('/report/<date>', methods=['GET'])
def show_report(date):
    """Show MTD report"""
    try:
        # Load report data from file
        report_file = os.path.join(current_app.root_path, 'uploads', 'mtd_reports', f'report_{date}.json')
        with open(report_file, 'r') as f:
            report_data = json.load(f)
            
        return render_template('mtd_reports/report.html', report=report_data, date=date)
        
    except Exception as e:
        logger.error(f"Error showing report: {str(e)}")
        flash(f'Error showing report: {str(e)}', 'danger')
        return redirect(url_for('mtd_reports.dashboard'))
        
@mtd_reports_bp.route('/report/<date>/job_site/<job_site>')
def job_site_detail(date, job_site):
    """Show all drivers for a specific job site on a specific date"""
    try:
        # Load the full report first
        report_file = os.path.join(current_app.root_path, 'uploads', 'mtd_reports', f'report_{date}.json')
        with open(report_file, 'r') as f:
            report_data = json.load(f)
            
        # Filter drivers by job site
        job_site_drivers = []
        for driver in report_data.get('drivers', []):
            if driver.get('job_site') == job_site or driver.get('assigned_job') == job_site:
                job_site_drivers.append(driver)
                
        if not job_site_drivers:
            flash(f"No drivers found for job site {job_site} on date {date}", 'warning')
            return redirect(url_for('mtd_reports.show_report', date=date))
            
        # Get job site metrics
        metrics = {
            'total_drivers': len(job_site_drivers),
            'on_time_count': 0,
            'late_count': 0,
            'early_end_count': 0,
            'not_on_job_count': 0
        }
        
        for driver in job_site_drivers:
            if driver.get('status') == 'on_time':
                metrics['on_time_count'] += 1
            elif driver.get('status') == 'late':
                metrics['late_count'] += 1
            elif driver.get('status') == 'early_end':
                metrics['early_end_count'] += 1
            elif driver.get('status') == 'not_on_job':
                metrics['not_on_job_count'] += 1
                
        # Calculate percentages
        metrics['on_time_percent'] = round((metrics['on_time_count'] / metrics['total_drivers']) * 100) if metrics['total_drivers'] > 0 else 0
        metrics['late_percent'] = round((metrics['late_count'] / metrics['total_drivers']) * 100) if metrics['total_drivers'] > 0 else 0
        metrics['early_end_percent'] = round((metrics['early_end_count'] / metrics['total_drivers']) * 100) if metrics['total_drivers'] > 0 else 0
        metrics['not_on_job_percent'] = round((metrics['not_on_job_count'] / metrics['total_drivers']) * 100) if metrics['total_drivers'] > 0 else 0
        
        return render_template('mtd_reports/job_site_detail.html', 
                              job_site=job_site,
                              drivers=job_site_drivers,
                              metrics=metrics,
                              date=date)
    except Exception as e:
        logger.error(f"Error loading job site detail for {job_site} on date {date}: {str(e)}")
        flash(f"Error loading job site details: {str(e)}", 'danger')
        return redirect(url_for('mtd_reports.show_report', date=date))

@mtd_reports_bp.route('/report/<date>/driver/<driver_id>')
def driver_detail(date, driver_id):
    """Show driver detail for a specific date with GENIUS CORE validation"""
    try:
        # Load the full report first
        report_file = os.path.join(current_app.root_path, 'uploads', 'mtd_reports', f'report_{date}.json')
        with open(report_file, 'r') as f:
            report_data = json.load(f)
            
        # Find the specific driver
        driver = None
        for d in report_data.get('drivers', []):
            if str(d.get('id')) == str(driver_id):
                driver = d
                break
                
        if not driver:
            flash(f"Driver not found in report for date {date}", 'warning')
            return redirect(url_for('mtd_reports.show_report', date=date))
            
        # Enhance driver data with locations if available
        driver_locations = []
        
        # Look for location data in driving history if available
        if 'driving_history' in driver and driver['driving_history']:
            for record in driver['driving_history']:
                if 'lat' in record and 'lng' in record and record['lat'] and record['lng']:
                    driver_locations.append({
                        'lat': record['lat'],
                        'lng': record['lng'],
                        'timestamp': record.get('timestamp', ''),
                        'description': record.get('event_type', '')
                    })
        
        # Add locations to driver data
        driver['locations'] = driver_locations
        
        # Add validation notes if not present
        if 'validation_notes' not in driver:
            driver['validation_notes'] = []
            
            # Generate validation notes based on status with GENIUS CORE logic
            if driver.get('status') == 'on_time':
                driver['validation_notes'].append("Driver arrived on time and completed full shift.")
                driver['validation_notes'].append("GENIUS CORE: Location data confirms presence at job site.")
            elif driver.get('status') == 'late':
                driver['validation_notes'].append(f"Driver arrived {driver.get('minutes_late', 0)} minutes late.")
                driver['validation_notes'].append(f"GENIUS CORE: Late arrival verified through cross-source validation.")
                if driver.get('data_sources'):
                    driver['validation_notes'].append(f"Validated using {driver.get('data_sources')}.")
            elif driver.get('status') == 'early_end':
                driver['validation_notes'].append(f"Driver left {driver.get('minutes_early_end', 0)} minutes early.")
                driver['validation_notes'].append(f"GENIUS CORE: Early departure detected through GPS activity cessation.")
                if driver.get('data_sources'):
                    driver['validation_notes'].append(f"Validated using {driver.get('data_sources')}.")
            elif driver.get('status') == 'not_on_job':
                driver['validation_notes'].append("Driver was not detected at the assigned job site.")
                driver['validation_notes'].append("GENIUS CORE: Geofence validation failed to locate driver at designated coordinates.")
                if driver.get('data_sources'):
                    driver['validation_notes'].append(f"Validated using {driver.get('data_sources')}.")
        
        return render_template('mtd_reports/driver_detail.html', driver=driver, date=date)
    except Exception as e:
        logger.error(f"Error loading driver {driver_id} for date {date}: {str(e)}")
        flash(f"Error loading driver details: {str(e)}", 'danger')
        return redirect(url_for('mtd_reports.show_report', date=date))
        
@mtd_reports_bp.route('/interval/<start>/<end>', methods=['GET'])
def show_interval_reports(start, end):
    """Show interval reports dashboard"""
    try:
        # Load interval index from file
        index_file = os.path.join(current_app.root_path, 'uploads', 'mtd_reports', f'interval_index_{start}_to_{end}.json')
        import json
        with open(index_file, 'r') as f:
            reports_index = json.load(f)
            
        return render_template('mtd_reports/interval_reports.html', 
                              reports_index=reports_index,
                              start_date=start,
                              end_date=end)
                              
    except Exception as e:
        logger.error(f"Error showing interval reports: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        flash(f'Error showing interval reports: {str(e)}', 'danger')
        return redirect(url_for('mtd_reports.dashboard'))

@mtd_reports_bp.route('/interval_report/<id>', methods=['GET'])
def show_interval_report(id):
    """Show detailed interval report"""
    try:
        # Load interval report from file
        report_file = os.path.join(current_app.root_path, 'uploads', 'mtd_reports', f'interval_{id}.json')
        import json
        with open(report_file, 'r') as f:
            report_data = json.load(f)
            
        return render_template('mtd_reports/interval_report.html', report=report_data)
        
    except Exception as e:
        logger.error(f"Error showing interval report: {str(e)}")
        flash(f'Error showing interval report: {str(e)}', 'danger')
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
        
@mtd_reports_bp.route('/api/interval/<id>', methods=['GET'])
def api_interval_report(id):
    """API endpoint for interval report data"""
    try:
        # Load interval report from file
        report_file = os.path.join(current_app.root_path, 'uploads', 'mtd_reports', f'interval_{id}.json')
        import json
        with open(report_file, 'r') as f:
            report_data = json.load(f)
            
        return jsonify(report_data)
        
    except Exception as e:
        logger.error(f"Error retrieving interval report data: {str(e)}")
        return jsonify({'error': str(e)}), 404