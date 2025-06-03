"""
Live Preview Panels
Split-screen views showing data transformations in real-time as filters are adjusted
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request

live_preview_bp = Blueprint('live_preview', __name__)

class LivePreviewEngine:
    """Real-time data preview system for fleet analytics"""
    
    def __init__(self):
        self.load_authentic_data()
    
    def load_authentic_data(self):
        """Load authentic fleet data for live previews"""
        try:
            # Load billing data
            from comprehensive_billing_engine import ComprehensiveBillingEngine
            billing_engine = ComprehensiveBillingEngine()
            self.billing_data = billing_engine.ragle_data
            
            # Load Gauge API data
            gauge_file = 'GAUGE API PULL 1045AM_05.15.2025.json'
            if os.path.exists(gauge_file):
                with open(gauge_file, 'r') as f:
                    self.gauge_data = json.load(f)
            else:
                self.gauge_data = {}
                
        except Exception as e:
            print(f"Loading preview data: {e}")
            self.billing_data = []
            self.gauge_data = {}
    
    def apply_filters(self, data_source, filters):
        """Apply filters to authentic data and return preview"""
        try:
            if data_source == 'billing':
                df = pd.DataFrame(self.billing_data)
                
                # Apply date range filter
                if 'date_range' in filters and len(df) > 0:
                    start_date = filters['date_range'].get('start')
                    end_date = filters['date_range'].get('end')
                    if start_date and end_date and 'date' in df.columns:
                        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
                
                # Apply equipment type filter
                if 'equipment_type' in filters and len(df) > 0:
                    equipment_types = filters['equipment_type']
                    if equipment_types and 'category' in df.columns:
                        df = df[df['category'].isin(equipment_types)]
                
                # Apply cost range filter
                if 'cost_range' in filters and len(df) > 0:
                    min_cost = filters['cost_range'].get('min', 0)
                    max_cost = filters['cost_range'].get('max', float('inf'))
                    if 'amount' in df.columns:
                        df = df[(df['amount'] >= min_cost) & (df['amount'] <= max_cost)]
                
                return {
                    'total_records': len(df),
                    'total_cost': df['amount'].sum() if 'amount' in df.columns and len(df) > 0 else 0,
                    'equipment_count': df['equipment_id'].nunique() if 'equipment_id' in df.columns and len(df) > 0 else 0,
                    'preview_data': df.head(10).to_dict('records') if len(df) > 0 else [],
                    'data_source': 'Authentic Ragle Billing Data'
                }
                
            elif data_source == 'assets':
                assets = self.gauge_data.get('assets', [])
                filtered_assets = assets
                
                # Apply GPS filter
                if 'gps_enabled' in filters:
                    gps_filter = filters['gps_enabled']
                    if gps_filter == 'enabled':
                        filtered_assets = [a for a in filtered_assets if a.get('gps_enabled', False)]
                    elif gps_filter == 'disabled':
                        filtered_assets = [a for a in filtered_assets if not a.get('gps_enabled', False)]
                
                # Apply asset type filter
                if 'asset_type' in filters:
                    asset_types = filters['asset_type']
                    if asset_types:
                        filtered_assets = [a for a in filtered_assets if a.get('type') in asset_types]
                
                # Apply hours range filter
                if 'hours_range' in filters:
                    min_hours = filters['hours_range'].get('min', 0)
                    max_hours = filters['hours_range'].get('max', float('inf'))
                    filtered_assets = [a for a in filtered_assets 
                                     if min_hours <= a.get('total_hours', 0) <= max_hours]
                
                return {
                    'total_assets': len(filtered_assets),
                    'gps_enabled': sum(1 for a in filtered_assets if a.get('gps_enabled', False)),
                    'total_hours': sum(a.get('total_hours', 0) for a in filtered_assets),
                    'preview_data': filtered_assets[:10],
                    'data_source': 'Authentic Gauge API Data'
                }
                
        except Exception as e:
            print(f"Filter application error: {e}")
            
        return {
            'error': 'Unable to apply filters to authentic data',
            'total_records': 0,
            'preview_data': []
        }
    
    def get_filter_options(self, data_source):
        """Get available filter options from authentic data"""
        try:
            if data_source == 'billing':
                df = pd.DataFrame(self.billing_data)
                
                return {
                    'equipment_types': df['category'].unique().tolist() if 'category' in df.columns else [],
                    'date_range': {
                        'min': df['date'].min() if 'date' in df.columns and len(df) > 0 else None,
                        'max': df['date'].max() if 'date' in df.columns and len(df) > 0 else None
                    },
                    'cost_range': {
                        'min': float(df['amount'].min()) if 'amount' in df.columns and len(df) > 0 else 0,
                        'max': float(df['amount'].max()) if 'amount' in df.columns and len(df) > 0 else 0
                    }
                }
                
            elif data_source == 'assets':
                assets = self.gauge_data.get('assets', [])
                
                return {
                    'asset_types': list(set(a.get('type', 'Unknown') for a in assets)),
                    'hours_range': {
                        'min': min(a.get('total_hours', 0) for a in assets) if assets else 0,
                        'max': max(a.get('total_hours', 0) for a in assets) if assets else 0
                    },
                    'gps_options': ['all', 'enabled', 'disabled']
                }
                
        except Exception as e:
            print(f"Filter options error: {e}")
            
        return {}

@live_preview_bp.route('/live-preview')
def live_preview_dashboard():
    """Live preview dashboard interface"""
    engine = LivePreviewEngine()
    
    # Get filter options for both data sources
    billing_options = engine.get_filter_options('billing')
    asset_options = engine.get_filter_options('assets')
    
    return render_template('live_preview_dashboard.html',
                         billing_options=billing_options,
                         asset_options=asset_options)

@live_preview_bp.route('/api/live-preview', methods=['POST'])
def api_live_preview():
    """Apply filters and return live preview of data"""
    data = request.get_json()
    data_source = data.get('data_source', 'billing')
    filters = data.get('filters', {})
    
    engine = LivePreviewEngine()
    preview_result = engine.apply_filters(data_source, filters)
    
    return jsonify({
        'preview': preview_result,
        'filters_applied': filters,
        'timestamp': datetime.now().isoformat()
    })

@live_preview_bp.route('/api/filter-options/<data_source>')
def api_filter_options(data_source):
    """Get available filter options for a data source"""
    engine = LivePreviewEngine()
    options = engine.get_filter_options(data_source)
    
    return jsonify({
        'data_source': data_source,
        'options': options,
        'timestamp': datetime.now().isoformat()
    })

def get_live_preview_engine():
    """Get live preview engine instance"""
    return LivePreviewEngine()