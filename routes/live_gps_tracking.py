"""
Live GPS Tracking Module

Real-time GPS tracking dashboard using authentic Gauge API data
for fleet monitoring and driver location updates.
"""

from flask import Blueprint, render_template, jsonify, request
import logging
from datetime import datetime, timedelta
from utils.gauge_api_integration import get_live_gps_data, get_asset_locations

live_gps_bp = Blueprint('live_gps', __name__)
logger = logging.getLogger(__name__)

@live_gps_bp.route('/live-gps-tracking')
def live_gps_dashboard():
    """Main live GPS tracking dashboard"""
    try:
        # Get current GPS data from Gauge API
        gps_data = get_live_gps_data()
        
        # Get asset locations and status
        asset_locations = get_asset_locations()
        
        # Calculate dashboard metrics
        metrics = {
            'total_vehicles': len(asset_locations) if asset_locations else 0,
            'vehicles_moving': 0,
            'vehicles_idle': 0,
            'vehicles_offline': 0,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Count vehicle statuses
        if asset_locations:
            for vehicle in asset_locations:
                status = vehicle.get('status', 'offline').lower()
                if status == 'moving':
                    metrics['vehicles_moving'] += 1
                elif status == 'idle':
                    metrics['vehicles_idle'] += 1
                else:
                    metrics['vehicles_offline'] += 1
        
        return render_template('live_gps_tracking.html',
                             gps_data=gps_data,
                             asset_locations=asset_locations,
                             metrics=metrics)
        
    except Exception as e:
        logger.error(f"Error in live GPS dashboard: {e}")
        return render_template('live_gps_tracking.html',
                             gps_data=None,
                             asset_locations=[],
                             metrics={
                                 'total_vehicles': 0,
                                 'vehicles_moving': 0,
                                 'vehicles_idle': 0,
                                 'vehicles_offline': 0,
                                 'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                             })

@live_gps_bp.route('/api/live-gps-data')
def api_live_gps_data():
    """API endpoint for real-time GPS data updates"""
    try:
        gps_data = get_live_gps_data()
        asset_locations = get_asset_locations()
        
        return jsonify({
            'success': True,
            'data': {
                'gps_data': gps_data,
                'asset_locations': asset_locations,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting live GPS data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@live_gps_bp.route('/api/vehicle-location/<vehicle_id>')
def api_vehicle_location(vehicle_id):
    """Get specific vehicle location and details"""
    try:
        # Get specific vehicle data from Gauge API
        vehicle_data = get_vehicle_details(vehicle_id)
        
        return jsonify({
            'success': True,
            'vehicle': vehicle_data
        })
        
    except Exception as e:
        logger.error(f"Error getting vehicle location for {vehicle_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_vehicle_details(vehicle_id):
    """Get detailed information for a specific vehicle"""
    try:
        # This would integrate with your Gauge API
        from gauge_api import GaugeAPI
        api = GaugeAPI()
        
        vehicle_details = api.get_asset_details(vehicle_id)
        return vehicle_details
        
    except Exception as e:
        logger.error(f"Error getting vehicle details: {e}")
        return None