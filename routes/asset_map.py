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

# Direct imports to avoid circular imports
from app import db
# Import models directly from their modules to avoid circular import issues
from models.asset import Asset
from models.asset_location import AssetLocation
from models.driver import Driver
from models.job_site import JobSite

logger = logging.getLogger(__name__)

# Create blueprint
asset_map_bp = Blueprint('asset_map', __name__, url_prefix='/asset-map')

@asset_map_bp.route('/')
def asset_map():
    """Asset Map main page"""
    # Get job sites for filtering
    job_sites = JobSite.query.filter_by(active=True).all()
    
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
    """API endpoint to get all assets with their current locations directly from the Gauge API"""
    try:
        # Query parameters for filtering
        asset_type = request.args.get('type')
        job_site_id = request.args.get('job_site')
        
        # Direct connection to the Gauge API - no fallbacks, pure real-time data
        from gauge_api import GaugeAPI
        import requests
        
        api = GaugeAPI()
        
        # Authenticate with API
        api.authenticate()
        
        # Get direct real-time asset data from API
        logger.info("Fetching real-time asset data directly from Gauge API")
        
        # Make direct API call to get assets
        try:
            # Use the endpoint for getting all assets from the asset list
            url = f"{api.api_url}/AssetList/{api.asset_list_id}"
            
            # Make direct authenticated request to API
            response = requests.get(
                url,
                auth=(api.username, api.password),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                timeout=15
            )
            
            if response.status_code != 200:
                logger.error(f"Gauge API returned status code {response.status_code}")
                raise Exception(f"API returned status code {response.status_code}")
            
            # Parse API response
            api_data = response.json()
            
            # Transform API data to our format
            assets_data = []
            for item in api_data:
                asset = {
                    'id': item.get('id') or item.get('AssetId'),
                    'asset_id': item.get('AssetId') or item.get('id'),
                    'name': item.get('Name') or item.get('AssetName'),
                    'type': item.get('Type') or item.get('AssetType'),
                    'latitude': item.get('Latitude') or item.get('latitude'),
                    'longitude': item.get('Longitude') or item.get('longitude'),
                    'last_update': datetime.now().isoformat(),
                    'driver': item.get('Driver') or item.get('DriverName'),
                    'status': 'active'
                }
                assets_data.append(asset)
                
            # Apply filters directly on API data
            if asset_type:
                assets_data = [a for a in assets_data if a.get('type') == asset_type]
            
            if job_site_id:
                # We would need to filter by job site - simplifying for now
                pass
                
            logger.info(f"Successfully fetched {len(assets_data)} assets directly from API")
            return jsonify(assets_data)
            
        except Exception as api_error:
            logger.error(f"Error fetching assets directly from API: {str(api_error)}")
            return jsonify([]), 500
            
        return jsonify(assets_data)
    except Exception as e:
        logger.error(f"Error in api_assets: {str(e)}")
        
        # Fallback to direct database query in case of error with data provider
        try:
            # Base query with safe defaults for filter variables
            asset_type_filter = request.args.get('type')
            job_site_filter = request.args.get('job_site')
            
            query = db.session.query(Asset)
            
            # Apply filters if provided
            if asset_type_filter:
                query = query.filter(Asset.type == asset_type_filter)
            
            if job_site_filter:
                # Join with AssetLocation to filter by job_site_id
                query = query.join(AssetLocation).filter(AssetLocation.job_site_id == job_site_filter)
            
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
        except Exception as inner_e:
            logger.error(f"Error in api_assets fallback: {str(inner_e)}")
            return jsonify({'error': f"Primary error: {str(e)}, Fallback error: {str(inner_e)}"}), 500

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
        
        # Use the asset data provider for reliable asset location data
        from utils.asset_data_provider import AssetDataProvider
        data_provider = AssetDataProvider()
        
        # Get asset locations with fallback mechanisms
        locations_data = data_provider.get_asset_location(asset_id, start_date, end_date)
        
        # If we got data from the provider, return it
        if locations_data:
            return jsonify(locations_data)
        
        # Fallback to direct database query
        # Get the asset locations using the location_timestamp column
        from sqlalchemy import column
        location_timestamp = getattr(AssetLocation, 'timestamp')
        locations = AssetLocation.query.filter(
            AssetLocation.asset_id == asset_id,
            location_timestamp >= start_date,
            location_timestamp < end_date
        ).order_by(location_timestamp).all()
        
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
        # Use the asset data provider for reliable job site data
        from utils.asset_data_provider import AssetDataProvider
        data_provider = AssetDataProvider()
        
        # Get job sites with fallback mechanisms
        job_sites_data = data_provider.get_job_sites(active_only=True)
        
        # If we got data from the provider, return it
        if job_sites_data:
            return jsonify(job_sites_data)
        
        # Fallback to direct database query
        # Get active job sites
        job_sites = JobSite.query.filter_by(active=True).all()
        
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
        
        # First try the data provider for reliable heatmap data with fallbacks
        from utils.asset_data_provider import AssetDataProvider
        data_provider = AssetDataProvider()
        
        # Get heatmap data with fallback mechanisms
        heatmap_data = data_provider.get_heatmap_data(start_date, end_date)
        
        # If we got data from the provider, return it
        if heatmap_data:
            return jsonify(heatmap_data)
            
        # Fallback to direct database query
        # Get the asset locations aggregated by geographic grid
        from sqlalchemy import column
        location_timestamp = getattr(AssetLocation, 'timestamp')
        locations = db.session.query(
            func.round(AssetLocation.latitude, 3).label('lat_grid'),
            func.round(AssetLocation.longitude, 3).label('lng_grid'),
            func.count().label('count')
        ).filter(
            location_timestamp >= start_date,
            location_timestamp <= end_date
        ).group_by('lat_grid', 'lng_grid').all()
        
        # Prepare the response
        result = []
        max_count = 10  # Default if no data
        if locations:
            max_count = max(count for _, _, count in locations)
            
        for lat_grid, lng_grid, count in locations:
            point = {
                'latitude': float(lat_grid),
                'longitude': float(lng_grid),
                'weight': min(count / max_count, 1.0)  # Normalize weight between 0 and 1
            }
            result.append(point)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in api_heatmap: {str(e)}")
        return jsonify({'error': str(e)}), 500