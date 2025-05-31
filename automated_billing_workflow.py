"""
TRAXOVO Automated Equipment Billing Workflow
Complete automation of Watson's equipment billing processes using authentic data sources
"""

import os
import json
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

class TRAXOVOBillingAutomation:
    """
    Complete automated billing workflow for equipment management
    Integrates GAUGE API, RAGLE Excel data, and all business processes
    """
    
    def __init__(self):
        self.gauge_api_key = os.environ.get('GAUGE_API_KEY')
        self.gauge_api_url = os.environ.get('GAUGE_API_URL')
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        
        # Data directories from our conversation history
        self.data_paths = {
            'ragle_billings': 'RAGLE EQ BILLINGS',
            'gauge_data': 'gauge_data',
            'attendance_data': 'attendance_data',
            'processed_documents': 'processed_documents',
            'exports': 'exports'
        }
        
        # Ensure directories exist
        for path in self.data_paths.values():
            os.makedirs(path, exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_authentic_gauge_data(self) -> Dict[str, Any]:
        """
        Fetch real-time equipment data from GAUGE API
        Returns actual asset statuses, not placeholder data
        """
        if not self.gauge_api_key or not self.gauge_api_url:
            self.logger.error("GAUGE API credentials not configured")
            return {'error': 'GAUGE API credentials required'}
        
        try:
            headers = {'Authorization': f'Bearer {self.gauge_api_key}'}
            
            # Get all assets with current status
            response = requests.get(f'{self.gauge_api_url}/assets', headers=headers)
            if response.status_code != 200:
                return {'error': f'GAUGE API error: {response.status_code}'}
            
            assets = response.json()
            
            # Process authentic asset data
            asset_analysis = {
                'total_assets': len(assets),
                'active_assets': sum(1 for a in assets if a.get('status', '').lower() == 'active'),
                'maintenance_assets': sum(1 for a in assets if a.get('status', '').lower() == 'maintenance'),
                'idle_assets': sum(1 for a in assets if a.get('status', '').lower() == 'idle'),
                'categories': len(set(a.get('category', '') for a in assets if a.get('category'))),
                'assets_by_category': {},
                'utilization_data': []
            }
            
            # Group by category for billing analysis
            for asset in assets:
                category = asset.get('category', 'Unknown')
                if category not in asset_analysis['assets_by_category']:
                    asset_analysis['assets_by_category'][category] = []
                asset_analysis['assets_by_category'][category].append(asset)
            
            return asset_analysis
            
        except Exception as e:
            self.logger.error(f"GAUGE API fetch error: {e}")
            return {'error': str(e)}

    def process_ragle_billing_data(self) -> Dict[str, Any]:
        """
        Process authentic RAGLE billing Excel files
        Extract revenue, costs, and equipment utilization
        """
        try:
            # Look for RAGLE Excel files in project directory
            ragle_files = [
                'RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm',
                'RAGLE EQ BILLINGS - MARCH 2025 (TO REVIEW 04.03.25).xlsm'
            ]
            
            billing_data = {
                'monthly_revenue': {},
                'equipment_costs': {},
                'project_billings': [],
                'ytd_total': 0
            }
            
            for file_name in ragle_files:
                if os.path.exists(file_name):
                    self.logger.info(f"Processing {file_name}")
                    
                    try:
                        # Read Excel file with multiple sheets
                        excel_data = pd.read_excel(file_name, sheet_name=None, engine='openpyxl')
                        
                        for sheet_name, df in excel_data.items():
                            # Extract billing information from each sheet
                            if 'total' in df.columns.str.lower():
                                total_col = df.columns[df.columns.str.lower().str.contains('total')][0]
                                monthly_total = df[total_col].sum()
                                
                                month_year = self._extract_month_from_filename(file_name)
                                billing_data['monthly_revenue'][month_year] = monthly_total
                                billing_data['ytd_total'] += monthly_total
                    
                    except Exception as e:
                        self.logger.error(f"Error processing {file_name}: {e}")
            
            return billing_data
            
        except Exception as e:
            self.logger.error(f"RAGLE data processing error: {e}")
            return {'error': str(e)}

    def _extract_month_from_filename(self, filename: str) -> str:
        """Extract month/year from RAGLE filename"""
        if 'APRIL 2025' in filename.upper():
            return 'April 2025'
        elif 'MARCH 2025' in filename.upper():
            return 'March 2025'
        return 'Unknown'

    def generate_automated_reports(self) -> Dict[str, Any]:
        """
        Generate comprehensive automated reports
        Combines GAUGE, RAGLE, and attendance data
        """
        # Get all authentic data sources
        gauge_data = self.get_authentic_gauge_data()
        ragle_data = self.process_ragle_billing_data()
        
        if 'error' in gauge_data:
            return {'error': 'Cannot generate reports without GAUGE API access'}
        
        # Generate executive summary
        executive_summary = {
            'report_date': datetime.now().isoformat(),
            'fleet_overview': {
                'total_equipment': gauge_data.get('total_assets', 0),
                'active_units': gauge_data.get('active_assets', 0),
                'utilization_rate': self._calculate_utilization_rate(gauge_data),
                'categories_managed': gauge_data.get('categories', 0)
            },
            'financial_performance': {
                'ytd_revenue': ragle_data.get('ytd_total', 0),
                'monthly_breakdown': ragle_data.get('monthly_revenue', {}),
                'revenue_per_asset': self._calculate_revenue_per_asset(gauge_data, ragle_data)
            },
            'operational_insights': self._generate_operational_insights(gauge_data, ragle_data),
            'recommendations': self._generate_recommendations(gauge_data, ragle_data)
        }
        
        return executive_summary

    def _calculate_utilization_rate(self, gauge_data: Dict) -> float:
        """Calculate fleet utilization rate from authentic data"""
        total = gauge_data.get('total_assets', 0)
        active = gauge_data.get('active_assets', 0)
        return (active / total * 100) if total > 0 else 0

    def _calculate_revenue_per_asset(self, gauge_data: Dict, ragle_data: Dict) -> float:
        """Calculate revenue per asset from authentic data"""
        total_assets = gauge_data.get('total_assets', 0)
        ytd_revenue = ragle_data.get('ytd_total', 0)
        return (ytd_revenue / total_assets) if total_assets > 0 else 0

    def _generate_operational_insights(self, gauge_data: Dict, ragle_data: Dict) -> List[str]:
        """Generate actionable operational insights"""
        insights = []
        
        # Asset utilization insights
        utilization = self._calculate_utilization_rate(gauge_data)
        if utilization < 80:
            insights.append(f"Fleet utilization at {utilization:.1f}% - opportunity for optimization")
        elif utilization > 95:
            insights.append(f"High utilization at {utilization:.1f}% - consider fleet expansion")
        
        # Maintenance insights
        maintenance_count = gauge_data.get('maintenance_assets', 0)
        if maintenance_count > 0:
            insights.append(f"{maintenance_count} assets in maintenance - monitor for patterns")
        
        # Revenue insights
        revenue_per_asset = self._calculate_revenue_per_asset(gauge_data, ragle_data)
        if revenue_per_asset > 0:
            insights.append(f"Revenue per asset: ${revenue_per_asset:,.2f} - track against industry benchmarks")
        
        return insights

    def _generate_recommendations(self, gauge_data: Dict, ragle_data: Dict) -> List[str]:
        """Generate strategic recommendations"""
        recommendations = []
        
        # Fleet optimization
        idle_assets = gauge_data.get('idle_assets', 0)
        if idle_assets > 5:
            recommendations.append(f"Optimize deployment of {idle_assets} idle assets")
        
        # Revenue optimization
        monthly_revenues = ragle_data.get('monthly_revenue', {})
        if len(monthly_revenues) >= 2:
            revenues = list(monthly_revenues.values())
            if len(revenues) >= 2 and revenues[-1] < revenues[-2]:
                recommendations.append("Investigate revenue decline trend")
        
        # Category analysis
        categories = gauge_data.get('assets_by_category', {})
        if categories:
            largest_category = max(categories.keys(), key=lambda k: len(categories[k]))
            recommendations.append(f"Focus optimization on {largest_category} category (largest fleet segment)")
        
        return recommendations

    def export_automated_report(self, report_data: Dict) -> str:
        """Export automated report to structured format"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"exports/automated_billing_report_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        self.logger.info(f"Automated report exported to {output_file}")
        return output_file

    def run_full_automation(self) -> Dict[str, Any]:
        """
        Execute complete automated billing workflow
        This is the main automation entry point
        """
        self.logger.info("Starting TRAXOVO automated billing workflow")
        
        try:
            # Step 1: Generate comprehensive report
            report = self.generate_automated_reports()
            
            if 'error' in report:
                return report
            
            # Step 2: Export report
            export_file = self.export_automated_report(report)
            
            # Step 3: Generate summary for Watson
            automation_summary = {
                'status': 'success',
                'execution_time': datetime.now().isoformat(),
                'report_file': export_file,
                'key_metrics': {
                    'total_assets': report['fleet_overview']['total_equipment'],
                    'active_assets': report['fleet_overview']['active_units'],
                    'utilization_rate': report['fleet_overview']['utilization_rate'],
                    'ytd_revenue': report['financial_performance']['ytd_revenue']
                },
                'insights_count': len(report['operational_insights']),
                'recommendations_count': len(report['recommendations']),
                'next_execution': (datetime.now() + timedelta(days=1)).isoformat()
            }
            
            self.logger.info("TRAXOVO automation completed successfully")
            return automation_summary
            
        except Exception as e:
            self.logger.error(f"Automation workflow error: {e}")
            return {'status': 'error', 'message': str(e)}

# Global automation instance
_automation_instance = None

def get_billing_automation():
    """Get the global billing automation instance"""
    global _automation_instance
    if _automation_instance is None:
        _automation_instance = TRAXOVOBillingAutomation()
    return _automation_instance