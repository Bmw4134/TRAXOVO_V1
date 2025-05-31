"""
TRAXORA Fleet Management System - Asset Manager Routes

This module provides routes for the enhanced asset management system,
based on the Gauge Smart Hub structure with full asset details.
"""

import os
import json
import logging
import traceback
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, jsonify, current_app, abort, send_from_directory
)
from werkzeug.utils import secure_filename
from sqlalchemy import or_

from app import db
from models.asset import Asset, AssetImage, AssetDocument, ServiceRecord
from utils.vin_lookup_service import get_vin_service
from gauge_api_legacy import GaugeAPI

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
asset_manager_bp = Blueprint('asset_manager', __name__, url_prefix='/asset-manager')

# Initialize gauge API client
get_unified_data("assets")
        
        if not gauge_assets:
            flash("No assets retrieved from Gauge API. Check connection and try again.", "warning")
            return redirect(url_for('asset_manager.dashboard'))
        
        # Track stats
        stats = {
            'new': 0,
            'updated': 0,
            'unchanged': 0,
            'errors': 0
        }
        
        # Process each asset
        for gauge_asset in gauge_assets:
            try:
                # Extract key fields - handle different API formats
                external_id = str(gauge_asset.get('id') or gauge_asset.get('ID') or gauge_asset.get('asset_id'))
                name = gauge_asset.get('name') or gauge_asset.get('Name') or gauge_asset.get('AssetName') or f"Asset {external_id}"
                asset_number = gauge_asset.get('asset_number') or gauge_asset.get('AssetNumber') or gauge_asset.get('UnitNumber')
                
                # Skip if missing key fields
                if not external_id or not name:
                    logger.warning(f"Skipping asset with incomplete data: {gauge_asset}")
                    stats['errors'] += 1
                    continue
                
                # Check if asset already exists in our database
                existing_asset = Asset.query.filter_by(external_id=external_id).first()
                
                if existing_asset:
                    # Update existing asset
                    asset_updated = False
                    
                    # Update fields with new values from Gauge
                    for field, gauge_field in [
                        ('name', ['name', 'Name', 'AssetName']),
                        ('asset_number', ['asset_number', 'AssetNumber', 'UnitNumber']),
                        ('status', ['status', 'Status', 'AssetStatus']),
                        ('category', ['category', 'Category', 'AssetCategory']),
                        ('model_year', ['model_year', 'ModelYear', 'Year']),
                        ('make', ['make', 'Make', 'Manufacturer']),
                        ('model', ['model', 'Model']),
                        ('type_tag', ['type', 'Type', 'AssetType']),
                        ('vin', ['vin', 'VIN']),
                        ('serial_number', ['serial_number', 'SerialNumber', 'Serial']),
                        ('job_number', ['job_number', 'JobNumber', 'Job']),
                        ('job_name', ['job_name', 'JobName', 'JobSite']),
                        ('latitude', ['latitude', 'Latitude', 'lat']),
                        ('longitude', ['longitude', 'Longitude', 'lng']),
                        ('odometer', ['odometer', 'Odometer', 'OdometerReading']),
                        ('hour_meter', ['hour_meter', 'HourMeter', 'Hours'])
                    ]:
                        # Try each possible gauge field name
                        for gf in gauge_field:
                            if gf in gauge_asset and gauge_asset[gf] is not None:
                                current_value = getattr(existing_asset, field)
                                new_value = gauge_asset[gf]
                                
                                # Convert values for comparison
                                if field in ['latitude', 'longitude', 'odometer', 'hour_meter'] and new_value:
                                    try:
                                        new_value = float(new_value)
                                    except (ValueError, TypeError):
                                        new_value = None
                                
                                # Update if different
                                if current_value != new_value:
                                    setattr(existing_asset, field, new_value)
                                    asset_updated = True
                                
                                break
                    
                    # Check for updated location description
                    location_fields = ['location', 'Location', 'CurrentLocation', 'LastLocation']
                    for loc_field in location_fields:
                        if loc_field in gauge_asset and gauge_asset[loc_field]:
                            if existing_asset.last_known_location != gauge_asset[loc_field]:
                                existing_asset.last_known_location = gauge_asset[loc_field]
                                asset_updated = True
                            break
                    
                    # Update the last_updated timestamp
                    if asset_updated:
                        existing_asset.last_updated = datetime.utcnow()
                        stats['updated'] += 1
                    else:
                        stats['unchanged'] += 1
                
                else:
                    # Create new asset
                    new_asset = Asset(
                        external_id=external_id,
                        name=name,
                        asset_number=asset_number,
                        status=gauge_asset.get('status') or gauge_asset.get('Status') or 'active',
                        category=gauge_asset.get('category') or gauge_asset.get('Category'),
                        model_year=gauge_asset.get('model_year') or gauge_asset.get('ModelYear') or gauge_asset.get('Year'),
                        make=gauge_asset.get('make') or gauge_asset.get('Make') or gauge_asset.get('Manufacturer'),
                        model=gauge_asset.get('model') or gauge_asset.get('Model'),
                        type_tag=gauge_asset.get('type') or gauge_asset.get('Type') or gauge_asset.get('AssetType'),
                        vin=gauge_asset.get('vin') or gauge_asset.get('VIN'),
                        serial_number=gauge_asset.get('serial_number') or gauge_asset.get('SerialNumber') or gauge_asset.get('Serial'),
                        job_number=gauge_asset.get('job_number') or gauge_asset.get('JobNumber') or gauge_asset.get('Job'),
                        job_name=gauge_asset.get('job_name') or gauge_asset.get('JobName') or gauge_asset.get('JobSite'),
                        last_known_location=gauge_asset.get('location') or gauge_asset.get('Location') or gauge_asset.get('CurrentLocation'),
                        api_source='gauge',
                        telematics_id=external_id
                    )
                    
                    # Add location coordinates if available
                    lat_field = next((f for f in ['latitude', 'Latitude', 'lat'] if f in gauge_asset and gauge_asset[f]), None)
                    lng_field = next((f for f in ['longitude', 'Longitude', 'lng'] if f in gauge_asset and gauge_asset[f]), None)
                    
                    if lat_field and lng_field:
                        try:
                            new_asset.latitude = float(gauge_asset[lat_field])
                            new_asset.longitude = float(gauge_asset[lng_field])
                        except (ValueError, TypeError):
                            pass
                    
                    # Add metrics if available
                    for metric, fields in [
                        ('odometer', ['odometer', 'Odometer', 'OdometerReading']),
                        ('hour_meter', ['hour_meter', 'HourMeter', 'Hours']),
                        ('fuel_level', ['fuel_level', 'FuelLevel', 'Fuel'])
                    ]:
                        field = next((f for f in fields if f in gauge_asset and gauge_asset[f] is not None), None)
                        if field:
                            try:
                                setattr(new_asset, metric, float(gauge_asset[field]))
                            except (ValueError, TypeError):
                                pass
                    
                    # Store raw telematics data
                    new_asset.telematics_data = gauge_asset
                    
                    # Add to database
                    db.session.add(new_asset)
                    stats['new'] += 1
            
            except Exception as asset_error:
                logger.error(f"Error processing asset from Gauge: {str(asset_error)}")
                stats['errors'] += 1
                continue
        
        # Commit all changes
        db.session.commit()
        
        # Report success
        flash(f"Successfully synced assets with Gauge: {stats['new']} new, {stats['updated']} updated, {stats['unchanged']} unchanged, {stats['errors']} errors", "success")
        return redirect(url_for('asset_manager.dashboard'))
    
    except Exception as e:
        logger.error(f"Error syncing with Gauge API: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Error syncing with Gauge API: {str(e)}", "danger")
        return redirect(url_for('asset_manager.dashboard'))

