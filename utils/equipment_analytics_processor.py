
"""
Equipment Analytics Processor for TRAXOVO
Processes uploaded equipment files for billing and utilization analysis
"""

import pandas as pd
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class EquipmentAnalyticsProcessor:
    def __init__(self):
        self.data_dir = 'attached_assets'
        self.equipment_master = None
        self.equipment_categories = None
        self.usage_detail = None
        self.cost_analysis = None
        self.service_codes = None
        
    def load_all_equipment_data(self):
        """Load all equipment-related files"""
        files_map = {
            'equipment_master': 'EQ LIST ALL DETAILS SELECTED 052925.xlsx',
            'equipment_categories': 'EQ CATEGORIES CONDENSED LIST 05.29.2025.xlsx',
            'usage_detail': 'EQUIPMENT USAGE DETAIL 010125-053125.xlsx',
            'cost_analysis': 'USAGE VS. COST ANALYSIS 010125-053125.xlsx',
            'service_codes': 'CURRENT EQ SERVICE-EXPENSE CODE LIST 052925.xlsx'
        }
        
        results = {}
        
        for data_type, filename in files_map.items():
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                try:
                    # Try multiple sheet reading strategies
                    df = self._load_excel_file(filepath)
                    if df is not None:
                        setattr(self, data_type, df)
                        results[data_type] = {
                            'loaded': True,
                            'rows': len(df),
                            'columns': list(df.columns)[:10]  # First 10 columns
                        }
                        logger.info(f"Loaded {filename}: {len(df)} rows")
                    else:
                        results[data_type] = {'loaded': False, 'error': 'Failed to parse Excel file'}
                except Exception as e:
                    logger.error(f"Error loading {filename}: {str(e)}")
                    results[data_type] = {'loaded': False, 'error': str(e)}
            else:
                results[data_type] = {'loaded': False, 'error': 'File not found'}
        
        return results
    
    def _load_excel_file(self, filepath):
        """Load Excel file with multiple fallback strategies"""
        try:
            # Strategy 1: Try loading first sheet
            df = pd.read_excel(filepath, sheet_name=0)
            if not df.empty:
                return self._clean_dataframe(df)
        except:
            pass
        
        try:
            # Strategy 2: Try loading all sheets and find the largest
            excel_file = pd.ExcelFile(filepath)
            largest_df = None
            max_rows = 0
            
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(filepath, sheet_name=sheet_name)
                    if len(df) > max_rows:
                        max_rows = len(df)
                        largest_df = df
                except:
                    continue
            
            if largest_df is not None:
                return self._clean_dataframe(largest_df)
        except:
            pass
        
        try:
            # Strategy 3: Try with different engines
            df = pd.read_excel(filepath, engine='openpyxl')
            return self._clean_dataframe(df)
        except:
            pass
        
        return None
    
    def _clean_dataframe(self, df):
        """Clean and standardize dataframe"""
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Clean column names
        df.columns = [str(col).strip().replace('\n', ' ').replace('\r', '') for col in df.columns]
        
        # Remove rows where all values are NaN or empty strings
        df = df[~df.apply(lambda row: row.astype(str).str.strip().eq('').all(), axis=1)]
        
        return df
    
    def generate_utilization_analysis(self):
        """Generate comprehensive utilization analysis"""
        if self.usage_detail is None or self.equipment_master is None:
            return {'error': 'Required data not loaded'}
        
        analysis = {
            'summary': {},
            'by_category': {},
            'by_equipment': [],
            'trends': {},
            'recommendations': []
        }
        
        # Summary metrics
        total_equipment = len(self.equipment_master) if self.equipment_master is not None else 0
        
        # Usage analysis
        if self.usage_detail is not None:
            usage_df = self.usage_detail
            
            # Find hour/usage columns
            hour_columns = [col for col in usage_df.columns if any(term in col.lower() for term in ['hour', 'hrs', 'usage', 'time'])]
            cost_columns = [col for col in usage_df.columns if any(term in col.lower() for term in ['cost', 'amount', 'revenue', 'billing'])]
            
            if hour_columns:
                hour_col = hour_columns[0]
                total_hours = usage_df[hour_col].sum() if pd.api.types.is_numeric_dtype(usage_df[hour_col]) else 0
                avg_hours_per_unit = total_hours / len(usage_df) if len(usage_df) > 0 else 0
                
                analysis['summary'].update({
                    'total_hours': total_hours,
                    'average_hours_per_unit': round(avg_hours_per_unit, 2),
                    'active_equipment_count': len(usage_df[usage_df[hour_col] > 0]) if pd.api.types.is_numeric_dtype(usage_df[hour_col]) else 0
                })
            
            if cost_columns:
                cost_col = cost_columns[0]
                total_cost = usage_df[cost_col].sum() if pd.api.types.is_numeric_dtype(usage_df[cost_col]) else 0
                
                analysis['summary'].update({
                    'total_cost': total_cost,
                    'average_cost_per_unit': round(total_cost / len(usage_df), 2) if len(usage_df) > 0 else 0
                })
        
        analysis['summary']['total_equipment'] = total_equipment
        analysis['summary']['utilization_rate'] = round((analysis['summary'].get('active_equipment_count', 0) / total_equipment * 100), 2) if total_equipment > 0 else 0
        
        return analysis
    
    def generate_cost_efficiency_report(self):
        """Generate cost efficiency analysis"""
        if self.cost_analysis is None:
            return {'error': 'Cost analysis data not loaded'}
        
        cost_df = self.cost_analysis
        
        # Find relevant columns
        equipment_cols = [col for col in cost_df.columns if any(term in col.lower() for term in ['equipment', 'asset', 'unit', 'id'])]
        usage_cols = [col for col in cost_df.columns if any(term in col.lower() for term in ['hour', 'usage', 'time'])]
        cost_cols = [col for col in cost_df.columns if any(term in col.lower() for term in ['cost', 'expense', 'amount'])]
        revenue_cols = [col for col in cost_df.columns if any(term in col.lower() for term in ['revenue', 'billing', 'income'])]
        
        report = {
            'efficiency_metrics': {},
            'top_performers': [],
            'underperformers': [],
            'category_analysis': {}
        }
        
        if equipment_cols and usage_cols and cost_cols:
            equipment_col = equipment_cols[0]
            usage_col = usage_cols[0]
            cost_col = cost_cols[0]
            
            # Calculate cost per hour
            cost_df['cost_per_hour'] = cost_df[cost_col] / cost_df[usage_col]
            cost_df['cost_per_hour'] = cost_df['cost_per_hour'].replace([float('inf'), -float('inf')], 0)
            
            # Efficiency metrics
            avg_cost_per_hour = cost_df['cost_per_hour'].mean()
            median_cost_per_hour = cost_df['cost_per_hour'].median()
            
            report['efficiency_metrics'] = {
                'average_cost_per_hour': round(avg_cost_per_hour, 2),
                'median_cost_per_hour': round(median_cost_per_hour, 2),
                'total_units_analyzed': len(cost_df)
            }
            
            # Top performers (lowest cost per hour with significant usage)
            significant_usage = cost_df[cost_df[usage_col] > cost_df[usage_col].quantile(0.25)]
            top_performers = significant_usage.nsmallest(10, 'cost_per_hour')
            
            report['top_performers'] = [
                {
                    'equipment': row[equipment_col],
                    'cost_per_hour': round(row['cost_per_hour'], 2),
                    'total_hours': row[usage_col],
                    'total_cost': row[cost_col]
                }
                for _, row in top_performers.iterrows()
            ]
            
            # Underperformers (high cost per hour)
            underperformers = cost_df.nlargest(10, 'cost_per_hour')
            
            report['underperformers'] = [
                {
                    'equipment': row[equipment_col],
                    'cost_per_hour': round(row['cost_per_hour'], 2),
                    'total_hours': row[usage_col],
                    'total_cost': row[cost_col]
                }
                for _, row in underperformers.iterrows()
            ]
        
        return report
    
    def generate_billing_optimization_recommendations(self):
        """Generate billing optimization recommendations"""
        recommendations = []
        
        # Load utilization analysis
        utilization = self.generate_utilization_analysis()
        cost_efficiency = self.generate_cost_efficiency_report()
        
        if 'summary' in utilization:
            util_rate = utilization['summary'].get('utilization_rate', 0)
            
            if util_rate < 70:
                recommendations.append({
                    'type': 'utilization',
                    'priority': 'high',
                    'title': 'Low Fleet Utilization Detected',
                    'description': f'Current utilization rate is {util_rate}%. Consider redistributing idle equipment or adjusting fleet size.',
                    'potential_savings': 'Up to 15% reduction in carrying costs'
                })
            
            if util_rate > 95:
                recommendations.append({
                    'type': 'capacity',
                    'priority': 'medium',
                    'title': 'High Utilization - Capacity Constraint Risk',
                    'description': f'Utilization rate is {util_rate}%. Consider expanding fleet or optimizing scheduling to prevent bottlenecks.',
                    'potential_impact': 'Prevent revenue loss from unmet demand'
                })
        
        if 'underperformers' in cost_efficiency and cost_efficiency['underperformers']:
            recommendations.append({
                'type': 'maintenance',
                'priority': 'high',
                'title': 'High-Cost Equipment Review Needed',
                'description': f'{len(cost_efficiency["underperformers"])} units showing high cost per hour. Review maintenance schedules and consider replacement.',
                'equipment_list': [item['equipment'] for item in cost_efficiency['underperformers'][:5]]
            })
        
        return recommendations
    
    def export_analytics_dashboard_data(self):
        """Export data for dashboard integration"""
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'utilization_analysis': self.generate_utilization_analysis(),
            'cost_efficiency': self.generate_cost_efficiency_report(),
            'recommendations': self.generate_billing_optimization_recommendations(),
            'data_sources': {
                'equipment_master_loaded': self.equipment_master is not None,
                'usage_detail_loaded': self.usage_detail is not None,
                'cost_analysis_loaded': self.cost_analysis is not None,
                'categories_loaded': self.equipment_categories is not None,
                'service_codes_loaded': self.service_codes is not None
            }
        }
        
        # Save to exports directory
        os.makedirs('exports/analytics', exist_ok=True)
        output_file = f'exports/analytics/equipment_analytics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(output_file, 'w') as f:
            json.dump(dashboard_data, f, indent=2, default=str)
        
        return dashboard_data, output_file

def get_equipment_analytics_processor():
    """Factory function to get processor instance"""
    processor = EquipmentAnalyticsProcessor()
    processor.load_all_equipment_data()
    return processor

if __name__ == "__main__":
    # Test the processor
    processor = EquipmentAnalyticsProcessor()
    load_results = processor.load_all_equipment_data()
    
    print("Load Results:")
    for data_type, result in load_results.items():
        print(f"  {data_type}: {result}")
    
    dashboard_data, output_file = processor.export_analytics_dashboard_data()
    print(f"\nDashboard data exported to: {output_file}")
