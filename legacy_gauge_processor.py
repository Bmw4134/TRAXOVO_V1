"""
Legacy GAUGE Formula Processor
Processes asset list exports with legacy formulas using pandas CSV conversion
"""

import pandas as pd
import json
import logging
import os
from typing import Dict, List, Any

class LegacyGaugeProcessor:
    """Process GAUGE data using legacy asset formulas"""
    
    def __init__(self):
        self.asset_mappings = {}
        self.legacy_formulas = {}
        self.processed_data = {}
        
    def process_asset_file(self, file_path: str):
        """Process asset file and extract legacy mappings"""
        try:
            # Convert Excel to CSV first for processing
            converted_file = self._convert_excel_to_csv(file_path)
            if converted_file:
                return self._process_csv_data(converted_file)
            return False
            
        except Exception as e:
            logging.error(f"Error processing asset file: {e}")
            return False
    
    def _convert_excel_to_csv(self, excel_path: str):
        """Convert Excel file to CSV for processing"""
        try:
            # Try to read Excel file with pandas
            df = pd.read_excel(excel_path, sheet_name=0)  # Read first sheet
            
            # Save as CSV
            csv_path = excel_path.replace('.xlsx', '_converted.csv')
            df.to_csv(csv_path, index=False)
            
            logging.info(f"Converted {excel_path} to {csv_path}")
            return csv_path
            
        except Exception as e:
            logging.error(f"Excel conversion error: {e}")
            return None
    
    def _process_csv_data(self, csv_path: str):
        """Process CSV data and extract asset mappings"""
        try:
            df = pd.read_csv(csv_path)
            
            # Extract asset mappings
            asset_mapping = {}
            legacy_mapping = {}
            
            for index, row in df.iterrows():
                # Look for asset ID and legacy ID columns
                asset_id = None
                legacy_id = None
                
                for col in df.columns:
                    col_lower = col.lower()
                    if 'asset' in col_lower and 'id' in col_lower:
                        asset_id = row[col]
                    elif any(term in col_lower for term in ['legacy', 'old', 'original']):
                        legacy_id = row[col]
                
                if asset_id and legacy_id:
                    asset_mapping[str(asset_id)] = str(legacy_id)
                    legacy_mapping[str(legacy_id)] = str(asset_id)
            
            self.asset_mappings = asset_mapping
            self.legacy_formulas = legacy_mapping
            
            logging.info(f"Processed {len(asset_mapping)} asset mappings")
            return True
            
        except Exception as e:
            logging.error(f"CSV processing error: {e}")
            return False
    
    def decode_gauge_reports(self, gauge_data: Dict) -> Dict:
        """Apply legacy mappings to decode GAUGE reports"""
        try:
            decoded_data = {}
            
            # Apply asset ID transformations
            if 'assets' in gauge_data:
                decoded_assets = []
                
                for asset in gauge_data['assets']:
                    decoded_asset = asset.copy()
                    
                    # Apply legacy mapping if available
                    asset_id = str(asset.get('asset_id', ''))
                    if asset_id in self.asset_mappings:
                        decoded_asset['legacy_id'] = self.asset_mappings[asset_id]
                        decoded_asset['mapping_applied'] = True
                    
                    decoded_assets.append(decoded_asset)
                
                decoded_data['assets'] = decoded_assets
                decoded_data['total_mapped'] = len([a for a in decoded_assets if a.get('mapping_applied')])
            
            # Process other data sections
            for key, value in gauge_data.items():
                if key != 'assets':
                    decoded_data[key] = value
            
            self.processed_data = decoded_data
            return decoded_data
            
        except Exception as e:
            logging.error(f"GAUGE decoding error: {e}")
            return gauge_data
    
    def get_enhanced_asset_data(self) -> Dict:
        """Get enhanced asset data with legacy mappings"""
        try:
            enhanced_data = {
                'asset_mappings': self.asset_mappings,
                'legacy_formulas': self.legacy_formulas,
                'processed_data': self.processed_data,
                'mapping_count': len(self.asset_mappings),
                'status': 'enhanced'
            }
            
            return enhanced_data
            
        except Exception as e:
            logging.error(f"Enhanced data error: {e}")
            return {}
    
    def save_processed_data(self, filename: str = 'legacy_gauge_mappings.json'):
        """Save processed legacy mappings"""
        try:
            data = {
                'asset_mappings': self.asset_mappings,
                'legacy_formulas': self.legacy_formulas,
                'processed_data': self.processed_data,
                'processing_summary': {
                    'total_mappings': len(self.asset_mappings),
                    'legacy_count': len(self.legacy_formulas),
                    'status': 'complete'
                }
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logging.info(f"Processed data saved to {filename}")
            return True
            
        except Exception as e:
            logging.error(f"Save error: {e}")
            return False

def process_legacy_gauge_file(file_path: str) -> Dict:
    """Main function to process legacy GAUGE file"""
    processor = LegacyGaugeProcessor()
    
    if processor.process_asset_file(file_path):
        processor.save_processed_data()
        return processor.get_enhanced_asset_data()
    else:
        return {'status': 'failed', 'error': 'Could not process file'}

# Auto-process the provided file
if __name__ == "__main__":
    file_path = 'attached_assets/asset list export - with legacy formulas_1749571821518.xlsx'
    if os.path.exists(file_path):
        result = process_legacy_gauge_file(file_path)
        print(f"Legacy GAUGE processing result: {result}")
    else:
        print(f"File not found: {file_path}")