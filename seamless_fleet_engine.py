"""
TRAXOVO Seamless Fleet Engine
Processes authentic GAUGE API data for the seamless fleet map interface
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any

class SeamlessFleetEngine:
    def __init__(self):
        self.gauge_data = self.load_gauge_data()
        self.asset_categories = self.build_category_mapping()
        
    def load_gauge_data(self) -> List[Dict]:
        """Load authentic GAUGE API data"""
        try:
            gauge_file = 'GAUGE API PULL 1045AM_05.15.2025.json'
            if os.path.exists(gauge_file):
                with open(gauge_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading GAUGE data: {e}")
        return []
    
    def build_category_mapping(self) -> Dict[str, str]:
        """Build comprehensive category mapping from authentic data"""
        categories = {}
        for asset in self.gauge_data:
            category = asset.get('AssetCategory', 'Other')
            asset_class = asset.get('AssetClass', '')
            if category not in categories:
                categories[category] = asset_class or category
        return categories
    
    def get_all_assets_for_map(self) -> List[Dict]:
        """Process all authentic assets for seamless map display"""
        processed_assets = []
        
        for asset in self.gauge_data:
            # Extract core asset information
            asset_id = asset.get('AssetIdentifier', 'Unknown')
            category = asset.get('AssetCategory', 'Other')
            make = asset.get('AssetMake', '')
            model = asset.get('AssetModel', '')
            
            # Determine status based on multiple factors
            status = self.determine_asset_status(asset)
            
            # Get location data
            latitude = asset.get('Latitude')
            longitude = asset.get('Longitude')
            location_name = asset.get('Location', 'Unknown Location')
            site = asset.get('Site', location_name)
            
            # Skip assets without valid coordinates
            if not latitude or not longitude:
                continue
                
            # Build comprehensive asset data
            processed_asset = {
                'id': asset_id,
                'name': f"{make} {model}".strip(),
                'label': asset.get('Label', asset_id),
                'category': category,
                'asset_class': asset.get('AssetClass', ''),
                'make': make,
                'model': model,
                'status': status,
                'active': asset.get('Active', False),
                'location': {
                    'lat': float(latitude),
                    'lng': float(longitude),
                    'name': location_name,
                    'site': site
                },
                'details': {
                    'engine_hours': asset.get('Engine1Hours', 0),
                    'odometer': asset.get('Odometer', 0),
                    'voltage': asset.get('Voltage', 0),
                    'battery_pct': asset.get('BackupBatteryPct', 0),
                    'speed': asset.get('Speed', 0),
                    'heading': asset.get('Heading', 'N'),
                    'ignition': asset.get('Ignition', False),
                    'serial_number': asset.get('SerialNumber', ''),
                    'imei': asset.get('IMEI', ''),
                    'last_update': asset.get('EventDateTimeString', ''),
                    'days_inactive': asset.get('DaysInactive', 'N/A'),
                    'reason': asset.get('Reason', 'Unknown')
                }
            }
            
            processed_assets.append(processed_asset)
        
        return processed_assets
    
    def determine_asset_status(self, asset: Dict) -> str:
        """Determine asset status based on multiple factors"""
        if not asset.get('Active', False):
            return 'offline'
        
        days_inactive = asset.get('DaysInactive', 'N/A')
        ignition = asset.get('Ignition', False)
        speed = asset.get('Speed', 0)
        
        # Active and moving
        if ignition and speed > 0:
            return 'active'
        
        # Recently used (within 7 days)
        if days_inactive != 'N/A':
            try:
                inactive_days = int(days_inactive)
                if inactive_days <= 7:
                    return 'active'
                elif inactive_days <= 30:
                    return 'idle'
                else:
                    return 'offline'
            except (ValueError, TypeError):
                pass
        
        # Default based on ignition
        return 'active' if ignition else 'idle'
    
    def get_category_filters(self) -> List[Dict]:
        """Get all equipment categories for filtering"""
        categories = {}
        
        for asset in self.gauge_data:
            category = asset.get('AssetCategory', 'Other')
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        # Convert to filter format
        filters = [{'id': 'all', 'name': 'All Assets', 'count': len(self.gauge_data)}]
        
        for category, count in sorted(categories.items()):
            filter_id = category.lower().replace(' ', '_')
            filters.append({
                'id': filter_id,
                'name': category,
                'count': count,
                'category': category
            })
        
        return filters
    
    def get_status_summary(self) -> Dict[str, int]:
        """Get status summary for the status panel"""
        summary = {'active': 0, 'idle': 0, 'offline': 0}
        
        for asset in self.gauge_data:
            status = self.determine_asset_status(asset)
            summary[status] += 1
        
        return summary
    
    def search_assets(self, query: str) -> List[Dict]:
        """Search assets by ID, make, model, or location"""
        query_lower = query.lower()
        matches = []
        
        for asset in self.gauge_data:
            asset_id = asset.get('AssetIdentifier', '').lower()
            make = asset.get('AssetMake', '').lower()
            model = asset.get('AssetModel', '').lower()
            location = asset.get('Location', '').lower()
            site = asset.get('Site', '').lower()
            
            if (query_lower in asset_id or 
                query_lower in make or 
                query_lower in model or 
                query_lower in location or 
                query_lower in site):
                
                matches.append({
                    'id': asset.get('AssetIdentifier'),
                    'name': f"{asset.get('AssetMake', '')} {asset.get('AssetModel', '')}".strip(),
                    'location': asset.get('Location', 'Unknown'),
                    'site': asset.get('Site', ''),
                    'lat': asset.get('Latitude'),
                    'lng': asset.get('Longitude')
                })
        
        return matches[:10]  # Limit to 10 results
    
    def get_asset_detail(self, asset_id: str) -> Dict:
        """Get detailed information for a specific asset"""
        for asset in self.gauge_data:
            if asset.get('AssetIdentifier') == asset_id:
                return {
                    'id': asset_id,
                    'name': f"{asset.get('AssetMake', '')} {asset.get('AssetModel', '')}".strip(),
                    'category': asset.get('AssetCategory', 'Other'),
                    'status': self.determine_asset_status(asset),
                    'location': {
                        'lat': asset.get('Latitude'),
                        'lng': asset.get('Longitude'),
                        'name': asset.get('Location', 'Unknown'),
                        'site': asset.get('Site', '')
                    },
                    'details': {
                        'engine_hours': f"{asset.get('Engine1Hours', 0):,} hrs",
                        'odometer': f"{asset.get('Odometer', 0):,} mi",
                        'voltage': f"{asset.get('Voltage', 0):.1f}V",
                        'battery': f"{asset.get('BackupBatteryPct', 0)}%",
                        'serial_number': asset.get('SerialNumber', 'N/A'),
                        'last_update': asset.get('EventDateTimeString', 'Unknown'),
                        'days_inactive': asset.get('DaysInactive', 'N/A'),
                        'ignition': 'On' if asset.get('Ignition') else 'Off',
                        'speed': f"{asset.get('Speed', 0)} mph",
                        'heading': asset.get('Heading', 'N'),
                        'reason': asset.get('Reason', 'Unknown')
                    }
                }
        return {}

# Global instance
seamless_fleet_engine = SeamlessFleetEngine()