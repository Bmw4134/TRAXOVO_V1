"""
Driver-Asset Manager Module

This module provides routes for managing and viewing driver-asset mappings
based on the Secondary Asset Identifier from the asset list.
"""

import os
import pandas as pd
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename

from utils.asset_driver_mapper import (
    get_driver_for_asset,
    get_asset_for_driver,
    get_all_mapped_drivers,
    refresh_mapping
)
from utils.driver_identity_integration import (
    import_assets_list,
    generate_driver_asset_report,
    validate_driver_vehicle_assignments
)

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
driver_asset_manager_bp = Blueprint('driver_asset_manager', __name__, url_prefix='/driver-asset-manager')

@driver_asset_manager_bp.route('/')
def dashboard():
    """Driver-Asset Manager Dashboard"""
    try:
        # Get all mapped drivers
        all_drivers = get_all_mapped_drivers()
        
        # Validate mappings
        validation_results = validate_driver_vehicle_assignments()
        
        # Prepare statistics
        stats = {
            'total_mappings': len(all_drivers),
            'valid_mappings': validation_results['valid_mappings'],
            'issue_count': len(validation_results['issues']),
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return render_template(
            'driver_asset_manager/dashboard.html',
            drivers=all_drivers,
            stats=stats,
            issues=validation_results['issues']
        )
    except Exception as e:
        logger.error(f"Error displaying driver asset manager dashboard: {str(e)}")
        flash(f"Error: {str(e)}", "danger")
        return render_template('driver_asset_manager/dashboard.html', drivers=[], stats={}, issues=[])

@driver_asset_manager_bp.route('/upload', methods=['GET', 'POST'])
def upload_assets_list():
    """Upload Assets List"""
    if request.method == 'POST':
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected', 'warning')
            return redirect(request.url)
            
        file = request.files['file']
        
        # Check if filename is empty
        if not file or file.filename == '':
            flash('No file selected', 'warning')
            return redirect(request.url)
            
        # Check file extension
        if not file.filename or not file.filename.endswith('.xlsx'):
            flash('Only Excel (.xlsx) files are supported', 'warning')
            return redirect(request.url)
            
        try:
            # Save uploaded file temporarily
            temp_dir = os.path.join(os.getcwd(), 'temp_extract')
            os.makedirs(temp_dir, exist_ok=True)
            
            if file.filename:
                temp_path = os.path.join(temp_dir, secure_filename(file.filename))
                file.save(temp_path)
            else:
                flash('Invalid filename', 'danger')
                return redirect(request.url)
            
            # Import assets list
            result = import_assets_list(temp_path)
            
            if result['success']:
                flash(result['message'], 'success')
            else:
                flash(result['message'], 'danger')
                
            return redirect(url_for('driver_asset_manager.dashboard'))
            
        except Exception as e:
            logger.error(f"Error uploading assets list: {str(e)}")
            flash(f"Error: {str(e)}", "danger")
            return redirect(request.url)
    
    return render_template('driver_asset_manager/upload.html')

@driver_asset_manager_bp.route('/export')
def export_driver_asset_report():
    """Export Driver-Asset Report"""
    try:
        # Generate report
        df = generate_driver_asset_report()
        
        # Save to Excel file
        export_dir = os.path.join(os.getcwd(), 'exports')
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_path = os.path.join(export_dir, f'driver_asset_mapping_{timestamp}.xlsx')
        
        df.to_excel(export_path, index=False)
        
        return send_file(export_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"Error exporting driver asset report: {str(e)}")
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('driver_asset_manager.dashboard'))

@driver_asset_manager_bp.route('/refresh')
def refresh_driver_mappings():
    """Refresh Driver Mappings"""
    try:
        # Refresh mappings
        count = refresh_mapping()
        
        flash(f"Successfully refreshed {count} driver mappings", "success")
        return redirect(url_for('driver_asset_manager.dashboard'))
        
    except Exception as e:
        logger.error(f"Error refreshing driver mappings: {str(e)}")
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('driver_asset_manager.dashboard'))

@driver_asset_manager_bp.route('/api/mappings')
def api_mappings():
    """API endpoint to get driver-asset mappings"""
    try:
        # Get all mapped drivers
        all_drivers = get_all_mapped_drivers()
        
        return jsonify({
            'success': True,
            'count': len(all_drivers),
            'mappings': all_drivers
        })
        
    except Exception as e:
        logger.error(f"Error getting driver-asset mappings: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })