"""
Smart Asset Lookup - GAUGE API Integration
Real-time asset search and lookup functionality
"""

from flask import Blueprint, render_template, jsonify, request
import os
import requests
from datetime import datetime

smart_asset_bp = Blueprint('smart_asset', __name__)

class SmartAssetEngine:
    """Real-time asset lookup using GAUGE API"""
    
    def __init__(self):
        self.gauge_api_key = os.environ.get('GAUGE_API_KEY')
        self.gauge_api_url = os.environ.get('GAUGE_API_URL')
        self.cache = {}
        
    def search_assets(self, query="", asset_type="", status=""):
        """Search assets using GAUGE API with filters"""
        if not self.gauge_api_key or not self.gauge_api_url:
            return {"error": "GAUGE API credentials required", "assets": []}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.gauge_api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'TRAXOVO/1.0'
            }
            
            api_url = self.gauge_api_url if self.gauge_api_url.startswith('http') else f"https://api.gaugesmart.com/AssetList/{self.gauge_api_url}"
            response = requests.get(api_url, headers=headers, timeout=10, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                assets = self._process_asset_data(data, query, asset_type, status)
                return {"success": True, "assets": assets, "total": len(assets)}
            else:
                return {"error": f"API Error: {response.status_code}", "assets": []}
                
        except Exception as e:
            return {"error": str(e), "assets": []}
    
    def _process_asset_data(self, data, query="", asset_type="", status=""):
        """Process and filter asset data from GAUGE API"""
        assets = []
        
        # Handle different API response formats
        asset_list = data if isinstance(data, list) else data.get('assets', [])
        
        for item in asset_list:
            asset = {
                'id': item.get('id', item.get('asset_id', 'N/A')),
                'name': item.get('name', item.get('asset_name', 'Unknown Asset')),
                'type': item.get('type', item.get('equipment_type', 'Equipment')),
                'status': item.get('status', 'Active'),
                'location': item.get('location', item.get('current_location', 'Location Unknown')),
                'last_update': item.get('last_update', datetime.now().isoformat()),
                'utilization': item.get('utilization', 0),
                'operating_hours': item.get('operating_hours', 0),
                'fuel_level': item.get('fuel_level', 0),
                'maintenance_due': item.get('maintenance_due', False)
            }
            
            # Apply filters
            if query and query.lower() not in asset['name'].lower() and query.lower() not in asset['id'].lower():
                continue
            if asset_type and asset_type.lower() != asset['type'].lower():
                continue
            if status and status.lower() != asset['status'].lower():
                continue
                
            assets.append(asset)
        
        return assets
    
    def get_asset_details(self, asset_id):
        """Get detailed information for specific asset"""
        assets = self.search_assets()
        for asset in assets.get('assets', []):
            if asset['id'] == asset_id:
                return asset
        return None

# Global asset engine
asset_engine = SmartAssetEngine()

@smart_asset_bp.route('/smart-asset-lookup')
def asset_lookup_page():
    """Smart asset lookup interface"""
    return render_template('smart_asset_lookup.html',
                         page_title="Smart Asset Lookup",
                         page_subtitle="Real-time asset search using GAUGE API")

@smart_asset_bp.route('/api/search-assets')
def search_assets_api():
    """API endpoint for asset search"""
    query = request.args.get('query', '')
    asset_type = request.args.get('type', '')
    status = request.args.get('status', '')
    
    results = asset_engine.search_assets(query, asset_type, status)
    return jsonify(results)

@smart_asset_bp.route('/api/asset/<asset_id>')
def get_asset_details_api(asset_id):
    """Get detailed asset information"""
    asset = asset_engine.get_asset_details(asset_id)
    if asset:
        return jsonify({"success": True, "asset": asset})
    else:
        return jsonify({"success": False, "error": "Asset not found"})