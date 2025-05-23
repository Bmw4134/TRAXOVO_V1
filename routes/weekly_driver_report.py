"""
TRAXORA Fleet Management System - Weekly Driver Report Routes

This module provides routes for processing and generating weekly driver reports
directly within the TRAXORA dashboard.
"""

import os
import json
import logging
import traceback
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, jsonify, current_app, abort, send_file
)
from werkzeug.utils import secure_filename

from utils.attendance_pipeline import process_attendance_data
from utils.enhanced_data_ingestion import load_csv_file, load_excel_file, infer_file_type
from utils.dynamic_timecard_processor import process_dynamic_timecard
from utils.multi_source_processor import combine_attendance_sources

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
weekly_driver_report_bp = Blueprint('weekly_driver_report', __name__, url_prefix='/weekly-driver-report')

def get_data_directory():
    """Get data directory, creating it if needed"""
    data_dir = os.path.join(current_app.root_path, 'data', 'weekly_driver_reports')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_reports_directory():
    """Get reports directory, creating it if needed"""
    reports_dir = os.path.join(current_app.root_path, 'reports', 'weekly_driver_reports')
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir

def get_upload_directory():
    """Get upload directory, creating it if needed"""
    upload_dir = os.path.join(current_app.root_path, 'uploads', 'weekly_reports')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

@weekly_driver_report_bp.route('/')
def dashboard():
    """Weekly driver report dashboard"""
    try:
        # Get the current week's date range (Monday to Sunday)
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        # Format dates for display
        start_date_str = start_of_week.strftime('%Y-%m-%d')
        end_date_str = end_of_week.strftime('%Y-%m-%d')
        
        # Check if reports exist for current week
        reports_dir = get_reports_directory()
        weekly_report_path = os.path.join(reports_dir, f"weekly_{start_date_str}_to_{end_date_str}.json")
        report_exists = os.path.exists(weekly_report_path)
        
        # Get list of weeks with reports
        available_weeks = []
        if os.path.exists(reports_dir):
            for filename in os.listdir(reports_dir):
                if filename.startswith('weekly_') and filename.endswith('.json'):
                    # Extract date range from filename
                    date_part = filename[7:-5]  # Remove 'weekly_' and '.json'
                    if '_to_' in date_part:
                        start_date, end_date = date_part.split('_to_')
                        try:
                            # Parse dates
                            start = datetime.strptime(start_date, '%Y-%m-%d').date()
                            end = datetime.strptime(end_date, '%Y-%m-%d').date()
                            
                            # Add to list
                            available_weeks.append({
                                'start_date': start_date,
                                'end_date': end_date,
                                'start_formatted': start.strftime('%b %d, %Y'),
                                'end_formatted': end.strftime('%b %d, %Y'),
                                'filename': filename
                            })
                        except ValueError:
                            continue
        
        # Sort weeks by start date (newest first)
        available_weeks.sort(key=lambda x: x['start_date'], reverse=True)
        
        return render_template(
            'weekly_driver_report/dashboard.html',
            start_date=start_date_str,
            end_date=end_date_str,
            start_formatted=start_of_week.strftime('%b %d, %Y'),
            end_formatted=end_of_week.strftime('%b %d, %Y'),
            report_exists=report_exists,
            available_weeks=available_weeks
        )
    
    except Exception as e:
        logger.error(f"Error displaying weekly driver report dashboard: {str(e)}")
        flash(f"Error displaying dashboard: {str(e)}", "danger")
        return render_template('weekly_driver_report/dashboard.html')

