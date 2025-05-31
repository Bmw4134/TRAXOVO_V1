"""
Geolocation Tracking Routes

This module provides routes for the real-time geolocation tracking feature,
which displays asset locations on a map with playful markers and animations.
"""
import os
import logging
import random
import json
import math
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from utils.activity_logger import log_navigation
from gauge_api_legacy import get_asset_data

# Create a logger
logger = logging.getLogger(__name__)

# Create the blueprint
geo_tracking_bp = Blueprint('geo_tracking', __name__, url_prefix='/geo-tracking')

@geo_tracking_bp.route('/')
@login_required
def index():
    """Display the real-time geolocation tracking map."""
    log_navigation(current_user.id, 'geo_tracking.index')
    return render_template('geo_tracking.html')

@geo_tracking_bp.route('/api/asset-locations')
@login_required
def get_asset_locations():
    """API endpoint to get real-time asset locations for the map."""
    try:
        # Check if we should use sample data (for development/testing)
        use_sample = request.args.get('sample', 'false').lower() == 'true'
        
        if use_sample:
            # Use sample data
            sample_assets = generate_sample_asset_data()
            logger.info(f"Using {len(sample_assets)} sample assets for development")
            return jsonify({
                'status': 'success',
                'assets': sample_assets,
                'timestamp': datetime.now().isoformat(),
                'source': 'sample'
            })
        
        # Try to get current asset data from Gauge API
        assets = get_asset_data(force_update=True)
        
        # Check if we got data from the API
        if not assets or len(assets) == 0:
            # If no assets or API error, use sample data instead
            logger.warning("No asset data available from Gauge API, using sample data")
            sample_assets = generate_sample_asset_data()
            return jsonify({
                'status': 'success',
                'assets': sample_assets,
                'timestamp': datetime.now().isoformat(),
                'source': 'sample',
                'notice': "Using sample data because Gauge API returned no results."
            })
        
        # Log the number of assets retrieved
        logger.info(f"Retrieved {len(assets)} assets from Gauge API")
        
        # Process asset data for map display
        processed_assets = process_assets_for_map(assets)
        
        # Return the asset data as JSON
        return jsonify({
            'status': 'success',
            'assets': processed_assets,
            'timestamp': datetime.now().isoformat(),
            'source': 'api'
        })
    except Exception as e:
        logger.error(f"Error retrieving asset locations: {str(e)}")
        
        # Fall back to sample data if API access fails
        logger.warning("API access failed, falling back to sample data")
        sample_assets = generate_sample_asset_data()
        
        return jsonify({
            'status': 'success',
            'assets': sample_assets,
            'timestamp': datetime.now().isoformat(),
            'source': 'sample',
            'notice': f"Using sample data because of API error: {str(e)}"
        })

def process_assets_for_map(assets):
    """
    Process asset data for map display.
    
    Args:
        assets (list): List of asset dictionaries from the Gauge API
        
    Returns:
        list: Processed asset data ready for map display
    """
    processed_assets = []
    
    for asset in assets:
        # Skip assets without location data
        if not asset.get('LastLatitude') or not asset.get('LastLongitude'):
            continue
        
        # Create a cleaner asset object for the map
        processed_asset = {
            'id': asset.get('AssetIdentifier', ''),
            'name': asset.get('Name', ''),
            'latitude': float(asset.get('LastLatitude')),
            'longitude': float(asset.get('LastLongitude')),
            'assetType': asset.get('Category', ''),
            'division': determine_division(asset),
            'ignition': asset.get('IgnitionOn', False),
            'speed': float(asset.get('Speed', 0)),
            'jobSite': asset.get('JobSite', ''),
            'driver': asset.get('Driver', ''),
            'lastUpdate': asset.get('LastReportTime', None),
            'status': determine_asset_status(asset)
        }
        
        processed_assets.append(processed_asset)
    
    return processed_assets

def determine_division(asset):
    """
    Determine the division for an asset based on its location or metadata.
    
    Args:
        asset (dict): Asset data
        
    Returns:
        str: Division code (DFW, HOU, WTX)
    """
    # Check if division is already in the asset data
    if asset.get('Division'):
        return asset.get('Division')
    
    # Look for division in other fields
    for field in ['Location', 'Name', 'Notes']:
        if asset.get(field):
            value = str(asset.get(field)).upper()
            if 'DFW' in value:
                return 'DFW'
            elif 'HOU' in value:
                return 'HOU'
            elif 'WTX' in value or 'WEST' in value:
                return 'WTX'
    
    # Determine by latitude/longitude
    lat = float(asset.get('LastLatitude', 0))
    lng = float(asset.get('LastLongitude', 0))
    
    # Very basic geographic assignment - would need to be refined with actual boundaries
    if 29.5 <= lat <= 30.5 and -96 >= lng >= -96.5:
        return 'HOU'
    elif lat > 31.5 and lng < -101:
        return 'WTX'
    else:
        return 'DFW'  # Default to DFW

