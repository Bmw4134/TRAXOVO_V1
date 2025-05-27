"""
Enhanced GPS Map Routes - TRAXOVO Fleet Management
Professional-grade mapping with smart features inspired by Gauge Smart, Samsara, and MyGeoTab
"""
import json
import logging
import random
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user

from gauge_api import GaugeAPI

logger = logging.getLogger(__name__)

enhanced_map_bp = Blueprint('enhanced_map', __name__, url_prefix='/enhanced-map')

@enhanced_map_bp.route('/')
@login_required
def dashboard():
    """Enhanced GPS map dashboard with professional features"""
    try:
        # Get asset data from Gauge API
        gauge_api = GaugeAPI()
        assets = gauge_api.get_assets()
        
        if not assets:
            logger.warning("No asset data available from Gauge API")
            assets = []
        
        # Calculate summary stats
        total_assets = len(assets)
        active_assets = len([a for a in assets if a.get('status') == 'active'])
        gps_enabled = len([a for a in assets if a.get('latitude') and a.get('longitude')])
        
        return render_template('enhanced_map/dashboard.html',
                             total_assets=total_assets,
                             active_assets=active_assets,
                             gps_enabled=gps_enabled,
                             last_updated=datetime.now().strftime('%I:%M %p'))
                             
    except Exception as e:
        logger.error(f"Error loading enhanced map dashboard: {e}")
        return render_template('enhanced_map/dashboard.html',
                             total_assets=0,
                             active_assets=0,
                             gps_enabled=0,
                             last_updated="Error loading data")

@enhanced_map_bp.route('/api/assets')
@login_required
def get_assets():
    """Get asset data for map display"""
    try:
        gauge_api = GaugeAPI()
        assets = gauge_api.get_assets()
        
        if not assets:
            return jsonify({
                'status': 'error',
                'message': 'No asset data available',
                'assets': []
            })
        
        # Process assets for map display
        map_assets = []
        for asset in assets:
            if asset.get('latitude') and asset.get('longitude'):
                # Determine asset status and icon
                status = determine_asset_status(asset)
                icon_type = get_asset_icon(asset)
                
                map_asset = {
                    'id': asset.get('id', 'unknown'),
                    'name': asset.get('name', 'Unknown Asset'),
                    'latitude': float(asset.get('latitude', 0)),
                    'longitude': float(asset.get('longitude', 0)),
                    'status': status,
                    'icon': icon_type,
                    'speed': asset.get('speed', 0),
                    'heading': asset.get('heading', 0),
                    'last_update': asset.get('last_update', ''),
                    'address': asset.get('address', ''),
                    'job_site': asset.get('job_site', 'Unknown'),
                    'operator': asset.get('operator', 'Unassigned'),
                    'engine_hours': asset.get('engine_hours', 0),
                    'fuel_level': asset.get('fuel_level', 0),
                    'battery_voltage': asset.get('battery_voltage', 0),
                    'is_billable': determine_billable_status(asset),
                    'geofence_status': check_geofence_status(asset)
                }
                map_assets.append(map_asset)
        
        return jsonify({
            'status': 'success',
            'assets': map_assets,
            'timestamp': datetime.now().isoformat(),
            'total_count': len(map_assets)
        })
        
    except Exception as e:
        logger.error(f"Error getting assets for map: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'assets': []
        })

@enhanced_map_bp.route('/api/geofences')
@login_required
def get_geofences():
    """Get geofence data for map display"""
    try:
        # Load geofence definitions
        geofences = [
            {
                'id': 'dfw_metro',
                'name': 'DFW Metro Zone',
                'type': 'polygon',
                'coordinates': [
                    [32.7767, -96.7970],  # Dallas center
                    [32.8998, -97.0403],  # Fort Worth
                    [32.9735, -96.6089],  # Plano
                    [32.6281, -96.5724],  # Mesquite
                    [32.7767, -96.7970]   # Back to Dallas
                ],
                'color': '#007bff',
                'description': 'Main DFW operational area'
            },
            {
                'id': 'houston_zone',
                'name': 'Houston Operations',
                'type': 'circle',
                'center': [29.7604, -95.3698],
                'radius': 50000,  # 50km radius
                'color': '#28a745',
                'description': 'Houston metropolitan area'
            },
            {
                'id': 'west_texas',
                'name': 'West Texas Region',
                'type': 'polygon',
                'coordinates': [
                    [32.4487, -99.7331],  # Abilene
                    [31.9973, -102.0779], # Midland
                    [31.6904, -106.4245], # El Paso
                    [30.2672, -103.3370], # Alpine
                    [32.4487, -99.7331]   # Back to Abilene
                ],
                'color': '#ffc107',
                'description': 'West Texas operational zone'
            }
        ]
        
        return jsonify({
            'status': 'success',
            'geofences': geofences
        })
        
    except Exception as e:
        logger.error(f"Error getting geofences: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'geofences': []
        })

