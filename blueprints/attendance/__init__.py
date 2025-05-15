"""
Attendance Blueprint

This module provides routes and functionality for daily driver attendance reporting, including:
- Prior day Late Start, Early End, Not On Job reports
- Current day Late Start, Not On Job reports
- Report history management
- Attendance metrics and analytics
"""

from flask import Blueprint, render_template, jsonify, request, current_app, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
import logging
import json
import os
from datetime import datetime, timedelta
import pandas as pd

from app import db
from models import Asset
from utils.reports import generate_prior_day_report, generate_current_day_report, run_daily_reports

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize blueprint
attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@attendance_bp.route('/')
@login_required
def index():
    """Render the main attendance dashboard."""
    # Get report history (last 7 days)
    reports_dir = 'reports'
    report_history = []
    
    if os.path.exists(reports_dir):
        date_dirs = sorted([d for d in os.listdir(reports_dir) if os.path.isdir(os.path.join(reports_dir, d))], reverse=True)
        # Get the most recent 7 days with reports
        for date_dir in date_dirs[:7]:
            date_path = os.path.join(reports_dir, date_dir)
            date_reports = []
            for report_file in os.listdir(date_path):
                if report_file.endswith('.xlsx'):
                    file_path = os.path.join(date_path, report_file)
                    report_type = "Prior Day" if "prior_day" in report_file else "Current Day"
                    date_reports.append({
                        'filename': report_file,
                        'path': file_path,
                        'size': os.path.getsize(file_path),
                        'created': datetime.fromtimestamp(os.path.getctime(file_path)),
                        'type': report_type
                    })
            if date_reports:
                report_history.append({
                    'date': date_dir,
                    'files': date_reports
                })
    
    return render_template('attendance/index.html', 
                          title="Attendance Reporting",
                          module="attendance",
                          report_history=report_history)

@attendance_bp.route('/prior-day')
@login_required
def prior_day():
    """Render prior day attendance report page."""
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    report_path = f"reports/{yesterday}/prior_day_attendance_{yesterday}.xlsx"
    
    # Check if report exists
    report_exists = os.path.exists(report_path)
    
    return render_template('attendance/prior_day.html', 
                          title="Prior Day Attendance Report",
                          module="attendance",
                          report_date=yesterday,
                          report_exists=report_exists,
                          report_path=report_path if report_exists else None)

@attendance_bp.route('/current-day')
@login_required
def current_day():
    """Render current day attendance report page."""
    today = datetime.now().strftime('%Y-%m-%d')
    report_path = f"reports/{today}/current_day_attendance_{today}.xlsx"
    
    # Check if report exists
    report_exists = os.path.exists(report_path)
    
    return render_template('attendance/current_day.html', 
                          title="Current Day Attendance Report",
                          module="attendance",
                          report_date=today,
                          report_exists=report_exists,
                          report_path=report_path if report_exists else None)

@attendance_bp.route('/history')
@login_required
def history():
    """Render attendance report history page."""
    # Get all reports organized by date
    reports_dir = 'reports'
    all_reports = []
    
    if os.path.exists(reports_dir):
        date_dirs = sorted([d for d in os.listdir(reports_dir) if os.path.isdir(os.path.join(reports_dir, d))], reverse=True)
        for date_dir in date_dirs:
            date_path = os.path.join(reports_dir, date_dir)
            date_reports = []
            for report_file in os.listdir(date_path):
                if report_file.endswith('.xlsx'):
                    file_path = os.path.join(date_path, report_file)
                    report_type = "Prior Day" if "prior_day" in report_file else "Current Day"
                    date_reports.append({
                        'filename': report_file,
                        'path': file_path,
                        'size': os.path.getsize(file_path),
                        'created': datetime.fromtimestamp(os.path.getctime(file_path)),
                        'type': report_type
                    })
            if date_reports:
                all_reports.append({
                    'date': date_dir,
                    'files': date_reports
                })
    
    return render_template('attendance/history.html', 
                          title="Attendance Report History",
                          module="attendance",
                          all_reports=all_reports)

@attendance_bp.route('/api/generate-prior-day')
@login_required
def api_generate_prior_day():
    """Generate the prior day attendance report."""
    try:
        result = generate_prior_day_report()
        
        if result['status'] == 'success':
            flash('Prior day attendance report generated successfully', 'success')
            return jsonify(result)
        else:
            flash(f'Error generating prior day report: {result.get("message", "Unknown error")}', 'error')
            return jsonify(result), 500
    except Exception as e:
        logger.error(f"Error generating prior day report: {e}")
        flash(f'Error generating report: {str(e)}', 'error')
        return jsonify({"status": "error", "message": str(e)}), 500

@attendance_bp.route('/api/generate-current-day')
@login_required
def api_generate_current_day():
    """Generate the current day attendance report."""
    try:
        result = generate_current_day_report()
        
        if result['status'] == 'success':
            flash('Current day attendance report generated successfully', 'success')
            return jsonify(result)
        else:
            flash(f'Error generating current day report: {result.get("message", "Unknown error")}', 'error')
            return jsonify(result), 500
    except Exception as e:
        logger.error(f"Error generating current day report: {e}")
        flash(f'Error generating report: {str(e)}', 'error')
        return jsonify({"status": "error", "message": str(e)}), 500

@attendance_bp.route('/api/run-daily-reports')
@login_required
def api_run_daily_reports():
    """Run all daily attendance reports."""
    try:
        result = run_daily_reports()
        
        all_successful = all(r['status'] == 'success' for r in result.values())
        
        if all_successful:
            flash('All daily attendance reports generated successfully', 'success')
        else:
            flash('Some reports failed to generate', 'warning')
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error running daily reports: {e}")
        flash(f'Error running reports: {str(e)}', 'error')
        return jsonify({"status": "error", "message": str(e)}), 500

@attendance_bp.route('/download/<path:filename>')
@login_required
def download_report(filename):
    """Download an attendance report file."""
    try:
        # Construct full path
        file_path = os.path.join('reports', filename)
        
        # Check if file exists
        if not os.path.isfile(file_path):
            flash(f'File not found: {filename}', 'error')
            return redirect(url_for('attendance.history'))
            
        # Send file for download
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading report file: {e}")
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('attendance.history'))

def register_blueprint(app):
    """Register the attendance blueprint with the app."""
    app.register_blueprint(attendance_bp)
    return attendance_bp