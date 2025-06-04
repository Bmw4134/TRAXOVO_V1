"""
Maintenance Analytics Module

This module processes:
- Work Order Detail Reports
- Heavy Equipment Expense Summaries
- Utilization data
- ROI/KPI calculations

It links individual work orders to assets, calculates maintenance KPIs,
and provides executive-level insights on equipment performance.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Data directories
DATA_DIR = 'data'
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed_files')
ANALYTICS_DIR = os.path.join(DATA_DIR, 'analytics')

# Ensure directories exist
for directory in [DATA_DIR, PROCESSED_DIR, ANALYTICS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

class WorkOrderProcessor:
    """
    Process Work Order Detail Reports and extract maintenance costs by asset
    """
    
    # Service code categories for classification
    SERVICE_CATEGORIES = {
        'ENGINE': ['ENGINE', 'ENGINE REPAIR', 'OIL CHANGE', 'FILTER'],
        'DRIVETRAIN': ['DRIVETRAIN', 'TRANSMISSION', 'DIFFERENTIAL', 'AXLE', 'CLUTCH'],
        'HYDRAULIC': ['HYDRAULIC', 'HYDRAULICS', 'HYDRO', 'CYLINDER'],
        'ELECTRICAL': ['ELECTRICAL', 'BATTERY', 'ALTERNATOR', 'STARTER'],
        'PREVENTATIVE': ['PM', 'PREVENTATIVE', 'PREVENT', 'INSPECTION'],
        'STRUCTURAL': ['STRUCTURAL', 'FRAME', 'WELD', 'BODY', 'CAB'],
        'WEAR_ITEMS': ['TIRE', 'TIRES', 'TRACK', 'TRACKS', 'UNDERCARRIAGE', 'CUTTING EDGE'],
        'SAFETY': ['SAFETY', 'LIGHT', 'LIGHTS', 'HORN', 'BACKUP ALARM', 'SEAT BELT']
    }
    
    def __init__(self, file_path):
        """
        Initialize the processor with file path
        
        Args:
            file_path (str): Path to the Work Order Detail Report Excel file
        """
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.processed_data = []
        self.asset_summary = {}
        self.meta_data = {
            'file_name': self.file_name,
            'processed_at': datetime.now().isoformat(),
            'period_start': None,
            'period_end': None,
            'total_cost': 0.0,
            'total_work_orders': 0,
            'total_assets': 0,
            'record_count': 0,
            'status': 'pending'
        }
    
    def process(self):
        """
        Process the Work Order Detail Report
        
        Returns:
            dict: Dictionary with processed data and metadata
        """
        logger.info(f"Processing Work Order Report: {self.file_path}")
        
        try:
            # Read the Excel file - try different sheets until we find data
            sheet_names = pd.ExcelFile(self.file_path).sheet_names
            df = None
            
            for sheet in sheet_names:
                try:
                    temp_df = pd.read_excel(self.file_path, sheet_name=sheet)
                    # Check if this sheet has WO data by looking for key columns
                    if any(col for col in temp_df.columns if 'WORK ORDER' in str(col).upper()):
                        df = temp_df
                        logger.info(f"Found Work Order data in sheet: {sheet}")
                        break
                except Exception as e:
                    logger.warning(f"Error reading sheet {sheet}: {e}")
            
            if df is None or df.empty:
                logger.warning(f"No usable data found in {self.file_path}")
                self.meta_data['status'] = 'error'
                self.meta_data['error'] = 'No usable data found'
                return {
                    'meta': self.meta_data,
                    'data': [],
                    'asset_summary': {}
                }
            
            # Normalize column names
            df.columns = [str(col).strip().upper() for col in df.columns]
            
            # Find key columns based on common patterns
            wo_num_col = next((col for col in df.columns if 'WORK ORDER' in col or 'WO' in col and 'NUMBER' in col), None)
            asset_id_col = next((col for col in df.columns if 'ASSET' in col and ('ID' in col or 'IDENT' in col)), None)
            asset_desc_col = next((col for col in df.columns if 'ASSET' in col and ('DESC' in col or 'NAME' in col)), None)
            service_desc_col = next((col for col in df.columns if 'SERV' in col or 'WORK' in col or 'REPAIR' in col), None)
            cost_col = next((col for col in df.columns if 'COST' in col or 'AMOUNT' in col or 'TOTAL' in col), None)
            date_col = next((col for col in df.columns if 'DATE' in col), None)
            
            # Ensure we have minimum required columns
            if not all([wo_num_col, asset_id_col, cost_col]):
                missing = []
                if not wo_num_col:
                    missing.append("Work Order Number")
                if not asset_id_col:
                    missing.append("Asset ID")
                if not cost_col:
                    missing.append("Cost/Amount")
                
                logger.warning(f"Missing required columns: {', '.join(missing)}")
                self.meta_data['status'] = 'error'
                self.meta_data['error'] = f"Missing required columns: {', '.join(missing)}"
                return {
                    'meta': self.meta_data,
                    'data': [],
                    'asset_summary': {}
                }
            
            # Extract date range if possible
            if date_col:
                try:
                    min_date = pd.to_datetime(df[date_col].min())
                    max_date = pd.to_datetime(df[date_col].max())
                    self.meta_data['period_start'] = min_date.strftime('%Y-%m-%d')
                    self.meta_data['period_end'] = max_date.strftime('%Y-%m-%d')
                except Exception as e:
                    logger.warning(f"Could not parse date range: {e}")
            
            # Process each row
            total_cost = 0.0
            asset_costs = defaultdict(float)
            asset_wo_counts = defaultdict(int)
            asset_categories = defaultdict(lambda: defaultdict(float))
            
            # Collect unique WO numbers
            unique_wo_numbers = set()
            
            for _, row in df.iterrows():
                try:
                    # Extract data
                    wo_num = str(row.get(wo_num_col, '')).strip()
                    asset_id = str(row.get(asset_id_col, '')).strip().upper()
                    asset_desc = str(row.get(asset_desc_col, '')).strip() if asset_desc_col else ''
                    service_desc = str(row.get(service_desc_col, '')).strip().upper() if service_desc_col else ''
                    
                    # Skip rows with missing key data
                    if not wo_num or not asset_id:
                        continue
                    
                    # Parse cost
                    cost = 0.0
                    cost_value = row.get(cost_col)
                    if pd.notna(cost_value):
                        # Handle string values like "$1,234.56"
                        if isinstance(cost_value, str):
                            cost_value = cost_value.replace('$', '').replace(',', '')
                        try:
                            cost = float(cost_value)
                        except (ValueError, TypeError):
                            cost = 0.0
                    
                    # Parse date
                    wo_date = None
                    if date_col and pd.notna(row.get(date_col)):
                        try:
                            wo_date = pd.to_datetime(row.get(date_col))
                            wo_date = wo_date.strftime('%Y-%m-%d')
                        except Exception:
                            wo_date = None
                    
                    # Categorize the service
                    service_category = self._categorize_service(service_desc)
                    
                    # Clean up asset ID (remove non-alphanumeric except dash)
                    # This helps match with GaugeSmart asset IDs
                    clean_asset_id = ''.join(c for c in asset_id if c.isalnum() or c == '-')
                    
                    # Create record
                    record = {
                        'work_order_number': wo_num,
                        'asset_id': clean_asset_id,
                        'asset_description': asset_desc,
                        'service_description': service_desc,
                        'service_category': service_category,
                        'cost': cost,
                        'date': wo_date
                    }
                    
                    # Add additional fields that might be present
                    for col in df.columns:
                        if col not in [wo_num_col, asset_id_col, asset_desc_col, service_desc_col, cost_col, date_col]:
                            field_name = col.lower().replace(' ', '_')
                            record[field_name] = row.get(col)
                    
                    # Add to processed data
                    self.processed_data.append(record)
                    
                    # Update totals
                    total_cost += cost
                    asset_costs[clean_asset_id] += cost
                    asset_categories[clean_asset_id][service_category] += cost
                    
                    # Count unique work orders per asset
                    if wo_num not in unique_wo_numbers:
                        unique_wo_numbers.add(wo_num)
                        asset_wo_counts[clean_asset_id] += 1
                    
                except Exception as e:
                    logger.warning(f"Error processing row: {e}")
            
            # Create asset summary
            for asset_id, cost in asset_costs.items():
                # Get category breakdown
                category_costs = asset_categories[asset_id]
                wo_count = asset_wo_counts[asset_id]
                
                self.asset_summary[asset_id] = {
                    'total_cost': cost,
                    'work_order_count': wo_count,
                    'avg_cost_per_wo': cost / wo_count if wo_count > 0 else 0.0,
                    'cost_by_category': dict(category_costs)
                }
            
            # Update metadata
            self.meta_data['total_cost'] = total_cost
            self.meta_data['total_work_orders'] = len(unique_wo_numbers)
            self.meta_data['total_assets'] = len(asset_costs)
            self.meta_data['record_count'] = len(self.processed_data)
            self.meta_data['status'] = 'success'
            
            # Save processed data
            self._save_processed_data()
            
            return {
                'meta': self.meta_data,
                'data': self.processed_data,
                'asset_summary': self.asset_summary
            }
            
        except Exception as e:
            logger.error(f"Error processing file {self.file_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.meta_data['status'] = 'error'
            self.meta_data['error'] = str(e)
            return {
                'meta': self.meta_data,
                'data': [],
                'asset_summary': {}
            }
    
    def _categorize_service(self, service_desc):
        """
        Categorize a service description into a predefined category
        
        Args:
            service_desc (str): Service description text
            
        Returns:
            str: Category name
        """
        if not service_desc:
            return 'UNCATEGORIZED'
        
        service_upper = service_desc.upper()
        
        for category, keywords in self.SERVICE_CATEGORIES.items():
            if any(keyword in service_upper for keyword in keywords):
                return category
        
        return 'UNCATEGORIZED'
    
    def _save_processed_data(self):
        """
        Save processed data to JSON files
        
        Returns:
            tuple: (data_file_path, summary_file_path)
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save detailed data
        data_file = os.path.join(PROCESSED_DIR, f"work_orders_{timestamp}.json")
        with open(data_file, 'w') as f:
            json.dump({
                'meta': self.meta_data,
                'data': self.processed_data
            }, f, indent=2)
        
        # Save asset summary
        summary_file = os.path.join(ANALYTICS_DIR, f"maintenance_summary_{timestamp}.json")
        with open(summary_file, 'w') as f:
            json.dump({
                'meta': self.meta_data,
                'asset_summary': self.asset_summary
            }, f, indent=2)
        
        logger.info(f"Saved work order data to {data_file}")
        logger.info(f"Saved maintenance summary to {summary_file}")
        
        return data_file, summary_file


