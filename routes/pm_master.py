"""
PM Master Module for batch processing of allocation files

This module handles the batch processing of multiple PM allocation files
and generates consolidated reports and exports.
"""

import os
import logging
import pandas as pd
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file
from flask_login import login_required
from werkzeug.utils import secure_filename

from utils.activity_logger import log_activity
from utils.file_processor import get_file_list_by_pattern, batch_process_allocation_files
from utils.excel_utils import create_consolidated_excel

# Define constants
UPLOADS_FOLDER = os.path.join(os.getcwd(), 'uploads')
EXPORTS_FOLDER = os.path.join(os.getcwd(), 'exports')
ATTACHED_ASSETS_FOLDER = os.path.join(os.getcwd(), 'attached_assets')

# Create blueprint
pm_master_bp = Blueprint('pm_master', __name__, url_prefix='/pm-master')

@pm_master_bp.route('/')
@login_required
def index():
    """PM Master Dashboard Page"""
    # Get all allocation files from the attached_assets folder with EQMO in the name
    allocation_files = get_file_list_by_pattern(
        ATTACHED_ASSETS_FOLDER, 
        pattern="EQMO.*BILLING.*ALLOCATIONS.*\\.xlsx$"
    )
    
    # Sort files by date modified (newest first)
    allocation_files.sort(key=lambda x: os.path.getmtime(os.path.join(ATTACHED_ASSETS_FOLDER, x)), reverse=True)
    
    # Get file details for display
    file_details = []
    for file in allocation_files:
        file_path = os.path.join(ATTACHED_ASSETS_FOLDER, file)
        file_details.append({
            'name': file,
            'size': f"{os.path.getsize(file_path) // 1024}K",
            'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M')
        })
    
    return render_template(
        'pm_master/index.html',
        title='PM Master Billing',
        files=file_details
    )

@pm_master_bp.route('/process', methods=['POST'])
@login_required
def process_batch():
    """Process all selected files in batch"""
    selected_files = request.form.getlist('selected_files')
    
    if not selected_files:
        # Find all FINAL REVISIONS files
        final_revision_files = get_file_list_by_pattern(
            ATTACHED_ASSETS_FOLDER, 
            pattern=".*FINAL REVISIONS.*\\.xlsx$"
        )
        
        if final_revision_files:
            # Use the newest FINAL REVISIONS file as the base
            final_revision_files.sort(key=lambda x: os.path.getmtime(os.path.join(ATTACHED_ASSETS_FOLDER, x)), reverse=True)
            base_file = final_revision_files[0]
            
            # Get all other EQMO files that don't contain FINAL REVISIONS
            other_files = get_file_list_by_pattern(
                ATTACHED_ASSETS_FOLDER, 
                pattern="EQMO.*BILLING.*ALLOCATIONS.*\\.xlsx$"
            )
            
            # Filter out any files that contain "FINAL REVISIONS"
            other_files = [f for f in other_files if "FINAL REVISIONS" not in f]
            
            # Process the files
            selected_files = [base_file] + other_files
        else:
            # Just get all allocation files
            selected_files = get_file_list_by_pattern(
                ATTACHED_ASSETS_FOLDER, 
                pattern="EQMO.*BILLING.*ALLOCATIONS.*\\.xlsx$"
            )
    
    if not selected_files:
        flash('No files found to process', 'warning')
        return redirect(url_for('pm_master.index'))
    
    # Log the start of batch processing
    log_activity('batch_process_start', f"Processing {len(selected_files)} allocation files")
    
    try:
        # Process the files and generate consolidated report
        results = batch_process_allocation_files(
            [os.path.join(ATTACHED_ASSETS_FOLDER, f) for f in selected_files]
        )
        
        # Generate a consolidated Excel file
        month_year = datetime.now().strftime('%B_%Y').upper()
        output_filename = f"CONSOLIDATED_PM_ALLOCATIONS_{month_year}.xlsx"
        output_path = os.path.join(EXPORTS_FOLDER, output_filename)
        
        create_consolidated_excel(results, output_path)
        
        # Log success
        log_activity('batch_process_complete', f"Successfully processed {len(selected_files)} files")
        
        # Return the batch results
        return render_template(
            'pm_master/batch_results.html',
            title='Batch Processing Results',
            results=results,
            files=selected_files,
            output_filename=output_filename
        )
        
    except Exception as e:
        logging.error(f"Error in batch processing: {str(e)}")
        log_activity('batch_process_error', f"Error: {str(e)}")
        flash(f'Error processing files: {str(e)}', 'danger')
        return redirect(url_for('pm_master.index'))

@pm_master_bp.route('/download/<filename>')
@login_required
def download_report(filename):
    """Download a generated report file"""
    file_path = os.path.join(EXPORTS_FOLDER, secure_filename(filename))
    if os.path.exists(file_path):
        log_activity('report_download', f"Downloaded {filename}")
        return send_file(file_path, as_attachment=True)
    else:
        flash('Report file not found', 'danger')
        return redirect(url_for('pm_master.index'))

@pm_master_bp.route('/view_report/<filename>')
@login_required
def view_report(filename):
    """View a generated report"""
    file_path = os.path.join(EXPORTS_FOLDER, secure_filename(filename))
    if os.path.exists(file_path):
        # For simplicity, we'll redirect to download in this implementation
        # In a real-world scenario, this would render a template with the report contents
        return redirect(url_for('pm_master.download_report', filename=filename))
    else:
        flash('Report file not found', 'danger')
        return redirect(url_for('pm_master.index'))

@pm_master_bp.route('/help')
@login_required
def help_page():
    """Help page for PM Master module"""
    return render_template(
        'pm_master/help.html',
        title='PM Master Help'
    )