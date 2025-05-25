"""
Report Browser

This module provides routes for browsing existing reports in the system,
without requiring users to re-upload data files.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, abort, jsonify, 
    request, redirect, url_for, send_file
)

logger = logging.getLogger(__name__)

# Create blueprint
report_browser_bp = Blueprint('report_browser', __name__, url_prefix='/reports')

def get_all_report_directories():
    """Get all report directories in the system"""
    report_dirs = []
    
    # Daily driver reports
    daily_dir = os.path.join('reports', 'daily_driver_reports')
    if os.path.exists(daily_dir):
        report_dirs.append({
            'name': 'Daily Driver Reports',
            'path': daily_dir,
            'type': 'daily',
            'icon': 'calendar-day'
        })
    
    # Weekly driver reports
    weekly_dir = os.path.join('reports', 'weekly_driver_reports')
    if os.path.exists(weekly_dir):
        report_dirs.append({
            'name': 'Weekly Driver Reports',
            'path': weekly_dir,
            'type': 'weekly',
            'icon': 'calendar-week'
        })
    
    # Attendance reports
    attendance_dir = os.path.join('reports', 'attendance_reports')
    if os.path.exists(attendance_dir):
        report_dirs.append({
            'name': 'Attendance Reports',
            'path': attendance_dir,
            'type': 'attendance',
            'icon': 'clipboard-check'
        })
    
    # Equipment billing reports
    billing_dir = os.path.join('reports', 'equipment_billing')
    if os.path.exists(billing_dir):
        report_dirs.append({
            'name': 'Equipment Billing Reports',
            'path': billing_dir,
            'type': 'billing',
            'icon': 'file-invoice-dollar'
        })
    
    return report_dirs

def get_reports_from_directory(directory, report_type='daily'):
    """Get all reports from a directory"""
    reports = []
    
    if not os.path.exists(directory):
        return reports
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        # Skip directories
        if os.path.isdir(file_path):
            continue
        
        # Get file info
        file_info = {
            'filename': filename,
            'path': file_path,
            'size': os.path.getsize(file_path),
            'modified': datetime.fromtimestamp(os.path.getmtime(file_path))
        }
        
        # Extract date from filename
        if report_type == 'daily' and 'DAILY_DRIVER_REPORT_' in filename and filename.endswith('.xlsx'):
            date_str = filename.replace('DAILY_DRIVER_REPORT_', '').replace('.xlsx', '').replace('_', '-')
            try:
                file_info['date'] = datetime.strptime(date_str, '%Y-%m-%d')
                file_info['formatted_date'] = file_info['date'].strftime('%A, %B %d, %Y')
                
                # Check if JSON data exists
                json_filename = f"driver_report_{date_str}.json"
                json_path = os.path.join(directory, json_filename)
                file_info['has_json'] = os.path.exists(json_path)
                file_info['json_path'] = json_path if file_info['has_json'] else None
                
                reports.append(file_info)
            except ValueError:
                # Skip files with invalid date format
                pass
        elif report_type == 'weekly' and 'WEEKLY_DRIVER_REPORT_' in filename and filename.endswith('.xlsx'):
            date_str = filename.replace('WEEKLY_DRIVER_REPORT_', '').replace('.xlsx', '').replace('_', '-')
            try:
                file_info['date'] = datetime.strptime(date_str, '%Y-%m-%d')
                file_info['formatted_date'] = file_info['date'].strftime('%B %d, %Y')
                reports.append(file_info)
            except ValueError:
                # Skip files with invalid date format
                pass
        elif report_type == 'attendance' or report_type == 'billing':
            # For other report types, just list all Excel files
            if filename.endswith('.xlsx'):
                file_info['formatted_date'] = file_info['modified'].strftime('%B %d, %Y')
                reports.append(file_info)
    
    # Sort reports by date, newest first
    reports.sort(key=lambda x: x.get('date', x.get('modified')), reverse=True)
    
    return reports

@report_browser_bp.route('/')
def index():
    """Report browser dashboard"""
    report_dirs = get_all_report_directories()
    
    # Get reports from each directory
    for directory in report_dirs:
        directory['reports'] = get_reports_from_directory(directory['path'], directory['type'])
    
    return render_template(
        'report_browser/index.html',
        report_dirs=report_dirs
    )

@report_browser_bp.route('/daily-driver/<date>')
def view_daily_driver_report(date):
    """View a specific daily driver report"""
    try:
        # Format date string
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Get report path
        report_dir = os.path.join('reports', 'daily_driver_reports')
        report_path = os.path.join(report_dir, f"DAILY_DRIVER_REPORT_{date.replace('-', '_')}.xlsx")
        
        if not os.path.exists(report_path):
            abort(404)
        
        # Check if JSON data exists
        json_path = os.path.join(report_dir, f"driver_report_{date}.json")
        report_data = None
        
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                report_data = json.load(f)
        
        return render_template(
            'daily_driver_report/view_enhanced.html',
            date=date,
            formatted_date=formatted_date,
            report_path=report_path,
            report_data=report_data
        )
    
    except Exception as e:
        logger.error(f"Error viewing daily driver report: {str(e)}")
        abort(500)

@report_browser_bp.route('/download/<report_type>/<path:filename>')
def download_report(report_type, filename):
    """Download a report file"""
    try:
        if report_type == 'daily':
            report_dir = os.path.join('reports', 'daily_driver_reports')
        elif report_type == 'weekly':
            report_dir = os.path.join('reports', 'weekly_driver_reports')
        elif report_type == 'attendance':
            report_dir = os.path.join('reports', 'attendance_reports')
        elif report_type == 'billing':
            report_dir = os.path.join('reports', 'equipment_billing')
        else:
            abort(404)
        
        file_path = os.path.join(report_dir, filename)
        
        if not os.path.exists(file_path):
            abort(404)
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        abort(500)

@report_browser_bp.route('/api/reports/<report_type>')
def api_get_reports(report_type):
    """API endpoint to get reports of a specific type"""
    try:
        if report_type == 'daily':
            report_dir = os.path.join('reports', 'daily_driver_reports')
        elif report_type == 'weekly':
            report_dir = os.path.join('reports', 'weekly_driver_reports')
        elif report_type == 'attendance':
            report_dir = os.path.join('reports', 'attendance_reports')
        elif report_type == 'billing':
            report_dir = os.path.join('reports', 'equipment_billing')
        else:
            return jsonify({'error': 'Invalid report type'}), 400
        
        reports = get_reports_from_directory(report_dir, report_type)
        
        # Convert datetime objects to strings
        for report in reports:
            if 'date' in report:
                report['date'] = report['date'].strftime('%Y-%m-%d')
            if 'modified' in report:
                report['modified'] = report['modified'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({'reports': reports})
    
    except Exception as e:
        logger.error(f"Error getting reports: {str(e)}")
        return jsonify({'error': str(e)}), 500