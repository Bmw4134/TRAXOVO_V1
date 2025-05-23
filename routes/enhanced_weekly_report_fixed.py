"""
TRAXORA Fleet Management System - Enhanced Weekly Driver Report Routes

This module provides routes for processing and generating enhanced weekly driver reports
using the new modern UI style across the TRAXORA dashboard.
"""
import json
import logging
import os
import shutil
from datetime import datetime, timedelta

import pandas as pd
from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request, send_file, session, url_for)
from werkzeug.utils import secure_filename

from utils.weekly_driver_utils import process_may_timecard_data, process_weekly_driver_data

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('weekly_report', __name__, url_prefix='/weekly-report')

def get_reports_directory():
    """Get reports directory, creating it if needed"""
    reports_dir = os.path.join(current_app.root_path, 'reports', 'weekly_driver_reports')
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir

def get_attached_assets_directory():
    """Get attached_assets directory, creating it if needed"""
    attached_assets_dir = os.path.join(os.getcwd(), 'attached_assets')
    os.makedirs(attached_assets_dir, exist_ok=True)
    return attached_assets_dir

@bp.route('/')
def dashboard():
    """Enhanced weekly driver report dashboard"""
    try:
        # Get the requested week's date range
        now = datetime.now()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # If no dates provided, default to the current week (Sunday to Saturday)
        if not start_date or not end_date:
            # Find the previous Sunday
            days_since_sunday = now.weekday() + 1  # +1 because weekday() returns 0 for Monday
            if days_since_sunday == 7:  # If today is Sunday
                days_since_sunday = 0
            
            start_date = (now - timedelta(days=days_since_sunday)).strftime('%Y-%m-%d')
            end_date = (now + timedelta(days=6-days_since_sunday)).strftime('%Y-%m-%d')
            
        # Check if we have a report for this date range
        reports_dir = get_reports_directory()
        report_filename = f"weekly_driver_report_{start_date}_to_{end_date}.json"
        report_path = os.path.join(reports_dir, report_filename)
        
        has_report = os.path.exists(report_path)
        
        # Get a list of available reports
        available_reports = []
        for filename in os.listdir(reports_dir):
            if filename.startswith("weekly_driver_report_") and filename.endswith(".json"):
                # Extract date range from filename
                date_part = filename.replace("weekly_driver_report_", "").replace(".json", "")
                if "to" in date_part:
                    report_start, report_end = date_part.split("_to_")
                    available_reports.append({
                        "start_date": report_start,
                        "end_date": report_end,
                        "filename": filename
                    })
        
        # Sort reports by start date (newest first)
        available_reports.sort(key=lambda x: x["start_date"], reverse=True)
        
        # Special handling for the May 18-24 report
        may_report = {
            "start_date": "2025-05-18",
            "end_date": "2025-05-24", 
            "is_may_report": True
        }
        
        # Add May report to available reports if not already present
        if not any(r["start_date"] == "2025-05-18" and r["end_date"] == "2025-05-24" for r in available_reports):
            available_reports.insert(0, may_report)
        
        return render_template(
            'enhanced_weekly_report/dashboard.html',
            start_date=start_date,
            end_date=end_date,
            has_report=has_report,
            available_reports=available_reports
        )
    except Exception as e:
        logger.error(f"Error displaying enhanced weekly driver report dashboard: {str(e)}")
        flash(f"Error displaying dashboard: {str(e)}", "danger")
        return render_template('enhanced_weekly_report/dashboard.html')

@bp.route('/upload')
def upload():
    """Display upload form for weekly driver report data files"""
    try:
        today = datetime.now().date().strftime('%Y-%m-%d')
        return render_template('enhanced_weekly_report/upload.html', today=today)
    except Exception as e:
        logger.error(f"Error displaying upload form: {str(e)}")
        flash(f"Error displaying upload form: {str(e)}", "danger")
        return redirect(url_for('weekly_report.dashboard'))

@bp.route('/upload/files', methods=['POST'])
def upload_files():
    """Upload data files for weekly driver report"""
    try:
        if 'files[]' not in request.files:
            flash('No files selected', 'warning')
            return redirect(url_for('weekly_report.upload'))
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, 'uploads', 'weekly_driver_reports')
        os.makedirs(upload_dir, exist_ok=True)
        
        files = request.files.getlist('files[]')
        if not files or len(files) == 0 or files[0].filename == '':
            flash('No files selected', 'warning')
            return redirect(url_for('weekly_report.upload'))
        
        # Save all uploaded files
        saved_files = []
        for file in files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                saved_files.append(file_path)
        
        # Get date range for the report
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        if not start_date or not end_date:
            flash('Start and end dates are required', 'warning')
            return redirect(url_for('weekly_report.upload'))
        
        # Process the uploaded files and generate report
        try:
            process_weekly_driver_data(saved_files, start_date, end_date)
            flash('Weekly driver report generated successfully', 'success')
            return redirect(url_for('weekly_report.view_report', start_date=start_date, end_date=end_date))
        except Exception as e:
            logger.error(f"Error processing files: {str(e)}")
            flash(f"Error processing files: {str(e)}", "danger")
            return redirect(url_for('weekly_report.upload'))
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}")
        flash(f"Error uploading files: {str(e)}", "danger")
        return redirect(url_for('weekly_report.upload'))

