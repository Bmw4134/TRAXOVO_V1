"""
File Parser Blueprint

This blueprint handles file uploads and parsing operations.
"""

import os
import json
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user

from utils.file_processor import FileProcessor, process_file, allowed_file

# Set up logger
logger = logging.getLogger(__name__)

# Set up blueprint
parser_bp = Blueprint('parser', __name__, url_prefix='/parser')

# Constants
UPLOAD_FOLDER = os.path.join('data', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'json', 'pdf'}

@parser_bp.route('/')
@login_required
def index():
    """
    Render the parser dashboard page
    """
    return render_template('parsers/index.html')

@parser_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """
    Handle file uploads
    """
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Check if a file was selected
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        # Check if the file is allowed
        if file and allowed_file(file.filename):
            # Secure the filename
            filename = secure_filename(file.filename)
            
            # Generate a unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{filename}"
            
            # Save the file
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(file_path)
            
            # Get file type from form
            file_type = request.form.get('file_type')
            
            # Process the file
            result = process_file(file_path, file_type, current_user.get_id())
            
            if result['success']:
                flash(f"File uploaded and processed successfully: {result['message']}", 'success')
                # Redirect to result page with file path parameter
                return redirect(url_for('parser.result', file_path=file_path))
            else:
                flash(f"Error processing file: {result['message']}", 'danger')
                return redirect(url_for('parser.upload'))
        else:
            flash(f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}", 'danger')
            return redirect(request.url)
    
    # GET request
    return render_template('parsers/upload.html', allowed_extensions=ALLOWED_EXTENSIONS)

@parser_bp.route('/result')
@login_required
def result():
    """
    Show the result of file processing
    """
    file_path = request.args.get('file_path')
    if not file_path or not os.path.exists(file_path):
        flash('File not found', 'danger')
        return redirect(url_for('parser.upload'))
    
    # Load processing result from metadata file
    metadata_path = f"{file_path}.meta.json"
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            metadata = {'error': f"Error loading metadata: {str(e)}"}
    else:
        metadata = {'error': 'Metadata file not found'}
    
    return render_template('parsers/result.html', 
                          file_path=file_path, 
                          filename=os.path.basename(file_path),
                          metadata=metadata)

@parser_bp.route('/api/upload', methods=['POST'])
@login_required
def api_upload():
    """
    API endpoint for file uploads
    """
    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['file']
    
    # Check if a file was selected
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
    
    # Check if the file is allowed
    if file and allowed_file(file.filename):
        # Secure the filename
        filename = secure_filename(file.filename)
        
        # Generate a unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        
        # Save the file
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        # Get file type from form
        file_type = request.form.get('file_type')
        
        # Process the file
        result = process_file(file_path, file_type, current_user.get_id())
        
        # Add file path to result
        result['file_path'] = file_path
        
        return jsonify(result)
    else:
        return jsonify({
            'success': False, 
            'message': f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        })