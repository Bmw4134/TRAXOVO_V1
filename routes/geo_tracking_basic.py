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
    """Provide sample asset data for development and testing."""
    # Generate sample data
    sample_assets = generate_sample_asset_data()
    
    # Return as JSON
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