@weekly_driver_report_bp.route('/generate', methods=['GET', 'POST'])
def generate_report():
    """Generate a weekly driver report"""
    if request.method == 'POST':
        try:
            # Get date range
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            
            if not start_date or not end_date:
                flash("Please provide start and end dates", "danger")
                return redirect(url_for('weekly_driver_report.dashboard'))
            
            # Validate date range
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                
                if start > end:
                    flash("Start date must be before end date", "danger")
                    return redirect(url_for('weekly_driver_report.dashboard'))
                
                if (end - start).days > 14:
                    flash("Date range should not exceed 14 days", "warning")
            except ValueError:
                flash("Invalid date format", "danger")
                return redirect(url_for('weekly_driver_report.dashboard'))
            
            # Process files for each day in the range
            current_date = start
            daily_reports = {}
            
            while current_date <= end:
                date_str = current_date.strftime('%Y-%m-%d')
                
                try:
                    logger.info(f"Processing data for date: {date_str}")
                    
                    # Look for files with the date in the filename
                    all_files = os.listdir(get_upload_directory())
                    date_files = [f for f in all_files if date_str in f]
                    
                    if not date_files:
                        logger.warning(f"No files found for date: {date_str}")
                        current_date += timedelta(days=1)
                        continue
                    
                    # Categorize files
                    driving_history_files = [f for f in date_files if 'driving' in f.lower() or 'drivinghistory' in f.lower()]
                    time_on_site_files = [f for f in date_files if 'timeonsite' in f.lower() or 'assetstimeonsite' in f.lower()]
                    activity_detail_files = [f for f in date_files if 'activity' in f.lower() or 'activitydetail' in f.lower()]
                    timecard_files = [f for f in date_files if 'timecard' in f.lower() or 'hours' in f.lower()]
                    
                    # Check for minimum required files
                    if not driving_history_files and not time_on_site_files:
                        logger.warning(f"Missing required files for date: {date_str}")
                        current_date += timedelta(days=1)
                        continue
                    
                    # Process files
                    driving_history_data = []
                    time_on_site_data = []
                    activity_detail_data = []
                    timecard_data = []
                    
                    # Process driving history files
                    for filename in driving_history_files:
                        file_path = os.path.join(get_upload_directory(), filename)
                        if filename.endswith('.csv'):
                            data = load_csv_file(file_path)
                        else:
                            data = load_excel_file(file_path)
                        
                        if data is not None:
                            driving_history_data.extend(data)
                    
                    # Process time on site files
                    for filename in time_on_site_files:
                        file_path = os.path.join(get_upload_directory(), filename)
                        if filename.endswith('.csv'):
                            data = load_csv_file(file_path)
                        else:
                            data = load_excel_file(file_path)
                        
                        if data is not None:
                            time_on_site_data.extend(data)
                    
                    # Process activity detail files
                    for filename in activity_detail_files:
                        file_path = os.path.join(get_upload_directory(), filename)
                        if filename.endswith('.csv'):
                            data = load_csv_file(file_path)
                        else:
                            data = load_excel_file(file_path)
                        
                        if data is not None:
                            activity_detail_data.extend(data)
                    
                    # Process timecard files
                    for filename in timecard_files:
                        file_path = os.path.join(get_upload_directory(), filename)
                        if filename.endswith('.xlsx'):
                            # Use dynamic timecard processor for Excel files
                            processed_data = process_dynamic_timecard(
                                file_path, 
                                start_date=date_str,
                                end_date=date_str
                            )
                            
                            if processed_data is not None and not processed_data.empty:
                                timecard_data.extend(processed_data.to_dict('records'))
                        else:
                            data = load_csv_file(file_path)
                            if data is not None:
                                timecard_data.extend(data)
                    
                    # Combine data from multiple sources
                    combined_data = combine_attendance_sources(
                        driving_history_data, 
                        time_on_site_data, 
                        activity_detail_data
                    )
                    
                    # Process attendance data
                    if combined_data:
                        attendance_report = process_attendance_data(combined_data, date_str, timecard_data)
                        
                        if attendance_report:
                            # Save daily report to reports directory
                            daily_report_dir = os.path.join(get_reports_directory(), date_str)
                            os.makedirs(daily_report_dir, exist_ok=True)
                            
                            with open(os.path.join(daily_report_dir, f"driver_report_{date_str}.json"), 'w') as f:
                                json.dump(attendance_report, f, indent=2)
                            
                            # Add to weekly report
                            daily_reports[date_str] = attendance_report
                    
                except Exception as day_error:
                    logger.error(f"Error processing data for date {date_str}: {str(day_error)}")
                    logger.error(traceback.format_exc())
                
                # Move to next day
                current_date += timedelta(days=1)
            
            # Create weekly report
            if daily_reports:
                weekly_report = {
                    'start_date': start_date,
                    'end_date': end_date,
                    'generated_at': datetime.now().isoformat(),
                    'daily_reports': daily_reports,
                    'summary': generate_weekly_summary(daily_reports)
                }
                
                # Save weekly report
                weekly_report_path = os.path.join(get_reports_directory(), f"weekly_{start_date}_to_{end_date}.json")
                with open(weekly_report_path, 'w') as f:
                    json.dump(weekly_report, f, indent=2)
                
                flash(f"Weekly report generated successfully for {start_date} to {end_date}", "success")
                return redirect(url_for('weekly_driver_report.view_report', start_date=start_date, end_date=end_date))
            else:
                flash("No data was processed for the selected date range. Please check uploaded files.", "warning")
                return redirect(url_for('weekly_driver_report.dashboard'))
            
        except Exception as e:
            logger.error(f"Error generating weekly report: {str(e)}")
            logger.error(traceback.format_exc())
            flash(f"Error generating weekly report: {str(e)}", "danger")
            return redirect(url_for('weekly_driver_report.dashboard'))
    
    # GET request - show form
    return render_template('weekly_driver_report/generate.html')

