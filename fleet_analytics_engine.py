"""
TRAXOVO Fleet Analytics Intelligence Engine
Advanced analytics for equipment performance, utilization, and operational insights
"""

import os
import json
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from collections import defaultdict

class FleetAnalyticsEngine:
    """
    Advanced fleet analytics providing actionable insights from authentic GAUGE data
    Real-time equipment performance, utilization patterns, and predictive maintenance
    """
    
    def __init__(self):
        self.gauge_api_key = os.environ.get('GAUGE_API_KEY')
        self.gauge_api_url = os.environ.get('GAUGE_API_URL')
        
        # Analytics categories
        self.analytics_modules = {
            'utilization_analysis': 'Equipment utilization patterns and optimization',
            'performance_tracking': 'Real-time performance metrics and trends',
            'maintenance_intelligence': 'Predictive maintenance and cost analysis',
            'location_analytics': 'Job site efficiency and equipment deployment',
            'driver_productivity': 'Operator performance and training insights',
            'cost_optimization': 'Operating costs and revenue optimization'
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def fetch_comprehensive_fleet_data(self) -> Dict[str, Any]:
        """
        Fetch complete fleet data from GAUGE API for analytics processing
        """
        if not self.gauge_api_key or not self.gauge_api_url:
            return {'error': 'GAUGE API credentials required for fleet analytics'}
        
        try:
            headers = {'Authorization': f'Bearer {self.gauge_api_key}'}
            
            # Fetch multiple data streams
            endpoints = {
                'assets': f'{self.gauge_api_url}/assets',
                'telemetry': f'{self.gauge_api_url}/telemetry',
                'maintenance': f'{self.gauge_api_url}/maintenance',
                'locations': f'{self.gauge_api_url}/locations',
                'operators': f'{self.gauge_api_url}/operators'
            }
            
            fleet_data = {}
            
            for data_type, url in endpoints.items():
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    fleet_data[data_type] = response.json()
                    self.logger.info(f"Successfully fetched {data_type} data")
                else:
                    self.logger.warning(f"Failed to fetch {data_type}: {response.status_code}")
                    fleet_data[data_type] = []
            
            return fleet_data
            
        except Exception as e:
            self.logger.error(f"Fleet data fetch error: {e}")
            return {'error': str(e)}

    def analyze_equipment_utilization(self, fleet_data: Dict) -> Dict[str, Any]:
        """
        Analyze equipment utilization patterns and identify optimization opportunities
        """
        assets = fleet_data.get('assets', [])
        telemetry = fleet_data.get('telemetry', [])
        
        utilization_analysis = {
            'overall_metrics': {},
            'by_category': {},
            'by_asset': {},
            'optimization_opportunities': [],
            'utilization_trends': {}
        }
        
        # Calculate overall utilization
        total_assets = len(assets)
        active_assets = sum(1 for asset in assets if asset.get('status', '').lower() == 'active')
        
        utilization_analysis['overall_metrics'] = {
            'total_fleet_size': total_assets,
            'active_equipment': active_assets,
            'utilization_rate': (active_assets / total_assets * 100) if total_assets > 0 else 0,
            'idle_equipment': total_assets - active_assets
        }
        
        # Analyze by category
        category_stats = defaultdict(lambda: {'total': 0, 'active': 0, 'hours': 0})
        
        for asset in assets:
            category = asset.get('category', 'Unknown')
            category_stats[category]['total'] += 1
            if asset.get('status', '').lower() == 'active':
                category_stats[category]['active'] += 1
                
            # Calculate operating hours from telemetry
            asset_telemetry = [t for t in telemetry if t.get('asset_id') == asset.get('id')]
            category_stats[category]['hours'] += self._calculate_operating_hours(asset_telemetry)
        
        for category, stats in category_stats.items():
            utilization_analysis['by_category'][category] = {
                'total_assets': stats['total'],
                'active_assets': stats['active'],
                'utilization_rate': (stats['active'] / stats['total'] * 100) if stats['total'] > 0 else 0,
                'total_operating_hours': stats['hours'],
                'avg_hours_per_asset': stats['hours'] / stats['total'] if stats['total'] > 0 else 0
            }
        
        # Identify optimization opportunities
        for category, data in utilization_analysis['by_category'].items():
            if data['utilization_rate'] < 70:
                utilization_analysis['optimization_opportunities'].append({
                    'category': category,
                    'issue': 'Low utilization rate',
                    'current_rate': data['utilization_rate'],
                    'recommendation': f'Reassign or consolidate {category} equipment',
                    'potential_savings': self._estimate_cost_savings(data)
                })
            elif data['utilization_rate'] > 95:
                utilization_analysis['optimization_opportunities'].append({
                    'category': category,
                    'issue': 'Over-utilization',
                    'current_rate': data['utilization_rate'],
                    'recommendation': f'Consider expanding {category} fleet',
                    'potential_revenue': self._estimate_revenue_opportunity(data)
                })
        
        return utilization_analysis

    def analyze_performance_metrics(self, fleet_data: Dict) -> Dict[str, Any]:
        """
        Real-time performance analysis and trend identification
        """
        assets = fleet_data.get('assets', [])
        telemetry = fleet_data.get('telemetry', [])
        
        performance_analysis = {
            'fleet_performance': {},
            'individual_assets': {},
            'performance_trends': {},
            'alerts': []
        }
        
        # Fleet-wide performance metrics
        total_runtime = sum(self._calculate_operating_hours([t for t in telemetry if t.get('asset_id') == asset.get('id')]) for asset in assets)
        total_fuel_consumed = sum(t.get('fuel_consumed', 0) for t in telemetry)
        
        performance_analysis['fleet_performance'] = {
            'total_operating_hours': total_runtime,
            'average_efficiency': self._calculate_fleet_efficiency(telemetry),
            'fuel_efficiency': total_fuel_consumed / total_runtime if total_runtime > 0 else 0,
            'productivity_score': self._calculate_productivity_score(fleet_data)
        }
        
        # Individual asset performance
        for asset in assets:
            asset_id = asset.get('id')
            asset_telemetry = [t for t in telemetry if t.get('asset_id') == asset_id]
            
            performance_analysis['individual_assets'][asset_id] = {
                'asset_name': asset.get('name', 'Unknown'),
                'category': asset.get('category', 'Unknown'),
                'operating_hours': self._calculate_operating_hours(asset_telemetry),
                'efficiency_rating': self._calculate_asset_efficiency(asset_telemetry),
                'maintenance_score': self._calculate_maintenance_score(asset, fleet_data.get('maintenance', [])),
                'performance_trend': self._analyze_performance_trend(asset_telemetry)
            }
            
            # Generate alerts for performance issues
            efficiency = self._calculate_asset_efficiency(asset_telemetry)
            if efficiency < 70:
                performance_analysis['alerts'].append({
                    'asset_id': asset_id,
                    'asset_name': asset.get('name'),
                    'type': 'performance',
                    'severity': 'high' if efficiency < 50 else 'medium',
                    'message': f'Low efficiency: {efficiency}%',
                    'recommendation': 'Schedule maintenance inspection'
                })
        
        return performance_analysis

    def analyze_maintenance_intelligence(self, fleet_data: Dict) -> Dict[str, Any]:
        """
        Predictive maintenance analysis and cost optimization
        """
        assets = fleet_data.get('assets', [])
        maintenance_records = fleet_data.get('maintenance', [])
        
        maintenance_analysis = {
            'predictive_insights': {},
            'cost_analysis': {},
            'maintenance_schedule': {},
            'recommendations': []
        }
        
        # Predictive maintenance insights
        for asset in assets:
            asset_id = asset.get('id')
            asset_maintenance = [m for m in maintenance_records if m.get('asset_id') == asset_id]
            
            maintenance_analysis['predictive_insights'][asset_id] = {
                'next_service_due': self._predict_next_service(asset, asset_maintenance),
                'failure_risk': self._calculate_failure_risk(asset, asset_maintenance),
                'recommended_actions': self._generate_maintenance_recommendations(asset, asset_maintenance)
            }
        
        # Cost analysis
        total_maintenance_cost = sum(m.get('cost', 0) for m in maintenance_records)
        maintenance_analysis['cost_analysis'] = {
            'total_annual_cost': total_maintenance_cost,
            'cost_per_asset': total_maintenance_cost / len(assets) if assets else 0,
            'cost_by_category': self._analyze_maintenance_costs_by_category(assets, maintenance_records),
            'cost_trends': self._analyze_cost_trends(maintenance_records)
        }
        
        return maintenance_analysis

    def generate_location_analytics(self, fleet_data: Dict) -> Dict[str, Any]:
        """
        Job site efficiency and equipment deployment analysis
        """
        locations = fleet_data.get('locations', [])
        assets = fleet_data.get('assets', [])
        
        location_analysis = {
            'site_efficiency': {},
            'deployment_optimization': {},
            'travel_analysis': {},
            'recommendations': []
        }
        
        # Analyze efficiency by job site
        for location in locations:
            site_id = location.get('id')
            site_assets = [a for a in assets if a.get('current_location') == site_id]
            
            location_analysis['site_efficiency'][site_id] = {
                'site_name': location.get('name'),
                'equipment_count': len(site_assets),
                'utilization_rate': self._calculate_site_utilization(site_assets),
                'productivity_score': self._calculate_site_productivity(site_assets, location),
                'optimization_potential': self._identify_site_optimization(site_assets, location)
            }
        
        return location_analysis

    def _calculate_operating_hours(self, telemetry_data: List) -> float:
        """Calculate total operating hours from telemetry data"""
        if not telemetry_data:
            return 0.0
        
        total_hours = 0.0
        for record in telemetry_data:
            # Sum engine hours or runtime data
            hours = record.get('engine_hours', record.get('runtime_hours', 0))
            total_hours += float(hours)
        
        return total_hours

    def _calculate_fleet_efficiency(self, telemetry_data: List) -> float:
        """Calculate overall fleet efficiency score"""
        if not telemetry_data:
            return 0.0
        
        efficiency_scores = []
        for record in telemetry_data:
            fuel_efficiency = record.get('fuel_efficiency', 0)
            productivity = record.get('productivity_score', 0)
            if fuel_efficiency > 0 and productivity > 0:
                efficiency_scores.append((fuel_efficiency + productivity) / 2)
        
        return sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 0.0

    def _calculate_productivity_score(self, fleet_data: Dict) -> float:
        """Calculate overall fleet productivity score"""
        # Complex calculation based on multiple factors
        utilization = self._calculate_overall_utilization(fleet_data)
        efficiency = self._calculate_fleet_efficiency(fleet_data.get('telemetry', []))
        
        return (utilization + efficiency) / 2

    def _calculate_overall_utilization(self, fleet_data: Dict) -> float:
        """Calculate overall fleet utilization percentage"""
        assets = fleet_data.get('assets', [])
        if not assets:
            return 0.0
        
        active_count = sum(1 for asset in assets if asset.get('status', '').lower() == 'active')
        return (active_count / len(assets)) * 100

    def export_analytics_report(self, analytics_data: Dict) -> str:
        """Export comprehensive analytics report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"reports/fleet_analytics_report_{timestamp}.json"
        
        os.makedirs('reports', exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(analytics_data, f, indent=2, default=str)
        
        self.logger.info(f"Analytics report exported to {output_file}")
        return output_file

    def run_comprehensive_analytics(self) -> Dict[str, Any]:
        """
        Execute complete fleet analytics workflow
        """
        self.logger.info("Starting comprehensive fleet analytics")
        
        try:
            # Fetch authentic fleet data
            fleet_data = self.fetch_comprehensive_fleet_data()
            
            if 'error' in fleet_data:
                return fleet_data
            
            # Run all analytics modules
            analytics_results = {
                'execution_time': datetime.now().isoformat(),
                'data_sources': list(fleet_data.keys()),
                'utilization_analysis': self.analyze_equipment_utilization(fleet_data),
                'performance_analysis': self.analyze_performance_metrics(fleet_data),
                'maintenance_intelligence': self.analyze_maintenance_intelligence(fleet_data),
                'location_analytics': self.generate_location_analytics(fleet_data)
            }
            
            # Export comprehensive report
            report_file = self.export_analytics_report(analytics_results)
            
            # Generate executive summary
            summary = {
                'status': 'success',
                'report_file': report_file,
                'key_insights': self._generate_executive_insights(analytics_results),
                'total_assets_analyzed': len(fleet_data.get('assets', [])),
                'analytics_modules_executed': len(self.analytics_modules)
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Fleet analytics error: {e}")
            return {'status': 'error', 'message': str(e)}

    def _generate_executive_insights(self, analytics_data: Dict) -> List[str]:
        """Generate executive-level insights from analytics"""
        insights = []
        
        # Utilization insights
        utilization = analytics_data.get('utilization_analysis', {})
        overall_rate = utilization.get('overall_metrics', {}).get('utilization_rate', 0)
        insights.append(f"Fleet utilization rate: {overall_rate:.1f}%")
        
        # Performance insights
        performance = analytics_data.get('performance_analysis', {})
        alerts = performance.get('alerts', [])
        if alerts:
            insights.append(f"{len(alerts)} performance alerts requiring attention")
        
        # Optimization opportunities
        opportunities = utilization.get('optimization_opportunities', [])
        if opportunities:
            insights.append(f"{len(opportunities)} optimization opportunities identified")
        
        return insights

# Global analytics instance
_analytics_instance = None

def get_fleet_analytics():
    """Get the global fleet analytics engine instance"""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = FleetAnalyticsEngine()
    return _analytics_instance