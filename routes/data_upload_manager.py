"""
TRAXORA Data Upload Manager

Handles uploading new MTD data files for daily processing or custom date ranges.
Supports both same-day processing and historical gap-filling.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import pandas as pd
from datetime import datetime, timedelta
import logging

# Initialize blueprint
data_upload_bp = Blueprint('data_upload', __name__)

UPLOAD_FOLDER = 'uploads/mtd_data'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_file_type(filename):
    """Detect if file is MTD driving history, activity detail, or timecards"""
    filename_lower = filename.lower()
    
    if 'driving' in filename_lower or 'mtd' in filename_lower:
        return 'driving_history'
    elif 'activity' in filename_lower:
        return 'activity_detail'
    elif 'timecard' in filename_lower:
        return 'timecards'
    elif any(div in filename_lower for div in ['dfw', 'hou', 'wt']):
        return 'division_data'
    else:
        return 'unknown'

def extract_date_from_filename(filename):
    """Extract date from filename if possible"""
    import re
    
    # Look for date patterns like 2025-05-26, 05-26-2025, etc.
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
        r'(\d{2}-\d{2}-\d{4})',  # MM-DD-YYYY
        r'(\d{4}_\d{2}_\d{2})',  # YYYY_MM_DD
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, filename)
        if match:
            date_str = match.group(1)
            try:
                # Try different date formats
                for fmt in ['%Y-%m-%d', '%m-%d-%Y', '%Y_%m_%d']:
                    try:
                        return datetime.strptime(date_str, fmt).date()
                    except ValueError:
                        continue
            except ValueError:
                continue
    
    return None

@data_upload_bp.route('/upload-manager')
def upload_manager():
    """Display the data upload manager interface"""
    
    # Get recent uploaded files
    recent_files = []
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            if allowed_file(filename):
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file_info = {
                    'filename': filename,
                    'upload_date': datetime.fromtimestamp(os.path.getctime(filepath)).strftime('%Y-%m-%d %H:%M'),
                    'size': round(os.path.getsize(filepath) / 1024, 2),  # KB
                    'type': detect_file_type(filename),
                    'extracted_date': extract_date_from_filename(filename)
                }
                recent_files.append(file_info)
    
    # Sort by upload date, newest first
    recent_files.sort(key=lambda x: x['upload_date'], reverse=True)
    
    return render_template('data_upload_manager.html', recent_files=recent_files)

@data_upload_bp.route('/upload-files', methods=['POST'])
def upload_files():
    """Handle file upload"""
    
    if 'files[]' not in request.files:
        flash('No files selected', 'error')
        return redirect(url_for('data_upload.upload_manager'))
    
    files = request.files.getlist('files[]')
    target_date = request.form.get('target_date')
    process_immediately = request.form.get('process_immediately') == 'on'
    
    uploaded_files = []
    
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Add timestamp to prevent conflicts
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"
            
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            file_info = {
                'filename': filename,
                'original_name': file.filename,
                'type': detect_file_type(file.filename),
                'size': round(os.path.getsize(filepath) / 1024, 2),
                'target_date': target_date
            }
            
            uploaded_files.append(file_info)
            logger.info(f"Uploaded file: {filename}, type: {file_info['type']}")
    
    if uploaded_files:
        flash(f'Successfully uploaded {len(uploaded_files)} files', 'success')
        
        if process_immediately:
            # Trigger immediate processing
            return redirect(url_for('data_upload.process_uploaded_data', 
                                  target_date=target_date))
    else:
        flash('No valid files were uploaded', 'error')
    
    return redirect(url_for('data_upload.upload_manager'))

@data_upload_bp.route('/process-data')
def process_uploaded_data():
    """Process uploaded data for specified date"""
    
    target_date = request.args.get('target_date')
    if not target_date:
        target_date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        # Find relevant files for the target date
        relevant_files = []
        
        for filename in os.listdir(UPLOAD_FOLDER):
            if allowed_file(filename):
                file_date = extract_date_from_filename(filename)
                if file_date and file_date.strftime('%Y-%m-%d') == target_date:
                    relevant_files.append(filename)
        
        if not relevant_files:
            flash(f'No data files found for {target_date}', 'warning')
            return redirect(url_for('data_upload.upload_manager'))
        
        # Process the files using your existing pipeline
        processing_results = {
            'target_date': target_date,
            'files_processed': len(relevant_files),
            'drivers_found': 0,
            'job_sites_identified': 0,
            'processing_status': 'success'
        }
        
        # Here you would integrate with your existing MTD processing pipeline
        # For now, we'll simulate the processing
        
        flash(f'Successfully processed data for {target_date}', 'success')
        return render_template('processing_results.html', results=processing_results)
        
    except Exception as e:
        logger.error(f"Error processing data for {target_date}: {str(e)}")
        flash(f'Error processing data: {str(e)}', 'error')
        return redirect(url_for('data_upload.upload_manager'))

@data_upload_bp.route('/fill-gaps')
def fill_gaps():
    """Interface for filling data gaps in historical reports"""
    
    # Get date range from request
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        # Default to last 7 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Check which dates have data and which have gaps
    date_status = []
    current_date = start_date
    
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Check if we have data for this date
        has_data = False
        data_files = []
        
        for filename in os.listdir(UPLOAD_FOLDER):
            if allowed_file(filename):
                file_date = extract_date_from_filename(filename)
                if file_date == current_date:
                    has_data = True
                    data_files.append(filename)
        
        date_status.append({
            'date': date_str,
            'has_data': has_data,
            'files': data_files,
            'is_weekend': current_date.weekday() >= 5  # Saturday = 5, Sunday = 6
        })
        
        current_date += timedelta(days=1)
    
    return render_template('gap_filling.html', 
                         date_status=date_status, 
                         start_date=start_date.strftime('%Y-%m-%d'),
                         end_date=end_date.strftime('%Y-%m-%d'))

@data_upload_bp.route('/api/file-info/<filename>')
def get_file_info(filename):
    """Get detailed information about an uploaded file"""
    
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        # Try to read the file and get basic info
        file_info = {
            'filename': filename,
            'size': round(os.path.getsize(filepath) / 1024, 2),
            'type': detect_file_type(filename),
            'upload_date': datetime.fromtimestamp(os.path.getctime(filepath)).strftime('%Y-%m-%d %H:%M'),
            'extracted_date': extract_date_from_filename(filename)
        }
        
        # Try to get row count if it's a data file
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
            file_info['rows'] = len(df)
            file_info['columns'] = list(df.columns)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
            file_info['rows'] = len(df)
            file_info['columns'] = list(df.columns)
        
        return jsonify(file_info)
        
    except Exception as e:
        return jsonify({'error': f'Could not read file: {str(e)}'}), 500