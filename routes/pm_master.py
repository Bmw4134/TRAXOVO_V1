"""
PM Master Billing Processor Routes

This module provides routes for the enhanced PM billing module that allows users to upload
an original PM sheet, feed in additional PM sheets, and generate a master completed output.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename

from flask import (
    Blueprint, render_template, request, flash, redirect,
    url_for, send_from_directory, jsonify, session, current_app
)
from flask_login import login_required

from utils.pm_master_processor import PMMasterProcessor, PMProcessingException

logger = logging.getLogger(__name__)

# Create blueprint
pm_master_bp = Blueprint('pm_master', __name__, url_prefix='/pm-master')

# File paths
UPLOADS_DIR = Path('./uploads')
UPLOADS_DIR.mkdir(exist_ok=True)

EXPORTS_DIR = Path('./exports')
EXPORTS_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    """Check if a file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@pm_master_bp.route('/', methods=['GET'])
@login_required
def index():
    """PM Master Billing main page"""
    # Get list of recent exports
    recent_exports = []
    try:
        for export_file in sorted(EXPORTS_DIR.glob('pm_master_*.xlsx'), 
                                key=lambda x: os.path.getmtime(x), 
                                reverse=True)[:10]:
            file_size = os.path.getsize(export_file)
            if file_size > 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.2f} MB"
            else:
                size_str = f"{file_size / 1024:.2f} KB"
                
            recent_exports.append({
                'name': export_file.name,
                'date': datetime.fromtimestamp(os.path.getmtime(export_file)).strftime('%Y-%m-%d %H:%M:%S'),
                'size': size_str,
                'path': str(export_file.relative_to(EXPORTS_DIR))
            })
    except Exception as e:
        logger.error(f"Error getting recent exports: {e}")
    
    # Get April 2025 allocation files
    april_files = []
    try:
        attached_dir = Path('./attached_assets')
        for file in attached_dir.glob('*.xlsx'):
            if 'EQMO' in file.name and 'BILLING ALLOCATIONS' in file.name and 'APRIL 2025' in file.name:
                file_size = os.path.getsize(file)
                if file_size > 1024 * 1024:
                    size_str = f"{file_size / (1024 * 1024):.2f} MB"
                else:
                    size_str = f"{file_size / 1024:.2f} KB"
                
                # Extract job code if available
                job_code = "Unknown"
                for part in file.name.split():
                    if part.startswith('202') and '-' in part:
                        job_code = part
                        break
                
                april_files.append({
                    'name': file.name,
                    'job_code': job_code,
                    'date': datetime.fromtimestamp(os.path.getmtime(file)).strftime('%Y-%m-%d %H:%M'),
                    'size': size_str,
                    'path': str(file.name)
                })
        
        # Sort files by job code
        april_files.sort(key=lambda x: x['job_code'])
    except Exception as e:
        logger.error(f"Error getting April files: {e}")
    
    # Check if there's a session state
    session_processor = session.get('pm_master_processor', {})
    processor_status = {
        'initialized': False,
        'files_processed': 0,
        'latest_file': None,
        'has_changes': False
    }
    
    if session_processor:
        processor_status['initialized'] = True
        processor_status['files_processed'] = session_processor.get('files_processed', 0)
        processor_status['latest_file'] = session_processor.get('latest_file')
        processor_status['has_changes'] = session_processor.get('has_changes', False)
    
    return render_template(
        'pm_master.html',
        recent_exports=recent_exports,
        april_files=april_files,
        april_file_count=len(april_files),
        processor_status=processor_status
    )


@pm_master_bp.route('/init', methods=['POST'])
@login_required
def init_processor():
    """Initialize the PM Master processor with an original file"""
    try:
        # Check if file was uploaded
        if 'original_file' not in request.files:
            flash("No file uploaded", "danger")
            return redirect(url_for('pm_master.index'))
        
        file = request.files['original_file']
        
        # Check if file was selected
        if file.filename == '':
            flash("No file selected", "danger")
            return redirect(url_for('pm_master.index'))
        
        # Check file extension
        if not allowed_file(file.filename):
            flash(f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}", "danger")
            return redirect(url_for('pm_master.index'))
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        file_path = UPLOADS_DIR / unique_filename
        file.save(file_path)
        
        # Initialize the processor
        try:
            processor = PMMasterProcessor(original_file=file_path)
            
            # Store in session that we've initialized
            session['pm_master_processor'] = {
                'original_file': str(file_path),
                'files_processed': 1,
                'latest_file': filename,
                'processed_files': [str(file_path)],
                'has_changes': False
            }
            
            flash(f"Successfully initialized PM Master with {filename}", "success")
            
        except PMProcessingException as e:
            flash(f"Error processing file: {str(e)}", "danger")
            if file_path.exists():
                os.remove(file_path)
            return redirect(url_for('pm_master.index'))
        
        return redirect(url_for('pm_master.index'))
        
    except Exception as e:
        logger.error(f"Error initializing PM Master processor: {str(e)}")
        flash(f"Error initializing processor: {str(e)}", "danger")
        return redirect(url_for('pm_master.index'))


