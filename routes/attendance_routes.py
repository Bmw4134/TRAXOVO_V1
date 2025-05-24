"""
TRAXORA Fleet Management System - Attendance Dashboard Routes

This module contains routes for the attendance dashboard, including
daily driver reports and attendance metrics.
"""
import os
import pandas as pd
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
import json

# Create a logger for this module
logger = logging.getLogger(__name__)

# Create a blueprint for the attendance dashboard
attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@attendance_bp.route('/')
def index():
    """Display the attendance dashboard index - redirect to enhanced weekly report"""
    return redirect(url_for('enhanced_weekly_report_bp.demo_may_week'))

@attendance_bp.route('/daily_driver_report')
def daily_driver_report():
    """Display the daily driver report dashboard"""
    # Get parameters from request
    selected_date = request.args.get('date', None)
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    # Get available dates from reports directory
    available_dates = get_available_report_dates()
    
    # If no date is selected, use the most recent available date
    if not selected_date and available_dates:
        selected_date = available_dates[0]
    
    # Load report data for the selected date
    report_data = load_report_data(selected_date)
    
    # Apply filters if any
    if report_data:
        if search_query:
            report_data = [record for record in report_data if search_query.lower() in str(record.get('Driver', '')).lower()]
        
        if status_filter:
            report_data = [record for record in report_data if str(record.get('Status', '')).lower() == status_filter.lower()]
    
    # Calculate statistics
    stats = calculate_statistics(report_data)
    
    return render_template(
        'attendance/daily_driver_report.html',
        title="Daily Driver Report",
        selected_date=selected_date,
        available_dates=available_dates,
        report_data=report_data,
        search_query=search_query,
        status_filter=status_filter,
        stats=stats
    )

@attendance_bp.route('/download_report')
def download_report():
    """Download the driver report for a specific date as Excel file"""
    date_str = request.args.get('date')
    
    if not date_str:
        flash('Please select a date to download the report', 'warning')
        return redirect(url_for('attendance.daily_driver_report'))
    
    try:
        # Construct the path to the Excel file
        reports_dir = os.path.join(os.getcwd(), 'exports', 'attendance')
        os.makedirs(reports_dir, exist_ok=True)
        
        excel_file = os.path.join(reports_dir, f'driver_report_{date_str}.xlsx')
        
        # Check if the file exists
        if not os.path.exists(excel_file):
            # If not, check if we have a JSON file and convert it to Excel
            json_file = os.path.join(reports_dir, f'driver_report_{date_str}.json')
            if os.path.exists(json_file):
                # Convert JSON to Excel
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                df = pd.DataFrame(data)
                df.to_excel(excel_file, index=False)
            else:
                # Generate a new report on the fly
                data = load_report_data(date_str)
                if data:
                    df = pd.DataFrame(data)
                    df.to_excel(excel_file, index=False)
                else:
                    flash(f'No report data found for {date_str}', 'danger')
                    return redirect(url_for('attendance.daily_driver_report'))
        
        # Return the Excel file for download
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=f'TRAXORA_Driver_Report_{date_str}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        flash(f'Error downloading report: {str(e)}', 'danger')
        return redirect(url_for('attendance.daily_driver_report'))

@attendance_bp.route('/process_report', methods=['POST'])
def process_report():
    """Process or regenerate a report for a specific date"""
    date_str = request.form.get('date')
    
    if not date_str:
        flash('Please select a date to process the report', 'warning')
        return redirect(url_for('attendance.daily_driver_report'))
    
    try:
        # Run the attendance pipeline for the specified date
        # This should be replaced with the actual implementation
        from utils.attendance_pipeline import process_attendance_data
        success = process_attendance_data(date_str)
        
        if success:
            flash(f'Report for {date_str} processed successfully', 'success')
        else:
            flash(f'Error processing report for {date_str}', 'danger')
    
    except ImportError:
        # Fallback if the attendance pipeline is not available
        logger.warning("Attendance pipeline module not found")
        flash('The attendance pipeline module is not available', 'warning')
    except Exception as e:
        logger.error(f"Error processing report: {str(e)}")
        flash(f'Error processing report: {str(e)}', 'danger')
    
    return redirect(url_for('attendance.daily_driver_report', date=date_str))

@attendance_bp.route('/api/dates')
def api_dates():
    """API endpoint to get available report dates"""
    available_dates = get_available_report_dates()
    return jsonify(available_dates)

