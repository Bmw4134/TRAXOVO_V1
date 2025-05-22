"""
TRAXORA | File Processing Route

This module provides routes for the web-based file processing interface,
allowing users to upload CSV/Excel files and see the classification results.
"""
import os
import json
import uuid
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename

from utils.enhanced_data_ingestion import load_data_file
from agents.driver_classifier_agent import handle as classify_drivers

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
file_processor_bp = Blueprint('file_processor', __name__, url_prefix='/process')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@file_processor_bp.route('/', methods=['GET'])
def index():
    """Render the file processing interface"""
    return render_template('file_processor/index.html')

@file_processor_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Handle file upload and processing
    
    This endpoint accepts a file upload, processes it using the enhanced
    data ingestion module, and then runs the driver classifier agent on
    the ingested data.
    """
    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # Check if file was selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check if file has allowed extension
    if not file.filename or not allowed_file(file.filename):
        return jsonify({
            'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename to avoid conflicts
        unique_filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save the uploaded file
        file.save(file_path)
        
        # Step 1: Process the file with enhanced data ingestion
        logger.info(f"Processing file: {file.filename}")
        data = load_data_file(file_path)
        
        if not data:
            logger.warning(f"No data extracted from file: {file.filename}")
            return jsonify({
                'error': 'No valid data could be extracted from the file'
            }), 400
        
        # Step 2: Run driver classification
        logger.info(f"Classifying {len(data)} records")
        result = classify_drivers(data)
        
        # Step 3: Prepare response
        classified_count = len(result.get('classified_drivers', []))
        skipped_count = len(result.get('skipped', []))
        
        # Save results for detailed analysis if needed
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = os.path.join(current_app.root_path, 'results')
        os.makedirs(results_dir, exist_ok=True)
        
        results_file = os.path.join(
            results_dir, 
            f"classification_{timestamp}_{secure_filename(file.filename)}.json"
        )
        
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Return the classification results
        return jsonify({
            'success': True,
            'file': file.filename,
            'records_processed': len(data),
            'classified_count': classified_count,
            'skipped_count': skipped_count,
            'classified_drivers': result.get('classified_drivers', []),
            'skipped_drivers': result.get('skipped', []),
            'metrics': result.get('metrics', {}),
            'results_file': os.path.basename(results_file)
        })
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    finally:
        # Clean up the uploaded file
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Error removing temporary file: {str(e)}")