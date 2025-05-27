"""
TRAXORA Fleet Management System - Time on Site Module

This module provides smart duration tracking and driver flagging for attendance compliance.
Analyzes uploaded driver CSV data to calculate time on site and flag attendance issues.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
import os
import logging
from datetime import datetime, timedelta
import json
from utils.monthly_report_generator import extract_all_drivers_from_mtd

logger = logging.getLogger(__name__)

time_site_bp = Blueprint('time_on_site', __name__, url_prefix='/time-on-site')

def calculate_time_on_site(start_time, end_time):
    """Calculate total time on site in hours"""
    if not start_time or not end_time:
        return 0
    
    try:
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        duration = end_time - start_time
        return round(duration.total_seconds() / 3600, 2)  # Convert to hours
    except:
        return 0

def flag_attendance_issues(hours_on_site):
    """Flag attendance issues based on time on site"""
    if hours_on_site < 2:
        return {
            'flag': 'low_attendance',
            'icon': '⚠️',
            'color': 'warning',
            'message': 'Low Attendance - Under 2 hours'
        }
    elif hours_on_site > 14:
        return {
            'flag': 'compliance_issue',
            'icon': '⚠️',
            'color': 'danger',
            'message': 'Potential Compliance Issue - Over 14 hours'
        }
    else:
        return {
            'flag': 'normal',
            'icon': '✓',
            'color': 'success',
            'message': 'Normal attendance'
        }

def parse_driver_csv_for_time_tracking(file_path):
    """Parse uploaded driver CSV to extract time on site data"""
    try:
        df = pd.read_csv(file_path)
        
        # Common CSV column variations for time tracking
        time_columns = {
            'driver_name': ['Driver', 'driver_name', 'Driver Name', 'Name'],
            'start_time': ['Start Time', 'start_time', 'Check In', 'Arrival', 'First Activity'],
            'end_time': ['End Time', 'end_time', 'Check Out', 'Departure', 'Last Activity'],
            'job_site': ['Job Site', 'job_site', 'Location', 'Project', 'Site']
        }
        
        # Map columns to standard names
        column_mapping = {}
        for standard_name, variations in time_columns.items():
            for variation in variations:
                if variation in df.columns:
                    column_mapping[variation] = standard_name
                    break
        
        # Rename columns to standard format
        df_mapped = df.rename(columns=column_mapping)
        
        time_data = []
        for _, row in df_mapped.iterrows():
            driver_name = row.get('driver_name', 'Unknown Driver')
            start_time = row.get('start_time')
            end_time = row.get('end_time')
            job_site = row.get('job_site', 'Unknown Site')
            
            hours_on_site = calculate_time_on_site(start_time, end_time)
            flag_info = flag_attendance_issues(hours_on_site)
            
            time_data.append({
                'driver_name': driver_name,
                'start_time': start_time,
                'end_time': end_time,
                'hours_on_site': hours_on_site,
                'job_site': job_site,
                'flag': flag_info
            })
        
        return time_data
        
    except Exception as e:
        logger.error(f"Error parsing CSV for time tracking: {str(e)}")
        return []

@time_site_bp.route('/')
def dashboard():
    """Time on Site dashboard showing driver duration tracking and flagging"""
    try:
        # Get drivers from MTD data for baseline
        all_drivers = extract_all_drivers_from_mtd()
        
        # Process time data from uploaded files if available
        uploaded_files_dir = os.path.join(os.getcwd(), 'uploads')
        time_data = []
        
        if os.path.exists(uploaded_files_dir):
            for filename in os.listdir(uploaded_files_dir):
                if filename.endswith('.csv'):
                    file_path = os.path.join(uploaded_files_dir, filename)
                    csv_time_data = parse_driver_csv_for_time_tracking(file_path)
                    time_data.extend(csv_time_data)
        
        # If no uploaded data, create sample data from MTD drivers
        if not time_data and all_drivers:
            for driver in all_drivers[:10]:  # Show first 10 drivers
                # Simulate time data for demonstration
                start_hour = 7 + (hash(driver.driver_name) % 3)  # 7-9 AM start
                end_hour = 16 + (hash(driver.driver_name) % 4)   # 4-7 PM end
                
                hours_on_site = end_hour - start_hour
                flag_info = flag_attendance_issues(hours_on_site)
                
                time_data.append({
                    'driver_name': driver.driver_name,
                    'start_time': f"{start_hour:02d}:00",
                    'end_time': f"{end_hour:02d}:00",
                    'hours_on_site': hours_on_site,
                    'job_site': getattr(driver, 'asset_assignment', 'Various Sites'),
                    'flag': flag_info
                })
        
        # Calculate summary statistics
        total_drivers = len(time_data)
        flagged_drivers = len([d for d in time_data if d['flag']['flag'] != 'normal'])
        avg_hours = round(sum([d['hours_on_site'] for d in time_data]) / total_drivers, 2) if total_drivers > 0 else 0
        
        dashboard_data = {
            'time_data': time_data,
            'total_drivers': total_drivers,
            'flagged_drivers': flagged_drivers,
            'avg_hours_on_site': avg_hours,
            'date': datetime.now().strftime('%B %d, %Y'),
            'last_updated': datetime.now().strftime('%I:%M %p')
        }
        
        return render_template('time_on_site/dashboard.html', data=dashboard_data)
        
    except Exception as e:
        logger.error(f"Error in time on site dashboard: {str(e)}")
        return f"Error loading time on site data: {str(e)}", 500

@time_site_bp.route('/upload', methods=['POST'])
def upload_time_data():
    """Upload and process driver CSV for time tracking"""
    try:
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('time_on_site.dashboard'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('time_on_site.dashboard'))
        
        if file and file.filename.endswith('.csv'):
            # Save uploaded file
            uploads_dir = os.path.join(os.getcwd(), 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            
            filename = f"time_tracking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            file_path = os.path.join(uploads_dir, filename)
            file.save(file_path)
            
            # Process the file
            time_data = parse_driver_csv_for_time_tracking(file_path)
            
            if time_data:
                flash(f'Successfully processed {len(time_data)} driver records', 'success')
            else:
                flash('No valid time data found in uploaded file', 'warning')
        else:
            flash('Please upload a CSV file', 'error')
        
        return redirect(url_for('time_on_site.dashboard'))
        
    except Exception as e:
        logger.error(f"Error uploading time data: {str(e)}")
        flash(f'Error processing file: {str(e)}', 'error')
        return redirect(url_for('time_on_site.dashboard'))

@time_site_bp.route('/api/time-data')
def api_time_data():
    """API endpoint for time on site data"""
    try:
        # Get current time data
        uploaded_files_dir = os.path.join(os.getcwd(), 'uploads')
        time_data = []
        
        if os.path.exists(uploaded_files_dir):
            for filename in os.listdir(uploaded_files_dir):
                if filename.endswith('.csv'):
                    file_path = os.path.join(uploaded_files_dir, filename)
                    csv_time_data = parse_driver_csv_for_time_tracking(file_path)
                    time_data.extend(csv_time_data)
        
        return jsonify({
            'status': 'success',
            'data': time_data,
            'total_drivers': len(time_data),
            'flagged_drivers': len([d for d in time_data if d['flag']['flag'] != 'normal'])
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500