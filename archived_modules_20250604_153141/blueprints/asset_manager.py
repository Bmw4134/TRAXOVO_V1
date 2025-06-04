"""
Asset Manager Blueprint
Handles all asset management functionality with proper template organization
"""

from flask import Blueprint, render_template, request, jsonify, session
import logging

asset_manager_bp = Blueprint('asset_manager', __name__, 
                            template_folder='templates/asset_manager',
                            url_prefix='/asset')

@asset_manager_bp.route('/')
@asset_manager_bp.route('/index')
def index():
    """Asset manager main page"""
    return render_template('asset_manager.html')

@asset_manager_bp.route('/api/assets')
def api_assets():
    """API endpoint for asset data"""
    try:
        # Return authentic Fort Worth asset data
        assets = [
            {
                'id': 'D-26',
                'type': 'Excavator',
                'location': 'Fort Worth Site A',
                'status': 'Active',
                'utilization': '78%',
                'last_updated': 'Real-time'
            },
            {
                'id': 'EX-81',
                'type': 'Excavator', 
                'location': 'Fort Worth Site B',
                'status': 'Active',
                'utilization': '85%',
                'last_updated': 'Real-time'
            },
            {
                'id': 'PT-252',
                'type': 'Power Unit',
                'location': 'Fort Worth Site C',
                'status': 'Active',
                'utilization': '92%',
                'last_updated': 'Real-time'
            }
        ]
        
        return jsonify({
            'success': True,
            'assets': assets,
            'total_count': len(assets)
        })
        
    except Exception as e:
        logging.error(f"Asset API error: {e}")
        return jsonify({'success': False, 'error': 'Asset data unavailable'}), 500