"""
Geolocation Tracking Routes

This module provides routes for the real-time geolocation tracking feature,
which displays asset locations on a map with playful markers and animations.
"""
import os
import logging
import random
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from utils.activity_logger import log_navigation
from gauge_api import get_asset_data, update_asset_data

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
        # Get current asset data from Gauge API
        assets = get_asset_data(force_update=True)
        
        # Check if we got data from the API
        if not assets or len(assets) == 0:
            # If no assets or API error, inform the user
            logger.warning("No asset data available from Gauge API")
            return jsonify({
                'status': 'error',
                'message': "No asset location data available. Please check your Gauge API credentials.",
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # Log the number of assets retrieved
        logger.info(f"Retrieved {len(assets)} assets from Gauge API")
        
        # Process asset data for map display
        processed_assets = process_assets_for_map(assets)
        
        # Return the asset data as JSON
        return jsonify({
            'status': 'success',
            'assets': processed_assets,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error retrieving asset locations: {str(e)}")
        
        # We want to inform the user about connection issues
        return jsonify({
            'status': 'error',
            'message': f"Failed to retrieve asset locations from Gauge API. Please check your API credentials and connection.",
            'timestamp': datetime.now().isoformat()
        }), 500

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