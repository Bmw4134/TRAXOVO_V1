"""
TRAXORA | File Upload Routes

This module provides routes for the enhanced file upload functionality.
"""
from flask import Blueprint, render_template, request, jsonify, current_app
import logging
import os
from werkzeug.utils import secure_filename
import uuid

# Configure logging
logger = logging.getLogger(__name__)

file_upload_bp = Blueprint('file_upload', __name__, url_prefix='/file-upload')

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    """Check if a file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@file_upload_bp.route('/')
def index():
    """File upload dashboard"""
    return render_template('file_upload/index.html', 
                           api_status='connected',
                           database_status='connected',
                           storage_status='connected')

@file_upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing"""
    try:
        # Check if files were uploaded
        if 'files[]' not in request.files:
            return jsonify({'error': 'No files selected'}), 400
        
        uploaded_files = request.files.getlist('files[]')
        
        # Check if any files were selected
        if not uploaded_files or uploaded_files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        # Process each file
        processed_files = []
        upload_dir = os.path.join(current_app.root_path, 'uploads')
        
        # Create upload directory if it doesn't exist
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        for file in uploaded_files:
            if file and allowed_file(file.filename):
                # Secure the filename and add a timestamp
                filename = secure_filename(file.filename)
                unique_filename = f"{os.path.splitext(filename)[0]}_{uuid.uuid4().hex[:8]}{os.path.splitext(filename)[1]}"
                file_path = os.path.join(upload_dir, unique_filename)
                
                # Save the file
                file.save(file_path)
                
                # Get file category based on name
                file_category = 'Unknown'
                if 'timeonsite' in filename.lower() or 'time_on_site' in filename.lower():
                    file_category = 'TimeOnSite'
                elif 'drivinghistory' in filename.lower() or 'driving_history' in filename.lower():
                    file_category = 'DrivingHistory'
                elif 'activitydetail' in filename.lower() or 'activity_detail' in filename.lower():
                    file_category = 'ActivityDetail'
                elif 'timecard' in filename.lower() or 'time_card' in filename.lower():
                    file_category = 'Timecard'
                
                processed_files.append({
                    'original_name': file.filename,
                    'saved_as': unique_filename,
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'category': file_category
                })
        
        # If no files were successfully processed
        if not processed_files:
            return jsonify({'error': 'No valid files were uploaded'}), 400
        
        # In a real application, we would process the files here
        # For this demo, we'll return success with sample processing results
        
        # Simulate processing
        total_records = sum([50 + i*10 for i in range(len(processed_files))])
        on_time_count = int(total_records * 0.7)  # 70% on time
        late_count = int(total_records * 0.2)     # 20% late
        absence_count = total_records - on_time_count - late_count  # 10% absent
        
        # Build response with report URLs
        report_url = '/file-upload/report/' + uuid.uuid4().hex[:8]
        csv_url = '/file-upload/download/' + uuid.uuid4().hex[:8] + '.csv'
        
        response = {
            'message': f'Successfully processed {len(processed_files)} files',
            'files': processed_files,
            'total_records': total_records,
            'on_time_count': on_time_count,
            'late_count': late_count,
            'absence_count': absence_count,
            'report_url': report_url,
            'csv_url': csv_url
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error during file upload: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@file_upload_bp.route('/report/<report_id>')
def view_report(report_id):
    """View a generated report"""
    # In a real application, we would retrieve the report from a database
    # For this demo, we'll just return a placeholder page
    return render_template('file_upload/report.html', 
                           report_id=report_id,
                           api_status='connected',
                           database_status='connected',
                           storage_status='connected')

@file_upload_bp.route('/download/<filename>')
def download_file(filename):
    """Download a generated file"""
    # In a real application, we would retrieve the file from storage
    # For this demo, we'll just return a placeholder response
    return jsonify({'message': f'Download {filename} not implemented yet'}), 501