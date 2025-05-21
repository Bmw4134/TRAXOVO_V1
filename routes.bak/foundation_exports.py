"""
Foundation Exports Routes

This module provides routes for generating and downloading foundation export files
based on the master EQ billing data.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename

from flask import (
    Blueprint, render_template, request, flash, redirect,
    url_for, send_from_directory, jsonify, session
)
from flask_login import login_required

from utils.foundation_exports import generate_foundation_imports, FoundationExportException

logger = logging.getLogger(__name__)

# Create blueprint
foundation_bp = Blueprint('foundation', __name__, url_prefix='/foundation')

# File paths
UPLOADS_DIR = Path('./uploads')
UPLOADS_DIR.mkdir(exist_ok=True)

EXPORTS_DIR = Path('./exports')
EXPORTS_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    """Check if a file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@foundation_bp.route('/', methods=['GET'])
@login_required
def index():
    """Foundation exports main page"""
    # Get list of recent exports
    recent_exports = []
    try:
        for export_file in sorted(EXPORTS_DIR.glob('Foundation_Imports_*.zip'), 
                                key=lambda x: os.path.getmtime(x), 
                                reverse=True)[:10]:
            recent_exports.append({
                'name': export_file.name,
                'date': datetime.fromtimestamp(os.path.getmtime(export_file)).strftime('%Y-%m-%d %H:%M:%S'),
                'size': os.path.getsize(export_file),  # Size in bytes
                'path': str(export_file.relative_to(EXPORTS_DIR))
            })
    except Exception as e:
        logger.error(f"Error getting recent exports: {e}")
    
    # Check for recently processed PM Master file
    has_pm_master = False
    pm_master_file = None
    try:
        pm_master_files = sorted(EXPORTS_DIR.glob('pm_master_*.xlsx'), 
                              key=lambda x: os.path.getmtime(x), 
                              reverse=True)
        if pm_master_files:
            has_pm_master = True
            pm_master_file = pm_master_files[0]
    except Exception as e:
        logger.error(f"Error checking for PM Master files: {e}")
    
    return render_template(
        'foundation_exports.html',
        recent_exports=recent_exports,
        has_pm_master=has_pm_master,
        pm_master_file=pm_master_file.name if pm_master_file else None
    )


@foundation_bp.route('/generate', methods=['POST'])
@login_required
def generate_exports():
    """Generate foundation exports from an EQ billing file"""
    try:
        # Check if file was uploaded
        if 'eq_billing_file' not in request.files:
            flash("No file uploaded", "danger")
            return redirect(url_for('foundation.index'))
        
        file = request.files['eq_billing_file']
        
        # Check if file was selected
        if file.filename == '':
            flash("No file selected", "danger")
            return redirect(url_for('foundation.index'))
        
        # Check file extension
        if not allowed_file(file.filename):
            flash(f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}", "danger")
            return redirect(url_for('foundation.index'))
        
        # Get month/year
        month_year = request.form.get('month_year', datetime.now().strftime("%B %Y"))
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        file_path = UPLOADS_DIR / unique_filename
        file.save(file_path)
        
        # Generate foundation exports
        try:
            result = generate_foundation_imports(file_path, month_year=month_year)
            
            # Store result in session
            session['foundation_result'] = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'zip_file': result.get('zip_file'),
                'zip_filename': os.path.basename(result.get('zip_file', '')),
                'month_year': result.get('month_year'),
                'export_files': result.get('export_files', [])
            }
            
            flash(f"Successfully generated foundation exports for {month_year}", "success")
            return redirect(url_for('foundation.result'))
            
        except FoundationExportException as e:
            flash(f"Error generating foundation exports: {str(e)}", "danger")
            if file_path.exists():
                os.remove(file_path)
            return redirect(url_for('foundation.index'))
        
    except Exception as e:
        logger.error(f"Error processing foundation exports: {str(e)}")
        flash(f"Error processing foundation exports: {str(e)}", "danger")
        return redirect(url_for('foundation.index'))


@foundation_bp.route('/result', methods=['GET'])
@login_required
def result():
    """Display the result of foundation export generation"""
    # Get the result from session
    foundation_result = session.get('foundation_result')
    if not foundation_result:
        flash("No foundation export result found", "warning")
        return redirect(url_for('foundation.index'))
    
    return render_template(
        'foundation_result.html',
        result=foundation_result
    )


@foundation_bp.route('/download/<path:filename>', methods=['GET'])
@login_required
def download_file(filename):
    """Download a generated file"""
    try:
        # Validate the filename to prevent path traversal
        file_path = EXPORTS_DIR / filename
        if not file_path.exists() or not file_path.is_file():
            flash("File not found", "danger")
            return redirect(url_for('foundation.index'))
        
        return send_from_directory(
            directory=EXPORTS_DIR,
            path=filename,
            as_attachment=True
        )
        
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        flash(f"Error downloading file: {str(e)}", "danger")
        return redirect(url_for('foundation.index'))


@foundation_bp.route('/generate-from-master', methods=['POST'])
@login_required
def generate_from_master():
    """Generate foundation exports from the latest PM Master file"""
    try:
        # Get the latest PM Master file
        pm_master_files = sorted(EXPORTS_DIR.glob('pm_master_*.xlsx'), 
                             key=lambda x: os.path.getmtime(x), 
                             reverse=True)
        
        if not pm_master_files:
            flash("No PM Master files found. Process your April allocation files first.", "danger")
            return redirect(url_for('foundation.index'))
        
        latest_master = pm_master_files[0]
        
        # Get month/year
        month_year = request.form.get('month_year', datetime.now().strftime("%B %Y"))
        
        # Get export format
        export_format = request.form.get('export_format', 'both')
        
        # Generate exports from the latest master file
        try:
            result = generate_foundation_imports(latest_master, month_year=month_year)
            
            # Store result in session
            session['foundation_result'] = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'zip_file': result.get('zip_file'),
                'zip_filename': os.path.basename(result.get('zip_file', '')),
                'month_year': result.get('month_year'),
                'export_files': result.get('export_files', []),
                'source_file': latest_master.name,
                'format': export_format
            }
            
            flash(f"Successfully generated Foundation exports for {month_year} from {latest_master.name}", "success")
            return redirect(url_for('foundation.export_result'))
            
        except FoundationExportException as e:
            flash(f"Error generating Foundation exports: {str(e)}", "danger")
            return redirect(url_for('foundation.index'))
        
    except Exception as e:
        logger.error(f"Error processing Foundation exports from PM Master: {str(e)}")
        flash(f"Error processing Foundation exports: {str(e)}", "danger")
        return redirect(url_for('foundation.index'))


@foundation_bp.route('/export-result', methods=['GET'])
@login_required
def export_result():
    """Show the results of foundation exports generation"""
    if 'foundation_result' not in session:
        flash("No recent export results found", "warning")
        return redirect(url_for('foundation.index'))
    
    result = session['foundation_result']
    
    return render_template('foundation_exports_result.html', result=result)