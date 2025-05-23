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
from gauge_api import GaugeAPI

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
asset_manager_bp = Blueprint('asset_manager', __name__, url_prefix='/asset-manager')

# Initialize gauge API client
gauge_api = GaugeAPI()

def get_upload_directory():
    """Get asset upload directory, creating it if needed"""
    upload_dir = os.path.join(current_app.root_path, 'uploads', 'assets')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

@asset_manager_bp.route('/')
def dashboard():
    """Asset manager dashboard"""
    try:
        # Fetch some stats about assets
        total_assets = Asset.query.count()
        active_assets = Asset.query.filter_by(status='active').count()
        maintenance_assets = Asset.query.filter_by(status='maintenance').count()
        
        # Get assets with recall alerts
        assets_with_recalls = Asset.query.filter(Asset.recall_alerts.isnot(None)).count()
        
        # Stats for asset categories
        cat_stats = db.session.query(
            Asset.category, db.func.count(Asset.id)
        ).group_by(Asset.category).all()
        
        # Format category stats
        category_stats = [
            {"category": cat or "Uncategorized", "count": count}
            for cat, count in cat_stats
        ]
        
        return render_template(
            'asset_manager/dashboard.html',
            total_assets=total_assets,
            active_assets=active_assets,
            maintenance_assets=maintenance_assets,
            assets_with_recalls=assets_with_recalls,
            category_stats=category_stats
        )
    except Exception as e:
        logger.error(f"Error displaying asset dashboard: {str(e)}")
        flash(f"Error displaying asset dashboard: {str(e)}", "danger")
        return render_template('asset_manager/dashboard.html')

@asset_manager_bp.route('/list')
def list_assets():
    """List all assets"""
    try:
        # Get filter parameters
        status = request.args.get('status', 'all')
        category = request.args.get('category', 'all')
        search_query = request.args.get('search', '')
        
        # Base query
        query = Asset.query
        
        # Apply filters
        if status != 'all':
            query = query.filter_by(status=status)
        
        if category != 'all':
            query = query.filter_by(category=category)
        
        # Apply search query
        if search_query:
            search_query = f"%{search_query}%"
            query = query.filter(
                or_(
                    Asset.name.ilike(search_query),
                    Asset.asset_number.ilike(search_query),
                    Asset.vin.ilike(search_query),
                    Asset.serial_number.ilike(search_query),
                    Asset.job_number.ilike(search_query),
                    Asset.job_name.ilike(search_query)
                )
            )
        
        # Get all statuses and categories for filters
        statuses = db.session.query(Asset.status).distinct().all()
        categories = db.session.query(Asset.category).distinct().all()
        
        # Execute query
        assets = query.order_by(Asset.asset_number).all()
        
        return render_template(
            'asset_manager/list.html',
            assets=assets,
            statuses=[status[0] for status in statuses if status[0]],
            categories=[category[0] for category in categories if category[0]],
            selected_status=status,
            selected_category=category,
            search_query=request.args.get('search', '')
        )
    
    except Exception as e:
        logger.error(f"Error listing assets: {str(e)}")
        flash(f"Error listing assets: {str(e)}", "danger")
        return render_template('asset_manager/list.html', assets=[])

@asset_manager_bp.route('/view/<int:asset_id>')
def view_asset(asset_id):
    """View asset details"""
    try:
        # Get asset by ID
        asset = Asset.query.get_or_404(asset_id)
        
        # Get related data
        images = AssetImage.query.filter_by(asset_id=asset_id).all()
        documents = AssetDocument.query.filter_by(asset_id=asset_id).all()
        service_records = ServiceRecord.query.filter_by(asset_id=asset_id).order_by(ServiceRecord.service_date.desc()).all()
        
        return render_template(
            'asset_manager/view.html',
            asset=asset,
            images=images,
            documents=documents,
            service_records=service_records
        )
    
    except Exception as e:
        logger.error(f"Error viewing asset {asset_id}: {str(e)}")
        flash(f"Error viewing asset: {str(e)}", "danger")
        return redirect(url_for('asset_manager.list_assets'))

