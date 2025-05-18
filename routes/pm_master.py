"""
PM Master Billing Routes Module

This module provides routes for processing PM allocation files and generating master billing exports.
"""

import os
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app, send_from_directory
from flask_login import login_required, current_user
import pandas as pd
import json

from app import db
from utils.activity_logger import log_activity
from utils.pm_master_billing import process_master_billing, find_all_allocation_files

# Create the blueprint
pm_master_bp = Blueprint('pm_master', __name__, url_prefix='/pm-master')

@pm_master_bp.route('/')
@login_required
def index():
    """PM Master Billing Dashboard"""
    # Get list of available allocation files
    allocation_files = find_all_allocation_files()
    
    # Get list of generated exports
    exports_dir = os.path.join(current_app.root_path, 'exports')
    os.makedirs(exports_dir, exist_ok=True)
    
    exports = []
    for filename in os.listdir(exports_dir):
        if filename.endswith('.xlsx') or filename.endswith('.csv'):
            export_path = os.path.join(exports_dir, filename)
            exports.append({
                'filename': filename,
                'path': export_path,
                'size': os.path.getsize(export_path),
                'modified': datetime.fromtimestamp(os.path.getmtime(export_path)).strftime('%Y-%m-%d %H:%M:%S')
            })
    
    # Sort exports by modified date (newest first)
    exports.sort(key=lambda x: x['modified'], reverse=True)
    
    return render_template('pm_master/index.html', 
                          allocation_files=allocation_files,
                          exports=exports)

@pm_master_bp.route('/process', methods=['POST'])
@login_required
def process_billing():
    """Process PM allocation files and generate master billing exports"""
    try:
        # Process the allocation files
        results = process_master_billing()
        
        if results['status'] == 'success':
            # Log the activity
            log_activity(
                'pm_master_billing_process',
                current_user.id,
                f"Generated master billing with {results['record_count']} records",
                metadata={
                    'record_count': results['record_count'],
                    'export_path': results['exports']['master_billing']['path'] if 'master_billing' in results['exports'] else None
                }
            )
            
            flash('Successfully processed PM allocation files and generated exports', 'success')
        else:
            flash(f"Error processing PM allocation files: {results['message']}", 'danger')
        
        return redirect(url_for('pm_master.index'))
        
    except Exception as e:
        flash(f"Error processing PM allocation files: {str(e)}", 'danger')
        return redirect(url_for('pm_master.index'))

@pm_master_bp.route('/download/<path:filename>')
@login_required
def download_export(filename):
    """Download an export file"""
    exports_dir = os.path.join(current_app.root_path, 'exports')
    return send_from_directory(exports_dir, filename, as_attachment=True)

@pm_master_bp.route('/generate-import-files', methods=['POST'])
@login_required
def generate_import_files():
    """Generate division-specific import files"""
    try:
        # Process the allocation files with focus on import file generation
        results = process_master_billing()
        
        if results['status'] == 'success' and 'import_files' in results['exports']:
            import_files = results['exports']['import_files']
            
            if import_files:
                # Log the activity
                log_activity(
                    'pm_master_import_files',
                    current_user.id,
                    f"Generated {len(import_files)} division import files",
                    metadata={
                        'import_files': [f['path'] for f in import_files]
                    }
                )
                
                # Create success message with links to download
                message = f"Successfully generated {len(import_files)} division import files: "
                file_links = []
                
                for file_info in import_files:
                    filename = os.path.basename(file_info['path'])
                    file_links.append(f"{file_info['division']} ({file_info['record_count']} records)")
                
                flash(message + ", ".join(file_links), 'success')
            else:
                flash("No import files were generated", 'warning')
        else:
            flash(f"Error generating import files: {results.get('message', 'Unknown error')}", 'danger')
        
        return redirect(url_for('pm_master.index'))
        
    except Exception as e:
        flash(f"Error generating import files: {str(e)}", 'danger')
        return redirect(url_for('pm_master.index'))

@pm_master_bp.route('/summary')
@login_required
def billing_summary():
    """View billing summary by division and job"""
    try:
        # Look for master billing export
        exports_dir = os.path.join(current_app.root_path, 'exports')
        master_billing_path = os.path.join(exports_dir, 'MASTER_EQUIP_BILLINGS_EXPORT_APRIL_2025.xlsx')
        
        if not os.path.exists(master_billing_path):
            flash("Master billing export not found", 'warning')
            return redirect(url_for('pm_master.index'))
        
        # Load the master billing data
        billing_data = pd.read_excel(master_billing_path, sheet_name='Equip Billings')
        
        # Calculate summary statistics
        division_summary = billing_data.groupby('division').agg({
            'amount': 'sum',
            'equip_id': 'nunique',
            'job': 'nunique'
        }).reset_index()
        
        division_summary.columns = ['Division', 'Total Amount', 'Unique Equipment', 'Unique Jobs']
        
        # Convert to records for template
        division_records = division_summary.to_dict('records')
        
        # Calculate job summary
        job_summary = billing_data.groupby(['division', 'job']).agg({
            'amount': 'sum',
            'equip_id': 'nunique',
            'units': 'sum'
        }).reset_index()
        
        job_summary.columns = ['Division', 'Job', 'Total Amount', 'Unique Equipment', 'Total Units']
        
        # Convert to records and group by division
        job_records_by_division = {}
        for division in job_summary['Division'].unique():
            division_jobs = job_summary[job_summary['Division'] == division].to_dict('records')
            job_records_by_division[division] = division_jobs
        
        # Total amount across all divisions
        total_amount = billing_data['amount'].sum()
        
        return render_template('pm_master/summary.html',
                              division_summary=division_records,
                              job_records_by_division=job_records_by_division,
                              total_amount=total_amount,
                              export_date=datetime.fromtimestamp(os.path.getmtime(master_billing_path)).strftime('%Y-%m-%d %H:%M:%S'))
        
    except Exception as e:
        flash(f"Error generating billing summary: {str(e)}", 'danger')
        return redirect(url_for('pm_master.index'))