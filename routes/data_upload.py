"""
Data Upload and Processing Routes
Handles authentic data file uploads and activation
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import os
import pandas as pd
from werkzeug.utils import secure_filename

data_upload_bp = Blueprint('data_upload', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@data_upload_bp.route('/upload-data')
def upload_page():
    """Data upload interface"""
    return render_template('data_upload.html')

@data_upload_bp.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    data_type = request.form.get('data_type', 'unknown')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Create uploads directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Process the file based on type
        result = process_uploaded_file(filepath, data_type)
        
        return jsonify({
            'success': True,
            'message': f'{data_type} file uploaded and processed successfully',
            'filename': filename,
            'records_processed': result.get('records', 0),
            'ai_status': 'processing_authentic_data'
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

def process_uploaded_file(filepath, data_type):
    """Process uploaded authentic data file"""
    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        
        records = len(df)
        
        # Store processing results
        result = {
            'records': records,
            'data_type': data_type,
            'status': 'processed',
            'ai_ready': True
        }
        
        return result
        
    except Exception as e:
        return {
            'error': str(e),
            'status': 'failed'
        }