@bp.route('/process-may-data')
def process_may_data():
    """Process May 18-24 data for the enhanced weekly report"""
    try:
        start_date = "2025-05-18"
        end_date = "2025-05-24"
        
        # Set up required file paths
        attached_assets_dir = get_attached_assets_directory()
        
        # Check if the May 18-24 timecard file exists
        timecard_file = os.path.join(attached_assets_dir, "Timecards - 2025-05-18 - 2025-05-24 (4).xlsx")
        if not os.path.exists(timecard_file):
            flash("May 18-24 timecard file not found", "warning")
            return redirect(url_for('weekly_report.upload'))
        
        # Process the timecard data
        process_may_timecard_data(timecard_file, start_date, end_date)
        flash("May 18-24 report generated successfully", "success")
        return redirect(url_for('weekly_report.view_report', start_date=start_date, end_date=end_date))
    except Exception as e:
        logger.error(f"Error processing May data: {str(e)}")
        flash(f"Error processing May data: {str(e)}", "danger")
        return redirect(url_for('weekly_report.dashboard'))

@bp.route('/report/<start_date>/<end_date>')
def view_report(start_date, end_date):
    """View an enhanced weekly driver report"""
    try:
        # Check if this is the May report
        is_may_report = (start_date == "2025-05-18" and end_date == "2025-05-24")
        
        # Load report data
        reports_dir = get_reports_directory()
        report_filename = f"weekly_driver_report_{start_date}_to_{end_date}.json"
        report_path = os.path.join(reports_dir, report_filename)
        
        if not os.path.exists(report_path) and is_may_report:
            # Generate May report if it doesn't exist
            return redirect(url_for('weekly_report.process_may_data'))
        
        if not os.path.exists(report_path):
            flash(f"Report not found for dates {start_date} to {end_date}", "warning")
            return redirect(url_for('weekly_report.dashboard'))
        
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        # Format dates for display
        formatted_start = datetime.strptime(start_date, '%Y-%m-%d').strftime('%b %d, %Y')
        formatted_end = datetime.strptime(end_date, '%Y-%m-%d').strftime('%b %d, %Y')
        
        # Create download links
        download_links = {
            'csv': url_for('weekly_report.download_report', start_date=start_date, end_date=end_date, format='csv'),
            'json': url_for('weekly_report.download_report', start_date=start_date, end_date=end_date, format='json')
        }
        
        # Get daily stats for the report
        day_stats = {}
        for driver in report_data.get('drivers', []):
            for day, status in driver.get('attendance', {}).items():
                if day not in day_stats:
                    day_stats[day] = {'total': 0, 'on_time': 0, 'late': 0, 'early_end': 0, 'not_on_job': 0}
                
                day_stats[day]['total'] += 1
                status_lower = status.lower() if status else ''
                
                if 'on time' in status_lower:
                    day_stats[day]['on_time'] += 1
                elif 'late' in status_lower:
                    day_stats[day]['late'] += 1
                elif 'early' in status_lower:
                    day_stats[day]['early_end'] += 1
                elif 'not on job' in status_lower:
                    day_stats[day]['not_on_job'] += 1
        
        # Sort days
        sorted_days = sorted(day_stats.keys())
        
        # Calculate driver stats
        driver_stats = {
            'total': len(report_data.get('drivers', [])),
            'with_employee_id': sum(1 for d in report_data.get('drivers', []) if d.get('employee_id')),
            'with_timecard': sum(1 for d in report_data.get('drivers', []) if d.get('timecard_data')),
        }
                
        return render_template(
            'enhanced_weekly_report/view.html',
            report=report_data,
            start_date=start_date,
            end_date=end_date,
            formatted_start=formatted_start,
            formatted_end=formatted_end,
            download_links=download_links,
            day_stats=day_stats,
            sorted_days=sorted_days,
            driver_stats=driver_stats,
            is_may_report=is_may_report
        )
    except Exception as e:
        logger.error(f"Error viewing report: {str(e)}")
        flash(f"Error viewing report: {str(e)}", "danger")
        return redirect(url_for('weekly_report.dashboard'))

