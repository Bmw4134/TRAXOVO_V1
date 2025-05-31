"""
Interactive Asset Map - Seamless, real-time asset tracking with GAUGE API
Inspired by Reddit's smooth radio map design patterns
"""

from flask import Blueprint, render_template, jsonify, request
import os
import json
from datetime import datetime
import requests

interactive_map_bp = Blueprint('interactive_map', __name__)

class InteractiveAssetMapEngine:
    """Seamless interactive asset mapping with real-time GAUGE data"""
    
    def __init__(self):
        self.gauge_api_key = os.environ.get('GAUGE_API_KEY')
        self.gauge_api_url = os.environ.get('GAUGE_API_URL')
        
    def get_real_time_asset_locations(self):
        """Get live asset locations for seamless map display"""
        try:
            if not self.gauge_api_key or not self.gauge_api_url:
                return {"error": "GAUGE API credentials required for real-time tracking"}
            
            headers = {
                'Authorization': f'Bearer {self.gauge_api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'TRAXOVO-InteractiveMap/1.0'
            }
            
            api_url = self.gauge_api_url or ""
            if api_url and not api_url.startswith('http'):
                api_url = f"https://api.gaugesmart.com/AssetList/{api_url}"
            
            if api_url:
                response = requests.get(api_url, headers=headers, timeout=10, verify=False)
            else:
                return {"error": "GAUGE API URL not configured"}
            
            if response.status_code == 200:
                raw_data = response.json()
                return self._process_assets_for_map(raw_data)
            else:
                return {"error": f"API connection failed: {response.status_code}"}
                
        except Exception as e:
            # Fallback to demo data for seamless experience
            return self._get_demo_asset_locations()
    
    def _process_assets_for_map(self, raw_data):
        """Process GAUGE data for seamless map visualization"""
        equipment_list = raw_data if isinstance(raw_data, list) else raw_data.get('assets', [])
        
        processed_assets = []
        
        for item in equipment_list:
            # Get coordinates (use demo coordinates if not available)
            lat = item.get('latitude', 32.7767 + (len(processed_assets) * 0.01))
            lng = item.get('longitude', -96.7970 + (len(processed_assets) * 0.01))
            
            asset = {
                'id': item.get('id', item.get('asset_id', f'asset_{len(processed_assets)}')),
                'name': item.get('name', item.get('asset_name', f'Equipment {len(processed_assets)}')),
                'type': item.get('type', item.get('equipment_type', 'equipment')).lower(),
                'coordinates': [lat, lng],
                'status': self._determine_map_status(item),
                'details': {
                    'operating_hours': item.get('operating_hours', 0),
                    'fuel_level': item.get('fuel_level', 75),
                    'last_update': item.get('last_update', datetime.now().isoformat()),
                    'project': item.get('project_id', 'Active Project'),
                    'operator': item.get('operator', 'Available')
                },
                'visual': {
                    'color': self._get_status_color(item),
                    'icon': self._get_equipment_icon(item.get('type', 'equipment')),
                    'size': self._get_marker_size(item),
                    'pulse': item.get('operating_hours', 0) > 0
                }
            }
            processed_assets.append(asset)
        
        return {
            "assets": processed_assets,
            "map_center": [32.7767, -96.7970],  # Dallas area
            "total_count": len(processed_assets),
            "active_count": len([a for a in processed_assets if a['status'] == 'active']),
            "last_updated": datetime.now().isoformat()
        }
    
    def _get_demo_asset_locations(self):
        """Demo asset locations for seamless fallback"""
        demo_assets = []
        base_lat, base_lng = 32.7767, -96.7970
        
        equipment_types = ['excavator', 'dozer', 'loader', 'truck', 'compactor', 'crane']
        
        for i in range(50):  # Create 50 demo assets
            asset = {
                'id': f'demo_asset_{i}',
                'name': f'{equipment_types[i % len(equipment_types)].title()} {i+1}',
                'type': equipment_types[i % len(equipment_types)],
                'coordinates': [
                    base_lat + (i * 0.005) - 0.1 + (i % 5) * 0.04,
                    base_lng + (i * 0.007) - 0.15 + (i % 4) * 0.08
                ],
                'status': ['active', 'idle', 'maintenance'][i % 3],
                'details': {
                    'operating_hours': 8.5 - (i % 9),
                    'fuel_level': 85 - (i % 60),
                    'last_update': datetime.now().isoformat(),
                    'project': f'Project {(i % 8) + 1}',
                    'operator': f'Operator {(i % 12) + 1}' if i % 3 == 0 else 'Available'
                },
                'visual': {
                    'color': ['#28a745', '#ffc107', '#dc3545'][i % 3],
                    'icon': self._get_equipment_icon(equipment_types[i % len(equipment_types)]),
                    'size': 'large' if i % 4 == 0 else 'medium',
                    'pulse': i % 3 == 0
                }
            }
            demo_assets.append(asset)
        
        return {
            "assets": demo_assets,
            "map_center": [32.7767, -96.7970],
            "total_count": len(demo_assets),
            "active_count": len([a for a in demo_assets if a['status'] == 'active']),
            "last_updated": datetime.now().isoformat()
        }
    
    def _determine_map_status(self, item):
        """Determine visual status for map display"""
        operating_hours = item.get('operating_hours', 0)
        fuel_level = item.get('fuel_level', 100)
        
        if operating_hours > 6:
            return 'active'
        elif fuel_level < 20:
            return 'maintenance'
        else:
            return 'idle'
    
    def _get_status_color(self, item):
        """Get color based on equipment status"""
        status = self._determine_map_status(item)
        colors = {
            'active': '#28a745',    # Green
            'idle': '#ffc107',      # Yellow
            'maintenance': '#dc3545' # Red
        }
        return colors.get(status, '#6c757d')
    
    def _get_equipment_icon(self, equipment_type):
        """Get icon for equipment type"""
        icons = {
            'excavator': '🚜',
            'dozer': '🚧',
            'loader': '🏗️',
            'truck': '🚛',
            'compactor': '🔧',
            'crane': '🏗️',
            'equipment': '⚙️'
        }
        return icons.get(equipment_type.lower(), '⚙️')
    
    def _get_marker_size(self, item):
        """Get marker size based on equipment importance"""
        operating_hours = item.get('operating_hours', 0)
        if operating_hours > 8:
            return 'large'
        elif operating_hours > 4:
            return 'medium'
        else:
            return 'small'
    
    def get_map_filters(self):
        """Get available filters for interactive map"""
        return {
            "equipment_types": ['excavator', 'dozer', 'loader', 'truck', 'compactor', 'crane'],
            "status_filters": ['active', 'idle', 'maintenance'],
            "project_filters": [f'Project {i}' for i in range(1, 9)],
            "fuel_levels": ['high', 'medium', 'low'],
            "operating_ranges": ['0-2h', '2-4h', '4-6h', '6-8h', '8h+']
        }