@enhanced_map_bp.route('/api/asset/<asset_id>/track')
@login_required
def get_asset_track(asset_id):
    """Get tracking history for a specific asset"""
    try:
        # For now, return a sample track - in production this would query actual GPS history
        hours_back = int(request.args.get('hours', 24))
        
        # This would normally query your tracking database
        track_points = generate_sample_track(asset_id, hours_back)
        
        return jsonify({
            'status': 'success',
            'asset_id': asset_id,
            'track_points': track_points,
            'hours_back': hours_back
        })
        
    except Exception as e:
        logger.error(f"Error getting track for asset {asset_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'track_points': []
        })

def determine_asset_status(asset):
    """Determine asset status based on data"""
    last_update = asset.get('last_update', '')
    speed = asset.get('speed', 0)
    engine_hours = asset.get('engine_hours', 0)
    
    if not last_update:
        return 'offline'
    
    # Parse last update time
    try:
        if isinstance(last_update, str):
            last_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
        else:
            last_time = last_update
        
        time_diff = datetime.now() - last_time.replace(tzinfo=None)
        
        if time_diff.total_seconds() > 3600:  # More than 1 hour
            return 'offline'
        elif speed > 5:  # Moving
            return 'moving'
        elif engine_hours and engine_hours > 0:  # Engine running but not moving
            return 'idle'
        else:
            return 'parked'
            
    except Exception:
        return 'unknown'

def get_asset_icon(asset):
    """Get appropriate icon for asset type"""
    asset_type = asset.get('type', '').lower()
    
    if 'excavator' in asset_type:
        return 'excavator'
    elif 'dozer' in asset_type or 'bulldozer' in asset_type:
        return 'dozer'
    elif 'loader' in asset_type:
        return 'loader'
    elif 'dump' in asset_type or 'truck' in asset_type:
        return 'truck'
    elif 'crane' in asset_type:
        return 'crane'
    elif 'generator' in asset_type:
        return 'generator'
    else:
        return 'equipment'

def determine_billable_status(asset):
    """Determine if asset is in billable status"""
    # Check if asset is on a job site and active
    job_site = asset.get('job_site', '')
    status = asset.get('status', '')
    
    return bool(job_site and job_site != 'Unknown' and status == 'active')

def check_geofence_status(asset):
    """Check if asset is within its assigned geofence"""
    lat = asset.get('latitude', 0)
    lng = asset.get('longitude', 0)
    
    if not lat or not lng:
        return 'unknown'
    
    # Simple geofence check for DFW area
    if 32.5 <= lat <= 33.0 and -97.5 <= lng <= -96.0:
        return 'inside'
    else:
        return 'outside'

def generate_sample_track(asset_id, hours_back):
    """Generate sample tracking data for development"""
    track_points = []
    base_time = datetime.now() - timedelta(hours=hours_back)
    
    # Sample coordinates around DFW
    base_lat = 32.7767
    base_lng = -96.7970
    
    for i in range(hours_back * 6):  # Every 10 minutes
        timestamp = base_time + timedelta(minutes=i * 10)
        
        # Add some random movement
        lat_offset = (i * 0.001) + (random.uniform(-0.002, 0.002) if 'random' in globals() else 0)
        lng_offset = (i * 0.001) + (random.uniform(-0.002, 0.002) if 'random' in globals() else 0)
        
        track_points.append({
            'timestamp': timestamp.isoformat(),
            'latitude': base_lat + lat_offset,
            'longitude': base_lng + lng_offset,
            'speed': max(0, 25 + (5 * (0.5 if i % 2 == 0 else -0.5))),
            'heading': (i * 5) % 360
        })
    
    return track_points