"""
Smart Auto-Complete Search System
Intelligent search with predictive suggestions for assets, drivers, and reports
"""

import pandas as pd
import json
import os
from datetime import datetime
from flask import Blueprint, render_template, jsonify, request
from fuzzywuzzy import fuzz, process

smart_search_bp = Blueprint('smart_search', __name__)

class SmartSearchEngine:
    """Intelligent search engine for fleet assets and data"""
    
    def __init__(self):
        self.load_search_index()
    
    def load_search_index(self):
        """Build comprehensive search index from authentic data"""
        self.search_index = []
        
        try:
            # Load Gauge API assets
            gauge_file = 'GAUGE API PULL 1045AM_05.15.2025.json'
            if os.path.exists(gauge_file):
                with open(gauge_file, 'r') as f:
                    gauge_data = json.load(f)
                    
                for asset in gauge_data.get('assets', []):
                    self.search_index.append({
                        'id': asset.get('asset_id', 'Unknown'),
                        'title': f"Asset {asset.get('asset_id', 'Unknown')}",
                        'subtitle': asset.get('type', 'Equipment'),
                        'category': 'asset',
                        'url': f"/asset-detail/{asset.get('asset_id', 'unknown')}",
                        'keywords': [asset.get('asset_id', ''), asset.get('type', ''), 'equipment', 'asset'],
                        'data': asset
                    })
            
            # Load billing data for equipment search
            from comprehensive_billing_engine import ComprehensiveBillingEngine
            billing_engine = ComprehensiveBillingEngine()
            billing_data = billing_engine.load_authentic_ragle_data()
            
            equipment_seen = set()
            for record in billing_data:
                equipment_id = record.get('equipment_id', 'Unknown')
                if equipment_id not in equipment_seen and equipment_id != 'Unknown':
                    equipment_seen.add(equipment_id)
                    self.search_index.append({
                        'id': equipment_id,
                        'title': f"Equipment {equipment_id}",
                        'subtitle': record.get('category', 'Equipment'),
                        'category': 'equipment',
                        'url': f"/equipment-detail/{equipment_id}",
                        'keywords': [equipment_id, record.get('category', ''), 'billing', 'equipment'],
                        'data': record
                    })
            
            # Add dashboard modules
            dashboard_modules = [
                {'id': 'dashboard', 'title': 'Main Dashboard', 'subtitle': 'Fleet Overview', 'url': '/', 'category': 'dashboard'},
                {'id': 'ai-assistant', 'title': 'AI Fleet Assistant', 'subtitle': 'Intelligent Analysis', 'url': '/ai-assistant', 'category': 'ai'},
                {'id': 'maintenance', 'title': 'Maintenance Countdown', 'subtitle': 'Service Scheduling', 'url': '/maintenance-countdown', 'category': 'maintenance'},
                {'id': 'vendor-analysis', 'title': 'Vendor A/P Analysis', 'subtitle': 'Cost Validation', 'url': '/vendor-analysis', 'category': 'financial'},
                {'id': 'dynamic-metrics', 'title': 'Dynamic Metrics', 'subtitle': 'Performance Analytics', 'url': '/dynamic-metrics', 'category': 'analytics'},
                {'id': 'equipment-lifecycle', 'title': 'Equipment Lifecycle', 'subtitle': 'Depreciation Analysis', 'url': '/equipment-lifecycle', 'category': 'equipment'},
                {'id': 'cost-intelligence', 'title': 'Cost Intelligence', 'subtitle': 'Savings Analysis', 'url': '/cost-intelligence', 'category': 'financial'},
                {'id': 'theft-alerts', 'title': 'Theft Alert System', 'subtitle': 'Security Monitoring', 'url': '/theft-alerts', 'category': 'security'},
                {'id': 'gps-efficiency', 'title': 'GPS Efficiency', 'subtitle': 'Location Intelligence', 'url': '/gps-efficiency', 'category': 'gps'},
                {'id': 'attendance', 'title': 'Attendance Tracking', 'subtitle': 'Driver Management', 'url': '/attendance', 'category': 'drivers'}
            ]
            
            for module in dashboard_modules:
                module['keywords'] = [module['title'].lower(), module['subtitle'].lower(), module['category']]
                self.search_index.append(module)
                
            print(f"Smart search index loaded: {len(self.search_index)} items")
            
        except Exception as e:
            print(f"Error loading search index: {e}")
            # Minimal fallback index
            self.search_index = [
                {'id': 'dashboard', 'title': 'Main Dashboard', 'subtitle': 'Fleet Overview', 'url': '/', 'category': 'dashboard', 'keywords': ['dashboard', 'main', 'fleet']}
            ]
    
    def search(self, query, limit=10):
        """Perform intelligent search with fuzzy matching"""
        if not query or len(query) < 2:
            return []
        
        query_lower = query.lower().strip()
        results = []
        
        # Direct ID matches (highest priority)
        for item in self.search_index:
            if query_lower == item['id'].lower():
                results.append({**item, 'score': 100, 'match_type': 'exact_id'})
        
        # Title matches
        for item in self.search_index:
            title_score = fuzz.partial_ratio(query_lower, item['title'].lower())
            if title_score > 60:
                results.append({**item, 'score': title_score + 10, 'match_type': 'title'})
        
        # Keyword matches
        for item in self.search_index:
            for keyword in item.get('keywords', []):
                keyword_score = fuzz.partial_ratio(query_lower, str(keyword).lower())
                if keyword_score > 70:
                    results.append({**item, 'score': keyword_score, 'match_type': 'keyword'})
        
        # Category matches
        for item in self.search_index:
            category_score = fuzz.partial_ratio(query_lower, item['category'].lower())
            if category_score > 70:
                results.append({**item, 'score': category_score - 10, 'match_type': 'category'})
        
        # Remove duplicates and sort by score
        seen_ids = set()
        unique_results = []
        for result in results:
            if result['id'] not in seen_ids:
                seen_ids.add(result['id'])
                unique_results.append(result)
        
        # Sort by score descending
        unique_results.sort(key=lambda x: x['score'], reverse=True)
        
        return unique_results[:limit]
    
    def get_suggestions(self, query):
        """Get search suggestions based on partial input"""
        if not query or len(query) < 1:
            # Return popular/recent items
            return [
                {'text': 'Asset Dashboard', 'category': 'dashboard'},
                {'text': 'Maintenance Alerts', 'category': 'maintenance'},
                {'text': 'Cost Analysis', 'category': 'financial'},
                {'text': 'GPS Tracking', 'category': 'gps'}
            ]
        
        suggestions = []
        query_lower = query.lower()
        
        # Collect potential matches
        for item in self.search_index:
            # Title suggestions
            if query_lower in item['title'].lower():
                suggestions.append({
                    'text': item['title'],
                    'category': item['category'],
                    'type': 'title'
                })
            
            # Keyword suggestions
            for keyword in item.get('keywords', []):
                if query_lower in str(keyword).lower() and len(str(keyword)) > 2:
                    suggestions.append({
                        'text': str(keyword).title(),
                        'category': item['category'],
                        'type': 'keyword'
                    })
        
        # Remove duplicates and limit
        unique_suggestions = []
        seen_texts = set()
        for suggestion in suggestions:
            if suggestion['text'] not in seen_texts:
                seen_texts.add(suggestion['text'])
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:8]
    
    def get_quick_access_items(self):
        """Get frequently accessed items for quick navigation"""
        return [
            {'title': 'Fleet Dashboard', 'url': '/', 'icon': '🚛', 'category': 'dashboard'},
            {'title': 'AI Assistant', 'url': '/ai-assistant', 'icon': '🤖', 'category': 'ai'},
            {'title': 'Maintenance Alerts', 'url': '/maintenance-countdown', 'icon': '🔧', 'category': 'maintenance'},
            {'title': 'Cost Analysis', 'url': '/cost-intelligence', 'icon': '💰', 'category': 'financial'},
            {'title': 'GPS Efficiency', 'url': '/gps-efficiency', 'icon': '📍', 'category': 'gps'},
            {'title': 'Equipment Lifecycle', 'url': '/equipment-lifecycle', 'icon': '⚙️', 'category': 'equipment'}
        ]

@smart_search_bp.route('/api/search')
def api_search():
    """Search API endpoint"""
    query = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 10))
    
    engine = SmartSearchEngine()
    results = engine.search(query, limit)
    
    return jsonify({
        'query': query,
        'results': results,
        'total': len(results),
        'timestamp': datetime.now().isoformat()
    })

@smart_search_bp.route('/api/suggestions')
def api_suggestions():
    """Search suggestions API endpoint"""
    query = request.args.get('q', '').strip()
    
    engine = SmartSearchEngine()
    suggestions = engine.get_suggestions(query)
    
    return jsonify({
        'query': query,
        'suggestions': suggestions,
        'timestamp': datetime.now().isoformat()
    })

@smart_search_bp.route('/api/quick-access')
def api_quick_access():
    """Quick access items API endpoint"""
    engine = SmartSearchEngine()
    items = engine.get_quick_access_items()
    
    return jsonify({
        'items': items,
        'timestamp': datetime.now().isoformat()
    })

def get_search_engine():
    """Get search engine instance"""
    return SmartSearchEngine()