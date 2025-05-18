"""
PM Master Billing Module Routes

This module provides routes for the PM Master Billing functionality, which
processes multiple PM allocation files to generate a consolidated master
billing report and division-specific exports.
"""

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from pathlib import Path
import logging
from datetime import datetime

# Import utilities
from utils.pm_master_billing import process_master_billing
from utils.activity_logger import log_activity

# Set up logger
logger = logging.getLogger(__name__)

# Create blueprint
pm_master_bp = Blueprint('pm_master', __name__, url_prefix='/pm-master')

# Create export directory
EXPORTS_DIR = Path('exports/pm_master')
EXPORTS_DIR.mkdir(exist_ok=True, parents=True)

@pm_master_bp.route('/')
@login_required
def index():
    """PM Master Dashboard Page"""
    # Check for existing export files
    export_files = []
    if EXPORTS_DIR.exists():
        for file in EXPORTS_DIR.glob('*.xlsx'):
            export_files.append({
                'name': file.name,
                'path': file.name,
                'size': f"{file.stat().st_size // 1024}K",
                'modified': datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                'division': file.name.split('_')[0] if '_' in file.name else 'MASTER'
            })
    
    # Sort files by date modified (newest first)
    export_files.sort(key=lambda x: x['modified'], reverse=True)
    
    # Get available allocation files from the attached_assets folder
    from utils.pm_master_billing import find_all_allocation_files
    allocation_files = find_all_allocation_files()
    
    # Format for display
    allocation_file_details = []
    for file_path in allocation_files:
        file_name = os.path.basename(file_path)
        file_stat = os.stat(file_path)
        allocation_file_details.append({
            'name': file_name,
            'size': f"{file_stat.st_size // 1024}K",
            'modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M')
        })
    
    return render_template(
        'pm_master/index.html',
        title='PM Master Billing',
        files=allocation_file_details,
        export_files=export_files
    )

@pm_master_bp.route('/process-batch', methods=['POST'])
@login_required
def process_batch():
    """Process all allocation files and generate exports"""
    try:
        # Log the action
        log_activity(
            activity_type='batch_process_start',
            description='Started PM Master batch processing',
            user_id=current_user.id
        )
        
        # Process all allocation files
        result = process_master_billing()
        
        if result['success']:
            # Log success
            log_activity(
                activity_type='batch_process_complete',
                description=f"Processed {result['file_count']} allocation files and generated {len(result['exports'])} exports",
                user_id=current_user.id,
                metadata={
                    'file_count': result['file_count'],
                    'record_count': result['record_count'],
                    'missing_rates': result['missing_rates'],
                    'exports': list(result['exports'].keys())
                }
            )
            
            # Flash success message
            flash(f"Successfully processed {result['file_count']} allocation files. Generated {len(result['exports'])} export files.", 'success')
        else:
            # Log failure
            log_activity(
                activity_type='batch_process_error',
                description=f"Error processing PM allocation files: {result['message']}",
                user_id=current_user.id
            )
            
            # Flash error message
            flash(f"Error processing PM allocation files: {result['message']}", 'danger')
        
        return redirect(url_for('pm_master.index'))
    
    except Exception as e:
        logger.error(f"Error in process_batch: {str(e)}")
        flash(f"An unexpected error occurred: {str(e)}", 'danger')
        return redirect(url_for('pm_master.index'))

@pm_master_bp.route('/download/<path:filename>')
@login_required
def download_export(filename):
    """Download an exported file"""
    try:
        file_path = EXPORTS_DIR / filename
        
        if not file_path.exists():
            flash(f"File not found: {filename}", 'danger')
            return redirect(url_for('pm_master.index'))
        
        # Log download activity
        log_activity(
            activity_type='report_download',
            description=f"Downloaded PM Master export: {filename}",
            user_id=current_user.id
        )
        
        return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        logger.error(f"Error in download_export: {str(e)}")
        flash(f"An unexpected error occurred: {str(e)}", 'danger')
        return redirect(url_for('pm_master.index'))

@pm_master_bp.route('/help')
@login_required
def help_page():
    """Display help information for PM Master Billing"""
    return render_template('pm_master/help.html', title='PM Master Help')