def determine_asset_status(asset):
    """
    Determine the operational status of an asset.
    
    Args:
        asset (dict): Asset data
        
    Returns:
        str: Status (active, idle, maintenance)
    """
    # Check if status is already in the asset data
    if asset.get('Status'):
        return asset.get('Status').lower()
    
    # Check if any maintenance flags are set
    if asset.get('InMaintenance') or asset.get('NeedsService'):
        return 'maintenance'
    
    # Check if the asset is active
    if asset.get('IgnitionOn') or asset.get('Speed', 0) > 0:
        return 'active'
    
    # If we've heard from it in the last 24 hours but it's not active
    last_report = asset.get('LastReportTime')
    if last_report:
        try:
            report_time = datetime.fromisoformat(last_report.replace('Z', '+00:00'))
            if (datetime.now() - report_time) < timedelta(hours=24):
                return 'idle'
        except (ValueError, TypeError):
            pass
    
    # Default status
    return 'idle'


def generate_sample_asset_data():
    """
    Generate sample asset data for development and testing.
    
    This function creates realistic sample data that mimics the structure
    of assets returned by the Gauge API.
    
    Returns:
        list: List of sample asset dictionaries
    """
    # Define center points for different regions
    regions = {
        'DFW': {'lat': 32.7767, 'lng': -96.7970, 'radius': 0.2, 'count': 15},
        'HOU': {'lat': 29.7604, 'lng': -95.3698, 'radius': 0.2, 'count': 8},
        'WTX': {'lat': 31.8457, 'lng': -102.3676, 'radius': 0.25, 'count': 6}
    }
    
    # Define asset types with their prefixes
    asset_types = [
        {'name': 'Excavator', 'prefix': 'EX', 'count': 10, 'icon': 'excavator'},
        {'name': 'Loader', 'prefix': 'LD', 'count': 6, 'icon': 'loader'},
        {'name': 'Dozer', 'prefix': 'DZ', 'count': 5, 'icon': 'dozer'},
        {'name': 'Truck', 'prefix': 'TK', 'count': 8, 'icon': 'truck'},
        {'name': 'Pickup', 'prefix': 'PU', 'count': 6, 'icon': 'pickup'}
    ]
    
    # Job sites
    job_sites = [
        '2024-019', '2023-032', '2024-016', '2023-034', '2024-025',
        '2022-008', '2023-016', '2024-030', '2024-045', '2024-050'
    ]
    
    # Drivers
    drivers = [
        'John Smith', 'Maria Garcia', 'David Johnson', 'Li Wei', 'Fatima Ali',
        'Robert Williams', 'Sarah Brown', 'Michael Davis', 'Emma Wilson', 'Unassigned'
    ]
    
    # Generate sample assets
    sample_assets = []
    asset_count = 0
    
    for region_code, region_data in regions.items():
        for asset_type in asset_types:
            # Determine how many of this type to create in this region
            count = min(asset_type['count'], region_data['count'])
            type_count = max(1, count // 2)  # At least 1 of each type per region
            
            for i in range(type_count):
                # Generate asset ID
                asset_id = f"{asset_type['prefix']}-{random.randint(10, 99)}"
                
                # Random position within region radius
                angle = random.uniform(0, 2 * 3.14159)
                distance = random.uniform(0, region_data['radius'])
                lat = region_data['lat'] + distance * math.cos(angle)
                lng = region_data['lng'] + distance * math.sin(angle)
                
                # Random attributes
                ignition = random.random() > 0.6
                speed = random.uniform(0, 35) if ignition else 0
                status = 'active' if ignition and speed > 0 else ('maintenance' if random.random() < 0.15 else 'idle')
                job_site = random.choice(job_sites)
                driver = random.choice(drivers) if random.random() > 0.2 else 'Unassigned'
                
                # Last update time (within the last hour)
                last_update = (datetime.now() - timedelta(minutes=random.randint(0, 60))).isoformat()
                
                # Create asset object
                asset = {
                    'id': asset_id,
                    'name': f"{asset_type['name']} {asset_id}",
                    'assetType': asset_type['name'],
                    'latitude': lat,
                    'longitude': lng,
                    'division': region_code,
                    'ignition': ignition,
                    'speed': speed,
                    'status': status,
                    'jobSite': job_site,
                    'driver': driver,
                    'lastUpdate': last_update
                }
                
                sample_assets.append(asset)
                asset_count += 1
    
    logger.info(f"Generated {asset_count} sample assets for the map")
    return sample_assets
@geo_tracking_bp.route('/')
def index():
    """Handler for /"""
    try:
        # Add your route handler logic here
        return render_template('geo_tracking/index.html')
    except Exception as e:
        logger.error(f"Error in index: {e}")
        return render_template('error.html', error=str(e)), 500

@geo_tracking_bp.route('/api/asset-locations')
def api_asset_locations():
    """Handler for /api/asset-locations"""
    try:
        # Add your route handler logic here
        return render_template('geo_tracking/api_asset_locations.html')
    except Exception as e:
        logger.error(f"Error in api_asset_locations: {e}")
        return render_template('error.html', error=str(e)), 500
