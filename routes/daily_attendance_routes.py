"""
Daily Attendance Routes

This module provides routes for the daily driver attendance report system,
allowing users to view, generate, and download reports.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file

from utils.legacy_formula_connector import process_daily_driver_report

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
daily_attendance_bp = Blueprint('daily_attendance', __name__, url_prefix='/daily-attendance')

@daily_attendance_bp.route('/')
def index():
    """Display the daily attendance dashboard"""
    # Get available dates from the reports directory
    available_dates = get_available_report_dates()
    
    # Get selected date from query parameter or use the latest date
    selected_date = request.args.get('date')
    if not selected_date and available_dates:
        selected_date = available_dates[0]  # Most recent date
    
    # Load report data for the selected date
    report_data = load_report_data(selected_date)
    
    return render_template(
        'daily_attendance/index.html',
        available_dates=available_dates,
        selected_date=selected_date,
        report_data=report_data
    )

@daily_attendance_bp.route('/generate', methods=['POST'])
def generate_report():
    """Generate a new attendance report"""
    date_str = request.form.get('date')
    
    if not date_str:
        flash('Please select a date for the report', 'warning')
        return redirect(url_for('daily_attendance.index'))
    
    try:
        # Get file paths from the form
        driving_history_file = request.form.get('driving_history_file')
        activity_detail_file = request.form.get('activity_detail_file')
        assets_time_file = request.form.get('assets_time_file')
        
        # Process the report using the legacy formula connector
        result = process_daily_driver_report(
            date_str, 
            driving_history_file, 
            activity_detail_file, 
            assets_time_file
        )
        
        if result["success"]:
            flash(f'Successfully generated report for {date_str}', 'success')
        else:
            flash(f'Error generating report: {result.get("error", "Unknown error")}', 'danger')
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        flash(f'Error generating report: {str(e)}', 'danger')
    
    return redirect(url_for('daily_attendance.index', date=date_str))

@daily_attendance_bp.route('/download/json/<date_str>')
def download_json(date_str):
    """Download the JSON report for a specific date"""
    report_file = f"reports/daily_driver_reports/attendance_report_{date_str}.json"
    
    if not os.path.exists(report_file):
        flash(f'Report not found for {date_str}', 'warning')
        return redirect(url_for('daily_attendance.index'))
    
    return send_file(report_file, as_attachment=True, download_name=f"attendance_report_{date_str}.json")

@daily_attendance_bp.route('/download/excel/<date_str>')
def download_excel(date_str):
    """Download the Excel report for a specific date"""
    report_file = f"exports/daily/daily_driver_report_{date_str}.xlsx"
    
    if not os.path.exists(report_file):
        flash(f'Excel report not found for {date_str}', 'warning')
        return redirect(url_for('daily_attendance.index'))
    
    return send_file(report_file, as_attachment=True, download_name=f"daily_driver_report_{date_str}.xlsx")

@daily_attendance_bp.route('/api/dates')
def api_dates():
    """API endpoint to get available report dates"""
    available_dates = get_available_report_dates()
    return jsonify(available_dates)

@daily_attendance_bp.route('/api/report/<date_str>')
def api_report(date_str):
    """API endpoint to get report data for a specific date"""
    report_data = load_report_data(date_str)
    
    if not report_data:
        return jsonify({"error": "Report not found"}), 404
    
    return jsonify(report_data)

@daily_attendance_bp.route('/upload', methods=['GET', 'POST'])
def upload_files():
    """Upload data files for report generation"""
    if request.method == 'POST':
        # Check if files were uploaded
        if 'driving_history' not in request.files and 'activity_detail' not in request.files and 'assets_time' not in request.files:
            flash('No files selected', 'warning')
            return redirect(request.url)
        
        # Get selected date
        date_str = request.form.get('date')
        if not date_str:
            flash('Please select a date', 'warning')
            return redirect(request.url)
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Process driving history file
        driving_history_file = None
        if 'driving_history' in request.files and request.files['driving_history'].filename:
            file = request.files['driving_history']
            filename = f"driving_history_{date_str}_{file.filename}"
            file_path = os.path.join('data', filename)
            file.save(file_path)
            driving_history_file = file_path
        
        # Process activity detail file
        activity_detail_file = None
        if 'activity_detail' in request.files and request.files['activity_detail'].filename:
            file = request.files['activity_detail']
            filename = f"activity_detail_{date_str}_{file.filename}"
            file_path = os.path.join('data', filename)
            file.save(file_path)
            activity_detail_file = file_path
        
        # Process assets time file
        assets_time_file = None
        if 'assets_time' in request.files and request.files['assets_time'].filename:
            file = request.files['assets_time']
            filename = f"assets_time_{date_str}_{file.filename}"
            file_path = os.path.join('data', filename)
            file.save(file_path)
            assets_time_file = file_path
        
        # Generate report
        result = process_daily_driver_report(
            date_str, 
            driving_history_file, 
            activity_detail_file, 
            assets_time_file
        )
        
        if result["success"]:
            flash(f'Successfully generated report for {date_str}', 'success')
        else:
            flash(f'Error generating report: {result.get("error", "Unknown error")}', 'danger')
        
        return redirect(url_for('daily_attendance.index', date=date_str))
    
    # GET request - show upload form
    return render_template('daily_attendance/upload.html')

# Helper functions

def get_available_report_dates():
    """Get a list of available report dates"""
    reports_dir = "reports/daily_driver_reports"
    available_dates = []
    
    if os.path.exists(reports_dir):
        for filename in os.listdir(reports_dir):
            if filename.startswith("attendance_report_") and filename.endswith(".json"):
                date_str = filename.replace("attendance_report_", "").replace(".json", "")
                try:
                    # Validate date format
                    datetime.strptime(date_str, "%Y-%m-%d")
                    available_dates.append(date_str)
                except ValueError:
                    continue
    
    # Sort dates in descending order (newest first)
    available_dates.sort(reverse=True)
    
    return available_dates

def load_report_data(date_str):
    """Load report data for a specific date"""
    if not date_str:
        return None
    
    report_file = f"reports/daily_driver_reports/attendance_report_{date_str}.json"
    
    if not os.path.exists(report_file):
        return None
    
    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        return report_data
    
    except Exception as e:
        logger.error(f"Error loading report data: {str(e)}")
        return None