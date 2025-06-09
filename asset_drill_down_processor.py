"""
TRAXOVO Asset Drill-Down Processor
Individual asset metrics, depreciation, lifecycle costing, and equipment management
"""

import csv
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

class AssetDrillDownProcessor:
    """Process individual asset data for comprehensive drill-down views"""
    
    def __init__(self):
        self.assets = {}
        self.depreciation_schedules = {}
        self.lifecycle_costs = {}
        self.maintenance_schedules = {}
        
    def extract_asset_details(self) -> Dict[str, Any]:
        """Extract comprehensive asset details from uploaded CSV files"""
        try:
            # Extract from DailyUsage CSV
            daily_usage_data = self._process_daily_usage()
            
            # Extract from ActivityDetail CSV  
            activity_data = self._process_activity_detail()
            
            # Extract from ServiceHistory CSV
            service_data = self._process_service_history()
            
            # Combine all data sources
            consolidated_assets = self._consolidate_asset_data(
                daily_usage_data, activity_data, service_data
            )
            
            return {
                'total_assets': len(consolidated_assets),
                'assets': consolidated_assets,
                'data_source': 'AUTHENTIC_CSV_EXPORTS',
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Asset extraction error: {e}")
            return {'error': 'Asset data processing failed'}
    
    def _process_daily_usage(self) -> Dict[str, Any]:
        """Process DailyUsage CSV for asset metrics"""
        assets = {}
        
        try:
            with open('attached_assets/DailyUsage_1749454857635.csv', 'r') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    if 'AssetLabel' in row and row['AssetLabel']:
                        asset_id = self._extract_asset_id(row['AssetLabel'])
                        
                        if asset_id not in assets:
                            assets[asset_id] = {
                                'asset_id': asset_id,
                                'asset_label': row['AssetLabel'],
                                'asset_type': row.get('AssetType', 'Unknown'),
                                'asset_category': row.get('AssetCategory', 'Unknown'),
                                'operator': self._extract_operator_name(row['AssetLabel']),
                                'total_distance': 0,
                                'total_hours': 0,
                                'utilization_data': [],
                                'locations': [],
                                'daily_records': []
                            }
                        
                        # Add daily metrics
                        distance = float(row.get('Distance', 0) or 0)
                        hours = float(row.get('Engine1Hours', 0) or 0)
                        
                        assets[asset_id]['total_distance'] += distance
                        assets[asset_id]['total_hours'] += hours
                        
                        assets[asset_id]['daily_records'].append({
                            'date': row.get('Date', ''),
                            'distance': distance,
                            'hours': hours,
                            'location': row.get('Location', ''),
                            'idle_time': row.get('Idle', 0),
                            'started': row.get('Started', ''),
                            'stopped': row.get('Stopped', '')
                        })
                        
        except Exception as e:
            logging.error(f"Daily usage processing error: {e}")
            
        return assets
    
    def _process_activity_detail(self) -> Dict[str, Any]:
        """Process ActivityDetail CSV for asset tracking data"""
        activity_assets = {}
        
        try:
            with open('attached_assets/ActivityDetail (4)_1749454854416.csv', 'r') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    if 'AssetLabel' in row and row['AssetLabel']:
                        asset_id = self._extract_asset_id(row['AssetLabel'])
                        
                        if asset_id not in activity_assets:
                            activity_assets[asset_id] = {
                                'asset_id': asset_id,
                                'asset_label': row['AssetLabel'],
                                'odometer': 0,
                                'hour_meter': 0,
                                'coordinates': [],
                                'key_events': [],
                                'project_assignments': []
                            }
                        
                        # Extract odometer and hour meter readings
                        if row.get('Odometerx'):
                            activity_assets[asset_id]['odometer'] = float(row['Odometerx'])
                        
                        if row.get('HourMeter'):
                            activity_assets[asset_id]['hour_meter'] = float(row['HourMeter'])
                        
                        # Extract GPS coordinates
                        if row.get('Latitude') and row.get('Longitude'):
                            activity_assets[asset_id]['coordinates'].append({
                                'lat': float(row['Latitude']),
                                'lng': float(row['Longitude']),
                                'timestamp': row.get('EventDateTimex', ''),
                                'location_description': row.get('Locationx', '')
                            })
                        
                        # Extract project assignments from location data
                        location = row.get('Locationx', '')
                        if 'project' in location.lower() or any(char.isdigit() for char in location[:10]):
                            project_id = self._extract_project_id(location)
                            if project_id:
                                activity_assets[asset_id]['project_assignments'].append({
                                    'project_id': project_id,
                                    'location': location,
                                    'timestamp': row.get('EventDateTimex', '')
                                })
                        
                        # Track key events
                        activity_assets[asset_id]['key_events'].append({
                            'timestamp': row.get('EventDateTimex', ''),
                            'event': row.get('Reasonx', ''),
                            'speed': row.get('Speed', 0),
                            'heading': row.get('Headingx', ''),
                            'voltage': row.get('Voltagex', 0)
                        })
                        
        except Exception as e:
            logging.error(f"Activity detail processing error: {e}")
            
        return activity_assets
    
    def _process_service_history(self) -> Dict[str, Any]:
        """Process ServiceHistory CSV for maintenance data"""
        service_assets = {}
        
        try:
            # Check if ServiceHistory file exists
            with open('attached_assets/ServiceHistoryReport_1749454738568.csv', 'r') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    if row.get('Asset'):
                        asset_id = self._extract_asset_id(row['Asset'])
                        
                        if asset_id not in service_assets:
                            service_assets[asset_id] = {
                                'asset_id': asset_id,
                                'service_history': [],
                                'next_service_due': None,
                                'maintenance_costs': 0
                            }
                        
                        service_assets[asset_id]['service_history'].append({
                            'service_date': row.get('ServiceDate', ''),
                            'service_type': row.get('ServiceType', ''),
                            'description': row.get('Description', ''),
                            'cost': float(row.get('Cost', 0) or 0),
                            'technician': row.get('Technician', ''),
                            'next_due': row.get('NextDue', '')
                        })
                        
                        service_assets[asset_id]['maintenance_costs'] += float(row.get('Cost', 0) or 0)
                        
        except Exception as e:
            logging.error(f"Service history processing error: {e}")
            
        return service_assets
    
    def _consolidate_asset_data(self, daily_data, activity_data, service_data) -> List[Dict[str, Any]]:
        """Consolidate all asset data sources into comprehensive asset profiles"""
        consolidated = []
        
        # Get all unique asset IDs
        all_asset_ids = set()
        all_asset_ids.update(daily_data.keys())
        all_asset_ids.update(activity_data.keys())
        all_asset_ids.update(service_data.keys())
        
        for asset_id in all_asset_ids:
            asset_profile = {
                'asset_id': asset_id,
                'asset_label': '',
                'asset_type': 'Unknown',
                'asset_category': 'Unknown',
                'operator': '',
                'metrics': {
                    'total_distance': 0,
                    'total_hours': 0,
                    'odometer_reading': 0,
                    'hour_meter_reading': 0,
                    'utilization_rate': 0,
                    'idle_percentage': 0
                },
                'location_data': {
                    'current_location': '',
                    'coordinates': [],
                    'project_assignments': []
                },
                'maintenance': {
                    'service_history': [],
                    'next_service_due': None,
                    'total_maintenance_cost': 0,
                    'maintenance_frequency': 'Unknown'
                },
                'depreciation': self._calculate_depreciation(asset_id, daily_data.get(asset_id, {})),
                'lifecycle_costing': self._calculate_lifecycle_costs(asset_id, daily_data.get(asset_id, {}), service_data.get(asset_id, {}))
            }
            
            # Merge daily usage data
            if asset_id in daily_data:
                daily = daily_data[asset_id]
                asset_profile['asset_label'] = daily['asset_label']
                asset_profile['asset_type'] = daily['asset_type']
                asset_profile['asset_category'] = daily['asset_category']
                asset_profile['operator'] = daily['operator']
                asset_profile['metrics']['total_distance'] = daily['total_distance']
                asset_profile['metrics']['total_hours'] = daily['total_hours']
                
                # Calculate utilization rate
                if daily['daily_records']:
                    total_days = len(daily['daily_records'])
                    active_days = len([r for r in daily['daily_records'] if r['hours'] > 0])
                    asset_profile['metrics']['utilization_rate'] = (active_days / total_days) * 100 if total_days > 0 else 0
            
            # Merge activity data
            if asset_id in activity_data:
                activity = activity_data[asset_id]
                asset_profile['metrics']['odometer_reading'] = activity['odometer']
                asset_profile['metrics']['hour_meter_reading'] = activity['hour_meter']
                asset_profile['location_data']['coordinates'] = activity['coordinates']
                asset_profile['location_data']['project_assignments'] = activity['project_assignments']
                
                if activity['coordinates']:
                    latest_coord = activity['coordinates'][-1]
                    asset_profile['location_data']['current_location'] = latest_coord.get('location_description', '')
            
            # Merge service data
            if asset_id in service_data:
                service = service_data[asset_id]
                asset_profile['maintenance']['service_history'] = service['service_history']
                asset_profile['maintenance']['total_maintenance_cost'] = service['maintenance_costs']
                asset_profile['maintenance']['next_service_due'] = service['next_service_due']
            
            consolidated.append(asset_profile)
        
        return consolidated
    
    def _extract_asset_id(self, asset_label: str) -> str:
        """Extract asset ID from asset label"""
        if not asset_label:
            return 'unknown'
        
        # Handle formats like "#210003 - AMMAR I. ELHAMAD" or "EX-15 CAT 324D"
        if '#' in asset_label:
            return asset_label.split('#')[1].split(' ')[0]
        elif 'EX-' in asset_label:
            return asset_label.split(' ')[0]
        else:
            return asset_label.split(' ')[0]
    
    def _extract_operator_name(self, asset_label: str) -> str:
        """Extract operator name from asset label"""
        if ' - ' in asset_label:
            parts = asset_label.split(' - ')
            if len(parts) > 1:
                name_part = parts[1].split(' ')[0:3]  # First 3 words typically name
                return ' '.join(name_part)
        return 'Unknown'
    
    def _extract_project_id(self, location: str) -> str:
        """Extract project ID from location string"""
        import re
        # Look for patterns like "2024-030" or "2019-044"
        project_match = re.search(r'\d{4}-\d{3}', location)
        if project_match:
            return project_match.group()
        return None
    
    def _calculate_depreciation(self, asset_id: str, daily_data: Dict) -> Dict[str, Any]:
        """Calculate asset depreciation based on usage and age"""
        if not daily_data:
            return {'annual_depreciation': 0, 'current_value': 0, 'depreciation_method': 'unknown'}
        
        # Estimate based on asset type and usage
        asset_type = daily_data.get('asset_type', '').lower()
        total_hours = daily_data.get('total_hours', 0)
        
        if 'excavator' in asset_type:
            initial_value = 250000  # Estimated CAT 324D value
            depreciation_rate = 0.15  # 15% annual
        elif 'ford' in asset_type or 'jeep' in asset_type:
            initial_value = 50000   # Estimated truck value
            depreciation_rate = 0.20  # 20% annual
        else:
            initial_value = 100000  # Default equipment value
            depreciation_rate = 0.12  # 12% annual
        
        # Calculate depreciation based on hours (assuming 2000 hours/year)
        years_equivalent = total_hours / 2000 if total_hours > 0 else 1
        current_value = initial_value * ((1 - depreciation_rate) ** years_equivalent)
        annual_depreciation = initial_value * depreciation_rate
        
        return {
            'initial_value': initial_value,
            'current_value': round(current_value, 2),
            'annual_depreciation': round(annual_depreciation, 2),
            'depreciation_rate': depreciation_rate,
            'depreciation_method': 'declining_balance',
            'equivalent_years': round(years_equivalent, 2)
        }
    
    def _calculate_lifecycle_costs(self, asset_id: str, daily_data: Dict, service_data: Dict) -> Dict[str, Any]:
        """Calculate total lifecycle costs for asset"""
        depreciation = self._calculate_depreciation(asset_id, daily_data)
        maintenance_costs = service_data.get('maintenance_costs', 0) if service_data else 0
        
        # Estimate operating costs based on hours
        total_hours = daily_data.get('total_hours', 0) if daily_data else 0
        fuel_cost_per_hour = 25  # Estimated fuel cost per hour
        operating_costs = total_hours * fuel_cost_per_hour
        
        total_lifecycle_cost = (
            depreciation['initial_value'] + 
            maintenance_costs + 
            operating_costs
        )
        
        return {
            'total_lifecycle_cost': round(total_lifecycle_cost, 2),
            'depreciation_cost': depreciation['initial_value'] - depreciation['current_value'],
            'maintenance_cost': maintenance_costs,
            'operating_cost': round(operating_costs, 2),
            'cost_per_hour': round(total_lifecycle_cost / total_hours, 2) if total_hours > 0 else 0,
            'cost_breakdown': {
                'depreciation_percentage': round(((depreciation['initial_value'] - depreciation['current_value']) / total_lifecycle_cost) * 100, 1) if total_lifecycle_cost > 0 else 0,
                'maintenance_percentage': round((maintenance_costs / total_lifecycle_cost) * 100, 1) if total_lifecycle_cost > 0 else 0,
                'operating_percentage': round((operating_costs / total_lifecycle_cost) * 100, 1) if total_lifecycle_cost > 0 else 0
            }
        }

def get_asset_drill_down_data():
    """Get comprehensive asset drill-down data"""
    processor = AssetDrillDownProcessor()
    return processor.extract_asset_details()

def get_individual_asset(asset_id: str):
    """Get detailed information for a specific asset"""
    processor = AssetDrillDownProcessor()
    all_assets = processor.extract_asset_details()
    
    for asset in all_assets.get('assets', []):
        if asset['asset_id'] == asset_id:
            return asset
    
    return None