class EquipmentROIAnalyzer:
    """
    Analyze equipment ROI by combining maintenance costs with utilization data
    """
    
    def __init__(self, maintenance_data=None, utilization_data=None, expense_data=None):
        """
        Initialize with maintenance and utilization data
        
        Args:
            maintenance_data (dict, optional): Output from WorkOrderProcessor
            utilization_data (dict, optional): Utilization data by asset
            expense_data (dict, optional): Heavy Equipment Expense data
        """
        self.maintenance_data = maintenance_data
        self.utilization_data = utilization_data
        self.expense_data = expense_data
        self.roi_data = {}
        self.meta_data = {
            'generated_at': datetime.now().isoformat(),
            'period': None,
            'total_assets': 0,
            'status': 'pending'
        }
    
    def analyze(self):
        """
        Perform ROI analysis by combining data sources
        
        Returns:
            dict: Analysis results
        """
        logger.info("Performing equipment ROI analysis")
        
        # Placeholder function for now - will be implemented in full version
        
        # Define analysis period
        if self.maintenance_data and self.maintenance_data.get('meta'):
            meta = self.maintenance_data.get('meta')
            period_start = meta.get('period_start')
            period_end = meta.get('period_end')
            if period_start and period_end:
                self.meta_data['period'] = f"{period_start} to {period_end}"
        
        # Create asset ROI records
        if self.maintenance_data and self.maintenance_data.get('asset_summary'):
            asset_summary = self.maintenance_data.get('asset_summary')
            
            for asset_id, maint_data in asset_summary.items():
                # Get utilization if available
                utilization = 0.0
                if self.utilization_data and asset_id in self.utilization_data:
                    utilization = self.utilization_data[asset_id].get('utilization', 0.0)
                
                # Get revenue/budget data if available
                revenue = 0.0
                budget = 0.0
                if self.expense_data and asset_id in self.expense_data:
                    revenue = self.expense_data[asset_id].get('revenue', 0.0)
                    budget = self.expense_data[asset_id].get('budget', 0.0)
                
                # Calculate ROI metrics
                total_cost = maint_data.get('total_cost', 0.0)
                
                # Calculate ROI if we have revenue and cost
                roi = 0.0
                if total_cost > 0 and revenue > 0:
                    roi = (revenue - total_cost) / total_cost * 100
                
                # Calculate budget variance
                budget_variance = 0.0
                if budget > 0:
                    budget_variance = (total_cost - budget) / budget * 100
                
                # Calculate efficiency score based on utilization and cost
                efficiency_score = 0.0
                if utilization > 0 and total_cost > 0:
                    # Higher utilization with lower cost = better efficiency
                    normalized_util = min(utilization, 1.0)  # Cap utilization at 100%
                    # Simple efficiency formula: score increases with utilization and decreases with cost
                    efficiency_score = normalized_util / (total_cost / 1000)  # Scale cost down
                
                # Create ROI record
                self.roi_data[asset_id] = {
                    'asset_id': asset_id,
                    'total_maintenance_cost': total_cost,
                    'work_order_count': maint_data.get('work_order_count', 0),
                    'utilization': utilization,
                    'revenue': revenue,
                    'budget': budget,
                    'roi': roi,
                    'budget_variance': budget_variance,
                    'efficiency_score': efficiency_score,
                    'maintenance_categories': maint_data.get('cost_by_category', {})
                }
            
            # Update meta data
            self.meta_data['total_assets'] = len(self.roi_data)
            self.meta_data['status'] = 'success'
        else:
            logger.warning("No maintenance data available for ROI analysis")
            self.meta_data['status'] = 'error'
            self.meta_data['error'] = 'No maintenance data available'
        
        # Save results
        self._save_analysis()
        
        return {
            'meta': self.meta_data,
            'roi_data': self.roi_data
        }
    
    def _save_analysis(self):
        """
        Save ROI analysis to JSON file
        
        Returns:
            str: Path to the saved file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(ANALYTICS_DIR, f"equipment_roi_{timestamp}.json")
        
        with open(output_file, 'w') as f:
            json.dump({
                'meta': self.meta_data,
                'roi_data': self.roi_data
            }, f, indent=2)
        
        logger.info(f"Saved ROI analysis to {output_file}")
        return output_file


def process_work_order_report(file_path):
    """
    Process a Work Order Detail Report
    
    Args:
        file_path (str): Path to the Work Order Detail Report Excel file
        
    Returns:
        dict: Processing results
    """
    processor = WorkOrderProcessor(file_path)
    return processor.process()


def analyze_equipment_roi(maintenance_data=None, utilization_data=None, expense_data=None):
    """
    Analyze equipment ROI
    
    Args:
        maintenance_data (dict, optional): Output from WorkOrderProcessor
        utilization_data (dict, optional): Utilization data by asset
        expense_data (dict, optional): Heavy Equipment Expense data
        
    Returns:
        dict: Analysis results
    """
    analyzer = EquipmentROIAnalyzer(maintenance_data, utilization_data, expense_data)
    return analyzer.analyze()


# Example usage
if __name__ == "__main__":
    # Test with a sample Work Order Report
    from pathlib import Path
    
    sample_files = [f for f in Path('attached_assets').glob('*WO*.xls*')]
    if sample_files:
        result = process_work_order_report(str(sample_files[0]))
        print(f"Processed {result['meta']['record_count']} records from {sample_files[0]}")
        
        # Perform ROI analysis with just maintenance data
        roi_result = analyze_equipment_roi(maintenance_data=result)
        print(f"Generated ROI analysis for {roi_result['meta']['total_assets']} assets")
    else:
        print("No sample Work Order Report found")