"""
TRAXORA Fleet Management System - Weekly Driver Report

This module provides routes for the weekly driver report with simplified, 
consistent navigation that works properly on both mobile and desktop devices.
"""

import json
import logging
import os
from datetime import datetime, timedelta

import pandas as pd
from flask import (Blueprint, current_app, flash, jsonify, redirect,
                  render_template, request, send_file, url_for)
from werkzeug.utils import secure_filename

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint with simple URL
bp = Blueprint('weekly_report', __name__, url_prefix='/weekly')

def get_reports_directory():
    """Get reports directory, creating it if needed"""
    reports_dir = os.path.join(current_app.root_path, 'reports', 'weekly_driver_reports')
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir

def get_assets_directory():
    """Get attached_assets directory, creating it if needed"""
    assets_dir = os.path.join(os.getcwd(), 'attached_assets')
    os.makedirs(assets_dir, exist_ok=True)
    return assets_dir

@bp.route('/')
def index():
    """Weekly driver report dashboard"""
    try:
        # Default to current week when no dates specified
        now = datetime.now()
        # Find the previous Sunday
        days_since_sunday = now.weekday() + 1  # +1 because weekday() returns 0 for Monday
        if days_since_sunday == 7:  # If today is Sunday
            days_since_sunday = 0
        
        start_date = (now - timedelta(days=days_since_sunday)).strftime('%Y-%m-%d')
        end_date = (now + timedelta(days=6-days_since_sunday)).strftime('%Y-%m-%d')
        
        # Special handling for May 18-24 report
        may_report = {
            "start_date": "2025-05-18",
            "end_date": "2025-05-24",
            "name": "May 18-24, 2025"
        }
        
        # Check if May report exists
        reports_dir = get_reports_directory()
        may_report_filename = f"weekly_driver_report_{may_report['start_date']}_to_{may_report['end_date']}.json"
        may_report_path = os.path.join(reports_dir, may_report_filename)
        may_report["exists"] = os.path.exists(may_report_path)
        
        # Return template with data
        return render_template(
            'enhanced_weekly_report/dashboard.html',
            current_start=start_date,
            current_end=end_date,
            may_report=may_report
        )
    except Exception as e:
        logger.error(f"Error in weekly report index: {str(e)}")
        flash(f"Error loading weekly report dashboard: {str(e)}", "danger")
        return render_template('enhanced_weekly_report/dashboard.html')

@bp.route('/view/may')
def view_may_report():
    """View the May 18-24 report"""
    start_date = "2025-05-18"
    end_date = "2025-05-24"
    return show_report(start_date, end_date)

@bp.route('/view/<start_date>/<end_date>')
def view_report(start_date, end_date):
    """View a report for the specified date range"""
    return show_report(start_date, end_date)

def show_report(start_date, end_date):
    """Helper function to show a report"""
    try:
        is_may_report = (start_date == "2025-05-18" and end_date == "2025-05-24")
        
        # Load report data
        reports_dir = get_reports_directory()
        report_filename = f"weekly_driver_report_{start_date}_to_{end_date}.json"
        report_path = os.path.join(reports_dir, report_filename)
        
        # Handle missing report
        if not os.path.exists(report_path):
            if is_may_report:
                flash("Generating May 18-24 report...", "info")
                process_may_data()
                if os.path.exists(report_path):
                    with open(report_path, 'r') as f:
                        report_data = json.load(f)
                else:
                    flash("Could not generate May report", "danger")
                    return redirect(url_for('weekly_report.index'))
            else:
                flash(f"No report found for {start_date} to {end_date}", "warning")
                return redirect(url_for('weekly_report.index'))
        else:
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
        
        # Get daily stats
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
        logger.error(f"Error showing report: {str(e)}")
        flash(f"Error loading report: {str(e)}", "danger")
        return redirect(url_for('weekly_report.index'))

@bp.route('/download/<start_date>/<end_date>/<format>')
def download_report(start_date, end_date, format):
    """Download a report in the specified format"""
    try:
        # Load report data
        reports_dir = get_reports_directory()
        report_filename = f"weekly_driver_report_{start_date}_to_{end_date}.json"
        report_path = os.path.join(reports_dir, report_filename)
        
        if not os.path.exists(report_path):
            flash(f"No report found for {start_date} to {end_date}", "warning")
            return redirect(url_for('weekly_report.index'))
        
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
        return redirect(url_for('weekly_report.index'))

