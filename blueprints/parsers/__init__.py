"""
File Parser Blueprint

This blueprint provides routes for file upload, processing, and management.
"""

from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for, send_file
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import pandas as pd
import json
from flask_login import login_required, current_user

from utils.file_processor import FileProcessor
from utils.cya import log_event

parser_bp = Blueprint('parser', __name__, url_prefix='/parser')

# Configure upload settings
UPLOAD_FOLDER = 'data/uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'xlsm'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@parser_bp.route('/', methods=['GET'])
@login_required
def index():
    """Render the parser dashboard"""
    # Get processing history
    processor = FileProcessor(current_user.id if current_user.is_authenticated else None)
    history = processor.get_processing_history(limit=20)
    
    # Group by file type
    history_by_type = {}
    for entry in history:
        file_type = entry['file_type']
        if file_type not in history_by_type:
            history_by_type[file_type] = []
        history_by_type[file_type].append(entry)
    
    return render_template(
        'parsers/index.html', 
        history=history,
        history_by_type=history_by_type
    )

@parser_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """Handle file uploads"""
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If no file selected
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        # If file is valid
        if file and allowed_file(file.filename):
            # Secure filename
            filename = secure_filename(file.filename)
            
            # Add timestamp to prevent overwriting
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename_parts = filename.rsplit('.', 1)
            filename = f"{filename_parts[0]}_{timestamp}.{filename_parts[1]}"
            
            # Save file
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            # Get file type from form
            file_type = request.form.get('file_type', None)
            
            # Process file
            processor = FileProcessor(current_user.id if current_user.is_authenticated else None)
            result = processor.process_file(file_path, file_type)
            
            # Log event
            log_event(
                'FILE_UPLOAD',
                f"File uploaded and processed: {filename}",
                user_id=current_user.id if current_user.is_authenticated else None,
                data_path=file_path,
                metadata={'result': result}
            )
            
            if result['status'] == 'success':
                flash(f"File '{filename}' processed successfully", 'success')
                # Redirect to processing result
                return redirect(url_for('parser.processing_result', file_name=filename))
            else:
                flash(f"Error processing file: {result['error']}", 'danger')
                return redirect(url_for('parser.index'))
        else:
            flash(f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}", 'danger')
            return redirect(request.url)
    
    return render_template('parsers/upload.html')

@parser_bp.route('/processing-result/<file_name>', methods=['GET'])
@login_required
def processing_result(file_name):
    """Display processing result for a file"""
    processor = FileProcessor(current_user.id if current_user.is_authenticated else None)
    history = processor.get_processing_history(limit=100)
    
    # Find the entry for this file
    result = None
    for entry in history:
        if entry['file_name'] == file_name:
            result = entry
            break
    
    if not result:
        flash(f"Processing result for '{file_name}' not found", 'danger')
        return redirect(url_for('parser.index'))
    
    # If the file was processed successfully, load a preview
    preview_data = None
    if result['status'] == 'SUCCESS' and result['processed_path'] and os.path.exists(result['processed_path']):
        try:
            df = pd.read_csv(result['processed_path'])
            preview_data = {
                'columns': df.columns.tolist(),
                'data': df.head(10).to_dict('records')
            }
        except Exception as e:
            preview_data = {'error': str(e)}
    
    return render_template(
        'parsers/result.html',
        result=result,
        preview=preview_data
    )

@parser_bp.route('/download/<int:file_id>', methods=['GET'])
@login_required
def download_processed_file(file_id):
    """Download a processed file"""
    processor = FileProcessor(current_user.id if current_user.is_authenticated else None)
    
    # Get processing history
    history = processor.get_processing_history(limit=100)
    
    # Find the entry for this file ID
    file_entry = None
    for entry in history:
        if entry['id'] == file_id:
            file_entry = entry
            break
    
    if not file_entry:
        flash(f"File with ID {file_id} not found", 'danger')
        return redirect(url_for('parser.index'))
    
    # Check if processed file exists
    if file_entry['status'] != 'SUCCESS' or not file_entry['processed_path'] or not os.path.exists(file_entry['processed_path']):
        flash(f"Processed file not found", 'danger')
        return redirect(url_for('parser.index'))
    
    # Log download event
    log_event(
        'FILE_DOWNLOAD',
        f"Downloaded processed file: {file_entry['file_name']}",
        user_id=current_user.id if current_user.is_authenticated else None,
        data_path=file_entry['processed_path']
    )
    
    return send_file(
        file_entry['processed_path'],
        as_attachment=True,
        download_name=f"processed_{file_entry['file_name']}.csv"
    )

@parser_bp.route('/reprocess/<int:file_id>', methods=['POST'])
@login_required
def reprocess_file(file_id):
    """Reprocess a previously processed file"""
    processor = FileProcessor(current_user.id if current_user.is_authenticated else None)
    
    result = processor.reprocess_file(file_id)
    
    if result['status'] == 'success':
        flash(f"File reprocessed successfully", 'success')
        return redirect(url_for('parser.processing_result', file_name=result['file_name']))
    else:
        flash(f"Error reprocessing file: {result['error']}", 'danger')
        return redirect(url_for('parser.index'))

@parser_bp.route('/compare', methods=['GET', 'POST'])
@login_required
def compare_files():
    """Compare two processed files"""
    processor = FileProcessor(current_user.id if current_user.is_authenticated else None)
    
    if request.method == 'POST':
        file_id1 = request.form.get('file_id1', type=int)
        file_id2 = request.form.get('file_id2', type=int)
        
        if not file_id1 or not file_id2:
            flash("Please select two files to compare", 'danger')
            return redirect(url_for('parser.compare_files'))
        
        result = processor.compare_files(file_id1, file_id2)
        
        if 'error' in result:
            flash(f"Error comparing files: {result['error']}", 'danger')
            return redirect(url_for('parser.compare_files'))
        
        return render_template(
            'parsers/compare_result.html',
            comparison=result
        )
    
    # Get list of processed files
    history = processor.get_processing_history(status='SUCCESS', limit=100)
    
    return render_template(
        'parsers/compare.html',
        files=history
    )