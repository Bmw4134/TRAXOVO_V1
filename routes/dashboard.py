
"""
Dashboard Routes - Real Data Connection
"""

from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from utils.dashboard_metrics import get_dashboard_metrics

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/api/metrics')
@login_required
def api_metrics():
    """API endpoint for real dashboard metrics"""
    try:
        metrics = get_dashboard_metrics()
        
        return jsonify({
            'success': True,
            'data': {
                'total_assets': metrics['assets']['total_assets'],
                'active_assets': metrics['assets']['active_assets'],
                'total_drivers': metrics['drivers']['total_drivers'],
                'estimated_revenue': metrics['revenue']['estimated_daily'],
                'asset_source': metrics['assets']['source'],
                'driver_source': metrics['drivers']['source'],
                'last_updated': metrics['last_updated']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'total_assets': 0,
                'active_assets': 0,
                'total_drivers': 0,
                'estimated_revenue': 0
            }
        })

@dashboard.route('/api/asset-count')
@login_required
def api_asset_count():
    """Direct asset count from API"""
    from utils.dashboard_metrics import get_real_asset_count
    
    data = get_real_asset_count()
    return jsonify({
        'total': data['total_assets'],
        'active': data['active_assets'],
        'source': data['source']
    })

@dashboard.route('/api/driver-count')
@login_required
def api_driver_count():
    """Direct driver count from data analysis"""
    from utils.dashboard_metrics import get_real_driver_count
    
    data = get_real_driver_count()
    return jsonify({
        'total': data['total_drivers'],
        'source': data['source'],
        'breakdown': {
            'from_assets': data.get('assigned_from_assets', 0),
            'from_csv': data.get('from_csv_files', 0)
        }
    })
