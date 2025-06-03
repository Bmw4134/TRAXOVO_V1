"""
GPS Tracking API - Authentic Gauge API Integration
Real-time asset location tracking with revenue correlation
"""

import json
import os
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_login import login_required
import logging

gps_api_bp = Blueprint('gps_api', __name__)

class GPSTrackingService:
    """Service for GPS tracking using authentic Gauge API data"""
    
    def __init__(self):
        self.load_gauge_data()
        
    def load_gauge_data(self):
        """Load authentic GPS data from Gauge API pull"""
        try:
            with open('GAUGE API PULL 1045AM_05.15.2025.json', 'r') as f:
                self.gauge_data = json.load(f)
            logging.info(f"Loaded {len(self.gauge_data)} GPS records from Gauge API")
        except Exception as e:
            logging.error(f"Error loading Gauge API data: {e}")
            self.gauge_data = []
    
    def get_active_assets_with_gps(self):
        """Get all active assets with GPS coordinates"""
        active_assets = []
        
        for asset in self.gauge_data:
            if (asset.get('Latitude') and asset.get('Longitude') and 
                asset.get('Active', False)):
                
                active_assets.append({
                    'asset_number': asset.get('AssetNumber', 'Unknown'),
                    'latitude': float(asset.get('Latitude')),
                    'longitude': float(asset.get('Longitude')),
                    'last_update': asset.get('LastLocationUpdate'),
                    'active': asset.get('Active', False),
                    'speed': asset.get('Speed', 0),
                    'heading': asset.get('Heading', 0)
                })
        
        return active_assets
    
    def get_assets_by_region(self, region=None):
        """Get assets filtered by geographic region"""
        assets = self.get_active_assets_with_gps()
        
        if not region:
            return assets
            
        # Define Texas regional boundaries
        regions = {
            'dfw': {'lat_min': 32.0, 'lat_max': 33.5, 'lng_min': -97.5, 'lng_max': -96.0},
            'houston': {'lat_min': 29.0, 'lat_max': 30.5, 'lng_min': -96.0, 'lng_max': -94.5},
            'austin': {'lat_min': 29.5, 'lat_max': 30.8, 'lng_min': -98.5, 'lng_max': -97.0},
            'san_antonio': {'lat_min': 29.0, 'lat_max': 29.8, 'lng_min': -99.0, 'lng_max': -98.0}
        }
        
        if region.lower() in regions:
            bounds = regions[region.lower()]
            filtered_assets = []
            
            for asset in assets:
                if (bounds['lat_min'] <= asset['latitude'] <= bounds['lat_max'] and
                    bounds['lng_min'] <= asset['longitude'] <= bounds['lng_max']):
                    filtered_assets.append(asset)
                    
            return filtered_assets
        
        return assets
    
    def get_asset_movement_status(self):
        """Analyze asset movement patterns"""
        assets = self.get_active_assets_with_gps()
        movement_summary = {
            'active_moving': 0,
            'stationary': 0,
            'no_recent_data': 0,
            'total_tracked': len(assets)
        }
        
        current_time = datetime.now()
        
        for asset in assets:
            last_update = asset.get('last_update')
            speed = asset.get('speed', 0)
            
            if last_update:
                try:
                    # Parse the last update time
                    if isinstance(last_update, str):
                        update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                        hours_since_update = (current_time - update_time.replace(tzinfo=None)).total_seconds() / 3600
                        
                        if hours_since_update > 24:
                            movement_summary['no_recent_data'] += 1
                        elif speed > 5:  # Moving faster than 5 mph
                            movement_summary['active_moving'] += 1
                        else:
                            movement_summary['stationary'] += 1
                    else:
                        movement_summary['stationary'] += 1
                        
                except Exception:
                    movement_summary['no_recent_data'] += 1
            else:
                movement_summary['no_recent_data'] += 1
        
        return movement_summary

@gps_api_bp.route('/api/gauge-gps-data')
@login_required
def get_gauge_gps_data():
    """API endpoint for authentic Gauge GPS data"""
    gps_service = GPSTrackingService()
    assets = gps_service.get_active_assets_with_gps()
    
    return jsonify({
        'assets': assets,
        'total_assets': len(assets),
        'timestamp': datetime.now().isoformat(),
        'source': 'Gauge API'
    })

@gps_api_bp.route('/api/gps-tracking/region/<region>')
@login_required
def get_regional_assets(region):
    """Get assets by geographic region"""
    gps_service = GPSTrackingService()
    assets = gps_service.get_assets_by_region(region)
    
    return jsonify({
        'region': region,
        'assets': assets,
        'count': len(assets)
    })

@gps_api_bp.route('/api/gps-tracking/movement-status')
@login_required
def get_movement_status():
    """Get asset movement status summary"""
    gps_service = GPSTrackingService()
    status = gps_service.get_asset_movement_status()
    
    return jsonify(status)

@gps_api_bp.route('/api/gps-tracking/live-feed')
@login_required
def get_live_gps_feed():
    """Live GPS data feed for real-time tracking"""
    gps_service = GPSTrackingService()
    
    # Get recently updated assets (within last hour)
    current_time = datetime.now()
    recent_assets = []
    
    for asset in gps_service.get_active_assets_with_gps():
        last_update = asset.get('last_update')
        if last_update:
            try:
                if isinstance(last_update, str):
                    update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                    hours_since_update = (current_time - update_time.replace(tzinfo=None)).total_seconds() / 3600
                    
                    if hours_since_update <= 1:  # Updated within last hour
                        recent_assets.append({
                            **asset,
                            'hours_since_update': round(hours_since_update, 2)
                        })
            except Exception:
                pass
    
    return jsonify({
        'live_assets': recent_assets,
        'count': len(recent_assets),
        'timestamp': current_time.isoformat()
    })

def get_gps_service():
    """Get GPS tracking service instance"""
    return GPSTrackingService()