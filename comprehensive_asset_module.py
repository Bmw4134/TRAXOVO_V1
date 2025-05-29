"""
Comprehensive Asset Management Module
Complete asset tracking with Gauge API integration, filtering, and detailed views
"""

import pandas as pd
import json
import os
from datetime import datetime
from flask import Blueprint, render_template, jsonify, request
from sqlalchemy import text

asset_module_bp = Blueprint('asset_module', __name__)

class AssetManager:
    """Manages all asset data from Gauge API and related systems"""
    
    def __init__(self):
        self.gauge_data = []
        self.load_gauge_assets()
        self.asset_categories = set()
        self.analyze_asset_data()
    
    def load_gauge_assets(self):
        """Load all assets from Gauge API data"""
        try:
            with open('GAUGE API PULL 1045AM_05.15.2025.json', 'r') as f:
                self.gauge_data = json.load(f)
                print(f"Loaded {len(self.gauge_data)} assets from Gauge API")
        except Exception as e:
            print(f"Error loading Gauge API data: {e}")
            self.gauge_data = []
    
    def analyze_asset_data(self):
        """Analyze asset data to build filters and categories"""
        for asset in self.gauge_data:
            category = asset.get('AssetCategory', 'Uncategorized')
            self.asset_categories.add(category)
    
    def get_all_assets(self, filters=None):
        """Get all assets with optional filtering"""
        assets = self.gauge_data.copy()
        
        if filters:
            # Filter by active status
            if filters.get('active_only'):
                assets = [a for a in assets if a.get('Active', False)]
            
            # Filter by category
            if filters.get('category'):
                assets = [a for a in assets if a.get('AssetCategory') == filters['category']]
            
            # Filter by GPS status
            if filters.get('gps_enabled'):
                assets = [a for a in assets if a.get('Latitude') and a.get('Longitude')]
            
            # Search filter
            if filters.get('search'):
                search_term = filters['search'].lower()
                assets = [a for a in assets if 
                         search_term in str(a.get('AssetNumber', '')).lower() or
                         search_term in str(a.get('Description', '')).lower() or
                         search_term in str(a.get('SerialNumber', '')).lower()]
        
        # Add computed fields
        for asset in assets:
            asset['gps_status'] = 'GPS Enabled' if (asset.get('Latitude') and asset.get('Longitude')) else 'No GPS'
            asset['status_display'] = 'Active' if asset.get('Active', False) else 'Inactive'
            asset['last_location_update'] = asset.get('LastLocationUpdate', 'Unknown')
        
        return assets
    
    def get_asset_detail(self, asset_number):
        """Get detailed information for a specific asset"""
        asset = next((a for a in self.gauge_data if str(a.get('AssetNumber')) == str(asset_number)), None)
        
        if not asset:
            return None
        
        # Enhance asset with additional details
        enhanced_asset = asset.copy()
        enhanced_asset.update({
            'gps_coordinates': f"{asset.get('Latitude', 'N/A')}, {asset.get('Longitude', 'N/A')}" if asset.get('Latitude') else 'No GPS Data',
            'location_accuracy': asset.get('LocationAccuracy', 'Unknown'),
            'last_movement': asset.get('LastMovement', 'Unknown'),
            'maintenance_status': self._get_maintenance_status(asset),
            'utilization_data': self._get_utilization_data(asset),
            'billing_history': self._get_billing_history(asset_number)
        })
        
        return enhanced_asset
    
    def _get_maintenance_status(self, asset):
        """Get maintenance status for asset"""
        # This would integrate with maintenance records
        return {
            'next_service_due': 'Calculate based on hours/miles',
            'last_service': 'From maintenance records',
            'service_alerts': []
        }
    
    def _get_utilization_data(self, asset):
        """Get utilization data for asset"""
        return {
            'hours_this_month': 'Calculate from GPS/telematics',
            'utilization_rate': 'Based on movement patterns',
            'revenue_generated': 'From billing records'
        }
    
    def _get_billing_history(self, asset_number):
        """Get billing history for asset from Excel workbooks"""
        billing_history = []
        
        billing_files = [
            "RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm",
            "RAGLE EQ BILLINGS - MARCH 2025 (TO REVIEW 04.03.25).xlsm"
        ]
        
        for file in billing_files:
            if os.path.exists(file):
                try:
                    df = pd.read_excel(file, engine='openpyxl')
                    
                    # Look for asset number in various columns
                    asset_matches = df[df.apply(lambda row: str(asset_number) in str(row).upper(), axis=1)]
                    
                    for _, row in asset_matches.iterrows():
                        billing_history.append({
                            'month': 'April 2025' if 'APRIL' in file else 'March 2025',
                            'details': row.to_dict(),
                            'source_file': file
                        })
                        
                except Exception as e:
                    print(f"Error reading billing file {file}: {e}")
        
        return billing_history
    
    def get_asset_statistics(self):
        """Get overall asset statistics"""
        total_assets = len(self.gauge_data)
        active_assets = len([a for a in self.gauge_data if a.get('Active', False)])
        gps_enabled = len([a for a in self.gauge_data if a.get('Latitude') and a.get('Longitude')])
        
        # Category breakdown
        category_stats = {}
        for asset in self.gauge_data:
            if asset.get('Active', False):  # Only count active assets
                category = asset.get('AssetCategory', 'Uncategorized')
                if category not in category_stats:
                    category_stats[category] = {'total': 0, 'gps_enabled': 0}
                category_stats[category]['total'] += 1
                if asset.get('Latitude') and asset.get('Longitude'):
                    category_stats[category]['gps_enabled'] += 1
        
        return {
            'total_assets': total_assets,
            'active_assets': active_assets,
            'inactive_assets': total_assets - active_assets,
            'gps_enabled': gps_enabled,
            'gps_coverage': f"{(gps_enabled/active_assets*100):.1f}%" if active_assets > 0 else "0%",
            'category_breakdown': category_stats,
            'last_sync': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

@asset_module_bp.route('/assets')
def asset_dashboard():
    """Main asset management dashboard"""
    asset_manager = AssetManager()
    stats = asset_manager.get_asset_statistics()
    categories = sorted(asset_manager.asset_categories)
    
    return render_template('assets/asset_dashboard.html', 
                         stats=stats, 
                         categories=categories)

@asset_module_bp.route('/api/assets')
def get_assets_api():
    """API endpoint for asset data with filtering"""
    asset_manager = AssetManager()
    
    # Get filter parameters
    filters = {
        'active_only': request.args.get('active_only') == 'true',
        'category': request.args.get('category'),
        'gps_enabled': request.args.get('gps_enabled') == 'true',
        'search': request.args.get('search')
    }
    
    # Remove None values
    filters = {k: v for k, v in filters.items() if v}
    
    assets = asset_manager.get_all_assets(filters)
    
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    start = (page - 1) * per_page
    end = start + per_page
    
    return jsonify({
        'assets': assets[start:end],
        'total': len(assets),
        'page': page,
        'per_page': per_page,
        'has_next': end < len(assets),
        'has_prev': page > 1
    })

@asset_module_bp.route('/assets/<asset_number>')
def asset_detail(asset_number):
    """Detailed view for specific asset"""
    asset_manager = AssetManager()
    asset = asset_manager.get_asset_detail(asset_number)
    
    if not asset:
        return render_template('404.html'), 404
    
    return render_template('assets/asset_detail.html', asset=asset)

@asset_module_bp.route('/api/assets/<asset_number>')
def get_asset_detail_api(asset_number):
    """API endpoint for asset details"""
    asset_manager = AssetManager()
    asset = asset_manager.get_asset_detail(asset_number)
    
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    
    return jsonify(asset)

@asset_module_bp.route('/assets/export')
def export_assets():
    """Export filtered assets to Excel"""
    asset_manager = AssetManager()
    
    # Get same filters as API
    filters = {
        'active_only': request.args.get('active_only') == 'true',
        'category': request.args.get('category'),
        'gps_enabled': request.args.get('gps_enabled') == 'true',
        'search': request.args.get('search')
    }
    filters = {k: v for k, v in filters.items() if v}
    
    assets = asset_manager.get_all_assets(filters)
    
    # Convert to DataFrame for export
    df = pd.DataFrame(assets)
    
    # Create export filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'assets_export_{timestamp}.xlsx'
    
    # Save to file
    export_path = f'exports/{filename}'
    os.makedirs('exports', exist_ok=True)
    df.to_excel(export_path, index=False)
    
    return jsonify({
        'message': 'Export completed',
        'filename': filename,
        'records': len(assets)
    })

@asset_module_bp.route('/api/asset-categories')
def get_asset_categories():
    """Get all available asset categories"""
    asset_manager = AssetManager()
    stats = asset_manager.get_asset_statistics()
    
    return jsonify({
        'categories': list(asset_manager.asset_categories),
        'category_stats': stats['category_breakdown']
    })