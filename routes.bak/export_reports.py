"""
Equipment Reports Export Module

This module provides routes for exporting equipment data in different formats
(Excel, CSV, JSON) with filtering capabilities by organization, region, and status.
"""

import logging
import os
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, send_file, current_app, jsonify
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from models import Asset, Organization
from utils.asset_export import generate_asset_export

# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
export_reports_bp = Blueprint(
    'export_reports',
    __name__,
    url_prefix='/export_reports'
)

# Ensure exports directory exists
EXPORTS_DIR = Path('exports')
EXPORTS_DIR.mkdir(exist_ok=True)

@export_reports_bp.route('/')
@login_required
def index():
    """
    Display the equipment reports export page with export options
    and recent exports list.
    """
    # Get all organizations for dropdown
    organizations = Organization.query.all()
    
    # Get recent exports
    recent_exports = []
    try:
        # Find all export files
        export_files = list(EXPORTS_DIR.glob('*.xlsx')) + \
                      list(EXPORTS_DIR.glob('*.csv')) + \
                      list(EXPORTS_DIR.glob('*.json'))
        
        # Sort by modification time (newest first)
        export_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Take the 10 most recent
        for file_path in export_files[:10]:
            file_stat = file_path.stat()
            # Convert size to KB or MB
            size_kb = file_stat.st_size / 1024
            if size_kb > 1024:
                size_str = f"{size_kb/1024:.1f} MB"
            else:
                size_str = f"{size_kb:.1f} KB"
                
            file_format = file_path.suffix.upper().replace('.', '')
            
            recent_exports.append({
                'name': file_path.name,
                'path': file_path.name,
                'format': file_format,
                'date': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                'size': size_str
            })
    except Exception as e:
        logger.error(f"Error retrieving recent exports: {e}")
    
    return render_template(
        'export_reports.html', 
        organizations=organizations,
        recent_exports=recent_exports
    )

@export_reports_bp.route('/generate', methods=['POST'])
@login_required
def generate_export():
    """
    Generate equipment reports based on selected filters and formats.
    """
    organization_id = request.form.get('organization_id', 'all')
    region = request.form.get('region', 'all')
    status = request.form.get('status', 'all')
    export_formats = request.form.getlist('export_format')
    
    if not export_formats:
        flash('Please select at least one export format', 'danger')
        return redirect(url_for('export_reports.index'))
    
    try:
        # Build query based on filters
        query = Asset.query
        
        # Apply organization filter
        if organization_id != 'all':
            query = query.filter(Asset.organization_id == organization_id)
            org_name = Organization.query.get(organization_id).name
        else:
            org_name = "All Organizations"
        
        # Apply region filter
        if region != 'all':
            query = query.filter(Asset.region == region)
        
        # Apply status filter
        if status != 'all':
            query = query.filter(Asset.status == status)
        
        # Execute query
        assets = query.all()
        
        if not assets:
            flash('No assets found matching the selected filters', 'warning')
            return redirect(url_for('export_reports.index'))
        
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Generate exports in selected formats
        generated_files = []
        for export_format in export_formats:
            filename = f"{timestamp}_assets_export"
            
            # Generate the export file using the asset_export utility
            export_path = generate_asset_export(
                assets=assets,
                export_format=export_format,
                filename=filename,
                organization=org_name,
                region=region if region != 'all' else 'All Regions',
                status=status if status != 'all' else 'All Statuses'
            )
            
            if export_path:
                format_name = {
                    'excel': 'Excel',
                    'csv': 'CSV',
                    'json': 'JSON'
                }.get(export_format, export_format.upper())
                
                generated_files.append({
                    'format': format_name,
                    'filename': os.path.basename(export_path),
                    'path': os.path.basename(export_path)
                })
        
        # Prepare result data for the template
        result = {
            'organization': org_name,
            'region': region if region != 'all' else 'All Regions',
            'status': status if status != 'all' else 'All Statuses',
            'asset_count': len(assets),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'files': generated_files
        }
        
        return render_template('export_reports_result.html', result=result)
    
    except Exception as e:
        logger.error(f"Error generating export: {e}")
        flash(f'Error generating export: {e}', 'danger')
        return redirect(url_for('export_reports.index'))

@export_reports_bp.route('/download/<filename>')
@login_required
def download_file(filename):
    """
    Download a generated export file.
    """
    try:
        # Secure the filename to prevent directory traversal
        filename = secure_filename(filename)
        file_path = os.path.join('exports', filename)
        
        # Verify file exists
        if not os.path.exists(file_path):
            flash('File not found', 'danger')
            return redirect(url_for('export_reports.index'))
        
        # Record download in history functionality can be added later
        # Currently disabled as we need to implement asset history tracking
        
        # Return the file for download
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        flash(f'Error downloading file: {e}', 'danger')
        return redirect(url_for('export_reports.index'))