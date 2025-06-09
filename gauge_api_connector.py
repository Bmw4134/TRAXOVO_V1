"""
Real GAUGE API Connector - Using authentic credentials from environment
Implements full telemetry, asset tracking, and real-time data integration
"""

import os
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class GaugeAPIConnector:
    def __init__(self):
        # Load credentials from environment secrets
        self.api_endpoint = os.environ.get('GAUGE_API_ENDPOINT')
        self.auth_token = os.environ.get('GAUGE_AUTH_TOKEN') 
        self.client_id = os.environ.get('GAUGE_CLIENT_ID')
        self.client_secret = os.environ.get('GAUGE_CLIENT_SECRET')
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TRAXOVO-NEXUS-API/1.0'
        })
        
        self.authenticated = False
        self.access_token = None
        self.last_auth_time = None
        
        if self.auth_token:
            self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
            self.authenticated = True
    
    def authenticate(self):
        """Authenticate with GAUGE API using provided credentials"""
        if not self.api_endpoint or not self.client_id:
            logging.error("GAUGE API credentials not configured")
            return False
        
        try:
            auth_url = f"{self.api_endpoint}/oauth/token"
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'read:assets read:telemetry read:maintenance'
            }
            
            response = self.session.post(auth_url, json=auth_data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
                self.authenticated = True
                self.last_auth_time = datetime.now()
                logging.info("✓ GAUGE API authentication successful")
                return True
            else:
                logging.error(f"GAUGE API auth failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"GAUGE API authentication error: {e}")
            return False
    
    def test_connection(self):
        """Test GAUGE API connection and authentication"""
        if not self.authenticated and not self.authenticate():
            return {
                'status': 'error',
                'message': 'Failed to authenticate with GAUGE API',
                'connected': False,
                'last_sync': None
            }
        
        try:
            # Test with health check endpoint
            health_url = f"{self.api_endpoint}/api/v1/health"
            response = self.session.get(health_url, timeout=15)
            
            if response.status_code == 200:
                return {
                    'status': 'connected',
                    'message': 'GAUGE API connection successful',
                    'connected': True,
                    'last_sync': datetime.now().isoformat(),
                    'endpoint': self.api_endpoint,
                    'response_time': f"{response.elapsed.total_seconds():.2f}s"
                }
            else:
                return {
                    'status': 'error',
                    'message': f'GAUGE API returned {response.status_code}',
                    'connected': False,
                    'last_sync': None
                }
                
        except requests.exceptions.Timeout:
            return {
                'status': 'timeout',
                'message': 'GAUGE API connection timeout',
                'connected': False,
                'last_sync': None
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Connection error: {str(e)}',
                'connected': False,
                'last_sync': None
            }
    
    def get_fleet_assets(self):
        """Retrieve complete fleet asset inventory from GAUGE API"""
        if not self.authenticated and not self.authenticate():
            return []
        
        try:
            assets_url = f"{self.api_endpoint}/api/v1/assets"
            response = self.session.get(assets_url, timeout=30)
            
            if response.status_code == 200:
                assets_data = response.json()
                return self.process_asset_data(assets_data)
            else:
                logging.error(f"Failed to fetch assets: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"Error fetching fleet assets: {e}")
            return []
    
    def get_real_time_telemetry(self, asset_ids: List[str] = None):
        """Get real-time telemetry data for specified assets"""
        if not self.authenticated and not self.authenticate():
            return {}
        
        try:
            telemetry_url = f"{self.api_endpoint}/api/v1/telemetry/live"
            params = {}
            if asset_ids:
                params['asset_ids'] = ','.join(asset_ids)
            
            response = self.session.get(telemetry_url, params=params, timeout=30)
            
            if response.status_code == 200:
                telemetry_data = response.json()
                return self.process_telemetry_data(telemetry_data)
            else:
                logging.error(f"Failed to fetch telemetry: {response.status_code}")
                return {}
                
        except Exception as e:
            logging.error(f"Error fetching telemetry: {e}")
            return {}
    
    def get_maintenance_schedule(self):
        """Retrieve maintenance scheduling data from GAUGE API"""
        if not self.authenticated and not self.authenticate():
            return []
        
        try:
            maintenance_url = f"{self.api_endpoint}/api/v1/maintenance/schedule"
            response = self.session.get(maintenance_url, timeout=30)
            
            if response.status_code == 200:
                maintenance_data = response.json()
                return self.process_maintenance_data(maintenance_data)
            else:
                logging.error(f"Failed to fetch maintenance data: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"Error fetching maintenance data: {e}")
            return []
    
    def get_asset_locations(self):
        """Get GPS locations for all fleet assets"""
        if not self.authenticated and not self.authenticate():
            return {}
        
        try:
            locations_url = f"{self.api_endpoint}/api/v1/assets/locations"
            response = self.session.get(locations_url, timeout=30)
            
            if response.status_code == 200:
                location_data = response.json()
                return self.process_location_data(location_data)
            else:
                logging.error(f"Failed to fetch locations: {response.status_code}")
                return {}
                
        except Exception as e:
            logging.error(f"Error fetching asset locations: {e}")
            return {}
    
    def process_asset_data(self, raw_data):
        """Process raw asset data from GAUGE API"""
        processed_assets = []
        
        assets = raw_data.get('assets', []) if isinstance(raw_data, dict) else raw_data
        
        for asset in assets:
            processed_asset = {
                'asset_id': asset.get('id'),
                'asset_type': asset.get('type'),
                'make': asset.get('make'),
                'model': asset.get('model'),
                'year': asset.get('year'),
                'serial_number': asset.get('serial_number'),
                'status': asset.get('status', 'active'),
                'location': asset.get('last_known_location'),
                'engine_hours': asset.get('engine_hours', 0),
                'odometer': asset.get('odometer', 0),
                'fuel_level': asset.get('fuel_level'),
                'battery_voltage': asset.get('battery_voltage'),
                'last_update': asset.get('last_update'),
                'division': asset.get('division'),
                'project': asset.get('current_project')
            }
            processed_assets.append(processed_asset)
        
        return processed_assets
    
    def process_telemetry_data(self, raw_data):
        """Process real-time telemetry data"""
        processed_telemetry = {}
        
        telemetry = raw_data.get('telemetry', {}) if isinstance(raw_data, dict) else raw_data
        
        for asset_id, data in telemetry.items():
            processed_telemetry[asset_id] = {
                'timestamp': data.get('timestamp'),
                'location': {
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'altitude': data.get('altitude')
                },
                'engine': {
                    'hours': data.get('engine_hours'),
                    'rpm': data.get('engine_rpm'),
                    'temperature': data.get('engine_temp'),
                    'oil_pressure': data.get('oil_pressure')
                },
                'fuel': {
                    'level': data.get('fuel_level'),
                    'consumption_rate': data.get('fuel_consumption'),
                    'tank_capacity': data.get('tank_capacity')
                },
                'operational': {
                    'status': data.get('operational_status'),
                    'idle_time': data.get('idle_time'),
                    'working_time': data.get('working_time'),
                    'utilization': data.get('utilization_pct')
                }
            }
        
        return processed_telemetry
    
    def process_maintenance_data(self, raw_data):
        """Process maintenance scheduling data"""
        processed_maintenance = []
        
        maintenance_items = raw_data.get('maintenance', []) if isinstance(raw_data, dict) else raw_data
        
        for item in maintenance_items:
            processed_item = {
                'asset_id': item.get('asset_id'),
                'maintenance_type': item.get('type'),
                'due_date': item.get('due_date'),
                'due_hours': item.get('due_hours'),
                'priority': item.get('priority', 'medium'),
                'description': item.get('description'),
                'estimated_cost': item.get('estimated_cost'),
                'estimated_downtime': item.get('estimated_downtime'),
                'vendor': item.get('vendor'),
                'status': item.get('status', 'scheduled')
            }
            processed_maintenance.append(processed_item)
        
        return processed_maintenance
    
    def process_location_data(self, raw_data):
        """Process GPS location data"""
        processed_locations = {}
        
        locations = raw_data.get('locations', {}) if isinstance(raw_data, dict) else raw_data
        
        for asset_id, location in locations.items():
            processed_locations[asset_id] = {
                'latitude': location.get('lat'),
                'longitude': location.get('lng'),
                'timestamp': location.get('timestamp'),
                'address': location.get('address'),
                'site_name': location.get('site_name'),
                'geofence': location.get('geofence'),
                'speed': location.get('speed'),
                'heading': location.get('heading')
            }
        
        return processed_locations
    
    def get_comprehensive_dashboard_data(self):
        """Get all data needed for comprehensive dashboard"""
        dashboard_data = {
            'connection_status': self.test_connection(),
            'fleet_assets': self.get_fleet_assets(),
            'telemetry': self.get_real_time_telemetry(),
            'maintenance': self.get_maintenance_schedule(),
            'locations': self.get_asset_locations(),
            'last_updated': datetime.now().isoformat()
        }
        
        return dashboard_data

# Initialize global GAUGE connector
gauge_connector = GaugeAPIConnector()