@asset_manager_bp.route('/add', methods=['GET', 'POST'])
def add_asset():
    """Add a new asset"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            asset_number = request.form.get('asset_number')
            status = request.form.get('status', 'active')
            category = request.form.get('category')
            model_year = request.form.get('model_year')
            make = request.form.get('make')
            model = request.form.get('model')
            vin = request.form.get('vin')
            serial_number = request.form.get('serial_number')
            
            # Create new asset object
            new_asset = Asset(
                name=name,
                asset_number=asset_number,
                status=status,
                category=category,
                model_year=model_year,
                make=make,
                model=model,
                vin=vin,
                serial_number=serial_number,
                description=request.form.get('description'),
                license_plate=request.form.get('license_plate'),
                job_number=request.form.get('job_number'),
                job_name=request.form.get('job_name'),
                address=request.form.get('address'),
                latitude=float(request.form.get('latitude')) if request.form.get('latitude') else None,
                longitude=float(request.form.get('longitude')) if request.form.get('longitude') else None,
                ownership_type=request.form.get('ownership_type'),
                billing_code=request.form.get('billing_code'),
                odometer=float(request.form.get('odometer')) if request.form.get('odometer') else None,
                hour_meter=float(request.form.get('hour_meter')) if request.form.get('hour_meter') else None,
                class_type=request.form.get('class_type'),
                type_tag=request.form.get('type_tag')
            )
            
            # Process dates
            if request.form.get('date_of_purchase'):
                new_asset.date_of_purchase = datetime.strptime(request.form.get('date_of_purchase'), '%Y-%m-%d').date()
            
            if request.form.get('last_service_date'):
                new_asset.last_service_date = datetime.strptime(request.form.get('last_service_date'), '%Y-%m-%d').date()
            
            if request.form.get('registration_expiration_date'):
                new_asset.registration_expiration_date = datetime.strptime(request.form.get('registration_expiration_date'), '%Y-%m-%d').date()
            
            # VIN Lookup if provided
            if vin and len(vin) == 17:
                try:
                    vin_service = get_vin_service()
                    vehicle_info = vin_service.lookup_vin(vin)
                    
                    if vehicle_info.get('success') and vehicle_info.get('data'):
                        data = vehicle_info.get('data')
                        
                        # Auto-fill fields if not already provided
                        if not model_year and data.get('year'):
                            new_asset.model_year = data.get('year')
                        
                        if not make and data.get('make'):
                            new_asset.make = data.get('make')
                        
                        if not model and data.get('model'):
                            new_asset.model = data.get('model')
                        
                        if not new_asset.type_tag and data.get('vehicle_type'):
                            new_asset.type_tag = data.get('vehicle_type')
                        
                        # Check for recalls
                        recall_info = vin_service.check_recalls(vin)
                        if recall_info.get('success') and recall_info.get('data'):
                            recall_data = recall_info.get('data')
                            if recall_data.get('recall_count', 0) > 0:
                                new_asset.recall_alerts = recall_data.get('recalls', [])
                
                except Exception as vin_error:
                    logger.warning(f"VIN lookup failed: {str(vin_error)}")
            
            # Handle image upload if provided
            if 'asset_image' in request.files:
                image_file = request.files['asset_image']
                if image_file.filename:
                    filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{image_file.filename}")
                    image_path = os.path.join(get_upload_directory(), filename)
                    image_file.save(image_path)
                    
                    # Set primary image URL
                    new_asset.primary_image_url = f"/uploads/assets/{filename}"
            
            # Add to database
            db.session.add(new_asset)
            db.session.commit()
            
            flash(f"Asset {new_asset.name} added successfully!", "success")
            return redirect(url_for('asset_manager.view_asset', asset_id=new_asset.id))
        
        except Exception as e:
            logger.error(f"Error adding asset: {str(e)}")
            logger.error(traceback.format_exc())
            flash(f"Error adding asset: {str(e)}", "danger")
            return render_template('asset_manager/add.html')
    
    # GET request - show form
    return render_template('asset_manager/add.html')

@asset_manager_bp.route('/edit/<int:asset_id>', methods=['GET', 'POST'])
def edit_asset(asset_id):
    """Edit an existing asset"""
    # Get asset by ID
    asset = Asset.query.get_or_404(asset_id)
    
    if request.method == 'POST':
        try:
            # Update asset with form data
            asset.name = request.form.get('name')
            asset.asset_number = request.form.get('asset_number')
            asset.status = request.form.get('status', 'active')
            asset.category = request.form.get('category')
            asset.model_year = request.form.get('model_year')
            asset.make = request.form.get('make')
            asset.model = request.form.get('model')
            asset.vin = request.form.get('vin')
            asset.serial_number = request.form.get('serial_number')
            asset.description = request.form.get('description')
            asset.license_plate = request.form.get('license_plate')
            asset.job_number = request.form.get('job_number')
            asset.job_name = request.form.get('job_name')
            asset.address = request.form.get('address')
            asset.latitude = float(request.form.get('latitude')) if request.form.get('latitude') else None
            asset.longitude = float(request.form.get('longitude')) if request.form.get('longitude') else None
            asset.ownership_type = request.form.get('ownership_type')
            asset.billing_code = request.form.get('billing_code')
            asset.odometer = float(request.form.get('odometer')) if request.form.get('odometer') else None
            asset.hour_meter = float(request.form.get('hour_meter')) if request.form.get('hour_meter') else None
            asset.class_type = request.form.get('class_type')
            asset.type_tag = request.form.get('type_tag')
            
            # Process dates
            if request.form.get('date_of_purchase'):
                asset.date_of_purchase = datetime.strptime(request.form.get('date_of_purchase'), '%Y-%m-%d').date()
            else:
                asset.date_of_purchase = None
            
            if request.form.get('last_service_date'):
                asset.last_service_date = datetime.strptime(request.form.get('last_service_date'), '%Y-%m-%d').date()
            else:
                asset.last_service_date = None
            
            if request.form.get('registration_expiration_date'):
                asset.registration_expiration_date = datetime.strptime(request.form.get('registration_expiration_date'), '%Y-%m-%d').date()
            else:
                asset.registration_expiration_date = None
            
            # Handle image upload if provided
            if 'asset_image' in request.files:
                image_file = request.files['asset_image']
                if image_file and image_file.filename:
                    filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{image_file.filename}")
                    image_path = os.path.join(get_upload_directory(), filename)
                    image_file.save(image_path)
                    
                    # Set primary image URL
                    asset.primary_image_url = f"/uploads/assets/{filename}"
            
            # Update the database
            db.session.commit()
            
            flash(f"Asset {asset.name} updated successfully!", "success")
            return redirect(url_for('asset_manager.view_asset', asset_id=asset.id))
        
        except Exception as e:
            logger.error(f"Error updating asset {asset_id}: {str(e)}")
            logger.error(traceback.format_exc())
            flash(f"Error updating asset: {str(e)}", "danger")
    
    # GET request - show edit form
    return render_template('asset_manager/edit.html', asset=asset)

@asset_manager_bp.route('/delete/<int:asset_id>', methods=['POST'])
def delete_asset(asset_id):
    """Delete an asset"""
    try:
        # Get asset by ID
        asset = Asset.query.get_or_404(asset_id)
        
        # Delete related records
        AssetImage.query.filter_by(asset_id=asset_id).delete()
        AssetDocument.query.filter_by(asset_id=asset_id).delete()
        ServiceRecord.query.filter_by(asset_id=asset_id).delete()
        
        # Delete the asset
        db.session.delete(asset)
        db.session.commit()
        
        flash(f"Asset {asset.name} deleted successfully.", "success")
        return redirect(url_for('asset_manager.list_assets'))
    
    except Exception as e:
        logger.error(f"Error deleting asset {asset_id}: {str(e)}")
        flash(f"Error deleting asset: {str(e)}", "danger")
        return redirect(url_for('asset_manager.view_asset', asset_id=asset_id))

@asset_manager_bp.route('/lookup-vin/<string:vin>', methods=['GET'])
def lookup_vin(vin):
    """API endpoint for VIN lookup"""
    try:
        if not vin or len(vin) != 17:
            return jsonify({
                'success': False,
                'error': 'Invalid VIN format. VIN should be 17 characters.'
            }), 400
        
        # Use VIN lookup service
        vin_service = get_vin_service()
        combined_info = vin_service.get_vehicle_info_with_recalls(vin)
        
        return jsonify(combined_info)
    
    except Exception as e:
        logger.error(f"Error looking up VIN {vin}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error looking up VIN: {str(e)}",
            'data': None
        }), 500

@asset_manager_bp.route('/sync-with-gauge', methods=['POST'])
def sync_with_gauge():
    """Sync assets with Gauge API"""
    try:
        # Get assets from Gauge API
        gauge_assets = gauge_api.get_assets()
        
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