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
            category = asset.get('AssetCategory') or ''
            if isinstance(category, str) and category.strip():
                categories.add(category.strip())
            
            # Geographic distribution
            district = asset.get('District') or ''
            if isinstance(district, str) and district.strip():
                districts.add(district.strip())
            
            # Equipment make tracking
            make = asset.get('AssetMake') or ''
            if isinstance(make, str) and make.strip():
                makes.add(make.strip())
            
            # Performance analytics
            days_inactive = asset.get('DaysInactive', 0) or 0
            engine_hours = asset.get('Engine1Hours', 0) or 0
            
            # Convert to numeric values safely
            try:
                days_inactive = float(days_inactive) if days_inactive else 0
                engine_hours = float(engine_hours) if engine_hours else 0
            except (ValueError, TypeError):
                days_inactive = 0
                engine_hours = 0
            
            if days_inactive > 7:
                performance_metrics['maintenance_due'] += 1
            if engine_hours > 5000:
                performance_metrics['high_value_assets'] += 1
            
            # Detailed asset info for frontend - separate active/inactive
            asset_detail = {
                'id': asset.get('DeviceSerialNumber', f'ASSET_{len(asset_details)}'),
                'category': category,
                'make': make,
                'model': asset.get('AssetModel', ''),
                'district': district,
                'active': asset.get('Active', False),
                'engine_hours': engine_hours,
                'days_inactive': days_inactive,
                'battery_pct': asset.get('BackupBatteryPct', 0),
                'class': asset.get('AssetClass', ''),
                'status': 'Active' if asset.get('Active', False) else 'Inactive'
            }
            asset_details.append(asset_detail)
        
        # Calculate elite metrics
        utilization_rate = round((active_assets / total_assets * 100), 1) if total_assets > 0 else 0
        
        # Separate active and inactive assets for better display control
        active_asset_details = [asset for asset in asset_details if asset['active']]
        inactive_asset_details = [asset for asset in asset_details if not asset['active']]
        
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
            'assets': active_asset_details[:100],  # Show active assets by default
            'inactive_assets': inactive_asset_details[:50],  # Separate inactive list
            'asset_tooltips': self._generate_asset_tooltips(asset_details[:150]) if hasattr(self, '_generate_asset_tooltips') else {},
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
    
    def _generate_asset_tooltips(self, asset_details):
        """Generate contextual hover tooltips for asset metrics"""
        tooltips = {}
        
        for asset in asset_details:
            asset_id = asset['id']
            
            # Calculate asset-specific metrics
            efficiency = self._calculate_asset_efficiency(asset)
            health_status = self._determine_health_status(asset)
            utilization_info = self._get_utilization_info(asset)
            
            tooltips[asset_id] = {
                'header': f"{asset['make']} {asset['model']}",
                'category': asset['category'],
                'status': asset['status'],
                'location': asset['district'] or 'Unknown Location',
                'metrics': {
                    'engine_hours': f"{asset['engine_hours']:,} hrs",
                    'efficiency_score': f"{efficiency}%",
                    'health_status': health_status,
                    'battery_level': f"{asset['battery_pct']}%",
                    'days_inactive': asset['days_inactive']
                },
                'utilization': utilization_info,
                'maintenance': {
                    'next_service': self._estimate_next_service(asset),
                    'priority': self._get_maintenance_priority(asset)
                },
                'performance_indicators': {
                    'productivity': self._calculate_productivity_score(asset),
                    'reliability': self._calculate_reliability_score(asset)
                }
            }
        
        return tooltips
    
    def _calculate_asset_efficiency(self, asset):
        """Calculate individual asset efficiency score"""
        base_score = 85
        if asset['days_inactive'] > 7:
            base_score -= 20
        if asset['engine_hours'] > 5000:
            base_score += 10
        if asset['battery_pct'] < 20:
            base_score -= 15
        return max(0, min(100, base_score))
    
    def _determine_health_status(self, asset):
        """Determine asset health status"""
        if asset['days_inactive'] > 14:
            return 'Needs Attention'
        elif asset['battery_pct'] < 30:
            return 'Battery Low'
        elif asset['engine_hours'] > 8000:
            return 'High Usage'
        else:
            return 'Good'
    
    def _get_utilization_info(self, asset):
        """Get asset utilization information"""
        if asset['active']:
            return {
                'status': 'Currently Active',
                'usage_pattern': 'Regular Operation',
                'efficiency': 'Optimal'
            }
        else:
            return {
                'status': 'Inactive',
                'idle_time': f"{asset['days_inactive']} days",
                'efficiency': 'Below Target'
            }
    
    def _estimate_next_service(self, asset):
        """Estimate next service requirement"""
        hours = asset['engine_hours']
        if hours > 7500:
            return 'Due Soon'
        elif hours > 5000:
            return 'Within 30 Days'
        else:
            return 'Not Required'
    
    def _get_maintenance_priority(self, asset):
        """Get maintenance priority level"""
        if asset['days_inactive'] > 14 or asset['engine_hours'] > 8000:
            return 'High'
        elif asset['battery_pct'] < 30:
            return 'Medium'
        else:
            return 'Low'
    
    def _calculate_productivity_score(self, asset):
        """Calculate productivity score"""
        if asset['active'] and asset['days_inactive'] < 3:
            return 'High'
        elif asset['active']:
            return 'Medium'
        else:
            return 'Low'
    
    def _calculate_reliability_score(self, asset):
        """Calculate reliability score"""
        if asset['engine_hours'] < 5000 and asset['battery_pct'] > 70:
            return 'Excellent'
        elif asset['engine_hours'] < 8000:
            return 'Good'
        else:
            return 'Fair'

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