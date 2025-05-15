"""
Parser Blueprint Module

This module handles file upload, processing, and management for various file formats.
"""
import os
import json
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for, send_file
from flask_login import login_required, current_user

# Import utility functions and classes
from utils.file_processor import process_file, allowed_file, get_processing_history
from utils.cya import log_event, backup_file, get_file_versions, ensure_directories

# Create blueprint
parser_bp = Blueprint('parser', __name__, url_prefix='/parser')

# Set up logging
logger = logging.getLogger(__name__)

# Create necessary directories
ensure_directories([
    'uploads',
    'backups',
    'data/processed',
    'data/reports'
])

@parser_bp.route('/')
@login_required
def index():
    """Render the main file management interface."""
    # Get processing history
    processing_history = get_processing_history(limit=25)
    
    # Get upload statistics
    stats = {
        'fringe': sum(1 for item in processing_history if item.get('file_type') == 'fringe'),
        'billing': sum(1 for item in processing_history if item.get('file_type') == 'billing'),
        'maintenance': sum(1 for item in processing_history if item.get('file_type') == 'maintenance'),
        'activity': sum(1 for item in processing_history if item.get('file_type') == 'activity'),
        'other': sum(1 for item in processing_history if item.get('file_type') not in ['fringe', 'billing', 'maintenance', 'activity'])
    }
    
    return render_template('parsers/index.html', 
                          processing_history=processing_history, 
                          stats=stats)

