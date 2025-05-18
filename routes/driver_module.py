"""
Driver Module Blueprint

This module handles all driver-related functionality including:
- Daily attendance reports
- Driver assignments
- Driver performance metrics
- Attendance tracking
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from flask import (Blueprint, current_app, flash, jsonify, redirect,
                  render_template, request, send_from_directory, url_for, session)
from flask_login import current_user, login_required

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize blueprint
driver_module_bp = Blueprint('driver_module', __name__, url_prefix='/drivers')

# Ensure data directories exist
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DRIVER_DATA_DIR = DATA_DIR / "drivers"
DRIVER_DATA_DIR.mkdir(exist_ok=True)

# Sample data for demonstration
def get_sample_driver_data():
    """Get sample driver data for demonstration"""
    return [
        {
            "id": 1,
            "name": "John Smith",
            "employee_id": "EMP-1001",
            "department": "Construction",
            "region": "North",
            "assigned_asset": "Truck 101",
            "phone": "555-1234",
            "email": "john.smith@example.com",
            "hire_date": "2023-05-10",
            "license_number": "DL1234567",
            "license_expiration": "2026-05-10"
        },
        {
            "id": 2,
            "name": "Sarah Wilson",
            "employee_id": "EMP-1002",
            "department": "Construction",
            "region": "South",
            "assigned_asset": "Excavator 203",
            "phone": "555-2345",
            "email": "sarah.wilson@example.com",
            "hire_date": "2022-08-15",
            "license_number": "DL7654321",
            "license_expiration": "2025-08-15"
        },
        {
            "id": 3,
            "name": "Mike Johnson",
            "employee_id": "EMP-1003",
            "department": "Transportation",
            "region": "East",
            "assigned_asset": "Truck 102",
            "phone": "555-3456",
            "email": "mike.johnson@example.com",
            "hire_date": "2024-01-20",
            "license_number": "DL9876543",
            "license_expiration": "2027-01-20"
        },
        {
            "id": 4,
            "name": "Lisa Brown",
            "employee_id": "EMP-1004",
            "department": "Construction",
            "region": "West",
            "assigned_asset": "Loader 410",
            "phone": "555-4567",
            "email": "lisa.brown@example.com",
            "hire_date": "2023-11-05",
            "license_number": "DL1357924",
            "license_expiration": "2026-11-05"
        },
        {
            "id": 5,
            "name": "David Martinez",
            "employee_id": "EMP-1005",
            "department": "Transportation",
            "region": "North",
            "assigned_asset": "Truck 103",
            "phone": "555-5678",
            "email": "david.martinez@example.com",
            "hire_date": "2022-03-15",
            "license_number": "DL2468135",
            "license_expiration": "2025-03-15"
        }
    ]

def get_sample_attendance_data():
    """Get sample attendance data for demonstration"""
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    two_days_ago = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    
    return {
        "late_starts": [
            {
                "date": today,
                "driver_id": 1,
                "driver_name": "John Smith",
                "job_site": "Project Alpha",
                "expected_time": "07:00",
                "actual_time": "07:45",
                "minutes_late": 45,
                "notes": "Traffic delay reported"
            },
            {
                "date": today,
                "driver_id": 2,
                "driver_name": "Sarah Wilson",
                "job_site": "Project Echo",
                "expected_time": "07:00",
                "actual_time": "07:30",
                "minutes_late": 30,
                "notes": ""
            },
            {
                "date": yesterday,
                "driver_id": 3,
                "driver_name": "Mike Johnson",
                "job_site": "Project Bravo",
                "expected_time": "06:30",
                "actual_time": "06:45",
                "minutes_late": 15,
                "notes": "Vehicle issue"
            },
            {
                "date": yesterday,
                "driver_id": 5,
                "driver_name": "David Martinez",
                "job_site": "Project Delta",
                "expected_time": "07:30",
                "actual_time": "08:15",
                "minutes_late": 45,
                "notes": "Weather delay"
            }
        ],
        "early_ends": [
            {
                "date": today,
                "driver_id": 3,
                "driver_name": "Mike Johnson",
                "job_site": "Project Bravo",
                "expected_time": "17:00",
                "actual_time": "16:30",
                "minutes_early": 30,
                "notes": "Work completed early"
            },
            {
                "date": today,
                "driver_id": 4,
                "driver_name": "Lisa Brown",
                "job_site": "Project Charlie",
                "expected_time": "17:30",
                "actual_time": "16:45",
                "minutes_early": 45,
                "notes": "Equipment maintenance needed"
            },
            {
                "date": yesterday,
                "driver_id": 2,
                "driver_name": "Sarah Wilson",
                "job_site": "Project Echo",
                "expected_time": "16:00",
                "actual_time": "15:15",
                "minutes_early": 45,
                "notes": ""
            },
            {
                "date": two_days_ago,
                "driver_id": 1,
                "driver_name": "John Smith",
                "job_site": "Project Alpha",
                "expected_time": "17:00",
                "actual_time": "16:00",
                "minutes_early": 60,
                "notes": "Site closed early due to safety concern"
            }
        ],
        "not_on_job": [
            {
                "date": today,
                "driver_id": 5,
                "driver_name": "David Martinez",
                "expected_job_site": "Project Delta",
                "actual_job_site": "Project Echo",
                "notes": "Reassigned by supervisor"
            },
            {
                "date": yesterday,
                "driver_id": 4,
                "driver_name": "Lisa Brown",
                "expected_job_site": "Project Charlie",
                "actual_job_site": "Shop",
                "notes": "Equipment breakdown"
            }
        ]
    }

def get_attendance_summary(date=None):
    """
    Get attendance summary for a specific date
    
    Args:
        date (str): Date string in YYYY-MM-DD format
        
    Returns:
        dict: Attendance summary
    """
    # Get sample data
    attendance_data = get_sample_attendance_data()
    
    # Use today if no date specified
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Filter data for the specified date
    late_starts = [item for item in attendance_data["late_starts"] if item["date"] == date]
    early_ends = [item for item in attendance_data["early_ends"] if item["date"] == date]
    not_on_job = [item for item in attendance_data["not_on_job"] if item["date"] == date]
    
    # Calculate on-time drivers (total - incidents)
    all_drivers = get_sample_driver_data()
    total_drivers = len(all_drivers)
    
    # Count unique drivers with incidents
    incident_driver_ids = set()
    for item in late_starts + early_ends + not_on_job:
        incident_driver_ids.add(item["driver_id"])
    
    on_time = total_drivers - len(incident_driver_ids)
    
    return {
        "date": date,
        "total_drivers": total_drivers,
        "late_starts": len(late_starts),
        "early_ends": len(early_ends),
        "not_on_job": len(not_on_job),
        "on_time": on_time,
        "incident_rate": round((len(incident_driver_ids) / total_drivers) * 100, 1) if total_drivers > 0 else 0
    }

# Routes
@driver_module_bp.route('/')
@login_required
def index():
    """Driver module home page"""
    drivers = get_sample_driver_data()
    return render_template('drivers/index.html', drivers=drivers)

@driver_module_bp.route('/list')
@login_required
def driver_list():
    """List all drivers"""
    drivers = get_sample_driver_data()
    return render_template('drivers/list.html', drivers=drivers)

@driver_module_bp.route('/<int:driver_id>')
@login_required
def driver_detail(driver_id):
    """Driver detail page"""
    # Find driver by ID
    drivers = get_sample_driver_data()
    driver = next((d for d in drivers if d["id"] == driver_id), None)
    
    if not driver:
        flash("Driver not found", "danger")
        return redirect(url_for('driver_module.driver_list'))
    
    # Get attendance history
    attendance_data = get_sample_attendance_data()
    
    # Filter for this driver
    late_starts = [item for item in attendance_data["late_starts"] if item["driver_id"] == driver_id]
    early_ends = [item for item in attendance_data["early_ends"] if item["driver_id"] == driver_id]
    not_on_job = [item for item in attendance_data["not_on_job"] if item["driver_id"] == driver_id]
    
    return render_template('drivers/detail.html', 
                          driver=driver, 
                          late_starts=late_starts,
                          early_ends=early_ends,
                          not_on_job=not_on_job)

@driver_module_bp.route('/daily_report')
@login_required
def daily_report():
    """Daily driver attendance report page"""
    # Get date parameter or use today
    report_date = request.args.get('date')
    if not report_date:
        report_date = datetime.now().strftime("%Y-%m-%d")
    
    # Get attendance data
    attendance_data = get_sample_attendance_data()
    
    # Filter data for the selected date
    late_starts = [item for item in attendance_data["late_starts"] if item["date"] == report_date]
    early_ends = [item for item in attendance_data["early_ends"] if item["date"] == report_date]
    not_on_job = [item for item in attendance_data["not_on_job"] if item["date"] == report_date]
    
    # Get summary metrics
    summary = get_attendance_summary(report_date)
    
    return render_template('drivers/daily_report.html',
                          report_date=report_date,
                          summary=summary,
                          late_starts=late_starts,
                          early_ends=early_ends,
                          not_on_job=not_on_job)

@driver_module_bp.route('/attendance_dashboard')
@login_required
def attendance_dashboard():
    """Driver attendance dashboard page"""
    # Get date range parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Default to last 7 days if not specified
    if not start_date:
        start_date = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # Generate date range
    date_range = []
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    while current_date <= end:
        date_range.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    
    # Get summary data for each date
    daily_summaries = []
    for date in date_range:
        daily_summaries.append(get_attendance_summary(date))
    
    # Get all drivers
    drivers = get_sample_driver_data()
    
    return render_template('drivers/attendance_dashboard.html',
                          start_date=start_date,
                          end_date=end_date,
                          daily_summaries=daily_summaries,
                          drivers=drivers)

@driver_module_bp.route('/export_report', methods=['POST'])
@login_required
def export_report():
    """Export driver report as PDF or CSV"""
    report_type = request.form.get('report_type', 'daily')
    report_date = request.form.get('report_date')
    export_format = request.form.get('format', 'pdf')
    
    if not report_date:
        report_date = datetime.now().strftime("%Y-%m-%d")
    
    # Generate report filename
    filename = f"{report_type}_report_{report_date}.{export_format}"
    
    # Log the export
    try:
        from utils.activity_logger import log_report_export
        log_report_export(report_type=report_type, format=export_format)
    except ImportError:
        # Activity logger not available
        pass
    
    # Generate and return the report
    if export_format == 'pdf':
        # In a real implementation, this would generate a PDF file
        # For demonstration, we'll simulate this
        return jsonify({
            "success": True,
            "message": f"Report exported as {filename}",
            "download_url": url_for('driver_module.download_report', filename=filename)
        })
    elif export_format == 'csv':
        # In a real implementation, this would generate a CSV file
        # For demonstration, we'll simulate this
        return jsonify({
            "success": True,
            "message": f"Report exported as {filename}",
            "download_url": url_for('driver_module.download_report', filename=filename)
        })
    else:
        return jsonify({
            "success": False,
            "message": f"Unsupported format: {export_format}"
        }), 400

@driver_module_bp.route('/download_report/<filename>')
@login_required
def download_report(filename):
    """Download a generated report"""
    # In a real implementation, this would retrieve the actual report file
    # For demonstration, we'll generate a sample report on-the-fly
    
    # Determine format from filename
    if filename.endswith('.pdf'):
        # Generate PDF
        from utils.report_generator import generate_pdf_report
        
        # Get date from filename
        import re
        date_match = re.search(r'\d{4}-\d{2}-\d{2}', filename)
        report_date = date_match.group(0) if date_match else datetime.now().strftime("%Y-%m-%d")
        
        # Get attendance data for the date
        attendance_data = get_sample_attendance_data()
        late_starts = [item for item in attendance_data["late_starts"] if item["date"] == report_date]
        early_ends = [item for item in attendance_data["early_ends"] if item["date"] == report_date]
        not_on_job = [item for item in attendance_data["not_on_job"] if item["date"] == report_date]
        
        # Format data for report
        data = {
            "summary": get_attendance_summary(report_date),
            "late_starts": late_starts,
            "early_ends": early_ends,
            "not_on_job": not_on_job
        }
        
        # Generate report
        report_path, _ = generate_pdf_report(
            report_type="daily_driver",
            data=data,
            title=f"Daily Driver Report - {report_date}"
        )
        
        # Send file
        return send_from_directory(os.path.dirname(report_path), os.path.basename(report_path))
    elif filename.endswith('.csv'):
        # Generate CSV
        from utils.report_generator import generate_csv_report
        
        # Get date from filename
        import re
        date_match = re.search(r'\d{4}-\d{2}-\d{2}', filename)
        report_date = date_match.group(0) if date_match else datetime.now().strftime("%Y-%m-%d")
        
        # Get attendance data for the date
        attendance_data = get_sample_attendance_data()
        late_starts = [item for item in attendance_data["late_starts"] if item["date"] == report_date]
        early_ends = [item for item in attendance_data["early_ends"] if item["date"] == report_date]
        not_on_job = [item for item in attendance_data["not_on_job"] if item["date"] == report_date]
        
        # Format data for report
        data = {
            "summary": get_attendance_summary(report_date),
            "late_starts": late_starts,
            "early_ends": early_ends,
            "not_on_job": not_on_job
        }
        
        # Generate report
        report_path, _ = generate_csv_report(
            report_type="daily_driver",
            data=data
        )
        
        # Send file
        return send_from_directory(os.path.dirname(report_path), os.path.basename(report_path))
    else:
        flash('Unsupported file format', 'danger')
        return redirect(url_for('driver_module.daily_report'))

@driver_module_bp.route('/api/drivers')
@login_required
def api_drivers():
    """API endpoint to get driver data"""
    drivers = get_sample_driver_data()
    
    # Filter by parameters
    department = request.args.get('department')
    region = request.args.get('region')
    
    if department:
        drivers = [d for d in drivers if d["department"] == department]
    if region:
        drivers = [d for d in drivers if d["region"] == region]
    
    return jsonify(drivers)

@driver_module_bp.route('/api/attendance')
@login_required
def api_attendance():
    """API endpoint to get attendance data"""
    # Get date parameter
    date = request.args.get('date')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    driver_id = request.args.get('driver_id')
    
    # Get attendance data
    attendance_data = get_sample_attendance_data()
    
    # Filter data based on parameters
    if date:
        attendance_data = {
            "late_starts": [item for item in attendance_data["late_starts"] if item["date"] == date],
            "early_ends": [item for item in attendance_data["early_ends"] if item["date"] == date],
            "not_on_job": [item for item in attendance_data["not_on_job"] if item["date"] == date]
        }
    elif start_date and end_date:
        attendance_data = {
            "late_starts": [item for item in attendance_data["late_starts"] if start_date <= item["date"] <= end_date],
            "early_ends": [item for item in attendance_data["early_ends"] if start_date <= item["date"] <= end_date],
            "not_on_job": [item for item in attendance_data["not_on_job"] if start_date <= item["date"] <= end_date]
        }
    
    if driver_id:
        try:
            driver_id = int(driver_id)
            attendance_data = {
                "late_starts": [item for item in attendance_data["late_starts"] if item["driver_id"] == driver_id],
                "early_ends": [item for item in attendance_data["early_ends"] if item["driver_id"] == driver_id],
                "not_on_job": [item for item in attendance_data["not_on_job"] if item["driver_id"] == driver_id]
            }
        except ValueError:
            pass
    
    return jsonify(attendance_data)

@driver_module_bp.route('/api/attendance/summary')
@login_required
def api_attendance_summary():
    """API endpoint to get attendance summary"""
    # Get date parameter
    date = request.args.get('date')
    
    # Get summary
    summary = get_attendance_summary(date)
    
    return jsonify(summary)

# Register blueprint function
def register_blueprint(app):
    app.register_blueprint(driver_module_bp)
    return app