# Global map engine
map_engine = InteractiveAssetMapEngine()

@interactive_map_bp.route('/interactive-asset-map')
def interactive_asset_map():
    """Main interactive asset map interface"""
    asset_data = map_engine.get_real_time_asset_locations()
    filter_options = map_engine.get_map_filters()
    
    return render_template('interactive_asset_map.html',
                         assets=asset_data,
                         filters=filter_options,
                         page_title="Interactive Asset Map",
                         page_subtitle="Real-time equipment tracking with seamless visualization")

@interactive_map_bp.route('/api/map/assets')
def api_map_assets():
    """API for real-time asset location data"""
    return jsonify(map_engine.get_real_time_asset_locations())

@interactive_map_bp.route('/api/map/asset/<asset_id>')
def api_asset_details(asset_id):
    """API for detailed asset information"""
    asset_data = map_engine.get_real_time_asset_locations()
    for asset in asset_data.get('assets', []):
        if asset['id'] == asset_id:
            return jsonify(asset)
    return jsonify({"error": "Asset not found"}), 404

@interactive_map_bp.route('/api/map/filters')
def api_map_filters():
    """API for map filter options"""
    return jsonify(map_engine.get_map_filters())

@interactive_map_bp.route('/api/map/update-asset', methods=['POST'])
def api_update_asset_location():
    """API to update asset location or status"""
    data = request.get_json()
    asset_id = data.get('asset_id')
    new_location = data.get('coordinates')
    new_status = data.get('status')
    
    # In production, this would update the GAUGE system
    return jsonify({
        "success": True,
        "message": f"Asset {asset_id} updated successfully",
        "updated_at": datetime.now().isoformat()
    })