@asset_manager_bp.route('/uploads/assets/<path:filename>')
def asset_uploads(filename):
    """Serve uploaded asset files"""
    return send_from_directory(get_upload_directory(), filename)

@asset_manager_bp.route('/add-service-record/<int:asset_id>', methods=['POST'])
def add_service_record(asset_id):
    """Add a service record to an asset"""
    try:
        # Verify asset exists
        asset = Asset.query.get_or_404(asset_id)
        
        # Create service record from form data
        service_record = ServiceRecord(
            asset_id=asset_id,
            service_date=datetime.strptime(request.form.get('service_date'), '%Y-%m-%d').date(),
            service_type=request.form.get('service_type'),
            description=request.form.get('description'),
            performed_by=request.form.get('performed_by')
        )
        
        # Add optional numeric fields
        for field in ['odometer', 'hour_meter', 'service_cost', 'parts_cost']:
            if request.form.get(field):
                try:
                    setattr(service_record, field, float(request.form.get(field)))
                except (ValueError, TypeError):
                    pass
        
        # Calculate total cost
        service_record.total_cost = (service_record.service_cost or 0) + (service_record.parts_cost or 0)
        
        # Update asset's last_service_date
        asset.last_service_date = service_record.service_date
        
        # Add to database
        db.session.add(service_record)
        db.session.commit()
        
        flash("Service record added successfully.", "success")
        return redirect(url_for('asset_manager.view_asset', asset_id=asset_id))
    
    except Exception as e:
        logger.error(f"Error adding service record: {str(e)}")
        flash(f"Error adding service record: {str(e)}", "danger")
        return redirect(url_for('asset_manager.view_asset', asset_id=asset_id))

@asset_manager_bp.route('/api/assets')
def api_assets():
    """API endpoint for assets data"""
    try:
        # Get assets for map display
        assets = Asset.query.filter(
            Asset.latitude.isnot(None), 
            Asset.longitude.isnot(None)
        ).all()
        
        # Format assets for API response
        asset_data = [asset.to_dict() for asset in assets]
        
        return jsonify({
            'success': True,
            'count': len(asset_data),
            'assets': asset_data
        })
    
    except Exception as e:
        logger.error(f"Error in assets API: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'assets': []
        }), 500

@asset_manager_bp.route('/map')
def asset_map():
    """Interactive asset map"""
    return render_template('asset_manager/map.html')