"""
TRAXOVO Unified Route System
Fixes URL/navigation mismatches and consolidates all routing
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from routes.accurate_asset_counter import get_accurate_asset_counter
import logging

unified_routes_bp = Blueprint('unified_routes', __name__)

# Fix fleet map route with accurate asset data
@unified_routes_bp.route('/fleet-map')
def fleet_map():
    """Unified fleet map with accurate asset counts"""
    try:
        # Get accurate asset data
        counter = get_accurate_asset_counter()
        counts = counter.get_accurate_counts()
        
        # Sample data for map filters - replace with authentic data
        context = {
            'active_assets': counts['total_assets'],
            'online_assets': counts['active_assets'],
            'sites': ['All Sites', 'Louisiana', 'Texas', 'Mississippi'],
            'groups': ['All Groups', 'Heavy Equipment', 'Light Vehicles', 'Support'],
            'categories': ['All Categories', 'Excavators', 'Dozers', 'Trucks', 'Trailers'],
            'classes': ['All Classes', 'Class A', 'Class B', 'Class C']
        }
        
        return render_template('fleet_map_unified.html', **context)
        
    except Exception as e:
        logging.error(f"Error loading fleet map: {e}")
        return render_template('fleet_map_unified.html', 
                             active_assets=0, online_assets=0,
                             sites=[], groups=[], categories=[], classes=[])

# Fix asset manager route
@unified_routes_bp.route('/asset-manager')
def asset_manager():
    """Unified asset manager with accurate counts"""
    try:
        counter = get_accurate_asset_counter()
        counts = counter.get_accurate_counts()
        assets = counter.get_detailed_asset_list()
        
        return render_template('asset_manager_unified.html', 
                             counts=counts, assets=assets)
    except Exception as e:
        logging.error(f"Error loading asset manager: {e}")
        return render_template('asset_manager_unified.html', 
                             counts={}, assets=[])

# Fix equipment lifecycle route
@unified_routes_bp.route('/equipment-lifecycle')
def equipment_lifecycle():
    """Equipment lifecycle management"""
    return render_template('equipment_lifecycle.html')

# Fix analytics routes
@unified_routes_bp.route('/revenue-analytics')
def revenue_analytics():
    """Revenue analytics dashboard"""
    return render_template('analytics_dashboard.html', module='revenue')

@unified_routes_bp.route('/cost-savings-simulator')
def cost_savings_simulator():
    """Cost savings simulation tools"""
    return render_template('analytics_dashboard.html', module='cost_savings')

@unified_routes_bp.route('/billing-consolidation')
def billing_consolidation():
    """Billing consolidation module"""
    return render_template('analytics_dashboard.html', module='billing')

# Fix attendance routes
@unified_routes_bp.route('/attendance-matrix')
def attendance_matrix():
    """Attendance tracking matrix"""
    return render_template('analytics_dashboard.html', module='attendance')

# Fix driver management
@unified_routes_bp.route('/driver-management')
def driver_management():
    """Driver management dashboard"""
    return render_template('analytics_dashboard.html', module='drivers')

# Fix executive reports
@unified_routes_bp.route('/executive-reports')
def executive_reports():
    """Executive reporting dashboard"""
    return render_template('analytics_dashboard.html', module='executive')

# Fix industry news
@unified_routes_bp.route('/industry-news')
def industry_news():
    """AEMP industry news and updates"""
    return render_template('analytics_dashboard.html', module='news')

# API Routes for accurate data
@unified_routes_bp.route('/api/unified-asset-counts')
def api_unified_asset_counts():
    """API for unified asset counts"""
    try:
        counter = get_accurate_asset_counter()
        counts = counter.get_accurate_counts()
        return jsonify(counts)
    except Exception as e:
        logging.error(f"Error getting asset counts: {e}")
        return jsonify({'error': str(e)}), 500

@unified_routes_bp.route('/api/unified-asset-list')
def api_unified_asset_list():
    """API for unified asset list"""
    try:
        counter = get_accurate_asset_counter()
        assets = counter.get_detailed_asset_list()
        return jsonify(assets)
    except Exception as e:
        logging.error(f"Error getting asset list: {e}")
        return jsonify({'error': str(e)}), 500

# Navigation consistency fixes
@unified_routes_bp.route('/dashboard')
def dashboard_redirect():
    """Redirect dashboard to main"""
    return redirect(url_for('main.dashboard'))

@unified_routes_bp.route('/live-fleet-map')
def live_fleet_map_redirect():
    """Redirect live fleet map to unified fleet map"""
    return redirect(url_for('unified_routes.fleet_map'))

@unified_routes_bp.route('/equipment-dispatch')
def equipment_dispatch():
    """Equipment dispatch module"""
    return render_template('analytics_dashboard.html', module='dispatch')

# Consolidated module access
@unified_routes_bp.route('/module/<module_name>')
def module_access(module_name):
    """Generic module access point"""
    valid_modules = [
        'asset-manager', 'fleet-map', 'attendance-matrix', 'driver-management',
        'executive-reports', 'equipment-lifecycle', 'revenue-analytics',
        'cost-savings-simulator', 'billing-consolidation', 'industry-news',
        'equipment-dispatch'
    ]
    
    if module_name in valid_modules:
        # Route to appropriate function
        if module_name == 'asset-manager':
            return asset_manager()
        elif module_name == 'fleet-map':
            return fleet_map()
        elif module_name == 'equipment-lifecycle':
            return equipment_lifecycle()
        else:
            return render_template('analytics_dashboard.html', module=module_name.replace('-', '_'))
    else:
        return redirect(url_for('main.dashboard'))

# Error handlers for consistency
@unified_routes_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html', 
                         error_code=404, 
                         error_message="Page not found"), 404

@unified_routes_bp.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return render_template('error.html', 
                         error_code=500, 
                         error_message="Internal server error"), 500