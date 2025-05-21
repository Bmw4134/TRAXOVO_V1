"""
PM Allocation Module

This module handles routes for PM allocation management and reconciliation.
"""

import os
import json
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the blueprint
pm_allocation_bp = Blueprint('pm_allocation', __name__, url_prefix='/billing')

@pm_allocation_bp.route('/pm-allocation-processor', methods=['GET', 'POST'])
@login_required
def pm_allocation_processor():
    """Process PM allocation files"""
    if request.method == 'POST':
        try:
            # Check if files were uploaded
            if 'baseFile' not in request.files or 'pmFiles' not in request.files:
                flash('Missing required files', 'danger')
                return redirect(request.url)
            
            base_file = request.files['baseFile']
            pm_files = request.files.getlist('pmFiles')
            
            # Check if files were actually selected
            if base_file.filename == '' or not pm_files or pm_files[0].filename == '':
                flash('No files selected', 'danger')
                return redirect(request.url)
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join('uploads', 'pm_allocation')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save base file
            base_file_path = os.path.join(upload_dir, 'base_' + base_file.filename)
            base_file.save(base_file_path)
            
            # Save PM files
            pm_file_paths = []
            for pm_file in pm_files:
                pm_file_path = os.path.join(upload_dir, pm_file.filename)
                pm_file.save(pm_file_path)
                pm_file_paths.append(pm_file_path)
            
            # Process the files using the PM allocation logic
            from calculate_pm_allocations import process_pm_allocation_files
            result = process_pm_allocation_files(base_file_path, pm_file_paths)
            
            # Store the result in session or a temporary file
            result_path = os.path.join('exports', 'pm_allocation', 'pm_allocation_results.json')
            os.makedirs(os.path.dirname(result_path), exist_ok=True)
            
            with open(result_path, 'w') as f:
                json.dump(result, f)
            
            flash('PM allocation files processed successfully', 'success')
            return redirect(url_for('pm_allocation.pm_allocation_results'))
            
        except Exception as e:
            logger.error(f"Error processing PM allocation files: {str(e)}")
            flash(f"Error processing files: {str(e)}", 'danger')
            return redirect(request.url)
    
    return render_template('pm_allocation/processor.html')

@pm_allocation_bp.route('/auto-process-pm')
@login_required
def auto_process_pm():
    """Auto-detect and process PM allocation files"""
    return render_template('pm_allocation/auto_process.html')

@pm_allocation_bp.route('/pm-allocation-results')
@login_required
def pm_allocation_results():
    """Show PM allocation comparison results"""
    try:
        # Check if results file exists
        result_path = os.path.join('exports', 'pm_allocation', 'pm_allocation_results.json')
        
        if not os.path.exists(result_path):
            flash('No PM allocation results found. Please process files first.', 'warning')
            return redirect(url_for('pm_allocation.pm_allocation_processor'))
        
        # Load results from the file
        with open(result_path, 'r') as f:
            results = json.load(f)
        
        # Extract summary data for display
        summary = {
            'total_files': len(results.get('pm_files', [])),
            'base_file': results.get('base_file', 'Unknown'),
            'total_changes': results.get('total_changes', 0),
            'changed_jobs': results.get('changed_jobs', []),
            'processing_date': results.get('processing_date', 'Unknown')
        }
        
        return render_template('pm_allocation/results.html', 
                              results=results,
                              summary=summary)
                              
    except Exception as e:
        logger.error(f"Error displaying PM allocation results: {str(e)}")
        flash(f"Error displaying results: {str(e)}", 'danger')
        return redirect(url_for('pm_allocation.pm_allocation_processor'))

@pm_allocation_bp.route('/pm-master-billing')
@login_required
def pm_master_billing():
    """PM Master Billing report"""
    return render_template('pm_allocation/master_billing.html')