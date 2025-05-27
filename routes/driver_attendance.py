"""
Driver Attendance Reporting System
Weekly driver attendance tracking and compliance reporting
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import json
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

driver_attendance_bp = Blueprint('driver_attendance', __name__)
logger = logging.getLogger(__name__)

@driver_attendance_bp.route('/')
def driver_attendance_dashboard():
    """Driver attendance calendar view with daily tracking"""
    try:
        # Get attendance data for current week
        attendance_data = load_weekly_attendance()
        
        return render_template('driver_attendance/daily.html', 
                             attendance_data=attendance_data,
                             current_date=datetime.now().strftime('%Y-%m-%d'))
    except Exception as e:
        logger.error(f"Error loading driver attendance dashboard: {e}")
        flash('Error loading attendance dashboard', 'error')
        return redirect(url_for('index'))

@driver_attendance_bp.route('/driver-attendance/upload')
def upload_form():
    """File upload form for attendance data"""
    try:
        return render_template('driver_attendance/upload.html')
    except Exception as e:
        logger.error(f"Error loading upload form: {e}")
        flash('Error loading upload form', 'error')
        return redirect(url_for('driver_attendance.driver_attendance_dashboard'))

@driver_attendance_bp.route('/driver-attendance/upload', methods=['POST'])
def process_attendance_upload():
    """Process uploaded attendance files"""
    try:
        uploaded_files = request.files.getlist('files')
        
        if not uploaded_files:
            return jsonify({
                'success': False,
                'message': 'No files uploaded'
            }), 400
        
        # Create attendance data directory
        attendance_dir = Path('./attendance_data')
        attendance_dir.mkdir(exist_ok=True)
        
        processed_files = []
        total_drivers = 0
        
        for file in uploaded_files:
            if file.filename:
                # Save uploaded file
                file_path = attendance_dir / file.filename
                file.save(file_path)
                
                # Process the file
                result = process_attendance_file(file_path)
                processed_files.append({
                    'filename': file.filename,
                    'result': result,
                    'success': result['success'] if result else False
                })
                
                if result and result['success']:
                    total_drivers += result.get('drivers_processed', 0)
        
        if total_drivers > 0:
            return jsonify({
                'success': True,
                'message': f'Drivers processed: {total_drivers}',
                'processed_files': processed_files
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No valid attendance data found',
                'processed_files': processed_files
            }), 400
            
    except Exception as e:
        logger.error(f"Error processing attendance upload: {e}")
        return jsonify({
            'success': False,
            'message': f'Upload error: {str(e)}'
        }), 500

def process_attendance_file(file_path):
    """Process individual attendance file"""
    try:
        # Determine file type and read
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            return {
                'success': False,
                'message': f'Unsupported file type: {file_path.suffix}'
            }
        
        # Validate required columns
        required_columns = ['Driver ID', 'Date', 'Check-in', 'Check-out']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                'success': False,
                'message': f'Invalid format - missing columns: {", ".join(missing_columns)}'
            }
        
        # Process attendance records
        attendance_records = []
        drivers_processed = set()
        
        for index, row in df.iterrows():
            # Validate required fields
            if pd.isna(row['Driver ID']) or pd.isna(row['Date']):
                continue
                
            # Parse date
            try:
                attendance_date = pd.to_datetime(row['Date']).strftime('%Y-%m-%d')
            except:
                continue
            
            # Create attendance record
            record = {
                'driver_id': str(row['Driver ID']),
                'date': attendance_date,
                'check_in': str(row['Check-in']) if pd.notna(row['Check-in']) else None,
                'check_out': str(row['Check-out']) if pd.notna(row['Check-out']) else None,
                'location': str(row.get('Location', '')) if pd.notna(row.get('Location', '')) else None,
                'status': 'present' if pd.notna(row['Check-in']) else 'absent'
            }
            
            attendance_records.append(record)
            drivers_processed.add(record['driver_id'])
        
        # Save processed data by date
        save_attendance_data(attendance_records)
        
        return {
            'success': True,
            'drivers_processed': len(drivers_processed),
            'records_processed': len(attendance_records),
            'file_path': str(file_path)
        }
        
    except Exception as e:
        logger.error(f"Error processing attendance file {file_path}: {e}")
        return {
            'success': False,
            'message': f'File processing error: {str(e)}'
        }

def save_attendance_data(attendance_records):
    """Save attendance records organized by date"""
    try:
        attendance_dir = Path('./attendance_data')
        attendance_dir.mkdir(exist_ok=True)
        
        # Group records by date
        date_groups = {}
        for record in attendance_records:
            date = record['date']
            if date not in date_groups:
                date_groups[date] = []
            date_groups[date].append(record)
        
        # Save each date group to a separate file
        for date, records in date_groups.items():
            date_file = attendance_dir / f'attendance_{date}.json'
            
            # Load existing data if file exists
            existing_data = []
            if date_file.exists():
                with open(date_file, 'r') as f:
                    existing_data = json.load(f)
            
            # Merge with new data (avoid duplicates)
            existing_driver_ids = {record['driver_id'] for record in existing_data}
            new_records = [record for record in records if record['driver_id'] not in existing_driver_ids]
            
            # Save updated data
            all_records = existing_data + new_records
            with open(date_file, 'w') as f:
                json.dump(all_records, f, indent=2)
        
        logger.info(f"Saved attendance data for {len(date_groups)} dates")
        
    except Exception as e:
        logger.error(f"Error saving attendance data: {e}")

def load_weekly_attendance():
    """Load attendance data for the current week"""
    try:
        attendance_dir = Path('./attendance_data')
        if not attendance_dir.exists():
            return {}
        
        # Get current week dates
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_dates = [week_start + timedelta(days=i) for i in range(7)]
        
        weekly_data = {}
        
        for date in week_dates:
            date_str = date.strftime('%Y-%m-%d')
            date_file = attendance_dir / f'attendance_{date_str}.json'
            
            if date_file.exists():
                with open(date_file, 'r') as f:
                    daily_records = json.load(f)
                    weekly_data[date_str] = daily_records
            else:
                weekly_data[date_str] = []
        
        return weekly_data
        
    except Exception as e:
        logger.error(f"Error loading weekly attendance: {e}")
        return {}

@driver_attendance_bp.route('/driver-attendance/api/daily/<date>')
def get_daily_attendance(date):
    """API endpoint for daily attendance data"""
    try:
        attendance_dir = Path('./attendance_data')
        date_file = attendance_dir / f'attendance_{date}.json'
        
        if date_file.exists():
            with open(date_file, 'r') as f:
                attendance_data = json.load(f)
            
            return jsonify({
                'success': True,
                'date': date,
                'attendance': attendance_data
            })
        else:
            return jsonify({
                'success': True,
                'date': date,
                'attendance': []
            })
            
    except Exception as e:
        logger.error(f"Error getting daily attendance for {date}: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500