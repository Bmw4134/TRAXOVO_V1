"""
Equipment Report Export Routes

This module provides routes for exporting equipment data in multiple formats
with a single click, supporting formats like Excel, CSV, PDF, and JSON.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
import json
import csv
import pandas as pd
from flask import (
    Blueprint, render_template, request, flash, redirect,
    url_for, send_from_directory, jsonify, current_app
)
from flask_login import login_required, current_user
from models.asset import Asset
from models.organization import Organization
from models.user_organization import UserOrganization
from utils.asset_export import generate_asset_report

logger = logging.getLogger(__name__)

# Create blueprint
export_reports_bp = Blueprint('export_reports', __name__, url_prefix='/export-reports')

# File paths
EXPORTS_DIR = Path('./exports')
EXPORTS_DIR.mkdir(exist_ok=True)


@export_reports_bp.route('/', methods=['GET'])
@login_required
def index():
    """Equipment Report Export main page"""
    # Get available organizations for the current user
    if current_user.is_admin:
        organizations = Organization.query.all()
    else:
        user_orgs = UserOrganization.query.filter_by(user_id=current_user.id).all()
        org_ids = [user_org.organization_id for user_org in user_orgs]
        organizations = Organization.query.filter(Organization.id.in_(org_ids)).all()
    
    # Get list of recent exports
    recent_exports = []
    try:
        for export_file in sorted(
            EXPORTS_DIR.glob('equipment_report_*.xlsx') | 
            EXPORTS_DIR.glob('equipment_report_*.csv') | 
            EXPORTS_DIR.glob('equipment_report_*.json'),
            key=lambda x: os.path.getmtime(x), 
            reverse=True
        )[:10]:
            recent_exports.append({
                'name': export_file.name,
                'format': export_file.suffix[1:].upper(),
                'date': datetime.fromtimestamp(os.path.getmtime(export_file)).strftime('%Y-%m-%d %H:%M:%S'),
                'size': f"{os.path.getsize(export_file) / 1024:.2f} KB",
                'path': str(export_file.relative_to(EXPORTS_DIR))
            })
    except Exception as e:
        logger.error(f"Error getting recent exports: {e}")
    
    return render_template(
        'export_reports.html',
        organizations=organizations,
        recent_exports=recent_exports
    )


@export_reports_bp.route('/generate', methods=['POST'])
@login_required
def generate_export():
    """Generate equipment report exports in multiple formats"""
    try:
        # Get request parameters
        org_id = request.form.get('organization_id')
        export_formats = request.form.getlist('export_format')
        region = request.form.get('region', 'all')
        status = request.form.get('status', 'all')
        
        if not export_formats:
            flash("Please select at least one export format", "warning")
            return redirect(url_for('export_reports.index'))
        
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Build query for assets
        query = Asset.query
        
        # Apply organization filter if specified
        if org_id and org_id != 'all':
            query = query.filter(Asset.organization_id == org_id)
            org_name = Organization.query.get(org_id).name
        else:
            org_name = "All"
            
        # Apply region filter if specified
        if region and region != 'all':
            query = query.filter(Asset.region == region)
            
        # Apply status filter if specified
        if status and status != 'all':
            query = query.filter(Asset.status == status)
            
        # Execute query
        assets = query.all()
        
        if not assets:
            flash("No assets found matching the specified criteria", "warning")
            return redirect(url_for('export_reports.index'))
        
        # Create list to store generated files
        generated_files = []
        
        # Generate exports in each requested format
        for export_format in export_formats:
            try:
                # Generate base filename
                base_filename = f"equipment_report_{org_name.replace(' ', '_')}_{timestamp}"
                
                if export_format == 'excel':
                    # Generate Excel export
                    filename = f"{base_filename}.xlsx"
                    file_path = EXPORTS_DIR / filename
                    
                    # Use the asset export utility to generate the Excel file
                    generate_asset_report(assets, file_path, 'excel')
                    
                    generated_files.append({
                        'format': 'Excel',
                        'filename': filename,
                        'path': str(file_path.relative_to(EXPORTS_DIR))
                    })
                    
                elif export_format == 'csv':
                    # Generate CSV export
                    filename = f"{base_filename}.csv"
                    file_path = EXPORTS_DIR / filename
                    
                    # Use the asset export utility to generate the CSV file
                    generate_asset_report(assets, file_path, 'csv')
                    
                    generated_files.append({
                        'format': 'CSV',
                        'filename': filename,
                        'path': str(file_path.relative_to(EXPORTS_DIR))
                    })
                    
                elif export_format == 'json':
                    # Generate JSON export
                    filename = f"{base_filename}.json"
                    file_path = EXPORTS_DIR / filename
                    
                    # Use the asset export utility to generate the JSON file
                    generate_asset_report(assets, file_path, 'json')
                    
                    generated_files.append({
                        'format': 'JSON',
                        'filename': filename,
                        'path': str(file_path.relative_to(EXPORTS_DIR))
                    })
                    
            except Exception as e:
                logger.error(f"Error generating {export_format} export: {str(e)}")
                flash(f"Error generating {export_format.upper()} export: {str(e)}", "danger")
        
        if generated_files:
            formats_str = ", ".join([f['format'] for f in generated_files])
            flash(f"Successfully generated {len(generated_files)} export(s) in {formats_str} format", "success")
            
            # Store the generated files in the session for the result page
            result = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'organization': org_name,
                'asset_count': len(assets),
                'region': region if region != 'all' else 'All Regions',
                'status': status if status != 'all' else 'All Statuses',
                'files': generated_files
            }
            
            return render_template('export_reports_result.html', result=result)
        else:
            flash("No export files were generated", "warning")
            return redirect(url_for('export_reports.index'))
        
    except Exception as e:
        logger.error(f"Error generating exports: {str(e)}")
        flash(f"Error generating exports: {str(e)}", "danger")
        return redirect(url_for('export_reports.index'))


@export_reports_bp.route('/download/<path:filename>', methods=['GET'])
@login_required
def download_file(filename):
    """Download a generated export file"""
    try:
        # Validate the filename to prevent path traversal
        file_path = EXPORTS_DIR / filename
        if not file_path.exists() or not file_path.is_file():
            flash("File not found", "danger")
            return redirect(url_for('export_reports.index'))
        
        return send_from_directory(
            directory=EXPORTS_DIR,
            path=filename,
            as_attachment=True
        )
        
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        flash(f"Error downloading file: {str(e)}", "danger")
        return redirect(url_for('export_reports.index'))