@weekly_driver_report_bp.route('/view/<start_date>/<end_date>')
def view_report(start_date, end_date):
    """View a weekly driver report"""
    try:
        # Get report from file
        report_path = os.path.join(get_reports_directory(), f"weekly_{start_date}_to_{end_date}.json")
        
        if not os.path.exists(report_path):
            flash("Report not found", "danger")
            return redirect(url_for('weekly_driver_report.dashboard'))
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        # Parse dates for display
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get dates in range
        date_range = []
        current_date = start
        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')
            formatted_date = current_date.strftime('%a, %b %d')
            
            date_range.append({
                'date': date_str,
                'formatted': formatted_date,
                'has_data': date_str in report.get('daily_reports', {})
            })
            
            current_date += timedelta(days=1)
        
        return render_template(
            'weekly_driver_report/view.html',
            report=report,
            start_date=start_date,
            end_date=end_date,
            start_formatted=start.strftime('%b %d, %Y'),
            end_formatted=end.strftime('%b %d, %Y'),
            date_range=date_range
        )
    
    except Exception as e:
        logger.error(f"Error viewing weekly report: {str(e)}")
        flash(f"Error viewing weekly report: {str(e)}", "danger")
        return redirect(url_for('weekly_driver_report.dashboard'))

@weekly_driver_report_bp.route('/api/day/<date>')
def api_day_data(date):
    """API endpoint to get data for a specific day"""
    try:
        # Get daily report from file
        daily_report_path = os.path.join(get_reports_directory(), date, f"driver_report_{date}.json")
        
        if not os.path.exists(daily_report_path):
            return jsonify({"error": "Report not found"}), 404
        
        with open(daily_report_path, 'r') as f:
            report = json.load(f)
        
        return jsonify(report)
    
    except Exception as e:
        logger.error(f"Error getting day data: {str(e)}")
        return jsonify({"error": f"Error getting day data: {str(e)}"}), 500

@weekly_driver_report_bp.route('/api/weekly/<start_date>/<end_date>')
def api_weekly_data(start_date, end_date):
    """API endpoint to get data for a weekly report"""
    try:
        # Get report from file
        report_path = os.path.join(get_reports_directory(), f"weekly_{start_date}_to_{end_date}.json")
        
        if not os.path.exists(report_path):
            return jsonify({"error": "Report not found"}), 404
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        return jsonify(report)
    
    except Exception as e:
        logger.error(f"Error getting weekly data: {str(e)}")
        return jsonify({"error": f"Error getting weekly data: {str(e)}"}), 500

