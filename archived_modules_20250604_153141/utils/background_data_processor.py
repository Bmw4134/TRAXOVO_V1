
import pandas as pd
import os
import json
from datetime import datetime
import threading
import logging

class BackgroundDataProcessor:
    """Handles heavy data processing in background to avoid startup timeouts"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.processing_lock = threading.Lock()
        
    def process_excel_files_async(self):
        """Process large Excel files in background thread"""
        def worker():
            try:
                with self.processing_lock:
                    self._process_revenue_data()
                    self._process_asset_data()
            except Exception as e:
                self.logger.error(f"Background processing error: {e}")
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    
    def _process_revenue_data(self):
        """Process revenue data from Excel files"""
        try:
            total_revenue = 0
            ragle_files = [
                'RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm',
                'RAGLE EQ BILLINGS - MARCH 2025 (TO REVIEW 04.03.25).xlsm'
            ]
            
            for file in ragle_files:
                if os.path.exists(file):
                    try:
                        # Use chunking for large files
                        excel_file = pd.ExcelFile(file)
                        for sheet_name in excel_file.sheet_names[:3]:  # Limit to first 3 sheets
                            try:
                                df = pd.read_excel(file, sheet_name=sheet_name, nrows=1000)  # Limit rows
                                if len(df) > 0:
                                    amount_cols = [col for col in df.columns if any(term in str(col).lower() for term in ['total', 'amount', 'revenue', 'billing'])]
                                    if amount_cols:
                                        for col in amount_cols:
                                            if pd.api.types.is_numeric_dtype(df[col]):
                                                revenue = df[col].sum()
                                                if revenue > 50000:
                                                    total_revenue += revenue
                                                    break
                            except Exception as e:
                                self.logger.warning(f"Sheet processing error: {e}")
                                continue
                    except Exception as e:
                        self.logger.error(f"File processing error for {file}: {e}")
            
            # Cache the results
            if total_revenue > 0:
                os.makedirs('data_cache', exist_ok=True)
                cache_data = {
                    'revenue': total_revenue,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'excel_processing'
                }
                with open('data_cache/revenue_data.json', 'w') as f:
                    json.dump(cache_data, f)
                    
        except Exception as e:
            self.logger.error(f"Revenue processing failed: {e}")
    
    def _process_asset_data(self):
        """Process asset data from Excel files"""
        try:
            unique_assets = set()
            equipment_files = [
                'attached_assets/EQ LIST ALL DETAILS SELECTED 052925.xlsx',
                'attached_assets/EQ CATEGORIES CONDENSED LIST 05.29.2025.xlsx'
            ]
            
            for file in equipment_files:
                if os.path.exists(file):
                    try:
                        # Process in chunks to avoid memory issues
                        df = pd.read_excel(file, engine='openpyxl', nrows=2000)
                        id_cols = [col for col in df.columns if any(term in str(col).lower() for term in ['equipment', 'asset', 'unit', 'id', 'number'])]
                        if id_cols:
                            for _, row in df.iterrows():
                                if pd.notna(row[id_cols[0]]):
                                    unique_assets.add(str(row[id_cols[0]]).strip())
                    except Exception as e:
                        self.logger.error(f"Asset file processing error for {file}: {e}")
            
            # Cache the results
            if len(unique_assets) > 100:
                os.makedirs('data_cache', exist_ok=True)
                cache_data = {
                    'count': len(unique_assets),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'excel_processing'
                }
                with open('data_cache/asset_count.json', 'w') as f:
                    json.dump(cache_data, f)
                    
        except Exception as e:
            self.logger.error(f"Asset processing failed: {e}")

# Global instance
background_processor = BackgroundDataProcessor()
