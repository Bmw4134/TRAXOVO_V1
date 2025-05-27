"""
Mobile-Optimized Map for TRAXOVO

This module provides a mobile-friendly GPS map interface that works perfectly 
on phones for field crews, using authentic Gauge API data.
"""
import logging
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from gauge_api import GaugeAPI

logger = logging.getLogger(__name__)

mobile_map_bp = Blueprint('mobile_map', __name__, url_prefix='/mobile-map')

@mobile_map_bp.route('/')
@login_required
def mobile_map():
    """Mobile-optimized map view for field crews"""
    return render_template('mobile_map.html')

@mobile_map_bp.route('/api/gauge-assets')
@login_required
def api_gauge_assets():
    """API endpoint to get authentic GPS assets for mobile map"""
    try:
        # Get authentic data from Gauge API
        gauge_api = GaugeAPI()
        assets = gauge_api.get_assets()
        
        if assets:
            # Format assets for mobile map display
            mobile_assets = []
            for asset in assets:
                if asset.get('latitude') and asset.get('longitude'):
                    mobile_assets.append({
                        'id': asset.get('id'),
                        'name': asset.get('name') or asset.get('description', f"Asset {asset.get('id')}"),
                        'latitude': float(asset.get('latitude')),
                        'longitude': float(asset.get('longitude')),
                        'description': asset.get('description', ''),
                        'last_update': asset.get('last_update'),
                        'speed': asset.get('speed', 0),
                        'status': asset.get('status', 'unknown')
                    })
            
            logger.info(f"Mobile map: Serving {len(mobile_assets)} authentic GPS assets")
            
            return jsonify({
                'success': True,
                'assets': mobile_assets,
                'total_count': len(mobile_assets),
                'source': 'Authentic Gauge API'
            })
        else:
            logger.warning("Mobile map: No assets returned from Gauge API")
            return jsonify({
                'success': False,
                'error': 'No assets available from authentic data source',
                'assets': []
            })
            
    except Exception as e:
        logger.error(f"Mobile map error: {e}")
        return jsonify({
            'success': False,
            'error': f'Error loading authentic GPS data: {str(e)}',
            'assets': []
        }), 500

@mobile_map_bp.route('/api/asset-status/<asset_id>')
@login_required
def api_asset_status(asset_id):
    """Get detailed status for specific asset on mobile"""
    try:
        gauge_api = GaugeAPI()
        asset_detail = gauge_api.get_asset_details(asset_id)
        
        if asset_detail:
            return jsonify({
                'success': True,
                'asset': asset_detail
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Asset not found in authentic data'
            }), 404
            
    except Exception as e:
        logger.error(f"Mobile asset status error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500