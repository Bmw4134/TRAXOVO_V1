"""
TRAXORA Fleet Management System - Automatic Attendance Routes

This module provides web routes for the automatic attendance processor,
allowing users to view and manage attendance reports through the web interface.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from utils.auto_attendance_processor import (
    process_attendance,
    process_date_range,
    auto_process_today,
    auto_process_yesterday,
    find_data_files
)

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
auto_attendance_bp = Blueprint('auto_attendance', __name__, url_prefix='/auto-attendance')

# Define constants
REPORTS_DIR = "reports"

@auto_attendance_bp.route('/')
def dashboard():
    """Display automatic attendance dashboard"""
    # Get list of available reports
    reports = []
    if os.path.exists(REPORTS_DIR):
        for file_name in os.listdir(REPORTS_DIR):
            if file_name.startswith('attendance_report_') and file_name.endswith('.json'):
                # Extract date from filename
                date_str = file_name.replace('attendance_report_', '').replace('.json', '')
                
                # Load report metadata
                try:
                    with open(os.path.join(REPORTS_DIR, file_name), 'r') as f:
                        report_data = json.load(f)
                        reports.append({
                            'date': date_str,
                            'file': file_name,
                            'driver_count': len(report_data.get('driver_records', [])),
                            'on_time': report_data.get('summary', {}).get('on_time', 0),
                            'late': report_data.get('summary', {}).get('late', 0),
                            'early_end': report_data.get('summary', {}).get('early_end', 0),
                            'not_on_job': report_data.get('summary', {}).get('not_on_job', 0),
                            'on_time_percentage': report_data.get('metrics', {}).get('on_time_percentage', 0),
                            'data_sources': report_data.get('data_sources', [])
                        })
                except Exception as e:
                    logger.error(f"Error loading report {file_name}: {e}")
    
    # Sort reports by date (newest first)
    reports.sort(key=lambda x: x['date'], reverse=True)
    
    # Check for input files for today
    today = datetime.now().strftime('%Y-%m-%d')
    file_types, _ = find_data_files(today)
    
    available_files = {
        'date': today,
        'driving_history': len(file_types['driving_history']),
        'time_on_site': len(file_types['time_on_site']),
        'activity_detail': len(file_types['activity_detail'])
    }
    
    return render_template(
        'auto_attendance/dashboard.html',
        reports=reports,
        available_files=available_files
    )

@auto_attendance_bp.route('/process', methods=['POST'])
def process_report():
    """Process attendance report"""
    date_str = request.form.get('date')
    force = 'force' in request.form
    
    if date_str:
        report_file = process_attendance(date_str, force)
        if report_file:
            flash(f"Successfully processed attendance report for {date_str}", "success")
        else:
            flash(f"Failed to process attendance report for {date_str}", "danger")
    else:
        flash("No date specified", "danger")
    
    return redirect(url_for('auto_attendance.dashboard'))

@auto_attendance_bp.route('/process-today', methods=['POST'])
def process_today():
    """Process today's attendance report"""
    report_file = auto_process_today()
    if report_file:
        flash("Successfully processed today's attendance report", "success")
    else:
        flash("Failed to process today's attendance report", "danger")
    
    return redirect(url_for('auto_attendance.dashboard'))

@auto_attendance_bp.route('/process-yesterday', methods=['POST'])
def process_yesterday():
    """Process yesterday's attendance report"""
    report_file = auto_process_yesterday()
    if report_file:
        flash("Successfully processed yesterday's attendance report", "success")
    else:
        flash("Failed to process yesterday's attendance report", "danger")
    
    return redirect(url_for('auto_attendance.dashboard'))

@auto_attendance_bp.route('/process-range', methods=['POST'])
def process_range():
    """Process date range"""
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    force = 'force' in request.form
    
    if start_date:
        reports = process_date_range(start_date, end_date, force)
        if reports:
            flash(f"Successfully processed {len(reports)} reports", "success")
        else:
            flash("Failed to process reports for date range", "danger")
    else:
        flash("No start date specified", "danger")
    
    return redirect(url_for('auto_attendance.dashboard'))

@auto_attendance_bp.route('/view/<date_str>')
def view_report(date_str):
    """View attendance report"""
    report_file = os.path.join(REPORTS_DIR, f"attendance_report_{date_str}.json")
    
    if os.path.exists(report_file):
        try:
            with open(report_file, 'r') as f:
                report_data = json.load(f)
                
            return render_template(
                'auto_attendance/view_report.html',
                report=report_data,
                date=date_str
            )
        except Exception as e:
            logger.error(f"Error loading report {report_file}: {e}")
            flash(f"Error loading report: {str(e)}", "danger")
    else:
        flash(f"Report for {date_str} not found", "danger")
    
    return redirect(url_for('auto_attendance.dashboard'))

@auto_attendance_bp.route('/api/report/<date_str>')
def api_get_report(date_str):
    """API endpoint to get report data"""
    report_file = os.path.join(REPORTS_DIR, f"attendance_report_{date_str}.json")
    
    if os.path.exists(report_file):
        try:
            with open(report_file, 'r') as f:
                report_data = json.load(f)
                
            return jsonify(report_data)
        except Exception as e:
            logger.error(f"Error loading report {report_file}: {e}")
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Report not found'}), 404

@auto_attendance_bp.route('/api/available-dates')
def api_available_dates():
    """API endpoint to get available report dates"""
    dates = []
    if os.path.exists(REPORTS_DIR):
        for file_name in os.listdir(REPORTS_DIR):
            if file_name.startswith('attendance_report_') and file_name.endswith('.json'):
                date_str = file_name.replace('attendance_report_', '').replace('.json', '')
                dates.append(date_str)
    
    return jsonify(sorted(dates, reverse=True))