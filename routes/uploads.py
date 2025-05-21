"""
File Upload Routes

This module handles file upload routes for activity detail, work zone hours,
equipment billing worksheets, and asset-driver mapping files.
"""
import os
from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, current_app, jsonify
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from models.reports import FileUpload
from utils.file_processor import (
    save_uploaded_file, process_uploaded_file, allowed_file
)

# Create blueprint
uploads_bp = Blueprint('uploads', __name__)

@uploads_bp.route('/upload', methods=['GET'])
@login_required
def upload_form():
    """Display file upload form"""
    # Get recent uploads for display
    recent_uploads = FileUpload.query.order_by(FileUpload.uploaded_at.desc()).limit(10).all()
    
    return render_template(
        'uploads/upload.html',
        recent_uploads=recent_uploads
    )

@uploads_bp.route('/upload/activity', methods=['POST'])
@login_required
def upload_activity():
    """Handle activity detail file upload"""
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        file_upload = save_uploaded_file(
            file=file,
            file_type='activity',
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        if file_upload:
            flash(f'Activity file "{file_upload.original_filename}" uploaded successfully!', 'success')
            
            # Process the file immediately
            success, message, records = process_uploaded_file(file_upload.id)
            if success:
                flash(f'Successfully processed {records} records.', 'success')
            else:
                flash(f'Error processing file: {message}', 'error')
        else:
            flash('Error saving file', 'error')
    else:
        flash(f'File type not allowed. Please upload CSV, JSON, XLSX or XLS files.', 'error')
    
    return redirect(url_for('uploads.upload_form'))

@uploads_bp.route('/upload/workzone', methods=['POST'])
@login_required
def upload_workzone():
    """Handle work zone hours file upload"""
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        file_upload = save_uploaded_file(
            file=file,
            file_type='workzone',
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        if file_upload:
            flash(f'Work Zone file "{file_upload.original_filename}" uploaded successfully!', 'success')
            
            # Process the file immediately
            success, message, records = process_uploaded_file(file_upload.id)
            if success:
                flash(f'Successfully processed {records} records.', 'success')
            else:
                flash(f'Error processing file: {message}', 'error')
        else:
            flash('Error saving file', 'error')
    else:
        flash(f'File type not allowed. Please upload CSV, JSON, XLSX or XLS files.', 'error')
    
    return redirect(url_for('uploads.upload_form'))

@uploads_bp.route('/upload/billing', methods=['POST'])
@login_required
def upload_billing():
    """Handle equipment billing file upload"""
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        file_upload = save_uploaded_file(
            file=file,
            file_type='billing',
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        if file_upload:
            flash(f'Billing file "{file_upload.original_filename}" uploaded successfully!', 'success')
            
            # Process the file immediately
            success, message, records = process_uploaded_file(file_upload.id)
            if success:
                flash(f'Successfully processed {records} records.', 'success')
            else:
                flash(f'Error processing file: {message}', 'error')
        else:
            flash('Error saving file', 'error')
    else:
        flash(f'File type not allowed. Please upload CSV, JSON, XLSX or XLS files.', 'error')
    
    return redirect(url_for('uploads.upload_form'))

@uploads_bp.route('/upload/mapping', methods=['POST'])
@login_required
def upload_mapping():
    """Handle asset-driver mapping file upload"""
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        file_upload = save_uploaded_file(
            file=file,
            file_type='mapping',
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        if file_upload:
            flash(f'Mapping file "{file_upload.original_filename}" uploaded successfully!', 'success')
            
            # Process the file immediately
            success, message, records = process_uploaded_file(file_upload.id)
            if success:
                flash(f'Successfully processed {records} records.', 'success')
            else:
                flash(f'Error processing file: {message}', 'error')
        else:
            flash('Error saving file', 'error')
    else:
        flash(f'File type not allowed. Please upload CSV, JSON, XLSX or XLS files.', 'error')
    
    return redirect(url_for('uploads.upload_form'))

@uploads_bp.route('/uploads/<int:upload_id>/process', methods=['POST'])
@login_required
def process_upload(upload_id):
    """Process a previously uploaded file"""
    file_upload = FileUpload.query.get_or_404(upload_id)
    
    success, message, records = process_uploaded_file(file_upload.id)
    if success:
        flash(f'Successfully processed {records} records.', 'success')
    else:
        flash(f'Error processing file: {message}', 'error')
    
    return redirect(url_for('uploads.upload_form'))

@uploads_bp.route('/uploads/<int:upload_id>/delete', methods=['POST'])
@login_required
def delete_upload(upload_id):
    """Delete an uploaded file"""
    file_upload = FileUpload.query.get_or_404(upload_id)
    
    # Delete the file if it exists
    filepath = os.path.join('uploads', file_upload.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Delete database record
    db.session.delete(file_upload)
    db.session.commit()
    
    flash(f'File "{file_upload.original_filename}" deleted successfully.', 'success')
    return redirect(url_for('uploads.upload_form'))
@uploads_bp.route('/upload')
def upload():
    """Handler for /upload"""
    try:
        # Add your route handler logic here
        return render_template('uploads/upload.html')
    except Exception as e:
        logger.error(f"Error in upload: {e}")
        return render_template('error.html', error=str(e)), 500

@uploads_bp.route('/upload/activity')
def upload_activity():
    """Handler for /upload/activity"""
    try:
        # Add your route handler logic here
        return render_template('uploads/upload_activity.html')
    except Exception as e:
        logger.error(f"Error in upload_activity: {e}")
        return render_template('error.html', error=str(e)), 500

@uploads_bp.route('/upload/workzone')
def upload_workzone():
    """Handler for /upload/workzone"""
    try:
        # Add your route handler logic here
        return render_template('uploads/upload_workzone.html')
    except Exception as e:
        logger.error(f"Error in upload_workzone: {e}")
        return render_template('error.html', error=str(e)), 500

@uploads_bp.route('/upload/billing')
def upload_billing():
    """Handler for /upload/billing"""
    try:
        # Add your route handler logic here
        return render_template('uploads/upload_billing.html')
    except Exception as e:
        logger.error(f"Error in upload_billing: {e}")
        return render_template('error.html', error=str(e)), 500

@uploads_bp.route('/upload/mapping')
def upload_mapping():
    """Handler for /upload/mapping"""
    try:
        # Add your route handler logic here
        return render_template('uploads/upload_mapping.html')
    except Exception as e:
        logger.error(f"Error in upload_mapping: {e}")
        return render_template('error.html', error=str(e)), 500

@uploads_bp.route('/uploads/<int:upload_id>/process')
def uploads_<int:upload_id>_process():
    """Handler for /uploads/<int:upload_id>/process"""
    try:
        # Add your route handler logic here
        return render_template('uploads/uploads_<int:upload_id>_process.html')
    except Exception as e:
        logger.error(f"Error in uploads_<int:upload_id>_process: {e}")
        return render_template('error.html', error=str(e)), 500

@uploads_bp.route('/uploads/<int:upload_id>/delete')
def uploads_<int:upload_id>_delete():
    """Handler for /uploads/<int:upload_id>/delete"""
    try:
        # Add your route handler logic here
        return render_template('uploads/uploads_<int:upload_id>_delete.html')
    except Exception as e:
        logger.error(f"Error in uploads_<int:upload_id>_delete: {e}")
        return render_template('error.html', error=str(e)), 500
