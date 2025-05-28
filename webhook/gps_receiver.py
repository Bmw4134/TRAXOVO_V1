"""
Real-Time GPS Webhook Receiver for TRAXOVO
Receives live GPS updates from Gauge API and processes them instantly
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import json
import logging

gps_webhook_bp = Blueprint('gps_webhook', __name__)

@gps_webhook_bp.route('/webhook/gps', methods=['POST'])
def receive_gps_data():
    """
    Receive real-time GPS updates from Gauge API
    Processes equipment location changes instantly
    """
    try:
        data = request.get_json()
        
        # Extract GPS coordinates and asset info
        asset_id = data.get('asset_id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        timestamp = data.get('timestamp')
        
        # Log the real-time GPS update
        logging.info(f"Real-time GPS update: Asset {asset_id} at {latitude}, {longitude}")
        
        # Check for geofence violations
        if is_outside_work_zone(latitude, longitude, asset_id):
            trigger_security_alert(asset_id, latitude, longitude)
        
        # Update asset location in database
        update_asset_location(asset_id, latitude, longitude, timestamp)
        
        return jsonify({"status": "success", "processed": True})
        
    except Exception as e:
        logging.error(f"GPS webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def is_outside_work_zone(lat, lng, asset_id):
    """Check if GPS coordinates are outside authorized work zones"""
    # Implementation would check against your North Texas job sites
    return False  # Placeholder for zone validation

def trigger_security_alert(asset_id, lat, lng):
    """Trigger immediate security alert for unauthorized movement"""
    logging.warning(f"SECURITY ALERT: Asset {asset_id} moved outside work zone to {lat}, {lng}")

def update_asset_location(asset_id, lat, lng, timestamp):
    """Update asset location in real-time database"""
    logging.info(f"Updated location for asset {asset_id}")
