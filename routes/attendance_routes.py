"""
Attendance Routes Module

This module provides routes for the attendance functionality,
including the daily driver report dashboard.
"""

import os
import json
from datetime import datetime, timedelta
import pandas as pd
from flask import Blueprint, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_login import login_required, current_user
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

# Helper functions
def get_available_dates():
    """Get a list of dates with available reports"""
    reports_dir = os.path.join('reports', 'daily_driver_reports')
    
    if not os.path.exists(reports_dir):
        return []
    
    dates = []
    for file in os.listdir(reports_dir):
        if file.startswith('DAILY_DRIVER_REPORT_') and file.endswith('.xlsx'):
            # Extract date from filename (format: DAILY_DRIVER_REPORT_YYYY_MM_DD.xlsx)
            try:
                date_str = file.replace('DAILY_DRIVER_REPORT_', '').replace('.xlsx', '')
                date_parts = date_str.split('_')
                if len(date_parts) == 3:
                    date_obj = datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
                    dates.append(date_obj.strftime('%Y-%m-%d'))
            except Exception as e:
                logger.error(f"Error parsing date from filename {file}: {str(e)}")
    
    # Sort dates in descending order (newest first)
    dates.sort(reverse=True)
    return dates

def get_report_data(date_str):
    """Get report data for a specific date"""
    # First, check if we have a JSON file with the processed data
    json_path = os.path.join('data', f'filtered_driving_data_{date_str}.json')
    
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON data for {date_str}: {str(e)}")
    
    # If JSON doesn't exist, check for the Excel report
    excel_path = os.path.join('reports', 'daily_driver_reports', f'DAILY_DRIVER_REPORT_{date_str.replace("-", "_")}.xlsx')
    
    if os.path.exists(excel_path):
        try:
            df = pd.read_excel(excel_path)
            return df.to_dict(orient='records')
        except Exception as e:
            logger.error(f"Error loading Excel data for {date_str}: {str(e)}")
    
    # If neither exists, return empty list
    return []

def get_report_stats(date_str):
    """Get summary statistics for a specific date"""
    data = get_report_data(date_str)
    
    if not data:
        return {
            "total_drivers": 0,
            "on_time": 0,
            "late": 0,
            "early_end": 0,
            "not_on_job": 0,
            "on_time_percentage": 0,
            "late_percentage": 0,
            "early_end_percentage": 0,
            "not_on_job_percentage": 0
        }
    
    # Count drivers by status
    total = len(data)
    on_time = sum(1 for record in data if record.get('Status', '').lower() == 'on_time')
    late = sum(1 for record in data if record.get('Status', '').lower() == 'late')
    early_end = sum(1 for record in data if record.get('Status', '').lower() == 'early_end')
    not_on_job = sum(1 for record in data if record.get('Status', '').lower() == 'not_on_job')
    
    # Calculate percentages
    on_time_pct = round((on_time / total) * 100 if total > 0 else 0)
    late_pct = round((late / total) * 100 if total > 0 else 0)
    early_end_pct = round((early_end / total) * 100 if total > 0 else 0)
    not_on_job_pct = round((not_on_job / total) * 100 if total > 0 else 0)
    
    return {
        "total_drivers": total,
        "on_time": on_time,
        "late": late,
        "early_end": early_end,
        "not_on_job": not_on_job,
        "on_time_percentage": on_time_pct,
        "late_percentage": late_pct,
        "early_end_percentage": early_end_pct,
        "not_on_job_percentage": not_on_job_pct
    }

def get_default_date():
    """Get the most recent date with available data"""
    dates = get_available_dates()
    return dates[0] if dates else datetime.now().strftime('%Y-%m-%d')

# Routes
@attendance_bp.route('/daily_driver_report')
@login_required
def daily_driver_report():
    """Daily Driver Report Dashboard"""
    # Get available dates
    available_dates = get_available_dates()
    
    # Get selected date (default to most recent)
    selected_date = request.args.get('date', get_default_date())
    
    # Get report data for selected date
    report_data = get_report_data(selected_date)
    
    # Get report statistics
    stats = get_report_stats(selected_date)
    
    # Get search filter (if any)
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    # Apply filters if needed
    if search_query or status_filter:
        filtered_data = []
        for record in report_data:
            # Check if record matches search query (case-insensitive)
            name_match = (not search_query or 
                          search_query.lower() in record.get('Driver', '').lower())
            
            # Check if record matches status filter
            status_match = (not status_filter or 
                            record.get('Status', '').lower() == status_filter.lower())
            
            # Include record if it matches both filters
            if name_match and status_match:
                filtered_data.append(record)
        
        report_data = filtered_data
    
    # Render template with data
    return render_template(
        'attendance/daily_driver_report.html',
        available_dates=available_dates,
        selected_date=selected_date,
        report_data=report_data,
        stats=stats,
        search_query=search_query,
        status_filter=status_filter
    )

@attendance_bp.route('/api/daily_driver_data')
@login_required
def api_daily_driver_data():
    """API endpoint for daily driver data (used for AJAX filtering)"""
    # Get selected date
    selected_date = request.args.get('date', get_default_date())
    
    # Get report data for selected date
    report_data = get_report_data(selected_date)
    
    # Get search filter (if any)
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    # Apply filters if needed
    if search_query or status_filter:
        filtered_data = []
        for record in report_data:
            # Check if record matches search query (case-insensitive)
            name_match = (not search_query or 
                          search_query.lower() in record.get('Driver', '').lower())
            
            # Check if record matches status filter
            status_match = (not status_filter or 
                            record.get('Status', '').lower() == status_filter.lower())
            
            # Include record if it matches both filters
            if name_match and status_match:
                filtered_data.append(record)
        
        report_data = filtered_data
    
    # Return JSON response
    return jsonify(report_data)

@attendance_bp.route('/download_report/<date>')
@login_required
def download_report(date):
    """Download Excel report for a specific date"""
    # Format date for filename
    formatted_date = date.replace('-', '_')
    
    # Construct file path
    file_path = os.path.join('reports', 'daily_driver_reports', f'DAILY_DRIVER_REPORT_{formatted_date}.xlsx')
    
    # Check if file exists
    if not os.path.exists(file_path):
        flash(f"Report for {date} not found.", "error")
        return redirect(url_for('attendance.daily_driver_report'))
    
    # Return file for download
    return send_file(
        file_path,
        as_attachment=True,
        download_name=f'DAILY_DRIVER_REPORT_{formatted_date}.xlsx'
    )

@attendance_bp.route('/process_report', methods=['POST'])
@login_required
def process_report():
    """Process/regenerate report for a specific date"""
    # Get date from form
    date_str = request.form.get('date')
    
    if not date_str:
        flash("Date is required.", "error")
        return redirect(url_for('attendance.daily_driver_report'))
    
    # TODO: Implement report processing logic here
    
    flash(f"Report for {date_str} processed successfully.", "success")
    return redirect(url_for('attendance.daily_driver_report', date=date_str))