# Helper functions
def get_available_report_dates():
    """Get a list of dates for which reports are available"""
    try:
        # Look for report files in the exports directory
        reports_dir = os.path.join(os.getcwd(), 'exports', 'attendance')
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir, exist_ok=True)
            return []
        
        # Look for JSON and Excel files
        files = os.listdir(reports_dir)
        dates = set()
        
        for file in files:
            if file.startswith('driver_report_') and (file.endswith('.json') or file.endswith('.xlsx')):
                date_str = file.replace('driver_report_', '').replace('.json', '').replace('.xlsx', '')
                dates.add(date_str)
        
        # Also check processed data directory
        processed_dir = os.path.join(os.getcwd(), 'processed')
        if os.path.exists(processed_dir):
            processed_files = os.listdir(processed_dir)
            for file in processed_files:
                if file.startswith('attendance_') and file.endswith('.json'):
                    date_str = file.replace('attendance_', '').replace('.json', '')
                    dates.add(date_str)
        
        # Return dates sorted in descending order (newest first)
        return sorted(list(dates), reverse=True)
    
    except Exception as e:
        logger.error(f"Error getting available report dates: {str(e)}")
        return []

def load_report_data(date_str):
    """Load report data for a specific date"""
    if not date_str:
        return []
    
    try:
        # Check for report files in different locations
        # 1. First try exports/attendance directory
        exports_path = os.path.join(os.getcwd(), 'exports', 'attendance', f'driver_report_{date_str}.json')
        if os.path.exists(exports_path):
            with open(exports_path, 'r') as f:
                return json.load(f)
        
        # 2. Try the processed directory
        processed_path = os.path.join(os.getcwd(), 'processed', f'attendance_{date_str}.json')
        if os.path.exists(processed_path):
            with open(processed_path, 'r') as f:
                return json.load(f)
        
        # 3. Try Excel files
        excel_path = os.path.join(os.getcwd(), 'exports', 'attendance', f'driver_report_{date_str}.xlsx')
        if os.path.exists(excel_path):
            df = pd.read_excel(excel_path)
            return df.to_dict('records')
        
        # 4. Try the weekly reports directory
        weekly_path = os.path.join(os.getcwd(), 'reports', 'weekly', f'daily_{date_str}.json')
        if os.path.exists(weekly_path):
            with open(weekly_path, 'r') as f:
                return json.load(f)
        
        # Check if we need to use raw file data
        # This is just a fallback with sample data if no real data exists
        # Try to load from attached_assets for May 18-24, 2025
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        if date_obj.year == 2025 and date_obj.month == 5 and 18 <= date_obj.day <= 24:
            try:
                weekly_data_path = os.path.join(os.getcwd(), 'attached_assets', 'weekly_driver_report_2025-05-18_to_2025-05-24.json')
                if os.path.exists(weekly_data_path):
                    with open(weekly_data_path, 'r') as f:
                        weekly_data = json.load(f)
                        # Filter data for the specific day
                        day_data = [record for record in weekly_data if record.get('Date') == date_str]
                        if day_data:
                            return day_data
            except Exception as e:
                logger.error(f"Error loading sample data: {str(e)}")
        
        logger.warning(f"No report data found for {date_str}")
        return []
    
    except Exception as e:
        logger.error(f"Error loading report data: {str(e)}")
        return []

def calculate_statistics(report_data):
    """Calculate statistics for the report data"""
    if not report_data:
        return {
            'total': 0,
            'on_time': 0,
            'late': 0,
            'early_end': 0,
            'not_on_job': 0,
            'on_time_percentage': 0,
            'late_percentage': 0,
            'early_end_percentage': 0,
            'not_on_job_percentage': 0
        }
    
    total = len(report_data)
    on_time = sum(1 for record in report_data if str(record.get('Status', '')).lower() == 'on time')
    late = sum(1 for record in report_data if str(record.get('Status', '')).lower() == 'late')
    early_end = sum(1 for record in report_data if str(record.get('Status', '')).lower() == 'early end')
    not_on_job = sum(1 for record in report_data if str(record.get('Status', '')).lower() == 'not on job')
    
    # Calculate percentages
    on_time_percentage = round((on_time / total) * 100) if total > 0 else 0
    late_percentage = round((late / total) * 100) if total > 0 else 0
    early_end_percentage = round((early_end / total) * 100) if total > 0 else 0
    not_on_job_percentage = round((not_on_job / total) * 100) if total > 0 else 0
    
    return {
        'total': total,
        'on_time': on_time,
        'late': late,
        'early_end': early_end,
        'not_on_job': not_on_job,
        'on_time_percentage': on_time_percentage,
        'late_percentage': late_percentage,
        'early_end_percentage': early_end_percentage,
        'not_on_job_percentage': not_on_job_percentage
    }