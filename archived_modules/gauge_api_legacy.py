"""
Legacy Gauge API Compatibility Layer
Redirects old API calls to unified data manager
"""

from services.unified_data_manager import get_unified_data

class GaugeAPI:
    """Compatibility wrapper for legacy code"""
    
    def __init__(self):
        pass
    
    def authenticate(self):
        return True
    
    def check_connection(self):
        health = get_unified_data("health")
        return health.get("api_status") == "active"
    
    def get_assets(self):
        return get_unified_data("assets").get("assets", [])
    
    def get_asset_locations(self, asset_id, start_date=None, end_date=None):
        return get_unified_data("locations")

def get_asset_data():
    """Legacy function compatibility"""
    return get_unified_data("assets").get("assets", [])

def test_gauge_api_connection():
    """Legacy function compatibility"""
    health = get_unified_data("health")
    return health.get("api_status") == "active"

def get_assets():
    """Legacy function compatibility"""
    return get_unified_data("assets").get("assets", [])
