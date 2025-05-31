"""
TRAXOVO Performance Optimization Engine
Elite enterprise-grade performance with intelligent caching and data flow
"""
import time
import json
from functools import lru_cache
from datetime import datetime, timedelta
import threading
import requests
import os

class ElitePerformanceEngine:
    """Ultra-high performance engine for enterprise fleet management"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_duration = 300  # 5 minutes
        self.background_refresh = True
        self._setup_background_refresh()
    
    def _setup_background_refresh(self):
        """Background thread for data refresh without blocking UI"""
        def refresh_worker():
            while self.background_refresh:
                try:
                    # Pre-load critical data in background
                    self.get_cached_gauge_data(force_refresh=True)
                    time.sleep(180)  # Refresh every 3 minutes
                except Exception as e:
                    print(f"Background refresh error: {e}")
                    time.sleep(60)
        
        refresh_thread = threading.Thread(target=refresh_worker, daemon=True)
        refresh_thread.start()
    
    def get_cached_gauge_data(self, force_refresh=False):
        """Intelligent caching system for GAUGE API data"""
        cache_key = 'gauge_fleet_data'
        current_time = time.time()
        
        # Check if cache is valid and not forced refresh
        if (not force_refresh and 
            cache_key in self.cache and 
            cache_key in self.cache_timestamps and
            current_time - self.cache_timestamps[cache_key] < self.cache_duration):
            return self.cache[cache_key]
        
        # Fetch fresh data
        try:
            gauge_api_key = os.environ.get('GAUGE_API_KEY')
            gauge_api_url = os.environ.get('GAUGE_API_URL')
            
            if gauge_api_key and gauge_api_url:
                headers = {'Authorization': f'Bearer {gauge_api_key}'}
                response = requests.get(gauge_api_url, headers=headers, verify=False, timeout=15)
                
                if response.status_code == 200:
                    raw_data = response.json()
                    
                    # Process and optimize data structure
                    processed_data = self._process_elite_fleet_data(raw_data)
                    
                    # Cache the processed data
                    self.cache[cache_key] = processed_data
                    self.cache_timestamps[cache_key] = current_time
                    
                    return processed_data
        
        except Exception as e:
            print(f"GAUGE API error: {e}")
            # Return cached data if available, even if expired
            return self.cache.get(cache_key, self._get_empty_data())
        
        return self._get_empty_data()
    
    def _process_elite_fleet_data(self, raw_data):
        """Process raw GAUGE data into elite dashboard format"""
        if not isinstance(raw_data, list):
            return self._get_empty_data()
        
        # Elite processing with advanced categorization
        total_assets = len(raw_data)
        active_assets = 0
        categories = set()
        districts = set()
        makes = set()
        asset_details = []
        performance_metrics = {
            'utilization_rate': 0,
            'maintenance_due': 0,
            'high_value_assets': 0,
            'critical_alerts': 0
        }
        
        for asset in raw_data:
            # Active status detection
            if asset.get('Active') == True:
                active_assets += 1
            
            # Category classification
            category = asset.get('AssetCategory', '').strip()
            if category:
                categories.add(category)
            
            # Geographic distribution
            district = asset.get('District', '').strip()
            if district:
                districts.add(district)
            
            # Equipment make tracking
            make = asset.get('AssetMake', '').strip()
            if make:
                makes.add(make)
            
            # Performance analytics
            days_inactive = asset.get('DaysInactive', 0) or 0
            engine_hours = asset.get('Engine1Hours', 0) or 0
            
            if days_inactive > 7:
                performance_metrics['maintenance_due'] += 1
            if engine_hours > 5000:
                performance_metrics['high_value_assets'] += 1
            
            # Detailed asset info for frontend
            asset_details.append({
                'id': asset.get('DeviceSerialNumber', f'ASSET_{len(asset_details)}'),
                'category': category,
                'make': make,
                'model': asset.get('AssetModel', ''),
                'district': district,
                'active': asset.get('Active', False),
                'engine_hours': engine_hours,
                'days_inactive': days_inactive,
                'battery_pct': asset.get('BackupBatteryPct', 0),
                'class': asset.get('AssetClass', '')
            })
        
        # Calculate elite metrics
        utilization_rate = round((active_assets / total_assets * 100), 1) if total_assets > 0 else 0
        
        return {
            'summary': {
                'total_assets': total_assets,
                'active_assets': active_assets,
                'inactive_assets': total_assets - active_assets,
                'categories': len(categories),
                'districts': len(districts),
                'makes': len(makes),
                'utilization_rate': utilization_rate
            },
            'categories': sorted(list(categories)),
            'districts': sorted(list(districts)),
            'makes': sorted(list(makes)),
            'performance': performance_metrics,
            'assets': asset_details[:100],  # Limit for performance
            'last_updated': datetime.now().isoformat(),
            'data_quality': 'authentic_gauge_api'
        }
    
    def _get_empty_data(self):
        """Return empty structure when no data available"""
        return {
            'summary': {
                'total_assets': 0,
                'active_assets': 0,
                'inactive_assets': 0,
                'categories': 0,
                'districts': 0,
                'makes': 0,
                'utilization_rate': 0
            },
            'categories': [],
            'districts': [],
            'makes': [],
            'performance': {'utilization_rate': 0, 'maintenance_due': 0, 'high_value_assets': 0, 'critical_alerts': 0},
            'assets': [],
            'last_updated': datetime.now().isoformat(),
            'data_quality': 'no_data'
        }
    
    def get_dashboard_metrics(self):
        """Get optimized metrics for dashboard display"""
        data = self.get_cached_gauge_data()
        return data['summary']
    
    def get_fleet_categories(self):
        """Get equipment categories for filtering"""
        data = self.get_cached_gauge_data()
        return {
            'categories': data['categories'],
            'total': len(data['categories'])
        }
    
    def get_performance_analytics(self):
        """Get advanced performance metrics"""
        data = self.get_cached_gauge_data()
        return {
            'utilization': data['summary']['utilization_rate'],
            'efficiency_score': min(100, data['summary']['utilization_rate'] * 1.2),
            'fleet_health': 'Excellent' if data['summary']['utilization_rate'] > 80 else 'Good',
            'maintenance_alerts': data['performance']['maintenance_due'],
            'asset_distribution': {
                'categories': len(data['categories']),
                'locations': len(data['districts']),
                'manufacturers': len(data['makes'])
            }
        }

# Global performance engine instance
performance_engine = ElitePerformanceEngine()

def get_performance_engine():
    """Get the global performance engine"""
    return performance_engine