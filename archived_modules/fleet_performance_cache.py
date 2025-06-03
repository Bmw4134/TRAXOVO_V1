"""
TRAXOVO Fleet Performance Cache
Intelligent caching system for instant load times with your authentic data
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

class FleetPerformanceCache:
    def __init__(self):
        self.cache_file = "fleet_cache.json"
        self.cache_duration = 300  # 5 minutes
        self.data = self.load_cache()
    
    def load_cache(self) -> Dict:
        """Load existing cache or create new one"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"last_update": None, "fleet_data": {}, "metrics": {}}
    
    def save_cache(self):
        """Save cache to disk"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.data, f)
    
    def is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self.data.get("last_update"):
            return False
        
        last_update = datetime.fromisoformat(self.data["last_update"])
        return datetime.now() - last_update < timedelta(seconds=self.cache_duration)
    
    def get_instant_fleet_metrics(self) -> Dict:
        """Get fleet metrics instantly from cache"""
        if self.is_cache_valid():
            return self.data.get("metrics", {})
        
        # Load fresh data from your Gauge API
        return self.refresh_fleet_data()
    
    def refresh_fleet_data(self) -> Dict:
        """Refresh cache with authentic Gauge API data"""
        try:
            # Load your authentic Gauge API data
            with open('GAUGE API PULL 1045AM_05.15.2025.json', 'r') as f:
                gauge_data = json.load(f)
            
            # Process authentic metrics from your real data
            total_assets = len(gauge_data)
            active_assets = len([a for a in gauge_data if a.get('Active', False)])
            gps_enabled = len([a for a in gauge_data if a.get('IMEI')])
            
            # Calculate real coverage from your authentic data
            coverage = (gps_enabled / total_assets * 100) if total_assets > 0 else 0
            
            metrics = {
                "total_assets": total_assets,
                "active_assets": active_assets, 
                "gps_enabled": gps_enabled,
                "coverage": round(coverage, 1),
                "last_sync": datetime.now().isoformat()
            }
            
            # Update cache with your real data
            self.data["metrics"] = metrics
            self.data["fleet_data"] = gauge_data
            self.data["last_update"] = datetime.now().isoformat()
            self.save_cache()
            
            return metrics
            
        except Exception as e:
            print(f"Error loading authentic data: {e}")
            # Force fresh data load - no fallback numbers
            if os.path.exists('GAUGE API PULL 1045AM_05.15.2025.json'):
                # Try again without exception handling
                with open('GAUGE API PULL 1045AM_05.15.2025.json', 'r') as f:
                    gauge_data = json.load(f)
                    return {
                        "total_assets": len(gauge_data),
                        "active_assets": len([a for a in gauge_data if a.get('Active', False)]),
                        "gps_enabled": len([a for a in gauge_data if a.get('IMEI')]),
                        "coverage": round((len([a for a in gauge_data if a.get('IMEI')]) / len(gauge_data) * 100), 1),
                        "last_sync": "Real data loaded"
                    }
            raise Exception("Cannot load authentic fleet data")
    
    def get_asset_list(self) -> List[Dict]:
        """Get processed asset list for instant display"""
        if not self.is_cache_valid():
            self.refresh_fleet_data()
        
        fleet_data = self.data.get("fleet_data", [])
        
        # Return processed asset list for instant loading
        assets = []
        for asset in fleet_data[:50]:  # Limit for performance
            assets.append({
                "id": asset.get("AssetIdentifier", "Unknown"),
                "name": asset.get("Label", "Unknown Asset"),
                "category": asset.get("AssetCategory", "Unknown"),
                "status": "Active" if asset.get("Active", False) else "Inactive",
                "location": asset.get("Location", "Unknown"),
                "latitude": asset.get("Latitude", 0),
                "longitude": asset.get("Longitude", 0),
                "speed": asset.get("Speed", 0),
                "lastUpdate": asset.get("EventDateTimeString", "Unknown")
            })
        
        return assets

# Global cache instance
fleet_cache = FleetPerformanceCache()

def get_instant_metrics():
    """Get instant fleet metrics"""
    return fleet_cache.get_instant_fleet_metrics()

def get_instant_assets():
    """Get instant asset list"""
    return fleet_cache.get_asset_list()