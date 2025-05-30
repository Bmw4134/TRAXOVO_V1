"""
Master Data Synchronization Engine
Syncs authentic Gauge API data into Supabase for unified access
"""

import os
import requests
import logging
from datetime import datetime
from typing import Dict, List, Any
from urllib3 import disable_warnings
disable_warnings()

logger = logging.getLogger(__name__)

class MasterDataSync:
    """Synchronizes authentic data between Gauge API and Supabase"""
    
    def __init__(self):
        # Gauge API credentials (working authentication)
        self.gauge_username = 'bwatson'
        self.gauge_password = 'Plsw@2900413477'
        self.asset_list_id = '28dcba94c01e453fa8e9215a068f30e4'
        self.gauge_url = 'https://api.gaugesmart.com'
        
        # Initialize Supabase
        self.supabase_client = None
        self._init_supabase()
    
    def _init_supabase(self):
        """Initialize Supabase connection"""
        try:
            from services.supabase_client import get_supabase_client
            self.supabase_client = get_supabase_client()
            logger.info("Supabase connection initialized")
        except Exception as e:
            logger.error(f"Supabase initialization error: {e}")
    
    def sync_authentic_assets(self) -> Dict[str, Any]:
        """Sync all 717 authentic assets from Gauge API to Supabase"""
        
        try:
            # Get authentic assets from Gauge API
            gauge_assets = self._fetch_gauge_assets()
            
            if not gauge_assets:
                return {'status': 'error', 'message': 'No assets retrieved from Gauge API'}
            
            # Process and sync to Supabase
            synced_count = 0
            active_count = 0
            
            for asset in gauge_assets:
                asset_data = self._process_asset_data(asset)
                
                if self._sync_asset_to_supabase(asset_data):
                    synced_count += 1
                    if asset_data.get('is_active'):
                        active_count += 1
            
            return {
                'status': 'success',
                'total_assets': len(gauge_assets),
                'synced_assets': synced_count,
                'active_assets': active_count,
                'sync_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Asset sync error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _fetch_gauge_assets(self) -> List[Dict]:
        """Fetch authentic assets from Gauge API"""
        
        try:
            endpoint = f"{self.gauge_url}/AssetList/{self.asset_list_id}"
            
            response = requests.get(
                endpoint,
                auth=(self.gauge_username, self.gauge_password),
                timeout=15,
                verify=False
            )
            
            if response.status_code == 200:
                assets = response.json()
                logger.info(f"Retrieved {len(assets)} authentic assets from Gauge API")
                return assets
            else:
                logger.error(f"Gauge API error {response.status_code}: {response.text[:200]}")
                return []
                
        except Exception as e:
            logger.error(f"Gauge API fetch error: {e}")
            return []
    
    def _process_asset_data(self, gauge_asset: Dict) -> Dict:
        """Process Gauge asset data for Supabase storage"""
        
        # Extract core data
        asset_id = gauge_asset.get('AssetIdentifier', '')
        name = gauge_asset.get('Label', 'Unknown Asset')
        gps_enabled = gauge_asset.get('IsGPSEnabled', False)
        
        # Determine category from asset name/ID
        category = self._determine_category(asset_id, name)
        
        # Process location data
        location_data = None
        last_location = gauge_asset.get('LastKnownLocation')
        if isinstance(last_location, dict):
            lat = last_location.get('Latitude')
            lng = last_location.get('Longitude')
            if lat and lng:
                location_data = {
                    'latitude': float(lat),
                    'longitude': float(lng),
                    'timestamp': last_location.get('Timestamp')
                }
        
        # Asset is active if it has GPS and valid identifier
        is_active = bool(gps_enabled and asset_id and asset_id != '')
        
        return {
            'asset_id': asset_id,
            'name': name,
            'category': category,
            'is_active': is_active,
            'gps_enabled': gps_enabled,
            'location': location_data,
            'raw_gauge_data': gauge_asset  # Store full data for reference
        }
    
    def _determine_category(self, asset_id: str, name: str) -> str:
        """Determine asset category from ID and name"""
        
        combined = f"{asset_id} {name}".upper()
        
        if any(term in combined for term in ['EX-', 'EXCAVATOR', 'CAT320', 'CAT330']):
            return 'Excavators'
        elif any(term in combined for term in ['BH-', 'BACKHOE']):
            return 'Backhoes'
        elif any(term in combined for term in ['DOZ-', 'DOZER', 'D6T', 'D8T']):
            return 'Dozers'
        elif any(term in combined for term in ['TRK-', 'TRUCK', 'F150', 'F250', 'F350']):
            return 'Trucks'
        elif any(term in combined for term in ['GRD-', 'GRADER', '140M', '160M']):
            return 'Graders'
        elif any(term in combined for term in ['CRN-', 'CRANE']):
            return 'Cranes'
        elif any(term in combined for term in ['SKS-', 'SKID', 'BOBCAT']):
            return 'Skid Steers'
        else:
            return 'Other Equipment'
    
    def _sync_asset_to_supabase(self, asset_data: Dict) -> bool:
        """Sync individual asset to Supabase"""
        
        if not self.supabase_client or not self.supabase_client.connected:
            return False
        
        try:
            # Use upsert to handle duplicates
            response = self.supabase_client.client.table('assets').upsert(
                asset_data,
                on_conflict='asset_id'
            ).execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Asset sync error for {asset_data.get('asset_id')}: {e}")
            return False
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status and asset counts"""
        
        if not self.supabase_client or not self.supabase_client.connected:
            return {
                'status': 'supabase_disconnected',
                'message': 'Supabase connection required'
            }
        
        try:
            # Get asset counts from Supabase
            response = self.supabase_client.client.table('assets').select('asset_id, is_active, category').execute()
            assets = response.data if response.data else []
            
            total_count = len(assets)
            active_count = len([a for a in assets if a.get('is_active')])
            
            # Category breakdown
            categories = {}
            for asset in assets:
                cat = asset.get('category', 'Unknown')
                categories[cat] = categories.get(cat, 0) + 1
            
            return {
                'status': 'synchronized',
                'total_assets': total_count,
                'active_assets': active_count,
                'categories': categories,
                'utilization_rate': round((active_count / total_count * 100), 1) if total_count > 0 else 0,
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Sync status error: {e}")
            return {'status': 'error', 'message': str(e)}

# Global instance
master_sync = MasterDataSync()

def get_master_sync():
    """Get the global master sync instance"""
    return master_sync

def sync_all_data():
    """Convenience function to sync all data"""
    return master_sync.sync_authentic_assets()