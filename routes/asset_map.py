"""
TRAXORA Fleet Management System - Asset Map Module

This module provides routes and functionality for the Asset Map, displaying
real-time asset locations and historical route data.
"""
import os
import logging
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, current_app
from sqlalchemy import func

import sys
import os

# Add the parent directory to the sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db
from models import Asset, AssetLocation, Driver, JobSite

logger = logging.getLogger(__name__)

# Create blueprint
asset_map_bp = Blueprint('asset_map', __name__, url_prefix='/asset-map')

@asset_map_bp.route('/')
def asset_map():
    """Asset Map main page"""
    # Get job sites for filtering
    job_sites = JobSite.query.filter_by(is_active=True).all()
    
    # Get asset types for filtering
    asset_types = db.session.query(Asset.type).distinct().all()
    asset_types = [t[0] for t in asset_types if t[0] is not None]
    
    return render_template(
        'asset_map/index.html',
        job_sites=job_sites,
        asset_types=asset_types
    )

@asset_map_bp.route('/api/assets')
def api_assets():
    """API endpoint to get all assets with their current locations"""
    try:
        # Query parameters for filtering
        asset_type = request.args.get('type')
        job_site_id = request.args.get('job_site')
        
        # Base query
        query = db.session.query(Asset)
        
        # Apply filters if provided
        if asset_type:
            query = query.filter(Asset.type == asset_type)
        
        if job_site_id:
            # Join with AssetLocation to filter by job_site_id
            query = query.join(AssetLocation).filter(AssetLocation.job_site_id == job_site_id)
        
        # Get the assets
        assets = query.filter(Asset.status == 'active').all()
        
        # Prepare the response
        result = []
        for asset in assets:
            asset_data = {
                'id': asset.id,
                'asset_id': asset.asset_id,
                'name': asset.name,
                'type': asset.type,
                'latitude': asset.last_latitude,
                'longitude': asset.last_longitude,
                'last_update': asset.last_location_update.isoformat() if asset.last_location_update else None,
                'driver': asset.current_driver.full_name if asset.current_driver else None,
                'status': asset.status
            }
            result.append(asset_data)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in api_assets: {str(e)}")
        return jsonify({'error': str(e)}), 500

@asset_map_bp.route('/api/asset/<int:asset_id>/route')
def api_asset_route(asset_id):
    """API endpoint to get the route for a specific asset"""
    try:
        # Get date range from query parameters, default to today
        start_date_str = request.args.get('start_date', datetime.now().strftime('%Y-%m-%d'))
        end_date_str = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        # Convert to datetime
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)  # Include the end date
        
        # Get the asset locations
        locations = AssetLocation.query.filter(
            AssetLocation.asset_id == asset_id,
            AssetLocation.timestamp >= start_date,
            AssetLocation.timestamp < end_date
        ).order_by(AssetLocation.timestamp).all()
        
        # Prepare the response
        result = []
        for location in locations:
            location_data = {
                'id': location.id,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'timestamp': location.timestamp.isoformat(),
                'speed': location.speed,
                'heading': location.heading,
                'job_site': location.job_site.name if location.job_site else None,
                'address': location.address,
                'ignition_status': location.ignition_status
            }
            result.append(location_data)
        
        return jsonify(result)
    except ValueError:
        return jsonify({'error': f"Invalid date format"}), 400
    except Exception as e:
        logger.error(f"Error in api_asset_route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@asset_map_bp.route('/api/job-sites')
def api_job_sites():
    """API endpoint to get all job sites"""
    try:
        # Get active job sites
        job_sites = JobSite.query.filter_by(is_active=True).all()
        
        # Prepare the response
        result = []
        for site in job_sites:
            site_data = {
                'id': site.id,
                'job_number': site.job_number,
                'name': site.name,
                'latitude': site.latitude,
                'longitude': site.longitude,
                'radius': site.radius,
                'address': site.address
            }
            result.append(site_data)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in api_job_sites: {str(e)}")
        return jsonify({'error': str(e)}), 500

@asset_map_bp.route('/api/heatmap')
def api_heatmap():
    """API endpoint to get heatmap data of asset activity"""
    try:
        # Get date range from query parameters, default to last 7 days
        days = int(request.args.get('days', 7))
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get the asset locations aggregated by geographic grid
        # This is a simplified example; in a real implementation, you might want to use
        # a more sophisticated algorithm for creating the heatmap
        locations = db.session.query(
            func.round(AssetLocation.latitude, 3).label('lat_grid'),
            func.round(AssetLocation.longitude, 3).label('lng_grid'),
            func.count().label('count')
        ).filter(
            AssetLocation.timestamp >= start_date,
            AssetLocation.timestamp <= end_date
        ).group_by('lat_grid', 'lng_grid').all()
        
        # Prepare the response
        result = []
        for lat_grid, lng_grid, count in locations:
            point = {
                'latitude': float(lat_grid),
                'longitude': float(lng_grid),
                'weight': min(count / 10, 1.0)  # Normalize weight between 0 and 1
            }
            result.append(point)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in api_heatmap: {str(e)}")
        return jsonify({'error': str(e)}), 500