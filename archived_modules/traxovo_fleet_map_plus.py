"""
TRAXOVO Fleet Map Plus - Real-time GPS tracking with 10-15 second updates
Superior to Gauge SmartHub Map with enhanced UI/UX and instant feedback
"""

import json
import os
import requests
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
import logging

fleet_map_bp = Blueprint('fleet_map', __name__)

class TRAXOVOFleetMap:
    """Advanced fleet mapping with real-time GPS updates"""
    
    def __init__(self):
        self.gauge_api_key = os.environ.get('GAUGE_API_KEY')
        self.update_interval = 15  # 15-second updates
        self.last_update = None
        
    def get_real_time_assets(self):
        """Get real-time asset locations from Gauge API"""
        if not self.gauge_api_key:
            return {
                'error': 'API_KEY_REQUIRED',
                'message': 'Gauge API key required for real fleet data',
                'assets': []
            }
        
        try:
            headers = {
                'Authorization': f'Bearer {self.gauge_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Gauge API endpoint for asset locations
            response = requests.get(
                'https://api.gauge.sh/v1/assets/locations',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                assets = self._process_asset_data(data)
                self.last_update = datetime.now()
                return {
                    'success': True,
                    'assets': assets,
                    'last_update': self.last_update.isoformat(),
                    'total_assets': len(assets)
                }
            else:
                return {
                    'error': 'API_ERROR',
                    'message': f'API returned status {response.status_code}',
                    'assets': []
                }
                
        except Exception as e:
            logging.error(f"Fleet map API error: {e}")
            return {
                'error': 'CONNECTION_ERROR',
                'message': 'Unable to connect to Gauge API',
                'assets': []
            }
    
    def _process_asset_data(self, api_data):
        """Process Gauge API data into map-ready format"""
        processed_assets = []
        
        for asset in api_data.get('assets', []):
            # Only include billable assets
            if asset.get('billable', False):
                processed_asset = {
                    'asset_id': asset.get('id'),
                    'name': asset.get('name'),
                    'lat': asset.get('latitude'),
                    'lng': asset.get('longitude'),
                    'status': self._determine_status(asset),
                    'last_seen': asset.get('last_update'),
                    'job_site': asset.get('job_site'),
                    'operator': asset.get('operator'),
                    'hours_today': asset.get('hours_today', 0),
                    'fuel_level': asset.get('fuel_level'),
                    'engine_hours': asset.get('engine_hours'),
                    'alerts': asset.get('active_alerts', [])
                }
                processed_assets.append(processed_asset)
        
        return processed_assets
    
    def _determine_status(self, asset):
        """Determine asset operational status"""
        last_update = asset.get('last_update')
        if not last_update:
            return 'offline'
        
        # Check if asset updated within last 5 minutes
        try:
            last_seen = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
            time_diff = datetime.now() - last_seen.replace(tzinfo=None)
            
            if time_diff.total_seconds() < 300:  # 5 minutes
                if asset.get('engine_running'):
                    return 'active'
                else:
                    return 'idle'
            else:
                return 'offline'
        except:
            return 'unknown'
    
    def get_job_sites(self):
        """Get active job site locations for geofencing"""
        # This would typically come from your job management system
        return [
            {
                'name': 'Downtown Construction Site',
                'lat': 32.7767,
                'lng': -96.7970,
                'radius': 500,  # meters
                'active_assets': 8
            },
            {
                'name': 'Highway 75 Expansion',
                'lat': 32.8207,
                'lng': -96.7729,
                'radius': 1000,
                'active_assets': 12
            }
        ]

# Initialize fleet map service
fleet_map_service = TRAXOVOFleetMap()

@fleet_map_bp.route('/fleet-map')
def fleet_map_interface():
    """Fleet Map interface with real-time updates"""
    return render_template('fleet_map.html')

@fleet_map_bp.route('/api/fleet-assets')
def api_fleet_assets():
    """Real-time asset location data"""
    assets_data = fleet_map_service.get_real_time_assets()
    return jsonify(assets_data)

@fleet_map_bp.route('/api/job-sites')
def api_job_sites():
    """Active job site locations"""
    job_sites = fleet_map_service.get_job_sites()
    return jsonify({
        'success': True,
        'job_sites': job_sites
    })

@fleet_map_bp.route('/api/asset-details/<asset_id>')
def api_asset_details(asset_id):
    """Detailed asset information"""
    # This would fetch detailed asset data
    return jsonify({
        'asset_id': asset_id,
        'name': f'Asset {asset_id}',
        'status': 'active',
        'details': {
            'engine_hours': 2847,
            'fuel_level': 75,
            'last_maintenance': '2025-05-15',
            'operator': 'John Smith',
            'current_job': 'Downtown Site'
        }
    })

@fleet_map_bp.route('/api/fleet-stats')
def api_fleet_stats():
    """Real-time fleet statistics for map sidebar"""
    assets_data = fleet_map_service.get_real_time_assets()
    
    if 'error' in assets_data:
        return jsonify({
            'error': assets_data['error'],
            'message': assets_data['message']
        })
    
    assets = assets_data['assets']
    
    stats = {
        'total_assets': len(assets),
        'active': len([a for a in assets if a['status'] == 'active']),
        'idle': len([a for a in assets if a['status'] == 'idle']),
        'offline': len([a for a in assets if a['status'] == 'offline']),
        'alerts': sum(len(a['alerts']) for a in assets),
        'last_update': assets_data.get('last_update')
    }
    
    return jsonify(stats)