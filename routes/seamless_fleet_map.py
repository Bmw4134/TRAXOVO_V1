"""
TRAXOVO Seamless Fleet Map Routes
Serves the seamless fleet map interface with authentic GAUGE data
"""

from flask import Blueprint, render_template, jsonify, request
from seamless_fleet_engine import seamless_fleet_engine
import logging

logger = logging.getLogger(__name__)

seamless_fleet_bp = Blueprint('seamless_fleet', __name__)

@seamless_fleet_bp.route('/fleet-map')
def fleet_map():
    """Seamless fleet map interface - accessible without authentication"""
    try:
        # Get initial data for the map
        categories = seamless_fleet_engine.get_category_filters()
        status_summary = seamless_fleet_engine.get_status_summary()
        
        return render_template('seamless_fleet_map.html', 
                             categories=categories,
                             status_summary=status_summary)
    except Exception as e:
        logger.error(f"Error loading fleet map: {e}")
        return render_template('seamless_fleet_map.html', 
                             categories=[],
                             status_summary={'active': 0, 'idle': 0, 'offline': 0})

@seamless_fleet_bp.route('/api/fleet/assets')
def api_fleet_assets():
    """API endpoint for all fleet assets"""
    try:
        # Get filter parameters
        category_filter = request.args.get('category', 'all')
        status_filter = request.args.get('status')
        
        # Get all assets
        assets = seamless_fleet_engine.get_all_assets_for_map()
        
        # Apply filters
        if category_filter != 'all':
            assets = [asset for asset in assets if asset['category'].lower().replace(' ', '_') == category_filter]
        
        if status_filter:
            assets = [asset for asset in assets if asset['status'] == status_filter]
        
        return jsonify({
            'status': 'success',
            'assets': assets,
            'count': len(assets),
            'timestamp': '2025-05-31T07:20:00Z'
        })
        
    except Exception as e:
        logger.error(f"Error fetching assets: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Unable to fetch asset data',
            'assets': [],
            'count': 0
        }), 500

@seamless_fleet_bp.route('/api/fleet/search')
def api_fleet_search():
    """API endpoint for asset search"""
    try:
        query = request.args.get('q', '').strip()
        
        if len(query) < 2:
            return jsonify({'results': []})
        
        results = seamless_fleet_engine.search_assets(query)
        
        return jsonify({
            'status': 'success',
            'results': results,
            'query': query
        })
        
    except Exception as e:
        logger.error(f"Error searching assets: {e}")
        return jsonify({
            'status': 'error',
            'results': [],
            'message': str(e)
        }), 500

@seamless_fleet_bp.route('/api/fleet/asset/<asset_id>')
def api_asset_detail(asset_id):
    """API endpoint for asset details"""
    try:
        asset_detail = seamless_fleet_engine.get_asset_detail(asset_id)
        
        if not asset_detail:
            return jsonify({
                'status': 'error',
                'message': 'Asset not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'asset': asset_detail
        })
        
    except Exception as e:
        logger.error(f"Error fetching asset detail: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@seamless_fleet_bp.route('/api/fleet/categories')
def api_fleet_categories():
    """API endpoint for available categories"""
    try:
        categories = seamless_fleet_engine.get_category_filters()
        
        return jsonify({
            'status': 'success',
            'categories': categories
        })
        
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return jsonify({
            'status': 'error',
            'categories': []
        }), 500

@seamless_fleet_bp.route('/api/fleet/status-summary')
def api_status_summary():
    """API endpoint for fleet status summary"""
    try:
        summary = seamless_fleet_engine.get_status_summary()
        
        return jsonify({
            'status': 'success',
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error fetching status summary: {e}")
        return jsonify({
            'status': 'error',
            'summary': {'active': 0, 'idle': 0, 'offline': 0}
        }), 500