@pm_master_bp.route('/add-file', methods=['POST'])
@login_required
def add_file():
    """Add a PM file to the master processor"""
    try:
        # Check if processor is initialized
        session_processor = session.get('pm_master_processor')
        if not session_processor:
            flash("PM Master not initialized. Please upload an original file first", "danger")
            return redirect(url_for('pm_master.index'))
        
        # Check if file was uploaded
        if 'pm_file' not in request.files:
            flash("No file uploaded", "danger")
            return redirect(url_for('pm_master.index'))
        
        file = request.files['pm_file']
        
        # Check if file was selected
        if file.filename == '':
            flash("No file selected", "danger")
            return redirect(url_for('pm_master.index'))
        
        # Check file extension
        if not allowed_file(file.filename):
            flash(f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}", "danger")
            return redirect(url_for('pm_master.index'))
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        file_path = UPLOADS_DIR / unique_filename
        file.save(file_path)
        
        # Get the processor state
        original_file = session_processor.get('original_file')
        processed_files = session_processor.get('processed_files', [])
        
        # Initialize the processor with the original file
        try:
            processor = PMMasterProcessor(original_file=original_file)
            
            # Add all previously processed files
            for prev_file in processed_files[1:]:  # Skip the original file
                processor.add_pm_file(prev_file)
            
            # Add the new file
            result = processor.add_pm_file(file_path)
            
            # Update session state
            session['pm_master_processor'] = {
                'original_file': original_file,
                'files_processed': len(processed_files) + 1,
                'latest_file': filename,
                'processed_files': processed_files + [str(file_path)],
                'has_changes': True,
                'last_result': result
            }
            
            # Display changes summary
            changes = result.get('changes', {})
            flash(
                f"Successfully added {filename}. "
                f"Changes: {changes.get('additions', 0)} additions, "
                f"{changes.get('modifications', 0)} modifications, "
                f"{changes.get('deletions', 0)} deletions", 
                "success"
            )
            
        except PMProcessingException as e:
            flash(f"Error processing file: {str(e)}", "danger")
            if file_path.exists():
                os.remove(file_path)
            return redirect(url_for('pm_master.index'))
        
        return redirect(url_for('pm_master.index'))
        
    except Exception as e:
        logger.error(f"Error adding file to PM Master processor: {str(e)}")
        flash(f"Error adding file: {str(e)}", "danger")
        return redirect(url_for('pm_master.index'))


@pm_master_bp.route('/generate', methods=['POST'])
@login_required
def generate_master():
    """Generate the master output file"""
    try:
        # Check if processor is initialized
        session_processor = session.get('pm_master_processor')
        if not session_processor:
            flash("PM Master not initialized. Please upload an original file first", "danger")
            return redirect(url_for('pm_master.index'))
        
        # Get the processor state
        original_file = session_processor.get('original_file')
        processed_files = session_processor.get('processed_files', [])
        
        # Initialize the processor with the original file
        try:
            processor = PMMasterProcessor(original_file=original_file)
            
            # Add all previously processed files
            for prev_file in processed_files[1:]:  # Skip the original file
                processor.add_pm_file(prev_file)
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = EXPORTS_DIR / f"pm_master_{timestamp}.xlsx"
            
            # Generate the master output
            result = processor.generate_master_output(output_path)
            
            if result.get('success'):
                # Get original data metrics
                original_data = processor.get_original_data_metrics()
                
                # Store the result in session
                session['pm_master_result'] = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'output_path': result.get('output_path'),
                    'file_name': output_path.name,
                    'summary': result.get('summary', {}),
                    'original': original_data
                }
                
                # Clear the processor state
                session.pop('pm_master_processor', None)
                
                flash(f"Successfully generated master output {output_path.name}", "success")
                return redirect(url_for('pm_master.result'))
            else:
                flash(f"Error generating master output: {result.get('message')}", "danger")
                return redirect(url_for('pm_master.index'))
            
        except PMProcessingException as e:
            flash(f"Error generating master output: {str(e)}", "danger")
            return redirect(url_for('pm_master.index'))
        
    except Exception as e:
        logger.error(f"Error generating master output: {str(e)}")
        flash(f"Error generating master output: {str(e)}", "danger")
        return redirect(url_for('pm_master.index'))


@pm_master_bp.route('/result', methods=['GET'])
@login_required
def result():
    """Display the result of master output generation"""
    # Get the result from session
    master_result = session.get('pm_master_result')
    if not master_result:
        flash("No PM Master result found", "warning")
        return redirect(url_for('pm_master.index'))
    
    return render_template(
        'pm_master_result.html',
        result=master_result
    )


@pm_master_bp.route('/download/<path:filename>', methods=['GET'])
@login_required
def download_file(filename):
    """Download a generated file"""
    try:
        # Validate the filename to prevent path traversal
        file_path = EXPORTS_DIR / filename
        if not file_path.exists() or not file_path.is_file():
            flash("File not found", "danger")
            return redirect(url_for('pm_master.index'))
        
        return send_from_directory(
            directory=EXPORTS_DIR,
            path=filename,
            as_attachment=True
        )
        
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        flash(f"Error downloading file: {str(e)}", "danger")
        return redirect(url_for('pm_master.index'))


@pm_master_bp.route('/reset', methods=['POST'])
@login_required
def reset():
    """Reset the PM Master processor"""
    # Clear session state
    session.pop('pm_master_processor', None)
    session.pop('pm_master_result', None)
    
    flash("PM Master processor reset", "success")
    return redirect(url_for('pm_master.index'))