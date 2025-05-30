"""
Comprehensive Asset Lifecycle Management Engine
Handles acquisitions, disposals, theft tracking, and depreciation analysis
"""

import os
import json
import logging
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class AssetLifecycleEngine:
    """Complete asset lifecycle management with authentic data integration"""
    
    def __init__(self):
        self.gauge_data = self._load_gauge_api_data()
        self.excel_data = self._load_excel_depreciation_data()
        self.asset_registry = self._build_comprehensive_registry()
        
    def _load_gauge_api_data(self):
        """Load authentic 717 assets from Gauge API"""
        try:
            url = 'https://api.gaugesmart.com/AssetList/28dcba94c01e453fa8e9215a068f30e4'
            auth = ('bwatson', 'Plsw@2900413477')
            
            response = requests.get(url, auth=auth, verify=False, timeout=10)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Loaded {len(data)} assets from Gauge API")
                return data
            else:
                logger.error(f"Gauge API error: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error loading Gauge data: {e}")
            return []
    
    def _load_excel_depreciation_data(self):
        """Load comprehensive depreciation data from April 2025 Excel"""
        try:
            file_path = 'RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm'
            
            # Load all relevant sheets
            equipment_df = pd.read_excel(file_path, sheet_name='Equip Table')
            rates_df = pd.read_excel(file_path, sheet_name='Equip Rates')
            billing_df = pd.read_excel(file_path, sheet_name='Equip Billings')
            
            return {
                'equipment': equipment_df,
                'rates': rates_df,
                'billing': billing_df,
                'loaded_at': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error loading Excel data: {e}")
            return {}
    
    def _build_comprehensive_registry(self):
        """Build comprehensive asset registry combining all data sources"""
        registry = {}
        
        # Process Gauge API data
        for asset in self.gauge_data:
            asset_id = asset.get('AssetId', asset.get('id', 'unknown'))
            registry[asset_id] = {
                'source': 'gauge_api',
                'name': asset.get('AssetName', asset.get('name', 'Unknown')),
                'status': asset.get('Status', 'unknown'),
                'location': {
                    'lat': asset.get('Latitude', 0),
                    'lng': asset.get('Longitude', 0),
                    'last_update': asset.get('LastUpdate', '')
                },
                'gauge_data': asset
            }
        
        # Enhance with Excel financial data
        if 'equipment' in self.excel_data:
            for _, row in self.excel_data['equipment'].iterrows():
                asset_id = row.get('Equipment #', '')
                if asset_id and asset_id in registry:
                    registry[asset_id].update({
                        'purchase_price': float(row.get('Purchase Price', 0) or 0),
                        'description': row.get('Equipment Description', ''),
                        'division': row.get('Division', ''),
                        'financial_status': row.get('Status', 'A')
                    })
                elif asset_id:
                    # Asset in Excel but not Gauge - potentially disposed/stolen
                    registry[asset_id] = {
                        'source': 'excel_only',
                        'name': row.get('Equipment Description', ''),
                        'purchase_price': float(row.get('Purchase Price', 0) or 0),
                        'status': 'disposed_or_stolen',
                        'division': row.get('Division', ''),
                        'financial_status': row.get('Status', 'I')
                    }
        
        # Add rate information
        if 'rates' in self.excel_data:
            for _, row in self.excel_data['rates'].iterrows():
                asset_id = row.get('Equip #', '')
                if asset_id and asset_id in registry:
                    registry[asset_id].update({
                        'monthly_rate': float(row.get('Rate', 0) or 0),
                        'category': row.get('Category', ''),
                        'utilization_rate': float(row.get('Month %', 0) or 0)
                    })
        
        return registry
    
    def get_fleet_summary(self):
        """Get accurate fleet summary with real counts"""
        active_count = 0
        inactive_count = 0
        disposed_stolen_count = 0
        total_value = 0
        
        for asset_id, asset in self.asset_registry.items():
            purchase_price = asset.get('purchase_price', 0)
            total_value += purchase_price
            
            if asset.get('source') == 'gauge_api':
                if asset.get('status', '').lower() in ['active', 'moving', 'on']:
                    active_count += 1
                else:
                    inactive_count += 1
            elif asset.get('status') == 'disposed_or_stolen':
                disposed_stolen_count += 1
        
        return {
            'total_assets': len(self.asset_registry),
            'active_assets': active_count,
            'inactive_assets': inactive_count,
            'disposed_stolen': disposed_stolen_count,
            'gauge_api_assets': len(self.gauge_data),
            'total_fleet_value': total_value,
            'data_sources': ['gauge_api', 'excel_april_2025']
        }
    
    def get_asset_detail(self, asset_id: str):
        """Get comprehensive asset details"""
        if asset_id not in self.asset_registry:
            return None
        
        asset = self.asset_registry[asset_id]
        
        # Calculate depreciation if purchase price available
        depreciation_info = {}
        if asset.get('purchase_price', 0) > 0:
            depreciation_info = self._calculate_depreciation(asset)
        
        return {
            'asset_id': asset_id,
            'basic_info': asset,
            'depreciation': depreciation_info,
            'billing_history': self._get_billing_history(asset_id),
            'location_history': self._get_location_history(asset_id)
        }
    
    def _calculate_depreciation(self, asset):
        """Calculate asset depreciation using authentic data"""
        purchase_price = asset.get('purchase_price', 0)
        
        # Standard construction equipment depreciation (5-7 years)
        useful_life_years = 7
        annual_depreciation = purchase_price / useful_life_years
        monthly_depreciation = annual_depreciation / 12
        
        # Estimate current book value (simplified)
        estimated_age_months = 36  # Default estimate, could be enhanced
        accumulated_depreciation = monthly_depreciation * estimated_age_months
        current_book_value = max(0, purchase_price - accumulated_depreciation)
        
        return {
            'purchase_price': purchase_price,
            'annual_depreciation': annual_depreciation,
            'monthly_depreciation': monthly_depreciation,
            'accumulated_depreciation': accumulated_depreciation,
            'current_book_value': current_book_value,
            'useful_life_years': useful_life_years
        }
    
    def _get_billing_history(self, asset_id: str):
        """Get billing history for asset"""
        if 'billing' not in self.excel_data:
            return []
        
        billing_df = self.excel_data['billing']
        asset_billing = billing_df[billing_df['Equip #'] == asset_id]
        
        return asset_billing.to_dict('records') if not asset_billing.empty else []
    
    def _get_location_history(self, asset_id: str):
        """Get location history for theft/disposal tracking"""
        asset = self.asset_registry.get(asset_id, {})
        gauge_data = asset.get('gauge_data', {})
        
        if gauge_data:
            return {
                'current_location': {
                    'lat': gauge_data.get('Latitude', 0),
                    'lng': gauge_data.get('Longitude', 0),
                    'last_update': gauge_data.get('LastUpdate', ''),
                    'address': gauge_data.get('Address', 'Unknown')
                },
                'status': 'tracked_via_gauge_api'
            }
        else:
            return {
                'status': 'no_gps_data',
                'last_known_location': 'Check Excel records for last job assignment'
            }
    
    def record_asset_disposal(self, asset_id: str, disposal_reason: str, location: str):
        """Record asset disposal/theft with location"""
        if asset_id in self.asset_registry:
            self.asset_registry[asset_id].update({
                'status': 'disposed',
                'disposal_reason': disposal_reason,
                'disposal_location': location,
                'disposal_date': datetime.now().isoformat()
            })
            return True
        return False
    
    def record_asset_acquisition(self, asset_data: Dict):
        """Record new asset acquisition"""
        asset_id = asset_data.get('equipment_id')
        if asset_id:
            self.asset_registry[asset_id] = {
                'source': 'manual_entry',
                'status': 'active',
                'acquisition_date': datetime.now().isoformat(),
                **asset_data
            }
            return True
        return False
    
    def get_depreciation_report(self):
        """Generate comprehensive depreciation report"""
        report = {
            'total_purchase_value': 0,
            'total_current_value': 0,
            'total_depreciation': 0,
            'assets_by_category': {},
            'high_value_assets': [],
            'generated_at': datetime.now().isoformat()
        }
        
        for asset_id, asset in self.asset_registry.items():
            purchase_price = asset.get('purchase_price', 0)
            category = asset.get('category', 'Unknown')
            
            if purchase_price > 0:
                depreciation_info = self._calculate_depreciation(asset)
                current_value = depreciation_info['current_book_value']
                
                report['total_purchase_value'] += purchase_price
                report['total_current_value'] += current_value
                report['total_depreciation'] += depreciation_info['accumulated_depreciation']
                
                # Group by category
                if category not in report['assets_by_category']:
                    report['assets_by_category'][category] = {
                        'count': 0,
                        'total_purchase': 0,
                        'total_current': 0
                    }
                
                report['assets_by_category'][category]['count'] += 1
                report['assets_by_category'][category]['total_purchase'] += purchase_price
                report['assets_by_category'][category]['total_current'] += current_value
                
                # Track high-value assets
                if purchase_price > 20000:
                    report['high_value_assets'].append({
                        'asset_id': asset_id,
                        'name': asset.get('name', ''),
                        'purchase_price': purchase_price,
                        'current_value': current_value,
                        'monthly_rate': asset.get('monthly_rate', 0)
                    })
        
        return report

# Global instance
asset_lifecycle_engine = AssetLifecycleEngine()

def get_asset_lifecycle_engine():
    """Get the asset lifecycle engine"""
    return asset_lifecycle_engine