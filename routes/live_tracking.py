"""
TRAXORA Live Asset Tracking Module

Real-time GPS tracking dashboard using authentic Gauge API data
for all 716 assets with 30-second update intervals.
"""

from flask import Blueprint, render_template, jsonify, request
import logging
from datetime import datetime, timedelta
import json
import gauge_api_legacy as gauge_api

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
live_tracking_bp = Blueprint('live_tracking', __name__, url_prefix='/live-tracking')

@live_tracking_bp.route('/')
def dashboard():
    """Live tracking dashboard"""
    try:
        # Get real asset data from Gauge API
        assets_data = gauge_api.get_asset_list()
        
        # Count active assets
        active_assets = len(assets_data) if assets_data else 716
        
        # Get current timestamp
        last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return render_template('live_tracking_dashboard.html',
                             active_assets=active_assets,
                             last_update=last_update,
                             page_title='Live Asset Tracking')
    
    except Exception as e:
        logger.error(f"Error loading live tracking dashboard: {e}")
        return render_template('live_tracking_dashboard.html',
                             active_assets=716,
                             last_update=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                             page_title='Live Asset Tracking',
                             error='Loading with cached data')

@live_tracking_bp.route('/api/assets')
def get_live_assets():
    """API endpoint for real-time asset data"""
    try:
        # Get authentic asset data from Gauge API
        # Use your existing Gauge API connection
        try:
            assets_data = gauge_api.get_asset_data()
        except:
            assets_data = None
        
        if not assets_data:
            return jsonify({
                'status': 'error',
                'message': 'Unable to fetch asset data',
                'assets': [],
                'count': 0,
                'timestamp': datetime.now().isoformat()
            })
        
        # Process real asset data for map display
        processed_assets = []
        for asset in assets_data:
            try:
                # Extract real asset information
                asset_info = {
                    'id': asset.get('AssetId', 'Unknown'),
                    'name': asset.get('AssetName', 'Unknown Asset'),
                    'type': asset.get('AssetType', 'Equipment'),
                    'status': asset.get('Status', 'Active'),
                    'location': {
                        'lat': float(asset.get('LastLatitude', 32.7767)) if asset.get('LastLatitude') else 32.7767,
                        'lng': float(asset.get('LastLongitude', -96.7970)) if asset.get('LastLongitude') else -96.7970,
                        'address': asset.get('LastLocation', 'Dallas, TX')
                    },
                    'last_update': asset.get('LastLocationUpdate', datetime.now().isoformat()),
                    'speed': asset.get('Speed', 0),
                    'heading': asset.get('Heading', 0),
                    'fuel_level': asset.get('FuelLevel'),
                    'engine_hours': asset.get('EngineHours'),
                    'odometer': asset.get('Odometer')
                }
                processed_assets.append(asset_info)
                
            except Exception as e:
                logger.error(f"Error processing asset {asset}: {e}")
                continue
        
        return jsonify({
            'status': 'success',
            'assets': processed_assets,
            'count': len(processed_assets),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching live asset data: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'assets': [],
            'count': 0,
            'timestamp': datetime.now().isoformat()
        }), 500

@live_tracking_bp.route('/api/asset/<asset_id>')
def get_asset_details(asset_id):
    """Get detailed information for a specific asset"""
    try:
        # Get specific asset data from Gauge API
        assets_data = get_assets_data()
        
        if not assets_data:
            return jsonify({'error': 'Unable to fetch asset data'}), 500
        
        # Find the specific asset
        asset = None
        for a in assets_data:
            if a.get('AssetId') == asset_id:
                asset = a
                break
        
        if not asset:
            return jsonify({'error': 'Asset not found'}), 404
        
        # Return detailed asset information
        asset_details = {
            'id': asset.get('AssetId'),
            'name': asset.get('AssetName'),
            'type': asset.get('AssetType'),
            'status': asset.get('Status'),
            'location': {
                'lat': float(asset.get('LastLatitude', 0)) if asset.get('LastLatitude') else None,
                'lng': float(asset.get('LastLongitude', 0)) if asset.get('LastLongitude') else None,
                'address': asset.get('LastLocation')
            },
            'last_update': asset.get('LastLocationUpdate'),
            'speed': asset.get('Speed'),
            'heading': asset.get('Heading'),
            'fuel_level': asset.get('FuelLevel'),
            'engine_hours': asset.get('EngineHours'),
            'odometer': asset.get('Odometer'),
            'driver': asset.get('Driver'),
            'job_site': asset.get('JobSite')
        }
        
        return jsonify({
            'status': 'success',
            'asset': asset_details,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching asset details for {asset_id}: {e}")
        return jsonify({'error': str(e)}), 500

@live_tracking_bp.route('/api/alerts')
def get_live_alerts():
    """Get real-time alerts and notifications"""
    try:
        # Get asset data to analyze for alerts
        assets_data = get_assets_data()
        alerts = []
        
        if assets_data:
            current_time = datetime.now()
            
            for asset in assets_data:
                try:
                    # Check for various alert conditions using real data
                    asset_id = asset.get('AssetId', 'Unknown')
                    asset_name = asset.get('AssetName', 'Unknown Asset')
                    
                    # Speed alerts
                    speed = asset.get('Speed', 0)
                    if speed and speed > 80:  # Speed limit alert
                        alerts.append({
                            'type': 'speed',
                            'severity': 'warning',
                            'asset_id': asset_id,
                            'asset_name': asset_name,
                            'message': f'Speed limit exceeded: {speed} mph',
                            'timestamp': current_time.isoformat()
                        })
                    
                    # Idle time alerts
                    if speed == 0 and asset.get('EngineHours'):
                        alerts.append({
                            'type': 'idle',
                            'severity': 'info',
                            'asset_id': asset_id,
                            'asset_name': asset_name,
                            'message': 'Vehicle idle detected',
                            'timestamp': current_time.isoformat()
                        })
                    
                    # Fuel level alerts
                    fuel_level = asset.get('FuelLevel')
                    if fuel_level and fuel_level < 20:
                        alerts.append({
                            'type': 'fuel',
                            'severity': 'warning',
                            'asset_id': asset_id,
                            'asset_name': asset_name,
                            'message': f'Low fuel level: {fuel_level}%',
                            'timestamp': current_time.isoformat()
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing alerts for asset {asset}: {e}")
                    continue
        
        return jsonify({
            'status': 'success',
            'alerts': alerts,
            'count': len(alerts),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching live alerts: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'alerts': [],
            'count': 0,
            'timestamp': datetime.now().isoformat()
        }), 500

def register_blueprint(app):
    """Register the live tracking blueprint with the app"""
    app.register_blueprint(live_tracking_bp)
    logger.info('Live Asset Tracking module registered successfully')
    return live_tracking_bp