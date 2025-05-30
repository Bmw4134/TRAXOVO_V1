"""
Deployment-Ready Data Engine
Uses authentic Gauge API data directly for immediate deployment
"""

import os
import requests
import logging
from datetime import datetime
from typing import Dict, List, Any
from urllib3 import disable_warnings
disable_warnings()

logger = logging.getLogger(__name__)

class DeploymentDataEngine:
    """Production-ready data engine using authentic Gauge API"""
    
    def __init__(self):
        # Working Gauge API credentials
        self.gauge_username = 'bwatson'
        self.gauge_password = 'Plsw@2900413477'
        self.asset_list_id = '28dcba94c01e453fa8e9215a068f30e4'
        self.gauge_url = 'https://api.gaugesmart.com'
        
        # Cache for performance
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes
        
    def get_fleet_metrics(self) -> Dict[str, Any]:
        """Get authentic fleet metrics for dashboard"""
        
        assets = self._get_cached_assets()
        
        if not assets:
            return {
                'total_assets': 0,
                'active_assets': 0,
                'monthly_revenue': 0.0,
                'fleet_utilization': 0.0,
                'status': 'api_connection_needed'
            }
        
        # Calculate real metrics from authentic data
        total_assets = len(assets)
        active_assets = len([a for a in assets if a.get('IsGPSEnabled', False)])
        
        # Calculate utilization based on GPS-enabled assets
        utilization = (active_assets / total_assets * 100) if total_assets > 0 else 0
        
        # Revenue calculation based on asset categories
        monthly_revenue = self._calculate_monthly_revenue(assets)
        
        return {
            'total_assets': total_assets,
            'active_assets': active_assets,
            'monthly_revenue': round(monthly_revenue / 1000000, 2),  # Convert to millions
            'fleet_utilization': round(utilization, 1),
            'status': 'authentic_data',
            'last_updated': datetime.now().isoformat()
        }
    
    def get_asset_categories(self) -> Dict[str, int]:
        """Get asset breakdown by category"""
        
        assets = self._get_cached_assets()
        categories = {}
        
        for asset in assets:
            category = self._categorize_asset(asset)
            categories[category] = categories.get(category, 0) + 1
            
        return categories
    
    def get_active_job_sites(self) -> List[Dict]:
        """Get job sites with active assets"""
        
        assets = self._get_cached_assets()
        job_sites = {}
        
        for asset in assets:
            location = asset.get('LastKnownLocation', {})
            if isinstance(location, dict) and location.get('Latitude') and location.get('Longitude'):
                # Group assets by approximate location
                lat = round(float(location['Latitude']), 2)
                lng = round(float(location['Longitude']), 2)
                site_key = f"{lat}_{lng}"
                
                if site_key not in job_sites:
                    job_sites[site_key] = {
                        'name': f"Job Site {len(job_sites) + 1}",
                        'latitude': lat,
                        'longitude': lng,
                        'assets': [],
                        'active_count': 0
                    }
                
                job_sites[site_key]['assets'].append({
                    'id': asset.get('AssetIdentifier', 'Unknown'),
                    'name': asset.get('Label', 'Unknown Asset'),
                    'active': asset.get('IsGPSEnabled', False)
                })
                
                if asset.get('IsGPSEnabled', False):
                    job_sites[site_key]['active_count'] += 1
        
        return list(job_sites.values())
    
    def _get_cached_assets(self) -> List[Dict]:
        """Get assets with caching for performance"""
        
        cache_key = 'gauge_assets'
        now = datetime.now().timestamp()
        
        # Check cache
        if cache_key in self._cache:
            cached_data, cache_time = self._cache[cache_key]
            if now - cache_time < self._cache_timeout:
                return cached_data
        
        # Fetch fresh data
        assets = self._fetch_gauge_assets()
        if assets:
            self._cache[cache_key] = (assets, now)
        
        return assets
    
    def _fetch_gauge_assets(self) -> List[Dict]:
        """Fetch authentic assets from Gauge API"""
        
        try:
            endpoint = f"{self.gauge_url}/AssetList/{self.asset_list_id}"
            
            response = requests.get(
                endpoint,
                auth=(self.gauge_username, self.gauge_password),
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                assets = response.json()
                logger.info(f"Retrieved {len(assets)} authentic assets")
                return assets
            else:
                logger.error(f"Gauge API error {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Asset fetch error: {e}")
            return []
    
    def _categorize_asset(self, asset: Dict) -> str:
        """Categorize asset based on identifier and name"""
        
        asset_id = asset.get('AssetIdentifier', '').upper()
        name = asset.get('Label', '').upper()
        combined = f"{asset_id} {name}"
        
        if any(term in combined for term in ['EX-', 'EXCAVATOR']):
            return 'Excavators'
        elif any(term in combined for term in ['BH-', 'BACKHOE']):
            return 'Backhoes'
        elif any(term in combined for term in ['DOZ-', 'DOZER']):
            return 'Dozers'
        elif any(term in combined for term in ['DTC-', 'DTF-', 'DTG-', 'TRUCK', 'F150', 'F250', 'F350']):
            return 'Trucks'
        elif any(term in combined for term in ['SS-', 'SKID']):
            return 'Skid Steers'
        elif any(term in combined for term in ['G-', 'GRADER']):
            return 'Graders'
        elif any(term in combined for term in ['WL-', 'WHEEL', 'LOADER']):
            return 'Wheel Loaders'
        else:
            return 'Other Equipment'
    
    def _calculate_monthly_revenue(self, assets: List[Dict]) -> float:
        """Calculate estimated monthly revenue based on asset types"""
        
        revenue = 0.0
        billing_rates = {
            'Excavators': 450.00,
            'Backhoes': 380.00,
            'Dozers': 420.00,
            'Trucks': 520.00,
            'Skid Steers': 280.00,
            'Graders': 425.00,
            'Wheel Loaders': 390.00,
            'Other Equipment': 350.00
        }
        
        # Assume 22 working days, 8 hours per day for active assets
        working_hours = 22 * 8
        
        for asset in assets:
            if asset.get('IsGPSEnabled', False):  # Only count active assets
                category = self._categorize_asset(asset)
                rate = billing_rates.get(category, 350.00)
                revenue += rate * working_hours
        
        return revenue
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        
        assets = self._fetch_gauge_assets()
        
        return {
            'gauge_api': 'connected' if assets else 'disconnected',
            'asset_count': len(assets) if assets else 0,
            'last_check': datetime.now().isoformat()
        }

# Global instance for deployment
deployment_engine = DeploymentDataEngine()

def get_deployment_engine():
    """Get the deployment-ready data engine"""
    return deployment_engine