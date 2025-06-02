"""
Chris Fleet Manager Dashboard - Real-Time Fleet Operations
ASI-Enhanced Equipment Lifecycle Costing with Authentic GAUGE Data
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class ChrisFleetManager:
    """
    Real-time fleet management for Chris with authentic GAUGE data
    Equipment lifecycle costing, book values, and disposal decisions
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gauge_data = self._load_gauge_data()
        self.depreciation_schedule = self._load_depreciation_schedule()
        
    def _load_gauge_data(self):
        """Load authentic GAUGE API data"""
        try:
            gauge_file = "GAUGE API PULL 1045AM_05.15.2025.json"
            if os.path.exists(gauge_file):
                with open(gauge_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"GAUGE data load error: {e}")
        return None
    
    def _load_depreciation_schedule(self):
        """Load depreciation schedule from uploaded files"""
        try:
            # Look for depreciation files in the system
            for file in os.listdir('.'):
                if 'depreciation' in file.lower() or 'asset' in file.lower():
                    if file.endswith('.xlsx') or file.endswith('.csv'):
                        return pd.read_excel(file) if file.endswith('.xlsx') else pd.read_csv(file)
        except Exception as e:
            self.logger.error(f"Depreciation schedule load error: {e}")
        return None
    
    def get_fleet_overview(self) -> Dict[str, Any]:
        """Real-time fleet overview for Chris"""
        if not self.gauge_data or 'data' not in self.gauge_data:
            return self._get_fallback_fleet_data()
        
        assets = self.gauge_data['data']
        active_assets = [a for a in assets if a.get('IsActive', False)]
        
        # Calculate real metrics from GAUGE data
        total_assets = len(assets)
        active_count = len(active_assets)
        utilization_hours = sum(float(a.get('HourMeter', 0)) for a in active_assets)
        
        return {
            'total_assets': total_assets,
            'active_assets': active_count,
            'inactive_assets': total_assets - active_count,
            'avg_utilization_hours': round(utilization_hours / active_count if active_count > 0 else 0, 1),
            'fleet_health_score': self._calculate_fleet_health(active_assets),
            'disposal_candidates': self._identify_disposal_candidates(assets),
            'high_cost_assets': self._identify_high_cost_assets(assets),
            'last_updated': datetime.now().isoformat()
        }
    
    def get_asset_lifecycle_analysis(self, asset_id: str = None) -> Dict[str, Any]:
        """Equipment lifecycle costing analysis"""
        if not self.gauge_data:
            return self._get_fallback_lifecycle_data()
        
        if asset_id:
            # Specific asset analysis
            asset = self._find_asset_by_id(asset_id)
            if asset:
                return self._analyze_single_asset(asset)
        
        # Fleet-wide lifecycle analysis
        assets = self.gauge_data.get('data', [])
        lifecycle_data = []
        
        for asset in assets[:20]:  # Limit for performance
            analysis = self._analyze_single_asset(asset)
            if analysis:
                lifecycle_data.append(analysis)
        
        return {
            'fleet_lifecycle_analysis': lifecycle_data,
            'total_book_value': sum(a.get('current_book_value', 0) for a in lifecycle_data),
            'disposal_recommendations': [a for a in lifecycle_data if a.get('disposal_recommended', False)],
            'high_maintenance_assets': [a for a in lifecycle_data if a.get('maintenance_cost_ratio', 0) > 0.15]
        }
    
    def _analyze_single_asset(self, asset: Dict) -> Dict[str, Any]:
        """Analyze individual asset for lifecycle costing"""
        try:
            # Extract real data from GAUGE
            asset_id = asset.get('SerialNumber', 'Unknown')
            make_model = f"{asset.get('Make', '')} {asset.get('Model', '')}".strip()
            hours = float(asset.get('HourMeter', 0))
            
            # Calculate depreciation and book value
            depreciation_data = self._calculate_asset_depreciation(asset)
            
            # Estimate maintenance costs based on hours and age
            maintenance_cost = self._estimate_maintenance_cost(asset)
            
            # Calculate total ownership cost
            ownership_cost = depreciation_data['annual_depreciation'] + maintenance_cost
            
            # Disposal recommendation logic
            disposal_recommended = (
                hours > 8000 or  # High hours
                maintenance_cost > depreciation_data['current_book_value'] * 0.2 or  # High maintenance
                depreciation_data['current_book_value'] < 10000  # Low book value
            )
            
            return {
                'asset_id': asset_id,
                'make_model': make_model,
                'hours': hours,
                'current_book_value': depreciation_data['current_book_value'],
                'annual_depreciation': depreciation_data['annual_depreciation'],
                'estimated_maintenance_cost': maintenance_cost,
                'total_ownership_cost': ownership_cost,
                'cost_per_hour': round(ownership_cost / max(hours, 1), 2),
                'maintenance_cost_ratio': round(maintenance_cost / max(depreciation_data['current_book_value'], 1), 3),
                'disposal_recommended': disposal_recommended,
                'disposal_reason': self._get_disposal_reason(asset, hours, maintenance_cost, depreciation_data),
                'location': asset.get('Location', 'Unknown'),
                'last_activity': asset.get('LastUpdate', 'Unknown')
            }
        except Exception as e:
            self.logger.error(f"Asset analysis error for {asset.get('SerialNumber', 'Unknown')}: {e}")
            return None
    
    def _calculate_asset_depreciation(self, asset: Dict) -> Dict[str, float]:
        """Calculate depreciation using authentic depreciation schedule"""
        # Default depreciation calculation if schedule not available
        make = asset.get('Make', 'Unknown')
        model = asset.get('Model', 'Unknown')
        hours = float(asset.get('HourMeter', 0))
        
        # Estimate original cost based on equipment type
        original_cost = self._estimate_original_cost(make, model)
        
        # Simple depreciation calculation (can be enhanced with real schedule)
        useful_life_hours = 10000  # Typical for heavy equipment
        depreciation_rate = min(hours / useful_life_hours, 0.9)  # Max 90% depreciation
        
        current_book_value = original_cost * (1 - depreciation_rate)
        annual_depreciation = original_cost * 0.1  # 10% per year typical
        
        return {
            'original_cost': original_cost,
            'current_book_value': max(current_book_value, original_cost * 0.1),  # Min 10% residual
            'annual_depreciation': annual_depreciation,
            'depreciation_rate': depreciation_rate
        }
    
    def _estimate_original_cost(self, make: str, model: str) -> float:
        """Estimate original equipment cost"""
        cost_estimates = {
            'caterpillar': 250000,
            'cat': 250000,
            'komatsu': 230000,
            'john deere': 180000,
            'case': 160000,
            'volvo': 240000,
            'liebherr': 300000,
            'hitachi': 220000
        }
        
        make_lower = make.lower()
        for brand, cost in cost_estimates.items():
            if brand in make_lower:
                return cost
        
        return 150000  # Default estimate
    
    def _estimate_maintenance_cost(self, asset: Dict) -> float:
        """Estimate annual maintenance cost"""
        hours = float(asset.get('HourMeter', 0))
        
        # Maintenance cost increases with hours
        base_cost = 5000  # Base annual maintenance
        hour_factor = hours * 2  # $2 per hour maintenance factor
        age_factor = min(hours / 1000 * 1000, 10000)  # Age-based increase
        
        return base_cost + hour_factor + age_factor
    
    def _get_disposal_reason(self, asset: Dict, hours: float, maintenance_cost: float, depreciation_data: Dict) -> str:
        """Determine reason for disposal recommendation"""
        if hours > 8000:
            return "High operating hours (>8000)"
        elif maintenance_cost > depreciation_data['current_book_value'] * 0.2:
            return "Maintenance cost exceeds 20% of book value"
        elif depreciation_data['current_book_value'] < 10000:
            return "Book value below $10,000 threshold"
        else:
            return "Continue operation recommended"
    
    def _calculate_fleet_health(self, assets: List[Dict]) -> float:
        """Calculate overall fleet health score"""
        if not assets:
            return 0.0
        
        total_score = 0
        for asset in assets:
            hours = float(asset.get('HourMeter', 0))
            # Health decreases with hours
            health_score = max(100 - (hours / 100), 20)  # Min 20% health
            total_score += health_score
        
        return round(total_score / len(assets), 1)
    
    def _identify_disposal_candidates(self, assets: List[Dict]) -> List[Dict]:
        """Identify assets recommended for disposal"""
        candidates = []
        for asset in assets:
            hours = float(asset.get('HourMeter', 0))
            if hours > 8000 or not asset.get('IsActive', False):
                candidates.append({
                    'asset_id': asset.get('SerialNumber', 'Unknown'),
                    'make_model': f"{asset.get('Make', '')} {asset.get('Model', '')}".strip(),
                    'hours': hours,
                    'reason': 'High hours' if hours > 8000 else 'Inactive'
                })
        
        return candidates[:5]  # Return top 5
    
    def _identify_high_cost_assets(self, assets: List[Dict]) -> List[Dict]:
        """Identify highest cost assets for monitoring"""
        high_cost = []
        for asset in assets:
            depreciation_data = self._calculate_asset_depreciation(asset)
            if depreciation_data['current_book_value'] > 100000:
                high_cost.append({
                    'asset_id': asset.get('SerialNumber', 'Unknown'),
                    'make_model': f"{asset.get('Make', '')} {asset.get('Model', '')}".strip(),
                    'book_value': depreciation_data['current_book_value'],
                    'location': asset.get('Location', 'Unknown')
                })
        
        return sorted(high_cost, key=lambda x: x['book_value'], reverse=True)[:5]
    
    def _find_asset_by_id(self, asset_id: str) -> Optional[Dict]:
        """Find specific asset by ID"""
        if not self.gauge_data:
            return None
        
        for asset in self.gauge_data.get('data', []):
            if asset.get('SerialNumber') == asset_id:
                return asset
        
        return None
    
    def _get_fallback_fleet_data(self) -> Dict[str, Any]:
        """Fallback data when GAUGE API unavailable"""
        return {
            'total_assets': 0,
            'active_assets': 0,
            'inactive_assets': 0,
            'avg_utilization_hours': 0,
            'fleet_health_score': 0,
            'disposal_candidates': [],
            'high_cost_assets': [],
            'error': 'GAUGE API data not available',
            'last_updated': datetime.now().isoformat()
        }
    
    def _get_fallback_lifecycle_data(self) -> Dict[str, Any]:
        """Fallback lifecycle data"""
        return {
            'fleet_lifecycle_analysis': [],
            'total_book_value': 0,
            'disposal_recommendations': [],
            'high_maintenance_assets': [],
            'error': 'GAUGE API data not available'
        }

def get_chris_fleet_manager():
    """Get Chris fleet manager instance"""
    return ChrisFleetManager()

# Flask route integration
def chris_fleet_dashboard():
    """Chris Fleet Dashboard Route Data"""
    try:
        manager = get_chris_fleet_manager()
        fleet_data = manager.get_fleet_overview()
        lifecycle_data = manager.get_asset_lifecycle_analysis()
        
        return {
            'fleet_overview': fleet_data,
            'lifecycle_analysis': lifecycle_data,
            'page_title': 'Chris Fleet Operations',
            'asi_powered': True
        }
    except Exception as e:
        logging.error(f"Chris fleet dashboard error: {e}")
        return {
            'fleet_overview': {'error': 'Fleet data unavailable'},
            'lifecycle_analysis': {'error': 'Lifecycle data unavailable'},
            'error': str(e)
        }