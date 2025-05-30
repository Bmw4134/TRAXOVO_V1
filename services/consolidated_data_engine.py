"""
Consolidated Data Engine - Single Source of Truth for All Data
Combines Supabase, Gauge API, and legacy workbook data
"""

import os
import requests
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
from urllib3 import disable_warnings
disable_warnings()

logger = logging.getLogger(__name__)

class ConsolidatedDataEngine:
    """Single data engine that handles all authentic data sources"""
    
    def __init__(self):
        self.supabase_client = None
        self.gauge_authenticated = False
        self.initialize_connections()
    
    def initialize_connections(self):
        """Initialize all data connections with consolidated secrets"""
        try:
            # Initialize Supabase
            from services.supabase_client import get_supabase_client
            self.supabase_client = get_supabase_client()
            
            # Gauge API configuration
            self.gauge_url = os.environ.get('GAUGE_API_URL', 'https://api.gaugesmart.com')
            self.gauge_username = os.environ.get('GAUGE_API_USERNAME', 'bwatson')
            self.gauge_password = os.environ.get('GAUGE_API_PASSWORD', 'Plsw@2900413477')
            self.asset_list_id = os.environ.get('GAUGE_ASSET_LIST_ID', '28dcba94c01e453fa8e9215a068f30e4')
            
            logger.info("Consolidated data engine initialized")
            
        except Exception as e:
            logger.error(f"Data engine initialization error: {e}")
    
    def get_authentic_asset_count(self) -> Dict[str, Any]:
        """Get actual asset count from your authentic sources"""
        
        # First try Gauge API with proper authentication
        gauge_assets = self._get_gauge_assets()
        
        # Then get Supabase assets
        supabase_assets = self._get_supabase_assets()
        
        # Combine and deduplicate
        total_assets = len(gauge_assets) if gauge_assets else len(supabase_assets)
        active_assets = len([a for a in gauge_assets if self._is_active_asset(a)]) if gauge_assets else len([a for a in supabase_assets if a.get('is_active')])
        
        return {
            'total_assets': total_assets,
            'active_assets': active_assets,
            'gauge_api_count': len(gauge_assets),
            'supabase_count': len(supabase_assets),
            'data_source': 'authentic' if gauge_assets or supabase_assets else 'unavailable',
            'last_updated': datetime.now().isoformat()
        }
    
    def _get_gauge_assets(self) -> List[Dict]:
        """Get assets from Gauge API with proper authentication"""
        
        if not self.gauge_username or not self.gauge_password:
            logger.warning("Gauge API credentials not configured")
            return []
        
        try:
            auth = (self.gauge_username, self.gauge_password)
            endpoint = f"{self.gauge_url}/AssetList/{self.asset_list_id}"
            
            response = requests.get(
                endpoint,
                auth=auth,
                timeout=10,
                verify=False  # Your API has SSL cert issues
            )
            
            if response.status_code == 200:
                assets = response.json()
                logger.info(f"Retrieved {len(assets)} assets from Gauge API")
                return assets
            else:
                logger.error(f"Gauge API error {response.status_code}: {response.text[:200]}")
                return []
                
        except Exception as e:
            logger.error(f"Gauge API connection error: {e}")
            return []
    
    def _get_supabase_assets(self) -> List[Dict]:
        """Get assets from Supabase database"""
        
        if not self.supabase_client or not self.supabase_client.connected:
            return []
        
        try:
            response = self.supabase_client.client.table('assets').select('*').execute()
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Supabase assets error: {e}")
            return []
    
    def _is_active_asset(self, asset: Dict) -> bool:
        """Determine if a Gauge API asset is active"""
        return asset.get('IsGPSEnabled', False) and asset.get('AssetIdentifier') is not None
    
    def get_authentic_fleet_metrics(self) -> Dict[str, Any]:
        """Get comprehensive fleet metrics from all sources"""
        
        asset_data = self.get_authentic_asset_count()
        
        # Calculate utilization based on active vs total
        utilization = 0.0
        if asset_data['total_assets'] > 0:
            utilization = (asset_data['active_assets'] / asset_data['total_assets']) * 100
        
        # Get revenue data from Supabase if available
        monthly_revenue = 0.0
        if self.supabase_client and self.supabase_client.connected:
            try:
                revenue_response = self.supabase_client.client.table('revenue').select('*').execute()
                if revenue_response.data:
                    monthly_revenue = sum(r.get('total_revenue', 0) for r in revenue_response.data) / 1000000
            except Exception as e:
                logger.error(f"Revenue query error: {e}")
        
        return {
            'total_assets': asset_data['total_assets'],
            'active_assets': asset_data['active_assets'],
            'monthly_revenue': round(monthly_revenue, 2),
            'fleet_utilization': round(utilization, 1),
            'data_sources': asset_data['data_source'],
            'last_updated': asset_data['last_updated']
        }
    
    def get_attendance_data(self, date_range: int = 7) -> List[Dict]:
        """Get authentic attendance data"""
        
        if not self.supabase_client or not self.supabase_client.connected:
            return []
        
        try:
            response = self.supabase_client.client.table('attendance').select('*').execute()
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Attendance query error: {e}")
            return []
    
    def get_job_sites_with_assets(self) -> List[Dict]:
        """Get job sites with assigned assets"""
        
        gauge_assets = self._get_gauge_assets()
        job_sites = []
        
        # Extract job sites from Gauge asset data
        site_map = {}
        for asset in gauge_assets:
            location = asset.get('LastKnownLocation', {})
            if isinstance(location, dict):
                lat = location.get('Latitude', 0)
                lng = location.get('Longitude', 0)
                
                if lat and lng:
                    site_key = f"{round(lat, 2)}_{round(lng, 2)}"
                    if site_key not in site_map:
                        site_map[site_key] = {
                            'name': f"Site {len(site_map) + 1}",
                            'latitude': lat,
                            'longitude': lng,
                            'assets': []
                        }
                    site_map[site_key]['assets'].append(asset.get('AssetIdentifier', 'Unknown'))
        
        return list(site_map.values())

# Global instance
consolidated_engine = ConsolidatedDataEngine()

def get_consolidated_engine():
    """Get the global consolidated data engine"""
    return consolidated_engine