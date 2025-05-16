"""
Asset-Driver Relationship Routes

This module provides routes for viewing and managing the relationships
between assets and their assigned drivers.
"""

import os
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, Asset, Driver
from utils.asset_driver_mapper import extract_asset_driver_mappings, update_drivers_in_database, generate_driver_asset_report
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
asset_drivers_bp = Blueprint('asset_drivers', __name__)

@asset_drivers_bp.route('/asset-drivers')
@login_required
def asset_driver_list():
    """Display asset-driver relationships"""
    
    try:
        # Get all drivers with assigned assets
        drivers_with_assets = Driver.query.filter(Driver.asset_id.isnot(None)).all()
        
        # Get all assets with assigned drivers
        assets_with_drivers = Asset.query.filter(Asset.driver_id.isnot(None)).all()
        
        # Count metrics
        total_assets = Asset.query.count()
        total_drivers = Driver.query.count()
        assigned_assets = len(assets_with_drivers)
        assigned_drivers = len(drivers_with_assets)
        
        return render_template(
            'asset_drivers/list.html',
            title='Asset-Driver Relationships',
            assets=assets_with_drivers,
            drivers=drivers_with_assets,
            metrics={
                'total_assets': total_assets,
                'total_drivers': total_drivers,
                'assigned_assets': assigned_assets,
                'assigned_drivers': assigned_drivers,
                'unassigned_assets': total_assets - assigned_assets,
                'unassigned_drivers': total_drivers - assigned_drivers
            }
        )
    except Exception as e:
        logger.error(f"Error retrieving asset-driver relationships: {e}")
        flash(f"Error retrieving asset-driver data: {str(e)}", "danger")
        return render_template('error.html', error=str(e))

@asset_drivers_bp.route('/asset-drivers/import', methods=['GET', 'POST'])
@login_required
def import_asset_drivers():
    """Import asset-driver relationships from Excel file"""
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'warning')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected', 'warning')
            return redirect(request.url)
        
        if file and file.filename.endswith(('.xlsx', '.xlsm', '.xls')):
            # Save the uploaded file
            uploads_dir = os.path.join(current_app.root_path, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"drivers_{timestamp}_{secure_filename(file.filename)}"
            filepath = os.path.join(uploads_dir, filename)
            
            file.save(filepath)
            
            # Process the file
            mapping_result = extract_asset_driver_mappings(filepath)
            
            if 'error' in mapping_result:
                flash(f"Error processing file: {mapping_result['error']}", 'danger')
                return redirect(url_for('asset_drivers.asset_driver_list'))
            
            # Update database with mappings
            update_result = update_drivers_in_database(mapping_result.get('mappings', {}), db.session)
            
            if 'error' in update_result:
                flash(f"Error updating database: {update_result['error']}", 'danger')
            else:
                flash(f"Successfully updated {update_result.get('updated_assets', 0)} assets and created {update_result.get('new_drivers', 0)} new drivers", 'success')
            
            return redirect(url_for('asset_drivers.asset_driver_list'))
        else:
            flash('Invalid file format. Please upload an Excel file (.xlsx, .xlsm, .xls)', 'warning')
            return redirect(request.url)
    
    return render_template('asset_drivers/import.html', title='Import Asset-Driver Relationships')

@asset_drivers_bp.route('/asset-drivers/assign/<int:asset_id>', methods=['GET', 'POST'])
@login_required
def assign_driver(asset_id):
    """Assign a driver to an asset"""
    
    asset = Asset.query.get_or_404(asset_id)
    
    if request.method == 'POST':
        driver_id = request.form.get('driver_id')
        
        if driver_id:
            driver = Driver.query.get(driver_id)
            
            if driver:
                # Update asset with driver
                asset.driver_id = driver.id
                
                # Update driver with asset
                driver.asset_id = asset.id
                
                db.session.commit()
                
                flash(f"Successfully assigned {driver.name} to {asset.asset_identifier}", 'success')
                return redirect(url_for('asset_drivers.asset_driver_list'))
            else:
                flash('Invalid driver selected', 'danger')
        else:
            # Unassign driver
            if asset.driver_id:
                driver = Driver.query.get(asset.driver_id)
                if driver:
                    driver.asset_id = None
                
                asset.driver_id = None
                db.session.commit()
                
                flash(f"Driver unassigned from {asset.asset_identifier}", 'success')
                return redirect(url_for('asset_drivers.asset_driver_list'))
    
    # Get all drivers for selection
    drivers = Driver.query.order_by(Driver.name).all()
    
    return render_template(
        'asset_drivers/assign.html',
        title=f'Assign Driver to {asset.asset_identifier}',
        asset=asset,
        drivers=drivers
    )

@asset_drivers_bp.route('/asset-drivers/generate-report')
@login_required
def generate_report():
    """Generate asset-driver relationship report"""
    
    try:
        # Get all asset-driver relationships
        assets = Asset.query.filter(Asset.driver_id.isnot(None)).all()
        
        # Prepare data for report
        mappings = {}
        for asset in assets:
            if asset.driver_id:
                driver = Driver.query.get(asset.driver_id)
                if driver:
                    mappings[asset.asset_identifier] = {
                        'employee_name': driver.name,
                        'employee_id': driver.employee_id
                    }
        
        # Generate report
        reports_dir = os.path.join(current_app.root_path, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        report_path = os.path.join(reports_dir, f"asset_driver_mapping_{timestamp}.xlsx")
        
        result = generate_driver_asset_report(mappings, report_path)
        
        if 'error' in result:
            flash(f"Error generating report: {result['error']}", 'danger')
            return redirect(url_for('asset_drivers.asset_driver_list'))
        
        flash(f"Report generated successfully with {result.get('count', 0)} entries", 'success')
        
        # Return the report for download
        return redirect(url_for('download_report', report_path=os.path.basename(report_path)))
    
    except Exception as e:
        logger.error(f"Error generating asset-driver report: {e}")
        flash(f"Error generating report: {str(e)}", 'danger')
        return redirect(url_for('asset_drivers.asset_driver_list'))

@asset_drivers_bp.route('/api/asset-drivers')
@login_required
def api_asset_drivers():
    """API endpoint to get asset-driver relationships in JSON format"""
    
    try:
        # Get all assets with drivers
        assets = Asset.query.filter(Asset.driver_id.isnot(None)).all()
        
        result = []
        for asset in assets:
            if asset.driver_id:
                driver = Driver.query.get(asset.driver_id)
                if driver:
                    result.append({
                        'asset_id': asset.id,
                        'asset_identifier': asset.asset_identifier,
                        'asset_description': asset.label or asset.description,
                        'driver_id': driver.id,
                        'driver_name': driver.name,
                        'driver_employee_id': driver.employee_id
                    })
        
        return jsonify({
            'status': 'success',
            'count': len(result),
            'data': result
        })
    
    except Exception as e:
        logger.error(f"Error in API endpoint: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500