@bp.route('/api/day/<date>')
def api_day_data(date):
    """API endpoint to get data for a specific day"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'Start and end dates are required'}), 400
        
        # Load report data
        reports_dir = get_reports_directory()
        report_filename = f"weekly_driver_report_{start_date}_to_{end_date}.json"
        report_path = os.path.join(reports_dir, report_filename)
        
        if not os.path.exists(report_path):
            return jsonify({'error': 'Report not found'}), 404
        
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        # Filter data for the requested date
        drivers_for_date = []
        for driver in report_data.get('drivers', []):
            if date in driver.get('attendance', {}):
                drivers_for_date.append({
                    'name': driver.get('name', ''),
                    'employee_id': driver.get('employee_id', ''),
                    'job_site': driver.get('job_sites', {}).get(date, ''),
                    'status': driver.get('attendance', {}).get(date, ''),
                    'log_on_time': driver.get('log_on_times', {}).get(date, ''),
                    'log_off_time': driver.get('log_off_times', {}).get(date, ''),
                    'timecard_hours': driver.get('timecard_hours', {}).get(date, '')
                })
        
        # Statistics for the day
        total = len(drivers_for_date)
        on_time = sum(1 for d in drivers_for_date if 'on time' in d['status'].lower())
        late = sum(1 for d in drivers_for_date if 'late' in d['status'].lower())
        early_end = sum(1 for d in drivers_for_date if 'early' in d['status'].lower())
        not_on_job = sum(1 for d in drivers_for_date if 'not on job' in d['status'].lower())
        
        stats = {
            'total': total,
            'on_time': on_time,
            'late': late,
            'early_end': early_end,
            'not_on_job': not_on_job,
            'on_time_percent': (on_time / total * 100) if total > 0 else 0
        }
        
        # Format the date for display
        formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%A, %b %d, %Y')
        
        return jsonify({
            'date': date,
            'formatted_date': formatted_date,
            'drivers': drivers_for_date,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error getting day data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/weekly/<start_date>/<end_date>')
def api_weekly_data(start_date, end_date):
    """API endpoint to get data for a weekly report"""
    try:
        # Load report data
        reports_dir = get_reports_directory()
        report_filename = f"weekly_driver_report_{start_date}_to_{end_date}.json"
        report_path = os.path.join(reports_dir, report_filename)
        
        if not os.path.exists(report_path):
            return jsonify({'error': 'Report not found'}), 404
        
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        return jsonify(report_data)
    except Exception as e:
        logger.error(f"Error getting weekly data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/download/<start_date>/<end_date>/<format>')
def download_report(start_date, end_date, format):
    """Download a weekly driver report in the specified format"""
    try:
        # Load report data
        reports_dir = get_reports_directory()
        report_filename = f"weekly_driver_report_{start_date}_to_{end_date}.json"
        report_path = os.path.join(reports_dir, report_filename)
        
        if not os.path.exists(report_path):
            flash(f"Report not found for dates {start_date} to {end_date}", "warning")
            return redirect(url_for('weekly_report.dashboard'))
        
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        if format == 'json':
            # Save a copy with a download-friendly name
            download_filename = f"weekly_driver_report_{start_date}_to_{end_date}_download.json"
            download_path = os.path.join(reports_dir, download_filename)
            with open(download_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            return send_file(download_path, as_attachment=True, download_name=download_filename)
        
        elif format == 'csv':
            # Create a CSV file from the JSON data
            rows = []
            for driver in report_data.get('drivers', []):
                driver_name = driver.get('name', '')
                employee_id = driver.get('employee_id', '')
                
                for date, status in driver.get('attendance', {}).items():
                    job_site = driver.get('job_sites', {}).get(date, '')
                    log_on_time = driver.get('log_on_times', {}).get(date, '')
                    log_off_time = driver.get('log_off_times', {}).get(date, '')
                    timecard_hours = driver.get('timecard_hours', {}).get(date, '')
                    
                    rows.append({
                        'Date': date,
                        'Driver Name': driver_name,
                        'Employee ID': employee_id,
                        'Job Site': job_site,
                        'Status': status,
                        'Log On Time': log_on_time,
                        'Log Off Time': log_off_time,
                        'Timecard Hours': timecard_hours
                    })
            
            # Convert to DataFrame and save as CSV
            df = pd.DataFrame(rows)
            csv_filename = f"weekly_driver_report_{start_date}_to_{end_date}.csv"
            csv_path = os.path.join(reports_dir, csv_filename)
            df.to_csv(csv_path, index=False)
            
            return send_file(csv_path, as_attachment=True, download_name=csv_filename)
        
        else:
            flash(f"Unsupported format: {format}", "warning")
            return redirect(url_for('weekly_report.view_report', start_date=start_date, end_date=end_date))
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        flash(f"Error downloading report: {str(e)}", "danger")
        return redirect(url_for('weekly_report.dashboard'))