@weekly_driver_report_bp.route('/upload', methods=['GET', 'POST'])
def upload_files():
    """Upload files for weekly driver report"""
    if request.method == 'POST':
        try:
            # Check if files were uploaded
            if 'files[]' not in request.files:
                flash("No files selected", "danger")
                return redirect(url_for('weekly_driver_report.upload_files'))
            
            files = request.files.getlist('files[]')
            
            if not files or all(file.filename == '' for file in files):
                flash("No files selected", "danger")
                return redirect(url_for('weekly_driver_report.upload_files'))
            
            # Save each file
            upload_dir = get_upload_directory()
            file_count = 0
            
            for file in files:
                if file and file.filename:
                    # Try to infer file type
                    file_type = infer_file_type(file)
                    
                    # Create filename with type prefix
                    if file_type:
                        prefix = file_type.replace(' ', '_')
                        filename = f"{prefix}_{secure_filename(file.filename)}"
                    else:
                        filename = secure_filename(file.filename)
                    
                    # Save file
                    file_path = os.path.join(upload_dir, filename)
                    file.save(file_path)
                    file_count += 1
            
            flash(f"Successfully uploaded {file_count} files", "success")
            return redirect(url_for('weekly_driver_report.dashboard'))
            
        except Exception as e:
            logger.error(f"Error uploading files: {str(e)}")
            flash(f"Error uploading files: {str(e)}", "danger")
            return redirect(url_for('weekly_driver_report.upload_files'))
    
    # GET request - show upload form
    return render_template('weekly_driver_report/upload.html')