@parser_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Handle file upload and processing."""
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part in the request', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user submits an empty form
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        # Check if the file is allowed
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join('uploads', filename)
            
            # Save the file
            file.save(file_path)
            
            # Get file type from form or auto-detect
            file_type = request.form.get('file_type', 'auto')
            
            # Process options
            options = {
                'create_backup': 'create_backup' in request.form,
                'audit_trail': 'audit_trail' in request.form,
                'deep_analysis': 'deep_analysis' in request.form,
                'reconcile_mode': 'reconcile_mode' in request.form
            }
            
            # Process the file
            result = process_file(file_path, file_type, current_user.id)
            
            if result['success']:
                # Log event
                log_event('file_upload', {
                    'filename': filename,
                    'file_type': file_type,
                    'file_path': file_path,
                    'user_id': current_user.id,
                    'success': True,
                    'options': options
                })
                
                # Create backup if requested
                if options['create_backup']:
                    backup_path = backup_file(file_path)
                    result['details']['backup_path'] = backup_path
                
                flash(f'File {filename} uploaded and processed successfully', 'success')
                
                # If AJAX request, return JSON
                if request.is_xhr or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': True,
                        'message': f'File {filename} uploaded and processed successfully',
                        'redirect_url': url_for('parser.result', file_path=file_path)
                    })
                
                # Otherwise, redirect to result page
                return redirect(url_for('parser.result', file_path=file_path))
            else:
                # Log event
                log_event('file_upload', {
                    'filename': filename,
                    'file_type': file_type,
                    'file_path': file_path,
                    'user_id': current_user.id,
                    'success': False,
                    'error': result['message']
                })
                
                flash(f'Error processing file: {result["message"]}', 'danger')
                
                # If AJAX request, return JSON
                if request.is_xhr or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'message': f'Error processing file: {result["message"]}'
                    })
                
                return redirect(request.url)
        else:
            flash(f'File type not allowed. Please upload one of the allowed file types.', 'danger')
            return redirect(request.url)
    
    # Handle GET request
    recent_files = get_processing_history(limit=5)
    return render_template('parsers/upload.html', recent_files=recent_files)

@parser_bp.route('/result')
@login_required
def result():
    """Display file processing results."""
    file_path = request.args.get('file_path')
    
    if not file_path or not os.path.exists(file_path):
        flash('File not found', 'danger')
        return redirect(url_for('parser.index'))
    
    # Get metadata from processing history
    history = get_processing_history()
    metadata = next((item for item in history if item.get('file_path') == file_path), None)
    
    if not metadata:
        flash('Processing metadata not found', 'warning')
        metadata = {
            'success': False,
            'message': 'Metadata not found for this file',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'details': {}
        }
    
    filename = os.path.basename(file_path)
    
    return render_template('parsers/result.html', 
                          file_path=file_path,
                          filename=filename,
                          metadata=metadata)

@parser_bp.route('/compare', methods=['GET'])
@login_required
def compare():
    """Render the file comparison interface."""
    # Get recent files for comparison
    recent_files = get_processing_history(limit=15)
    
    # Get backup files
    backup_files = get_file_versions()
    
    return render_template('parsers/compare.html', 
                          recent_files=recent_files,
                          backup_files=backup_files)

@parser_bp.route('/compare_result', methods=['POST'])
@login_required
def compare_result():
    """Process and display file comparison results."""
    # Get the files to compare
    file1_type = request.form.get('file1_type')
    file2_type = request.form.get('file2_type')
    
    # Get file 1 path based on type
    if file1_type == 'recent':
        file1_path = request.form.get('file1_recent')
    elif file1_type == 'upload':
        # Handle file upload
        if 'file1_upload' not in request.files:
            flash('No file part in the request', 'danger')
            return redirect(url_for('parser.compare'))
        
        file = request.files['file1_upload']
        if file.filename == '':
            flash('No file selected for comparison (File 1)', 'danger')
            return redirect(url_for('parser.compare'))
        
        if not allowed_file(file.filename):
            flash('File type not allowed for comparison (File 1)', 'danger')
            return redirect(url_for('parser.compare'))
            
        filename = secure_filename(file.filename)
        file1_path = os.path.join('uploads', 'temp_comparison_1_' + filename)
        file.save(file1_path)
    elif file1_type == 'backup':
        file1_path = request.form.get('file1_backup_file')
    else:
        flash('Invalid file type selection for File 1', 'danger')
        return redirect(url_for('parser.compare'))
    
    # Get file 2 path based on type
    if file2_type == 'recent':
        file2_path = request.form.get('file2_recent')
    elif file2_type == 'upload':
        # Handle file upload
        if 'file2_upload' not in request.files:
            flash('No file part in the request', 'danger')
            return redirect(url_for('parser.compare'))
        
        file = request.files['file2_upload']
        if file.filename == '':
            flash('No file selected for comparison (File 2)', 'danger')
            return redirect(url_for('parser.compare'))
        
        if not allowed_file(file.filename):
            flash('File type not allowed for comparison (File 2)', 'danger')
            return redirect(url_for('parser.compare'))
            
        filename = secure_filename(file.filename)
        file2_path = os.path.join('uploads', 'temp_comparison_2_' + filename)
        file.save(file2_path)
    elif file2_type == 'backup':
        file2_path = request.form.get('file2_backup_file')
    else:
        flash('Invalid file type selection for File 2', 'danger')
        return redirect(url_for('parser.compare'))
    
    # Get comparison options
    options = {
        'ignore_whitespace': 'ignore_whitespace' in request.form,
        'ignore_case': 'ignore_case' in request.form,
        'smart_match': 'smart_match' in request.form,
        'generate_report': 'generate_report' in request.form,
        'reconcile_changes': 'reconcile_changes' in request.form,
        'highlight_changes': 'highlight_changes' in request.form
    }
    
    # Compare files
    from utils.file_comparison import compare_files
    comparison_result = compare_files(file1_path, file2_path, options)
    
    # Log event
    log_event('file_comparison', {
        'file1_path': file1_path,
        'file2_path': file2_path,
        'user_id': current_user.id,
        'options': options,
        'success': comparison_result['success']
    })
    
    if comparison_result['success']:
        flash('Files compared successfully', 'success')
        
        # Save comparison result for viewing
        result_id = datetime.now().strftime('%Y%m%d%H%M%S')
        result_path = os.path.join('data', 'processed', f'comparison_{result_id}.json')
        
        with open(result_path, 'w') as f:
            json.dump(comparison_result, f)
        
        return redirect(url_for('parser.view_comparison', result_id=result_id))
    else:
        flash(f'Error comparing files: {comparison_result["message"]}', 'danger')
        return redirect(url_for('parser.compare'))

@parser_bp.route('/view_comparison/<result_id>')
@login_required
def view_comparison(result_id):
    """View comparison results."""
    result_path = os.path.join('data', 'processed', f'comparison_{result_id}.json')
    
    if not os.path.exists(result_path):
        flash('Comparison result not found', 'danger')
        return redirect(url_for('parser.compare'))
    
    with open(result_path, 'r') as f:
        comparison_result = json.load(f)
    
    return render_template('parsers/comparison_result.html', 
                          result=comparison_result,
                          result_id=result_id)

@parser_bp.route('/reprocess', methods=['POST'])
@login_required
def reprocess():
    """Reprocess a file."""
    file_path = request.args.get('file_path')
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({
            'success': False,
            'message': 'File not found'
        })
    
    # Get file type from history
    history = get_processing_history()
    metadata = next((item for item in history if item.get('file_path') == file_path), None)
    
    file_type = metadata.get('file_type', 'auto') if metadata else 'auto'
    
    # Reprocess file
    result = process_file(file_path, file_type, current_user.id)
    
    # Log event
    log_event('file_reprocess', {
        'file_path': file_path,
        'file_type': file_type,
        'user_id': current_user.id,
        'success': result['success']
    })
    
    if result['success']:
        return jsonify({
            'success': True,
            'message': 'File reprocessed successfully',
            'redirect_url': url_for('parser.result', file_path=file_path)
        })
    else:
        return jsonify({
            'success': False,
            'message': f'Error reprocessing file: {result["message"]}'
        })

@parser_bp.route('/download/<path:file_path>')
@login_required
def download_file(file_path):
    """Download a file."""
    # Prevent directory traversal
    if '..' in file_path:
        flash('Invalid file path', 'danger')
        return redirect(url_for('parser.index'))
    
    if not os.path.exists(file_path):
        flash('File not found', 'danger')
        return redirect(url_for('parser.index'))
    
    # Log event
    log_event('file_download', {
        'file_path': file_path,
        'user_id': current_user.id
    })
    
    return send_file(file_path, as_attachment=True)