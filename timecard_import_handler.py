"""
Ground Works Timecard Import Handler
Handles Excel timecard imports for weekly attendance tracking (Sunday-Saturday)
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

timecard_import_bp = Blueprint('timecard_import', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_week_range(date_str=None):
    """Get Sunday-Saturday week range for given date"""
    if date_str:
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
    else:
        target_date = datetime.now()
    
    # Find the Sunday of this week
    days_since_sunday = target_date.weekday() + 1 if target_date.weekday() != 6 else 0
    week_start = target_date - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)
    
    return week_start, week_end

def process_ground_works_timecard(file_path, target_week=None):
    """Process Ground Works timecard Excel file for specific week"""
    try:
        # Determine week range
        if target_week:
            week_start, week_end = get_week_range(target_week)
        else:
            week_start, week_end = get_week_range()
        
        logger.info(f"Processing timecard for week: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")
        
        # Read Excel file
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            # Try to read Excel file, checking multiple sheets
            excel_file = pd.ExcelFile(file_path)
            df = None
            
            # Look for timecard data in sheets
            for sheet_name in excel_file.sheet_names:
                temp_df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Check if this sheet has timecard-like columns
                timecard_indicators = ['employee', 'date', 'time', 'hours', 'clock', 'shift']
                if any(any(indicator in str(col).lower() for indicator in timecard_indicators) for col in temp_df.columns):
                    df = temp_df
                    logger.info(f"Found timecard data in sheet: {sheet_name}")
                    break
            
            if df is None:
                df = pd.read_excel(file_path)  # Use first sheet as fallback
        
        # Identify relevant columns
        employee_cols = [col for col in df.columns if any(term in str(col).lower() for term in ['employee', 'name', 'worker', 'driver'])]
        date_cols = [col for col in df.columns if any(term in str(col).lower() for term in ['date', 'day', 'shift'])]
        time_cols = [col for col in df.columns if any(term in str(col).lower() for term in ['time', 'hours', 'clock', 'in', 'out'])]
        
        logger.info(f"Found columns - Employee: {employee_cols}, Date: {date_cols}, Time: {time_cols}")
        
        if not employee_cols:
            return {'success': False, 'message': 'No employee column found in timecard file'}
        
        # Process attendance records
        attendance_records = []
        employees_processed = set()
        
        for idx, row in df.iterrows():
            try:
                # Get employee name
                employee_name = None
                for emp_col in employee_cols:
                    if pd.notna(row.get(emp_col)):
                        employee_name = str(row[emp_col]).strip()
                        break
                
                if not employee_name:
                    continue
                
                # Process date information
                work_date = None
                for date_col in date_cols:
                    if pd.notna(row.get(date_col)):
                        try:
                            if isinstance(row[date_col], str):
                                work_date = pd.to_datetime(row[date_col]).date()
                            elif hasattr(row[date_col], 'date'):
                                work_date = row[date_col].date()
                            else:
                                work_date = pd.to_datetime(str(row[date_col])).date()
                            break
                        except:
                            continue
                
                # Check if date falls within target week
                if work_date and week_start.date() <= work_date <= week_end.date():
                    # Calculate hours worked
                    total_hours = 0
                    
                    for time_col in time_cols:
                        if pd.notna(row.get(time_col)) and 'hour' in str(time_col).lower():
                            try:
                                total_hours += float(row[time_col])
                            except:
                                pass
                    
                    # Determine status
                    status = 'Present' if total_hours > 0 else 'Absent'
                    if total_hours > 8:
                        status = 'Overtime'
                    
                    attendance_record = {
                        'employee_name': employee_name,
                        'employee_id': row.get('Employee ID', f"GW_{len(employees_processed)+1:03d}"),
                        'date': work_date.strftime('%Y-%m-%d'),
                        'day_of_week': work_date.strftime('%A'),
                        'hours_worked': total_hours,
                        'status': status,
                        'division': row.get('Division', row.get('Dept', 'Ground Works')),
                        'job_code': row.get('Job Code', row.get('JobCode', 'GENERAL'))
                    }
                    
                    attendance_records.append(attendance_record)
                    employees_processed.add(employee_name)
                    
            except Exception as e:
                logger.warning(f"Error processing row {idx}: {e}")
                continue
        
        return {
            'success': True,
            'message': f'Successfully processed {len(attendance_records)} attendance records for {len(employees_processed)} employees',
            'records': attendance_records,
            'employees_count': len(employees_processed),
            'week_range': f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"
        }
        
    except Exception as e:
        logger.error(f"Error processing timecard file: {e}")
        return {'success': False, 'message': f'Error processing file: {str(e)}'}

@timecard_import_bp.route('/timecard-import')
def timecard_import_page():
    """Timecard import interface"""
    return render_template('timecard_import.html')

@timecard_import_bp.route('/api/timecard-upload', methods=['POST'])
def upload_timecard():
    """Handle timecard file upload and processing"""
    if 'timecard_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400
    
    file = request.files['timecard_file']
    target_week = request.form.get('target_week')  # Optional week selection
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Ensure upload directory exists
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            saved_filename = f"timecard_{timestamp}_{filename}"
            file_path = os.path.join(UPLOAD_FOLDER, saved_filename)
            file.save(file_path)
            
            # Process the timecard file
            result = process_ground_works_timecard(file_path, target_week)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': result['message'],
                    'data': {
                        'employees_processed': result['employees_count'],
                        'records_count': len(result['records']),
                        'week_range': result['week_range'],
                        'filename': saved_filename
                    }
                })
            else:
                return jsonify({'success': False, 'message': result['message']}), 400
                
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'}), 500
    
    return jsonify({'success': False, 'message': 'Invalid file type'}), 400

@timecard_import_bp.route('/api/weekly-attendance/<week_offset>')
def get_weekly_attendance(week_offset=0):
    """Get attendance data for specific week"""
    try:
        week_offset = int(week_offset)
        target_date = datetime.now() - timedelta(weeks=week_offset)
        week_start, week_end = get_week_range(target_date.strftime('%Y-%m-%d'))
        
        # Look for processed timecard files for this week
        attendance_data = []
        
        if os.path.exists(UPLOAD_FOLDER):
            for file in os.listdir(UPLOAD_FOLDER):
                if file.startswith('timecard_') and file.endswith(('.xlsx', '.xls')):
                    file_path = os.path.join(UPLOAD_FOLDER, file)
                    result = process_ground_works_timecard(file_path, target_date.strftime('%Y-%m-%d'))
                    
                    if result['success']:
                        attendance_data.extend(result['records'])
        
        return jsonify({
            'success': True,
            'week_range': f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}",
            'data': attendance_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500