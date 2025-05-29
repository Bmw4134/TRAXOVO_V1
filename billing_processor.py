"""
Billing Intelligence Processor
Reads actual March and April billing Excel files to calculate real revenue
"""

import pandas as pd
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BillingProcessor:
    """Process actual billing data from Excel files"""
    
    def __init__(self):
        self.billing_files = [
            'RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm',
            'RAGLE EQ BILLINGS - MARCH 2025 (TO REVIEW 04.03.25).xlsm'
        ]
        self.current_month_data = None
        self.previous_month_data = None
        
    def load_billing_data(self):
        """Load billing data from Excel files"""
        try:
            # Load April 2025 data (current)
            april_file = 'RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm'
            if os.path.exists(april_file):
                self.current_month_data = self._process_billing_file(april_file, 'April 2025')
            
            # Load March 2025 data (previous)
            march_file = 'RAGLE EQ BILLINGS - MARCH 2025 (TO REVIEW 04.03.25).xlsm'
            if os.path.exists(march_file):
                self.previous_month_data = self._process_billing_file(march_file, 'March 2025')
                
            return True
        except Exception as e:
            logger.error(f"Error loading billing data: {e}")
            return False
    
    def _process_billing_file(self, file_path, month_name):
        """Process individual billing Excel file"""
        try:
            # Read Excel file with multiple sheets
            excel_file = pd.ExcelFile(file_path)
            
            billing_data = {
                'month': month_name,
                'total_revenue': 0,
                'equipment_count': 0,
                'divisions': {},
                'equipment_categories': {},
                'usage_rates': [],
                'daily_rates': []
            }
            
            # Process each sheet looking for billing data
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # Look for revenue columns - specifically "Allocation x Usage Rate Total"
                    revenue_cols = [col for col in df.columns if any(term in str(col).lower() 
                                  for term in ['allocation x usage rate total', 'total', 'revenue', 'billing', 'amount'])]
                    
                    if revenue_cols:
                        revenue_col = revenue_cols[0]  # Use first matching column
                        
                        # Process each row for equipment billing
                        for idx, row in df.iterrows():
                            try:
                                # Get revenue amount
                                revenue_value = row.get(revenue_col, 0)
                                if pd.notna(revenue_value) and isinstance(revenue_value, (int, float)) and revenue_value > 0:
                                    billing_data['total_revenue'] += revenue_value
                                    billing_data['equipment_count'] += 1
                                    
                                    # Get equipment details
                                    equipment_id = row.get('Equipment ID', row.get('Asset ID', f'EQ_{idx}'))
                                    division = row.get('Division', row.get('Div', 'Unknown'))
                                    category = row.get('Category', row.get('Type', 'Equipment'))
                                    usage_rate = row.get('Usage Rate', row.get('Utilization', 0))
                                    daily_rate = row.get('Daily Rate', row.get('Rate', 0))
                                    
                                    # Aggregate by division
                                    if division not in billing_data['divisions']:
                                        billing_data['divisions'][division] = {
                                            'revenue': 0,
                                            'equipment_count': 0
                                        }
                                    billing_data['divisions'][division]['revenue'] += revenue_value
                                    billing_data['divisions'][division]['equipment_count'] += 1
                                    
                                    # Aggregate by category
                                    if category not in billing_data['equipment_categories']:
                                        billing_data['equipment_categories'][category] = {
                                            'revenue': 0,
                                            'equipment_count': 0
                                        }
                                    billing_data['equipment_categories'][category]['revenue'] += revenue_value
                                    billing_data['equipment_categories'][category]['equipment_count'] += 1
                                    
                                    # Track usage rates and daily rates
                                    if usage_rate and usage_rate > 0:
                                        billing_data['usage_rates'].append(float(usage_rate))
                                    if daily_rate and daily_rate > 0:
                                        billing_data['daily_rates'].append(float(daily_rate))
                                        
                            except Exception as e:
                                continue  # Skip problematic rows
                                
                except Exception as e:
                    logger.warning(f"Could not process sheet {sheet_name}: {e}")
                    continue
            
            return billing_data
            
        except Exception as e:
            logger.error(f"Error processing billing file {file_path}: {e}")
            return None
    
    def get_monthly_revenue(self):
        """Get current month revenue"""
        if not self.current_month_data:
            self.load_billing_data()
        
        if self.current_month_data:
            return self.current_month_data['total_revenue']
        return 0
    
    def get_billable_assets(self):
        """Get count of billable assets"""
        if not self.current_month_data:
            self.load_billing_data()
        
        if self.current_month_data:
            return self.current_month_data['equipment_count']
        return 0
    
    def get_utilization_rate(self):
        """Calculate average utilization rate"""
        if not self.current_month_data:
            self.load_billing_data()
        
        if self.current_month_data and self.current_month_data['usage_rates']:
            return sum(self.current_month_data['usage_rates']) / len(self.current_month_data['usage_rates'])
        return 0
    
    def get_avg_daily_rate(self):
        """Calculate average daily rate"""
        if not self.current_month_data:
            self.load_billing_data()
        
        if self.current_month_data and self.current_month_data['daily_rates']:
            return sum(self.current_month_data['daily_rates']) / len(self.current_month_data['daily_rates'])
        return 0
    
    def get_division_performance(self):
        """Get performance breakdown by division"""
        if not self.current_month_data:
            self.load_billing_data()
        
        if self.current_month_data:
            return self.current_month_data['divisions']
        return {}
    
    def get_equipment_category_revenue(self):
        """Get revenue breakdown by equipment category"""
        if not self.current_month_data:
            self.load_billing_data()
        
        if self.current_month_data:
            return self.current_month_data['equipment_categories']
        return {}
    
    def get_month_over_month_comparison(self):
        """Compare current month to previous month"""
        if not self.current_month_data or not self.previous_month_data:
            self.load_billing_data()
        
        comparison = {
            'current_month': {
                'revenue': self.current_month_data['total_revenue'] if self.current_month_data else 0,
                'equipment_count': self.current_month_data['equipment_count'] if self.current_month_data else 0
            },
            'previous_month': {
                'revenue': self.previous_month_data['total_revenue'] if self.previous_month_data else 0,
                'equipment_count': self.previous_month_data['equipment_count'] if self.previous_month_data else 0
            }
        }
        
        # Calculate percentage changes
        if comparison['previous_month']['revenue'] > 0:
            comparison['revenue_change'] = ((comparison['current_month']['revenue'] - comparison['previous_month']['revenue']) / comparison['previous_month']['revenue']) * 100
        else:
            comparison['revenue_change'] = 0
            
        if comparison['previous_month']['equipment_count'] > 0:
            comparison['equipment_change'] = ((comparison['current_month']['equipment_count'] - comparison['previous_month']['equipment_count']) / comparison['previous_month']['equipment_count']) * 100
        else:
            comparison['equipment_change'] = 0
        
        return comparison

# Global billing processor instance
billing_processor = BillingProcessor()

def get_billing_processor():
    """Get the global billing processor instance"""
    return billing_processor