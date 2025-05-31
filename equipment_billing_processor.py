"""
TRAXOVO Equipment Billing Processor
Comprehensive billing system for monthly equipment charges using authentic GAUGE data
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

class EquipmentBillingProcessor:
    """Process GAUGE equipment data for monthly billing calculations"""
    
    def __init__(self):
        self.billing_rates = self.load_billing_rates()
        self.processed_data = {}
        self.billing_summary = {}
        
    def load_billing_rates(self) -> Dict[str, float]:
        """Load equipment billing rates by category"""
        # Standard equipment billing rates (per hour)
        return {
            'Excavator': 95.00,
            'Excavator (Med)': 85.00,
            'Excavator (Large)': 110.00,
            'Bulldozer': 120.00,
            'Wheel Loader': 75.00,
            'Compactor': 65.00,
            'Grader': 85.00,
            'Backhoe': 70.00,
            'Skid Steer': 45.00,
            'Dump Truck': 55.00,
            'Water Truck': 50.00,
            'Pickup Truck': 35.00,
            'Heavy Truck': 60.00,
            'Truck Tractor': 65.00,
            'Trailer': 25.00,
            'Flatbed Trailer': 30.00,
            'Generator': 15.00,
            'Compressor': 20.00,
            'Light Plant': 12.00,
            'Welder': 25.00,
            'Default': 50.00  # Fallback rate
        }
    
    def process_gauge_upload(self, file_path: str) -> Dict[str, Any]:
        """Process uploaded GAUGE equipment report"""
        try:
            # Read GAUGE data (supports CSV, Excel, JSON)
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                df = pd.DataFrame(data)
            else:
                raise ValueError("Unsupported file format")
            
            logging.info(f"Loaded GAUGE data: {len(df)} records")
            
            # Process billing calculations
            billing_results = self.calculate_monthly_billing(df)
            
            return {
                'status': 'success',
                'records_processed': len(df),
                'billing_summary': billing_results,
                'upload_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"GAUGE upload processing error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'upload_timestamp': datetime.now().isoformat()
            }
    
    def calculate_monthly_billing(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate monthly billing from GAUGE equipment data"""
        billing_summary = {
            'total_billable_hours': 0,
            'total_revenue': 0,
            'equipment_breakdown': {},
            'project_breakdown': {},
            'daily_summaries': {}
        }
        
        # Group by equipment and calculate hours
        for _, row in df.iterrows():
            asset_name = row.get('AssetName', 'Unknown')
            asset_category = row.get('AssetCategory', 'Default')
            hours = float(row.get('Engine1Hours', 0) or 0)
            project = row.get('CurrentJob', 'Unassigned')
            
            # Get billing rate for this equipment category
            rate = self.billing_rates.get(asset_category, self.billing_rates['Default'])
            
            # Calculate revenue for this equipment
            revenue = hours * rate
            
            # Update equipment breakdown
            if asset_category not in billing_summary['equipment_breakdown']:
                billing_summary['equipment_breakdown'][asset_category] = {
                    'total_hours': 0,
                    'total_revenue': 0,
                    'rate_per_hour': rate,
                    'asset_count': 0
                }
            
            billing_summary['equipment_breakdown'][asset_category]['total_hours'] += hours
            billing_summary['equipment_breakdown'][asset_category]['total_revenue'] += revenue
            billing_summary['equipment_breakdown'][asset_category]['asset_count'] += 1
            
            # Update project breakdown
            if project not in billing_summary['project_breakdown']:
                billing_summary['project_breakdown'][project] = {
                    'total_hours': 0,
                    'total_revenue': 0,
                    'equipment_used': set()
                }
            
            billing_summary['project_breakdown'][project]['total_hours'] += hours
            billing_summary['project_breakdown'][project]['total_revenue'] += revenue
            billing_summary['project_breakdown'][project]['equipment_used'].add(asset_name)
            
            # Update totals
            billing_summary['total_billable_hours'] += hours
            billing_summary['total_revenue'] += revenue
        
        # Convert sets to lists for JSON serialization
        for project in billing_summary['project_breakdown']:
            billing_summary['project_breakdown'][project]['equipment_used'] = \
                list(billing_summary['project_breakdown'][project]['equipment_used'])
        
        return billing_summary
    
    def generate_billing_report(self, billing_data: Dict[str, Any]) -> str:
        """Generate formatted billing report"""
        report = []
        report.append("=" * 60)
        report.append("TRAXOVO MONTHLY EQUIPMENT BILLING REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        report.append("BILLING SUMMARY:")
        report.append(f"Total Billable Hours: {billing_data['total_billable_hours']:,.2f}")
        report.append(f"Total Revenue: ${billing_data['total_revenue']:,.2f}")
        report.append("")
        
        # Equipment breakdown
        report.append("EQUIPMENT BREAKDOWN:")
        report.append("-" * 40)
        for category, data in billing_data['equipment_breakdown'].items():
            report.append(f"{category}:")
            report.append(f"  Assets: {data['asset_count']}")
            report.append(f"  Hours: {data['total_hours']:,.2f}")
            report.append(f"  Rate: ${data['rate_per_hour']:,.2f}/hour")
            report.append(f"  Revenue: ${data['total_revenue']:,.2f}")
            report.append("")
        
        # Project breakdown
        report.append("PROJECT BREAKDOWN:")
        report.append("-" * 40)
        for project, data in billing_data['project_breakdown'].items():
            report.append(f"{project}:")
            report.append(f"  Hours: {data['total_hours']:,.2f}")
            report.append(f"  Revenue: ${data['total_revenue']:,.2f}")
            report.append(f"  Equipment Count: {len(data['equipment_used'])}")
            report.append("")
        
        return "\n".join(report)
    
    def export_billing_excel(self, billing_data: Dict[str, Any], output_path: str):
        """Export billing data to Excel format"""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                'Metric': ['Total Billable Hours', 'Total Revenue', 'Report Date'],
                'Value': [
                    f"{billing_data['total_billable_hours']:,.2f}",
                    f"${billing_data['total_revenue']:,.2f}",
                    datetime.now().strftime('%Y-%m-%d')
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Equipment breakdown sheet
            equipment_data = []
            for category, data in billing_data['equipment_breakdown'].items():
                equipment_data.append({
                    'Equipment Category': category,
                    'Asset Count': data['asset_count'],
                    'Total Hours': data['total_hours'],
                    'Rate per Hour': data['rate_per_hour'],
                    'Total Revenue': data['total_revenue']
                })
            pd.DataFrame(equipment_data).to_excel(writer, sheet_name='Equipment', index=False)
            
            # Project breakdown sheet
            project_data = []
            for project, data in billing_data['project_breakdown'].items():
                project_data.append({
                    'Project': project,
                    'Total Hours': data['total_hours'],
                    'Total Revenue': data['total_revenue'],
                    'Equipment Count': len(data['equipment_used'])
                })
            pd.DataFrame(project_data).to_excel(writer, sheet_name='Projects', index=False)

def get_billing_processor():
    """Get billing processor instance"""
    return EquipmentBillingProcessor()