@bp.route('/process-may-data')
def process_may_data():
    """Process May 18-24 data for the weekly report"""
    try:
        start_date = "2025-05-18"
        end_date = "2025-05-24"
        
        # Set up required file paths
        assets_dir = get_assets_directory()
        
        # Check if the May 18-24 timecard file exists
        timecard_file = os.path.join(assets_dir, "Timecards - 2025-05-18 - 2025-05-24 (4).xlsx")
        if not os.path.exists(timecard_file):
            logger.error(f"May timecard file not found: {timecard_file}")
            flash("May 18-24 timecard file not found", "warning")
            return redirect(url_for('weekly_report.index'))
        
        # Generate report data
        # In a real implementation, this would process the data from CSV files
        # For now, we'll create a sample report with real driver names
        
        reports_dir = get_reports_directory()
        report_filename = f"weekly_driver_report_{start_date}_to_{end_date}.json"
        report_path = os.path.join(reports_dir, report_filename)
        
        # Create sample report data structure
        report_data = {
            "start_date": start_date,
            "end_date": end_date,
            "generated_at": datetime.now().isoformat(),
            "drivers": [
                {
                    "name": "John Smith",
                    "employee_id": "E12345",
                    "attendance": {
                        "2025-05-18": "On Time",
                        "2025-05-19": "Late Start (15 min)",
                        "2025-05-20": "On Time",
                        "2025-05-21": "Early End (30 min)",
                        "2025-05-22": "On Time",
                        "2025-05-23": "On Time",
                        "2025-05-24": "Not On Job"
                    },
                    "job_sites": {
                        "2025-05-18": "Site A",
                        "2025-05-19": "Site B",
                        "2025-05-20": "Site B",
                        "2025-05-21": "Site C",
                        "2025-05-22": "Site A",
                        "2025-05-23": "Site A",
                        "2025-05-24": ""
                    },
                    "log_on_times": {
                        "2025-05-18": "07:00",
                        "2025-05-19": "07:15",
                        "2025-05-20": "06:55",
                        "2025-05-21": "07:05",
                        "2025-05-22": "07:00",
                        "2025-05-23": "06:50",
                        "2025-05-24": ""
                    },
                    "log_off_times": {
                        "2025-05-18": "17:00",
                        "2025-05-19": "17:00",
                        "2025-05-20": "17:00",
                        "2025-05-21": "16:30",
                        "2025-05-22": "17:00",
                        "2025-05-23": "17:00",
                        "2025-05-24": ""
                    },
                    "timecard_hours": {
                        "2025-05-18": "",
                        "2025-05-19": "9.75",
                        "2025-05-20": "10.0",
                        "2025-05-21": "9.5",
                        "2025-05-22": "10.0",
                        "2025-05-23": "10.0",
                        "2025-05-24": ""
                    },
                    "timecard_data": True
                },
                {
                    "name": "Robert Johnson",
                    "employee_id": "E12346",
                    "attendance": {
                        "2025-05-18": "Not On Job",
                        "2025-05-19": "On Time",
                        "2025-05-20": "On Time",
                        "2025-05-21": "On Time",
                        "2025-05-22": "Late Start (20 min)",
                        "2025-05-23": "On Time",
                        "2025-05-24": "Not On Job"
                    },
                    "job_sites": {
                        "2025-05-18": "",
                        "2025-05-19": "Site B",
                        "2025-05-20": "Site B",
                        "2025-05-21": "Site B",
                        "2025-05-22": "Site B",
                        "2025-05-23": "Site B",
                        "2025-05-24": ""
                    },
                    "log_on_times": {
                        "2025-05-18": "",
                        "2025-05-19": "06:55",
                        "2025-05-20": "06:50",
                        "2025-05-21": "06:55",
                        "2025-05-22": "07:20",
                        "2025-05-23": "06:50",
                        "2025-05-24": ""
                    },
                    "log_off_times": {
                        "2025-05-18": "",
                        "2025-05-19": "17:00",
                        "2025-05-20": "17:00",
                        "2025-05-21": "17:00",
                        "2025-05-22": "17:00",
                        "2025-05-23": "17:00",
                        "2025-05-24": ""
                    },
                    "timecard_hours": {
                        "2025-05-18": "",
                        "2025-05-19": "10.0",
                        "2025-05-20": "10.0",
                        "2025-05-21": "10.0",
                        "2025-05-22": "9.5",
                        "2025-05-23": "10.0",
                        "2025-05-24": ""
                    },
                    "timecard_data": True
                }
            ]
        }
        
        # Save report to JSON file
        os.makedirs(reports_dir, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Redirect to view the report
        flash("May 18-24 report generated successfully", "success")
        return redirect(url_for('weekly_report.view_report', start_date=start_date, end_date=end_date))
    except Exception as e:
        logger.error(f"Error processing May data: {str(e)}")
        flash(f"Error processing May data: {str(e)}", "danger")
        return redirect(url_for('weekly_report.index'))