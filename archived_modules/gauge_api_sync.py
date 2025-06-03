"""
Gauge API Synchronization Module
Pulls real asset data from Gauge API and caches it every 5 minutes
"""

import os
import json
import time
import requests
import logging
from datetime import datetime, timedelta
from performance_optimizer import get_performance_optimizer

class GaugeAPISync:
    """Synchronizes asset data from Gauge API with smart caching"""
    
    def __init__(self):
        self.api_key = os.environ.get('GAUGE_API_KEY')
        self.api_url = os.environ.get('GAUGE_API_URL')
        self.optimizer = get_performance_optimizer()
        self.sync_interval = 300  # 5 minutes
        self.last_sync = 0
        
        # Asset data cache
        self.cached_assets = {}
        self.cached_drivers = {}
        self.cached_locations = {}
        
    def is_api_configured(self):
        """Check if Gauge API credentials are available"""
        return bool(self.api_key and self.api_url)
    
    def get_headers(self):
        """Get API headers with authentication"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def should_sync(self):
        """Check if data should be synced (every 5 minutes)"""
        return (time.time() - self.last_sync) > self.sync_interval
    
    def sync_assets_from_gauge(self):
        """Pull real asset data from Gauge API"""
        if not self.is_api_configured():
            logging.warning("Gauge API not configured - using Foundation data only")
            return self.get_foundation_fallback_assets()
        
        try:
            # Sync assets - handle SSL verification issues
            assets_response = requests.get(
                f"{self.api_url}",
                headers=self.get_headers(),
                timeout=30,
                verify=False  # Handle SSL certificate mismatch
            )
            
            if assets_response.status_code == 200:
                assets_data = assets_response.json()
                self.cached_assets = self.process_asset_data(assets_data)
                logging.info(f"Synced {len(self.cached_assets)} assets from Gauge API")
            else:
                logging.error(f"Gauge API assets error: {assets_response.status_code}")
                return self.get_foundation_fallback_assets()
            
            # Sync driver assignments
            drivers_response = requests.get(
                f"{self.api_url}/drivers",
                headers=self.get_headers(),
                timeout=30
            )
            
            if drivers_response.status_code == 200:
                drivers_data = drivers_response.json()
                self.cached_drivers = self.process_driver_data(drivers_data)
                logging.info(f"Synced {len(self.cached_drivers)} drivers from Gauge API")
            
            # Sync GPS locations
            locations_response = requests.get(
                f"{self.api_url}/locations",
                headers=self.get_headers(),
                timeout=30
            )
            
            if locations_response.status_code == 200:
                locations_data = locations_response.json()
                self.cached_locations = self.process_location_data(locations_data)
                logging.info(f"Synced {len(self.cached_locations)} GPS locations from Gauge API")
            
            # Cache the synced data
            self.cache_synced_data()
            self.last_sync = time.time()
            
            return self.get_consolidated_asset_data()
            
        except requests.RequestException as e:
            logging.error(f"Gauge API connection error: {e}")
            return self.get_foundation_fallback_assets()
        except Exception as e:
            logging.error(f"Gauge API sync error: {e}")
            return self.get_foundation_fallback_assets()
    
    def process_asset_data(self, api_data):
        """Process raw asset data from Gauge API"""
        processed_assets = {}
        
        for asset in api_data.get('assets', []):
            asset_id = asset.get('id') or asset.get('asset_id')
            processed_assets[asset_id] = {
                'id': asset_id,
                'name': asset.get('name', 'Unknown Asset'),
                'type': asset.get('type', 'Equipment'),
                'status': asset.get('status', 'unknown'),
                'gps_enabled': asset.get('gps_enabled', False),
                'last_seen': asset.get('last_seen'),
                'operator': asset.get('operator'),
                'job_site': asset.get('job_site'),
                'utilization': asset.get('utilization', 0),
                'maintenance_due': asset.get('maintenance_due'),
                'revenue_generated': asset.get('revenue_generated', 0)
            }
        
        return processed_assets
    
    def process_driver_data(self, api_data):
        """Process driver assignment data from Gauge API"""
        processed_drivers = {}
        
        for driver in api_data.get('drivers', []):
            driver_id = driver.get('id') or driver.get('driver_id')
            processed_drivers[driver_id] = {
                'id': driver_id,
                'name': driver.get('name', 'Unknown Driver'),
                'status': driver.get('status', 'unknown'),
                'current_asset': driver.get('current_asset'),
                'check_in_time': driver.get('check_in_time'),
                'location': driver.get('location'),
                'phone': driver.get('phone')
            }
        
        return processed_drivers
    
    def process_location_data(self, api_data):
        """Process GPS location data from Gauge API"""
        processed_locations = {}
        
        for location in api_data.get('locations', []):
            asset_id = location.get('asset_id')
            if asset_id:
                processed_locations[asset_id] = {
                    'asset_id': asset_id,
                    'latitude': location.get('latitude'),
                    'longitude': location.get('longitude'),
                    'timestamp': location.get('timestamp'),
                    'speed': location.get('speed', 0),
                    'heading': location.get('heading', 0),
                    'accuracy': location.get('accuracy', 0)
                }
        
        return processed_locations
    
    def cache_synced_data(self):
        """Cache synced data using performance optimizer"""
        cache_data = {
            'assets': self.cached_assets,
            'drivers': self.cached_drivers,
            'locations': self.cached_locations,
            'sync_time': datetime.now().isoformat(),
            'next_sync': (datetime.now() + timedelta(seconds=self.sync_interval)).isoformat()
        }
        
        self.optimizer.save_to_cache('gauge_api_sync', cache_data)
    
    def load_cached_data(self):
        """Load cached Gauge API data"""
        cached_data = self.optimizer.load_from_cache('gauge_api_sync')
        
        if cached_data:
            self.cached_assets = cached_data.get('assets', {})
            self.cached_drivers = cached_data.get('drivers', {})
            self.cached_locations = cached_data.get('locations', {})
            return True
        
        return False
    
    def get_foundation_fallback_assets(self):
        """Fallback to Foundation data when Gauge API unavailable"""
        logging.info("Using Foundation fallback data - Gauge API sync unavailable")
        return {
            'total_assets': 0,  # Will be populated from real API call
            'gps_enabled': 0,   # Will be populated from real API call  
            'active_assets': 0, # Will be populated from real API call
            'maintenance_due': 0,
            'note': 'Connecting to Gauge API for real asset data...',
            'assets': {},
            'drivers': {},
            'locations': {}
        }
    
    def get_consolidated_asset_data(self):
        """Get consolidated asset data from all sources"""
        return {
            'total_assets': len(self.cached_assets),
            'gps_enabled': sum(1 for asset in self.cached_assets.values() if asset.get('gps_enabled')),
            'active_assets': sum(1 for asset in self.cached_assets.values() if asset.get('status') == 'active'),
            'maintenance_due': sum(1 for asset in self.cached_assets.values() if asset.get('maintenance_due')),
            'assets': self.cached_assets,
            'drivers': self.cached_drivers,
            'locations': self.cached_locations,
            'last_sync': datetime.fromtimestamp(self.last_sync).isoformat() if self.last_sync else None,
            'sync_source': 'gauge_api'
        }
    
    def get_asset_details(self, asset_id):
        """Get detailed information for a specific asset"""
        if asset_id in self.cached_assets:
            asset = self.cached_assets[asset_id]
            location = self.cached_locations.get(asset_id, {})
            
            return {
                **asset,
                'gps_location': location,
                'real_time': True,
                'data_source': 'gauge_api'
            }
        
        return {
            'asset_id': asset_id,
            'name': f'Asset {asset_id}',
            'status': 'unknown',
            'note': 'Asset details require Gauge API connection',
            'real_time': False,
            'data_source': 'foundation_fallback'
        }
    
    def sync_now(self):
        """Force immediate sync with Gauge API"""
        self.last_sync = 0  # Force sync
        return self.sync_assets_from_gauge()
    
    def get_sync_status(self):
        """Get synchronization status"""
        return {
            'api_configured': self.is_api_configured(),
            'last_sync': datetime.fromtimestamp(self.last_sync).isoformat() if self.last_sync else None,
            'next_sync': (datetime.fromtimestamp(self.last_sync + self.sync_interval)).isoformat() if self.last_sync else None,
            'sync_interval_minutes': self.sync_interval / 60,
            'cached_assets': len(self.cached_assets),
            'cached_drivers': len(self.cached_drivers),
            'cached_locations': len(self.cached_locations)
        }

# Global sync instance
gauge_sync = GaugeAPISync()

def get_gauge_sync():
    """Get the global Gauge API sync instance"""
    return gauge_sync

def get_real_asset_data():
    """Get real asset data with automatic 5-minute sync"""
    sync = get_gauge_sync()
    
    # Load cached data first
    sync.load_cached_data()
    
    # Sync if needed
    if sync.should_sync():
        return sync.sync_assets_from_gauge()
    else:
        return sync.get_consolidated_asset_data()