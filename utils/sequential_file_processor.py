
"""
Sequential File Processor for TRAXOVO
Handles Excel files sequentially with proper error handling and deduplication
"""

import os
import pandas as pd
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SequentialFileProcessor:
    def __init__(self):
        self.processed_files = {}
        self.data_cache = 'data_cache'
        os.makedirs(self.data_cache, exist_ok=True)
    
    def process_all_files(self):
        """Process all data files sequentially"""
        results = {
            'gauge_api': self.process_gauge_api(),
            'fleet_utilization': self.process_fleet_utilization_files(),
            'work_orders': self.process_work_order_files(),
            'equipment_history': self.process_equipment_history(),
            'billing_reports': self.process_billing_reports()
        }
        
        # Save comprehensive results
        with open(f'{self.data_cache}/sequential_processing_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return results
    
    def process_gauge_api(self):
        """Process Gauge API JSON file"""
        file_path = 'GAUGE API PULL 1045AM_05.15.2025.json'
        if not os.path.exists(file_path):
            return {'error': 'Gauge API file not found'}
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                # Deduplicate assets
                unique_assets = {}
                for asset in data:
                    asset_id = (asset.get('id') or asset.get('asset_id') or 
                               asset.get('name') or asset.get('AssetName'))
                    if asset_id:
                        unique_assets[str(asset_id)] = asset
                
                result = {
                    'total_records': len(data),
                    'unique_assets': len(unique_assets),
                    'asset_ids': list(unique_assets.keys()),
                    'processed_at': datetime.now().isoformat()
                }
                
                logger.info(f"Processed Gauge API: {len(unique_assets)} unique assets")
                return result
            
        except Exception as e:
            logger.error(f"Error processing Gauge API: {e}")
            return {'error': str(e)}
    
    def process_fleet_utilization_files(self):
        """Process Fleet Utilization Excel files"""
        files = [
            'attached_assets/FleetUtilization (2).xlsx',
            'attached_assets/FleetUtilization (3).xlsx'
        ]
        
        results = {}
        for file_path in files:
            if os.path.exists(file_path):
                try:
                    # Read second sheet (first is usually summary/fluff)
                    excel_file = pd.ExcelFile(file_path, engine='openpyxl')
                    sheet_names = excel_file.sheet_names
                    
                    if len(sheet_names) > 1:
                        df = pd.read_excel(file_path, sheet_name=1, engine='openpyxl')
                    else:
                        df = pd.read_excel(file_path, sheet_name=0, engine='openpyxl')
                    
                    # Extract key metrics
                    asset_columns = [col for col in df.columns if 
                                   any(keyword in str(col).lower() for keyword in 
                                       ['asset', 'equipment', 'unit', 'vehicle'])]
                    
                    utilization_columns = [col for col in df.columns if 
                                         any(keyword in str(col).lower() for keyword in 
                                             ['utilization', 'hours', 'runtime', 'usage'])]
                    
                    results[os.path.basename(file_path)] = {
                        'total_records': len(df),
                        'asset_columns': asset_columns,
                        'utilization_columns': utilization_columns,
                        'sheet_names': sheet_names,
                        'processed_at': datetime.now().isoformat()
                    }
                    
                    logger.info(f"Processed fleet utilization: {file_path}")
                    
                except Exception as e:
                    results[os.path.basename(file_path)] = {'error': str(e)}
                    logger.error(f"Error processing {file_path}: {e}")
        
        return results
    
    def process_work_order_files(self):
        """Process Work Order Detail Reports"""
        file_path = 'attached_assets/WORK ORDER DETAIL REPORT 01.01.2020-05.31.2025.xlsx'
        
        if not os.path.exists(file_path):
            return {'error': 'Work order file not found'}
        
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Extract work order metrics
            work_order_columns = [col for col in df.columns if 
                                any(keyword in str(col).lower() for keyword in 
                                    ['work', 'order', 'job', 'task', 'maintenance'])]
            
            asset_columns = [col for col in df.columns if 
                           any(keyword in str(col).lower() for keyword in 
                               ['asset', 'equipment', 'unit'])]
            
            return {
                'total_records': len(df),
                'work_order_columns': work_order_columns,
                'asset_columns': asset_columns,
                'date_range': '2020-2025',
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing work orders: {e}")
            return {'error': str(e)}
    
    def process_equipment_history(self):
        """Process Equipment Detail History Report"""
        file_path = 'attached_assets/Equipment Detail History Report_01.01.2020-05.31.2025.xlsx'
        
        if not os.path.exists(file_path):
            return {'error': 'Equipment history file not found'}
        
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Extract equipment history metrics
            equipment_columns = [col for col in df.columns if 
                               any(keyword in str(col).lower() for keyword in 
                                   ['equipment', 'asset', 'unit', 'machine'])]
            
            history_columns = [col for col in df.columns if 
                             any(keyword in str(col).lower() for keyword in 
                                 ['history', 'date', 'time', 'event', 'status'])]
            
            return {
                'total_records': len(df),
                'equipment_columns': equipment_columns,
                'history_columns': history_columns,
                'date_range': '2020-2025',
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing equipment history: {e}")
            return {'error': str(e)}
    
    def process_billing_reports(self):
        """Process Foundation billing reports"""
        files = [
            'RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm',
            'RAGLE EQ BILLINGS - MARCH 2025 (TO REVIEW 04.03.25).xlsm'
        ]
        
        results = {}
        total_revenue = 0
        unique_assets = set()
        
        for file_path in files:
            if os.path.exists(file_path):
                try:
                    df = pd.read_excel(file_path, engine='openpyxl')
                    
                    # Find revenue columns
                    revenue_columns = [col for col in df.columns if 
                                     any(keyword in str(col).lower() for keyword in 
                                         ['total', 'amount', 'cost', 'billing', 'revenue'])]
                    
                    # Find asset columns
                    asset_columns = [col for col in df.columns if 
                                   any(keyword in str(col).lower() for keyword in 
                                       ['asset', 'equipment', 'unit'])]
                    
                    # Calculate revenue
                    file_revenue = 0
                    if revenue_columns:
                        for col in revenue_columns:
                            try:
                                col_sum = pd.to_numeric(df[col], errors='coerce').sum()
                                if pd.notna(col_sum) and col_sum > file_revenue:
                                    file_revenue = col_sum
                            except:
                                continue
                    
                    # Extract unique assets
                    file_assets = set()
                    if asset_columns:
                        for col in asset_columns:
                            assets = df[col].dropna().astype(str).unique()
                            file_assets.update(assets)
                    
                    total_revenue += file_revenue
                    unique_assets.update(file_assets)
                    
                    results[os.path.basename(file_path)] = {
                        'total_records': len(df),
                        'revenue': file_revenue,
                        'unique_assets': len(file_assets),
                        'revenue_columns': revenue_columns,
                        'asset_columns': asset_columns,
                        'processed_at': datetime.now().isoformat()
                    }
                    
                    logger.info(f"Processed billing: {file_path} - ${file_revenue:,.2f}")
                    
                except Exception as e:
                    results[os.path.basename(file_path)] = {'error': str(e)}
                    logger.error(f"Error processing {file_path}: {e}")
        
        results['summary'] = {
            'total_revenue': total_revenue,
            'total_unique_assets': len(unique_assets),
            'processed_files': len([r for r in results.values() if 'error' not in r])
        }
        
        return results

# Global processor instance
sequential_processor = SequentialFileProcessor()
