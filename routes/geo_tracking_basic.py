"""
Basic Geolocation Tracking Module - Mobile-friendly and public

This module provides a simplified version of the geolocation tracking
features without requiring login, making it easier to access from mobile devices.
"""

from datetime import datetime
import random
import logging
from flask import Blueprint, render_template, jsonify, request

geo_tracking_basic_bp = Blueprint('geo_tracking_basic', __name__, url_prefix='/map-view')

# Set up logging
logger = logging.getLogger(__name__)

@geo_tracking_basic_bp.route('/')
def map_view():
    """Display the basic map view without requiring login."""
    return render_template('map_view_basic.html')

@geo_tracking_basic_bp.route('/api/sample-assets')
def get_sample_assets():
    """Provide real asset data from the Gauge API."""
    try:
        # Try to import the gauge_api module
        from gauge_api import update_asset_data, get_asset_data
        
        # Try to get real data from Gauge API with force_update=True to get fresh data
        real_assets = get_asset_data(force_update=True)
        
        # If we got real data, format it for the map view
        if real_assets and len(real_assets) > 0:
            logger.info(f"Returning {len(real_assets)} real assets from Gauge API")
            
            # Format assets for map display
            formatted_assets = []
            for asset in real_assets:
                # Extract asset info
                asset_id = asset.get('id') or asset.get('assetID') or asset.get('AssetID') or 'Unknown'
                asset_name = asset.get('name') or asset.get('assetName') or asset.get('AssetName') or f'Asset {asset_id}'
                
                # Extract location info
                lat = asset.get('latitude') or asset.get('lat') or asset.get('Latitude') or None
                lng = asset.get('longitude') or asset.get('lng') or asset.get('Longitude') or None
                
                # Only include assets with valid location
                if lat and lng and float(lat) != 0 and float(lng) != 0:
                    # Create formatted asset
                    formatted_asset = {
                        'id': asset_id,
                        'name': asset_name,
                        'assetType': asset.get('assetType') or asset.get('type') or 'Equipment',
                        'status': asset.get('status') or 'active',
                        'division': asset.get('division') or asset.get('region') or 'DFW',
                        'jobSite': asset.get('jobSite') or asset.get('site') or asset.get('location') or 'Unknown',
                        'driver': asset.get('driver') or asset.get('operator') or 'Unassigned',
                        'latitude': float(lat),
                        'longitude': float(lng),
                        'speed': asset.get('speed') or 0,
                        'heading': asset.get('heading') or asset.get('direction') or 0,
                        'lastUpdated': asset.get('lastUpdated') or asset.get('timestamp') or datetime.now().isoformat()
                    }
                    formatted_assets.append(formatted_asset)
            
            # Return formatted assets
            if formatted_assets:
                return jsonify({
                    'status': 'success',
                    'assets': formatted_assets,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'gauge_api'
                })
    except Exception as e:
        logger.error(f"Error getting real asset data: {e}")
    
    # Only generate sample data as a last resort
    sample_assets = generate_sample_asset_data()
    logger.info(f"Returning {len(sample_assets)} sample assets (fallback)")
    
    # Return sample data
    return jsonify({
        'status': 'success',
        'assets': sample_assets,
        'timestamp': datetime.now().isoformat(),
        'source': 'sample'
    })

def generate_sample_asset_data():
    """Generate sample asset data for development and testing."""
    asset_types = ['Excavator', 'Loader', 'Dozer', 'Truck', 'Pickup']
    statuses = ['active', 'idle', 'maintenance']
    divisions = ['DFW', 'HOU', 'WTX']
    job_sites = [
        'TX-290 Expansion', 'Dallas Bypass', 'Houston Port Terminal',
        'Fort Worth Regional', 'Midland Highway 20', 'Lubbock Commercial',
        'San Antonio River Project', 'Austin Metro Extension'
    ]
    
    # Regional centers for random coordinate generation
    region_centers = {
        'DFW': (32.7767, -96.7970),  # Dallas
        'HOU': (29.7604, -95.3698),  # Houston
        'WTX': (31.8457, -102.3676)  # Midland
    }
    
    # Generate sample assets
    sample_assets = []
    
    # Number of assets to generate
    asset_count = random.randint(15, 25)
    
    for i in range(asset_count):
        # Determine asset type
        asset_type = random.choice(asset_types)
        
        # Generate asset ID
        prefix = asset_type[0:2].upper()
        number = random.randint(1000, 9999)
        asset_id = f"{prefix}{number}"
        
        # Determine division
        division = random.choice(divisions)
        
        # Get coordinates near division center
        center_lat, center_lng = region_centers[division]
        
        # Random offset (approximately within 30 miles)
        lat_offset = random.uniform(-0.4, 0.4)
        lng_offset = random.uniform(-0.4, 0.4)
        
        # Create asset data
        asset = {
            'id': asset_id,
            'name': f"{asset_type} {number}",
            'assetType': asset_type,
            'status': random.choice(statuses),
            'division': division,
            'jobSite': random.choice(job_sites),
            'driver': f"Driver {random.randint(1, 20)}",
            'latitude': center_lat + lat_offset,
            'longitude': center_lng + lng_offset,
            'speed': random.randint(0, 35) if random.random() > 0.3 else 0,
            'heading': random.randint(0, 359) if random.random() > 0.3 else 0,
            'lastUpdated': datetime.now().isoformat()
        }
        
        sample_assets.append(asset)
    
    return sample_assets