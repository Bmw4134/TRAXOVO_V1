"""
Simplified Geolocation Tracking Routes

This module provides basic routes for real-time geolocation tracking
to be used when Gauge API credentials are not available.
"""
import math
import random
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify

# Create a blueprint
geo_tracking_basic_bp = Blueprint('geo_tracking_basic', __name__, url_prefix='/map-view')

@geo_tracking_basic_bp.route('/')
def index():
    """Display a simplified map view that doesn't require login."""
    return render_template('map_view_basic.html')

@geo_tracking_basic_bp.route('/api/sample-assets')
def get_sample_assets():
    """Provide sample asset data for development and testing."""
    # Generate sample data
    sample_assets = generate_basic_sample_data()
    
    # Return as JSON
    return jsonify({
        'status': 'success',
        'assets': sample_assets,
        'timestamp': datetime.now().isoformat(),
        'source': 'sample'
    })

def generate_basic_sample_data():
    """Generate basic sample asset data for the map."""
    # Center points for different regions
    regions = {
        'DFW': {'lat': 32.7767, 'lng': -96.7970, 'count': 10},
        'HOU': {'lat': 29.7604, 'lng': -95.3698, 'count': 5},
        'WTX': {'lat': 31.8457, 'lng': -102.3676, 'count': 5}
    }
    
    # Asset types
    asset_types = ['Excavator', 'Loader', 'Dozer', 'Truck', 'Pickup']
    
    # Job sites
    job_sites = ['2024-019', '2023-032', '2024-016', '2023-034', '2024-025']
    
    # Generate sample assets
    sample_assets = []
    
    for region_code, region_data in regions.items():
        for i in range(region_data['count']):
            # Random position within region (0.2 degree radius)
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, 0.2)
            lat = region_data['lat'] + distance * math.cos(angle)
            lng = region_data['lng'] + distance * math.sin(angle)
            
            # Random asset type
            asset_type = random.choice(asset_types)
            
            # Create ID based on type
            prefix = asset_type[0:2].upper()
            asset_id = f"{prefix}-{random.randint(10, 99)}"
            
            # Status (60% active, 30% idle, 10% maintenance)
            status_roll = random.random()
            if status_roll < 0.6:
                status = 'active'
                ignition = True
                speed = random.uniform(5, 35)
            elif status_roll < 0.9:
                status = 'idle'
                ignition = False
                speed = 0
            else:
                status = 'maintenance'
                ignition = False
                speed = 0
            
            # Create asset
            asset = {
                'id': asset_id,
                'name': f"{asset_type} {asset_id}",
                'latitude': lat,
                'longitude': lng,
                'assetType': asset_type,
                'division': region_code,
                'ignition': ignition,
                'speed': speed,
                'status': status,
                'jobSite': random.choice(job_sites),
                'driver': 'Sample Driver',
                'lastUpdate': (datetime.now() - timedelta(minutes=random.randint(0, 60))).isoformat()
            }
            
            sample_assets.append(asset)
    
    return sample_assets