@weekly_driver_report_bp.route('/download/<start_date>/<end_date>/<format>')
def download_report(start_date, end_date, format):
    """Download report in specified format"""
    try:
        # Get report from file
        report_path = os.path.join(get_reports_directory(), f"weekly_{start_date}_to_{end_date}.json")
        
        if not os.path.exists(report_path):
            flash("Report not found", "danger")
            return redirect(url_for('weekly_driver_report.dashboard'))
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        if format == 'json':
            # Create JSON file
            download_path = os.path.join(get_data_directory(), f"weekly_report_{start_date}_to_{end_date}.json")
            with open(download_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            return send_file(
                download_path,
                as_attachment=True,
                download_name=f"weekly_driver_report_{start_date}_to_{end_date}.json",
                mimetype='application/json'
            )
        
        elif format == 'csv':
            # Generate CSV file with all driver records
            import csv
            from io import StringIO
            
            # Prepare CSV data
            csv_data = StringIO()
            writer = csv.writer(csv_data)
            
            # Write header
            writer.writerow([
                'Date', 'Driver Name', 'Job Number', 'Job Name', 
                'Classification', 'Start Time', 'End Time', 
                'Working Hours', 'Late Minutes', 'Early End Minutes',
                'GPS Verified', 'Timecard Hours', 'Hours Difference'
            ])
            
            # Write driver records for each day
            for date, daily_report in report.get('daily_reports', {}).items():
                for driver in daily_report.get('driver_records', []):
                    writer.writerow([
                        date,
                        driver.get('driver_name', ''),
                        driver.get('job_number', ''),
                        driver.get('job_name', ''),
                        driver.get('classification', ''),
                        driver.get('start_time', ''),
                        driver.get('end_time', ''),
                        driver.get('hours', 0),
                        driver.get('late_minutes', 0),
                        driver.get('early_end_minutes', 0),
                        'Yes' if driver.get('gps_verified', False) else 'No',
                        driver.get('timecard_hours', ''),
                        driver.get('hours_difference', '')
                    ])
            
            # Save to file
            download_path = os.path.join(get_data_directory(), f"weekly_driver_report_{start_date}_to_{end_date}.csv")
            with open(download_path, 'w', newline='') as f:
                f.write(csv_data.getvalue())
            
            return send_file(
                download_path,
                as_attachment=True,
                download_name=f"weekly_driver_report_{start_date}_to_{end_date}.csv",
                mimetype='text/csv'
            )
        
        else:
            flash(f"Unsupported format: {format}", "danger")
            return redirect(url_for('weekly_driver_report.view_report', start_date=start_date, end_date=end_date))
    
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        flash(f"Error downloading report: {str(e)}", "danger")
        return redirect(url_for('weekly_driver_report.dashboard'))

def generate_weekly_summary(daily_reports):
    """Generate a summary of weekly attendance data"""
    try:
        # Initialize counters
        summary = {
            'total_drivers': 0,
            'on_time_count': 0,
            'late_count': 0,
            'early_end_count': 0,
            'not_on_job_count': 0,
            'average_late_minutes': 0,
            'average_early_end_minutes': 0,
            'driver_attendance': {},
            'job_attendance': {}
        }
        
        # Track late minutes and early end minutes for averages
        total_late_minutes = 0
        total_early_end_minutes = 0
        
        # Process each daily report
        for date, report in daily_reports.items():
            # Get driver records
            driver_records = report.get('driver_records', [])
            
            # Count drivers by classification
            on_time_drivers = sum(1 for d in driver_records if d.get('classification') == 'on_time')
            late_drivers = sum(1 for d in driver_records if d.get('classification') == 'late')
            early_end_drivers = sum(1 for d in driver_records if d.get('classification') == 'early_end')
            not_on_job_drivers = sum(1 for d in driver_records if d.get('classification') == 'not_on_job')
            
            # Accumulate totals
            summary['total_drivers'] += len(driver_records)
            summary['on_time_count'] += on_time_drivers
            summary['late_count'] += late_drivers
            summary['early_end_count'] += early_end_drivers
            summary['not_on_job_count'] += not_on_job_drivers
            
            # Calculate late and early end minutes
            for driver in driver_records:
                # Track driver attendance
                driver_name = driver.get('driver_name', 'Unknown')
                if driver_name not in summary['driver_attendance']:
                    summary['driver_attendance'][driver_name] = {
                        'days_worked': 0,
                        'on_time_count': 0,
                        'late_count': 0,
                        'early_end_count': 0,
                        'not_on_job_count': 0
                    }
                
                summary['driver_attendance'][driver_name]['days_worked'] += 1
                
                classification = driver.get('classification', '')
                if classification == 'on_time':
                    summary['driver_attendance'][driver_name]['on_time_count'] += 1
                elif classification == 'late':
                    summary['driver_attendance'][driver_name]['late_count'] += 1
                    
                    # Add late minutes
                    late_minutes = driver.get('late_minutes', 0)
                    if late_minutes:
                        total_late_minutes += late_minutes
                        
                elif classification == 'early_end':
                    summary['driver_attendance'][driver_name]['early_end_count'] += 1
                    
                    # Add early end minutes
                    early_end_minutes = driver.get('early_end_minutes', 0)
                    if early_end_minutes:
                        total_early_end_minutes += early_end_minutes
                        
                elif classification == 'not_on_job':
                    summary['driver_attendance'][driver_name]['not_on_job_count'] += 1
                
                # Track job site attendance
                job_number = driver.get('job_number', '')
                job_name = driver.get('job_name', '')
                job_key = f"{job_number} - {job_name}" if job_number and job_name else job_number or job_name or 'Unknown'
                
                if job_key not in summary['job_attendance']:
                    summary['job_attendance'][job_key] = {
                        'total_drivers': 0,
                        'on_time_count': 0,
                        'late_count': 0,
                        'early_end_count': 0,
                        'not_on_job_count': 0
                    }
                
                summary['job_attendance'][job_key]['total_drivers'] += 1
                
                if classification == 'on_time':
                    summary['job_attendance'][job_key]['on_time_count'] += 1
                elif classification == 'late':
                    summary['job_attendance'][job_key]['late_count'] += 1
                elif classification == 'early_end':
                    summary['job_attendance'][job_key]['early_end_count'] += 1
                elif classification == 'not_on_job':
                    summary['job_attendance'][job_key]['not_on_job_count'] += 1
        
        # Calculate averages
        if summary['late_count'] > 0:
            summary['average_late_minutes'] = round(total_late_minutes / summary['late_count'], 1)
        
        if summary['early_end_count'] > 0:
            summary['average_early_end_minutes'] = round(total_early_end_minutes / summary['early_end_count'], 1)
        
        # Calculate percentages
        total_classifications = summary['on_time_count'] + summary['late_count'] + summary['early_end_count'] + summary['not_on_job_count']
        
        if total_classifications > 0:
            summary['on_time_percentage'] = round((summary['on_time_count'] / total_classifications) * 100, 1)
            summary['late_percentage'] = round((summary['late_count'] / total_classifications) * 100, 1)
            summary['early_end_percentage'] = round((summary['early_end_count'] / total_classifications) * 100, 1)
            summary['not_on_job_percentage'] = round((summary['not_on_job_count'] / total_classifications) * 100, 1)
        else:
            summary['on_time_percentage'] = 0
            summary['late_percentage'] = 0
            summary['early_end_percentage'] = 0
            summary['not_on_job_percentage'] = 0
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating weekly summary: {str(e)}")
        return {}