"""
Excel Data Processor for Foundation Equipment Reports
Processes authentic Excel files to extract equipment, usage, and driver mapping data
"""

import pandas as pd
import os
from typing import Dict, List, Any
import numpy as np

class ExcelDataProcessor:
    
    def __init__(self):
        self.data_dir = "attached_assets"
        
    def process_equipment_categories(self) -> Dict:
        """Process EQ CATEGORIES CONDENSED LIST to get equipment classifications"""
        try:
            file_path = os.path.join(self.data_dir, "EQ CATEGORIES CONDENSED LIST 05.29.2025.xlsx")
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Clean column names - remove hidden spaces and special characters
            df.columns = df.columns.str.strip().str.replace(r'[^\w\s]', '', regex=True)
            
            categories = {}
            for _, row in df.iterrows():
                if pd.notna(row.iloc[0]):  # First column usually contains equipment ID
                    eq_id = str(row.iloc[0]).strip()
                    category = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else "Unknown"
                    categories[eq_id] = category
                    
            return {
                'total_categories': len(set(categories.values())),
                'equipment_categories': categories,
                'category_counts': pd.Series(list(categories.values())).value_counts().to_dict()
            }
            
        except Exception as e:
            print(f"Error processing equipment categories: {e}")
            return {'total_categories': 0, 'equipment_categories': {}, 'category_counts': {}}
    
    def process_equipment_usage_detail(self) -> Dict:
        """Process EQUIPMENT USAGE DETAIL to get authentic usage patterns"""
        try:
            file_path = os.path.join(self.data_dir, "EQUIPMENT USAGE DETAIL 010125-053125.xlsx")
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Clean and standardize column names
            df.columns = df.columns.str.strip().str.replace(r'[^\w\s]', '', regex=True)
            
            usage_data = {
                'total_records': len(df),
                'date_range': '2025-01-01 to 2025-05-31',
                'equipment_usage': {},
                'driver_assignments': {},
                'utilization_stats': {}
            }
            
            # Process each row to extract equipment and driver data
            for _, row in df.iterrows():
                if pd.notna(row.iloc[0]):
                    eq_id = str(row.iloc[0]).strip()
                    
                    # Extract driver information (usually in second or third column)
                    driver = None
                    for col_idx in range(1, min(len(row), 4)):
                        if pd.notna(row.iloc[col_idx]) and isinstance(row.iloc[col_idx], str):
                            potential_driver = str(row.iloc[col_idx]).strip()
                            if len(potential_driver) > 2 and not potential_driver.isdigit():
                                driver = potential_driver
                                break
                    
                    if driver:
                        usage_data['driver_assignments'][eq_id] = driver
                        
                    # Extract usage hours or utilization data
                    for col_idx in range(len(row)):
                        if pd.notna(row.iloc[col_idx]) and isinstance(row.iloc[col_idx], (int, float)):
                            if row.iloc[col_idx] > 0 and row.iloc[col_idx] < 1000:  # Reasonable hour range
                                usage_data['equipment_usage'][eq_id] = float(row.iloc[col_idx])
                                break
                                
            return usage_data
            
        except Exception as e:
            print(f"Error processing equipment usage detail: {e}")
            return {'total_records': 0, 'equipment_usage': {}, 'driver_assignments': {}}
    
    def process_usage_vs_cost_analysis(self) -> Dict:
        """Process USAGE VS. COST ANALYSIS for financial efficiency metrics"""
        try:
            file_path = os.path.join(self.data_dir, "USAGE VS. COST ANALYSIS 010125-053125.xlsx")
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Clean column names
            df.columns = df.columns.str.strip().str.replace(r'[^\w\s]', '', regex=True)
            
            cost_analysis = {
                'total_analyzed': len(df),
                'equipment_costs': {},
                'cost_per_hour': {},
                'efficiency_ratings': {}
            }
            
            for _, row in df.iterrows():
                if pd.notna(row.iloc[0]):
                    eq_id = str(row.iloc[0]).strip()
                    
                    # Extract cost data (look for currency values)
                    for col_idx in range(len(row)):
                        if pd.notna(row.iloc[col_idx]) and isinstance(row.iloc[col_idx], (int, float)):
                            value = float(row.iloc[col_idx])
                            if value > 100:  # Likely a cost value
                                cost_analysis['equipment_costs'][eq_id] = value
                                break
                                
            return cost_analysis
            
        except Exception as e:
            print(f"Error processing usage vs cost analysis: {e}")
            return {'total_analyzed': 0, 'equipment_costs': {}, 'cost_per_hour': {}}
    
    def process_equipment_service_codes(self) -> Dict:
        """Process CURRENT EQ SERVICE-EXPENSE CODE LIST for maintenance tracking"""
        try:
            file_path = os.path.join(self.data_dir, "CURRENT EQ SERVICE-EXPENSE CODE LIST 052925.xlsx")
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Clean column names
            df.columns = df.columns.str.strip().str.replace(r'[^\w\s]', '', regex=True)
            
            service_data = {
                'total_service_codes': len(df),
                'equipment_service_map': {},
                'expense_codes': {},
                'maintenance_categories': {}
            }
            
            for _, row in df.iterrows():
                if pd.notna(row.iloc[0]):
                    eq_id = str(row.iloc[0]).strip()
                    
                    # Extract service codes and expense codes
                    service_code = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else None
                    expense_code = str(row.iloc[2]).strip() if len(row) > 2 and pd.notna(row.iloc[2]) else None
                    
                    if service_code:
                        service_data['equipment_service_map'][eq_id] = service_code
                    if expense_code:
                        service_data['expense_codes'][eq_id] = expense_code
                        
            return service_data
            
        except Exception as e:
            print(f"Error processing service codes: {e}")
            return {'total_service_codes': 0, 'equipment_service_map': {}, 'expense_codes': {}}
    
    def process_equipment_details(self) -> Dict:
        """Process EQ LIST ALL DETAILS SELECTED for comprehensive equipment data"""
        try:
            file_path = os.path.join(self.data_dir, "EQ LIST ALL DETAILS SELECTED 052925.xlsx")
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Clean column names
            df.columns = df.columns.str.strip().str.replace(r'[^\w\s]', '', regex=True)
            
            equipment_details = {
                'total_equipment': len(df),
                'equipment_registry': {},
                'asset_details': {},
                'operational_status': {}
            }
            
            for _, row in df.iterrows():
                if pd.notna(row.iloc[0]):
                    eq_id = str(row.iloc[0]).strip()
                    
                    # Build comprehensive equipment profile
                    equipment_profile = {
                        'id': eq_id,
                        'description': str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else "Equipment",
                        'status': 'Active',
                        'details': {}
                    }
                    
                    # Extract additional details from remaining columns
                    for col_idx in range(2, min(len(row), 10)):
                        if pd.notna(row.iloc[col_idx]):
                            equipment_profile['details'][f'field_{col_idx}'] = str(row.iloc[col_idx]).strip()
                    
                    equipment_details['equipment_registry'][eq_id] = equipment_profile
                    
            return equipment_details
            
        except Exception as e:
            print(f"Error processing equipment details: {e}")
            return {'total_equipment': 0, 'equipment_registry': {}, 'asset_details': {}}
    
    def create_comprehensive_asset_mapping(self) -> Dict:
        """Create comprehensive mapping of assets, drivers, and financial data"""
        
        categories = self.process_equipment_categories()
        usage_detail = self.process_equipment_usage_detail()
        cost_analysis = self.process_usage_vs_cost_analysis()
        service_codes = self.process_equipment_service_codes()
        equipment_details = self.process_equipment_details()
        
        # Merge all data sources
        comprehensive_mapping = {
            'summary': {
                'total_equipment': equipment_details['total_equipment'],
                'active_drivers': len(set(usage_detail['driver_assignments'].values())),
                'equipment_categories': categories['total_categories'],
                'service_codes': service_codes['total_service_codes'],
                'usage_records': usage_detail['total_records']
            },
            'asset_driver_mapping': usage_detail['driver_assignments'],
            'equipment_categories': categories['equipment_categories'],
            'equipment_costs': cost_analysis['equipment_costs'],
            'service_mapping': service_codes['equipment_service_map'],
            'equipment_registry': equipment_details['equipment_registry']
        }
        
        return comprehensive_mapping

# Global instance
_excel_processor = None

def get_excel_processor():
    """Get the Excel processor instance"""
    global _excel_processor
    if _excel_processor is None:
        _excel_processor = ExcelDataProcessor()
    return _excel_processor