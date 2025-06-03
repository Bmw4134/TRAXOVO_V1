"""
Ground Works Timecard Excel Import System
Processes weekly timecard files (Sunday-Saturday) and populates Attendance Matrix
"""

import pandas as pd
import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
import logging

timecard_bp = Blueprint('timecard_processor', __name__)

class TimecardProcessor:
    """Processes Ground Works Excel timecard files"""
    
    def __init__(self):
        self.upload_folder = 'uploads/timecards'
        self.allowed_extensions = {'.xlsx', '.xls', '.csv'}
        self.ensure_upload_directory()
        
    def ensure_upload_directory(self):
        """Create upload directory if it doesn't exist"""
        os.makedirs(self.upload_folder, exist_ok=True)
        
    def is_allowed_file(self, filename):
        """Check if file extension is allowed"""
        return any(filename.lower().endswith(ext) for ext in self.allowed_extensions)
        
    def process_timecard_file(self, file_path):
        """Process Ground Works timecard Excel file"""
        try:
            # Read Excel file - try multiple sheet detection
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                # Check for multiple sheets
                xl_file = pd.ExcelFile(file_path)
                if len(xl_file.sheet_names) > 1:
                    # Look for timecard data in common sheet names
                    sheet_names = ['Timecard', 'Weekly', 'Hours', 'Attendance']
                    target_sheet = None
                    for sheet in sheet_names:
                        if sheet in xl_file.sheet_names:
                            target_sheet = sheet
                            break
                    if not target_sheet:
                        target_sheet = xl_file.sheet_names[0]
                    df = pd.read_excel(file_path, sheet_name=target_sheet)
                else:
                    df = pd.read_excel(file_path)
            
            # Process the timecard data
            processed_data = self._extract_timecard_data(df)
            return processed_data
            
        except Exception as e:
            logging.error(f"Error processing timecard file: {e}")
            return {'error': str(e)}
    
    def _extract_timecard_data(self, df):
        """Extract employee timecard data from DataFrame"""
        processed_records = []
        
        # Common column name variations for Ground Works format
        employee_id_cols = ['Employee ID', 'EmpID', 'ID', 'Employee_ID', 'Emp_ID']
        employee_name_cols = ['Employee Name', 'Name', 'Employee', 'EmpName', 'Full Name']
        asset_id_cols = ['Asset ID', 'Equipment', 'Asset', 'Equipment ID', 'Machine']
        
        # Find actual column names
        employee_id_col = self._find_column(df, employee_id_cols)
        employee_name_col = self._find_column(df, employee_name_cols)
        asset_id_col = self._find_column(df, asset_id_cols)
        
        # Find date columns (Sunday through Saturday)
        date_columns = []
        for col in df.columns:
            if any(day in str(col).upper() for day in ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']):
                date_columns.append(col)
        
        # If no day columns found, look for date patterns
        if not date_columns:
            for col in df.columns:
                try:
                    pd.to_datetime(str(col))
                    date_columns.append(col)
                except:
                    continue
        
        # Process each employee row
        for index, row in df.iterrows():
            if pd.isna(row.get(employee_id_col)):
                continue
                
            employee_record = {
                'employee_id': str(row.get(employee_id_col, '')).strip(),
                'employee_name': str(row.get(employee_name_col, '')).strip(),
                'asset_id': str(row.get(asset_id_col, '')).strip(),
                'weekly_hours': {},
                'total_hours': 0.0
            }
            
            total_hours = 0.0
            for date_col in date_columns:
                hours = self._parse_hours(row.get(date_col, 0))
                day_name = self._get_day_name(date_col)
                employee_record['weekly_hours'][day_name] = hours
                total_hours += hours
            
            employee_record['total_hours'] = total_hours
            processed_records.append(employee_record)
        
        return {
            'success': True,
            'records_processed': len(processed_records),
            'employees': processed_records,
            'week_start': self._determine_week_start(date_columns),
            'file_processed': datetime.now().isoformat()
        }
    
    def _find_column(self, df, possible_names):
        """Find the actual column name from possible variations"""
        for col in df.columns:
            for possible in possible_names:
                if possible.upper() in str(col).upper():
                    return col
        return possible_names[0] if possible_names else None
    
    def _parse_hours(self, value):
        """Parse hours from various formats"""
        if pd.isna(value) or value == '':
            return 0.0
        try:
            if isinstance(value, str):
                # Handle time formats like "8:00" or "8.5h"
                if ':' in value:
                    parts = value.split(':')
                    hours = float(parts[0])
                    minutes = float(parts[1]) / 60.0 if len(parts) > 1 else 0.0
                    return hours + minutes
                elif 'h' in value.lower():
                    return float(value.lower().replace('h', '').strip())
                else:
                    return float(value)
            return float(value)
        except:
            return 0.0
    
    def _get_day_name(self, column_name):
        """Extract day name from column"""
        day_mapping = {
            'SUN': 'Sunday', 'MON': 'Monday', 'TUE': 'Tuesday', 
            'WED': 'Wednesday', 'THU': 'Thursday', 'FRI': 'Friday', 'SAT': 'Saturday'
        }
        
        col_upper = str(column_name).upper()
        for abbr, full_name in day_mapping.items():
            if abbr in col_upper:
                return full_name
        return str(column_name)
    
    def _determine_week_start(self, date_columns):
        """Determine the week start date from columns"""
        try:
            for col in date_columns:
                if 'SUN' in str(col).upper():
                    # Try to extract date from column name
                    date_str = str(col).replace('SUN', '').replace('Sunday', '').strip()
                    if date_str:
                        return pd.to_datetime(date_str).strftime('%Y-%m-%d')
        except:
            pass
        return datetime.now().strftime('%Y-%m-%d')

# Initialize processor
processor = TimecardProcessor()

@timecard_bp.route('/timecard-import')
def timecard_import_page():
    """Timecard import interface"""
    return render_template('timecard_import.html')

@timecard_bp.route('/api/upload-timecard', methods=['POST'])
def upload_timecard():
    """API endpoint for timecard file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not processor.is_allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload Excel or CSV files.'}), 400
    
    # Save uploaded file
    filename = secure_filename(file.filename or 'timecard.xlsx')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{filename}"
    file_path = os.path.join(processor.upload_folder, filename)
    file.save(file_path)
    
    # Process the file
    result = processor.process_timecard_file(file_path)
    
    if 'error' in result:
        return jsonify(result), 500
    
    return jsonify(result)

@timecard_bp.route('/api/timecard-data')
def get_timecard_data():
    """Get processed timecard data for Attendance Matrix"""
    # This would typically fetch from database
    # For now, return sample structure for integration
    return jsonify({
        'week_start': '2025-05-25',
        'week_end': '2025-05-31',
        'employees': [
            {
                'employee_id': 'EMP001',
                'employee_name': 'John Smith',
                'asset_id': 'AST-101',
                'weekly_hours': {
                    'Sunday': 0, 'Monday': 8.0, 'Tuesday': 8.5,
                    'Wednesday': 7.5, 'Thursday': 8.0, 'Friday': 8.0, 'Saturday': 0
                },
                'total_hours': 40.0
            }
        ]
    })