"""
CSV Error Handler for TRAXOVO Fleet Data
Handles encoding issues, validation, and proper data processing
"""

import csv
import os
import json
import logging
from typing import Dict, List, Any, Optional
import chardet

class CSVErrorHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.processed_data = {}
        self.assets_dir = "attached_assets"
        
    def detect_encoding(self, file_path: str) -> str:
        """Detect file encoding using chardet"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # Read first 10KB
                result = chardet.detect(raw_data)
                return result.get('encoding', 'utf-8')
        except Exception as e:
            self.logger.warning(f"Encoding detection failed for {file_path}: {e}")
            return 'utf-8'
    
    def read_csv_with_fallback(self, file_path: str) -> List[Dict[str, Any]]:
        """Read CSV with multiple encoding fallbacks"""
        encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']
        
        # Try detected encoding first
        detected_encoding = self.detect_encoding(file_path)
        if detected_encoding and detected_encoding not in encodings:
            encodings.insert(0, detected_encoding)
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    reader = csv.DictReader(f)
                    data = list(reader)
                    if data:
                        self.logger.info(f"Successfully read {file_path} with {encoding} encoding")
                        return data
            except Exception as e:
                self.logger.debug(f"Failed to read {file_path} with {encoding}: {e}")
                continue
        
        self.logger.error(f"Could not read CSV file: {file_path}")
        return []
    
    def validate_asset_data(self, data: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
        """Validate and clean asset data"""
        if not data:
            return {'valid': False, 'error': 'No data found'}
        
        # Count valid rows
        valid_rows = [row for row in data if any(value.strip() for value in row.values() if value)]
        
        # Extract key fields based on filename patterns
        asset_count = 0
        if 'asset' in filename.lower():
            asset_count = len(valid_rows)
        elif 'activity' in filename.lower():
            asset_count = len(set(row.get('Asset', '') for row in valid_rows if row.get('Asset')))
        elif 'driving' in filename.lower():
            asset_count = len(set(row.get('Vehicle', '') for row in valid_rows if row.get('Vehicle')))
        else:
            asset_count = len(valid_rows)
        
        return {
            'valid': True,
            'total_rows': len(data),
            'valid_rows': len(valid_rows),
            'asset_count': asset_count,
            'columns': list(data[0].keys()) if data else [],
            'sample_data': valid_rows[:3] if valid_rows else []
        }
    
    def process_all_csv_files(self) -> Dict[str, Any]:
        """Process all CSV files with error handling"""
        results = {
            'total_files': 0,
            'processed_files': 0,
            'failed_files': [],
            'total_assets': 0,
            'file_details': {},
            'processing_errors': []
        }
        
        if not os.path.exists(self.assets_dir):
            return results
        
        csv_files = [f for f in os.listdir(self.assets_dir) if f.endswith('.csv')]
        results['total_files'] = len(csv_files)
        
        for filename in csv_files:
            file_path = os.path.join(self.assets_dir, filename)
            
            try:
                # Read CSV data
                data = self.read_csv_with_fallback(file_path)
                
                if data:
                    # Validate data
                    validation = self.validate_asset_data(data, filename)
                    
                    if validation['valid']:
                        results['processed_files'] += 1
                        results['total_assets'] += validation['asset_count']
                        results['file_details'][filename] = validation
                        
                        # Store processed data
                        self.processed_data[filename] = data
                    else:
                        results['failed_files'].append({
                            'filename': filename,
                            'error': validation.get('error', 'Validation failed')
                        })
                else:
                    results['failed_files'].append({
                        'filename': filename,
                        'error': 'Could not read file with any encoding'
                    })
                    
            except Exception as e:
                error_msg = f"Processing error: {str(e)}"
                results['processing_errors'].append({
                    'filename': filename,
                    'error': error_msg
                })
                self.logger.error(f"Error processing {filename}: {e}")
        
        return results
    
    def get_fleet_summary(self) -> Dict[str, Any]:
        """Generate fleet summary from processed data"""
        if not self.processed_data:
            self.process_all_csv_files()
        
        summary = {
            'total_assets': 0,
            'active_assets': 0,
            'asset_types': {},
            'maintenance_due': 0,
            'safety_events': 0,
            'fuel_efficiency': 0.0,
            'data_sources': list(self.processed_data.keys())
        }
        
        # Process each file type
        for filename, data in self.processed_data.items():
            if 'asset' in filename.lower():
                summary['total_assets'] += len(data)
                summary['active_assets'] += len([row for row in data if row.get('Status', '').lower() in ['active', 'in use']])
            
            elif 'maintenance' in filename.lower():
                summary['maintenance_due'] += len([row for row in data if row.get('Status', '').lower() in ['due', 'overdue']])
            
            elif 'safety' in filename.lower() or 'activity' in filename.lower():
                summary['safety_events'] += len(data)
        
        return summary
    
    def fix_csv_processing_errors(self) -> Dict[str, Any]:
        """Main method to fix CSV processing errors"""
        self.logger.info("Starting CSV error fixing process")
        
        # Process all files
        results = self.process_all_csv_files()
        
        # Calculate success rate
        success_rate = (results['processed_files'] / max(results['total_files'], 1)) * 100
        
        return {
            'success': True,
            'files_processed': results['processed_files'],
            'total_files': results['total_files'],
            'success_rate': round(success_rate, 1),
            'total_assets': results['total_assets'],
            'failed_files': results['failed_files'],
            'processing_errors': results['processing_errors'],
            'fleet_summary': self.get_fleet_summary()
        }

# Global instance for use in app.py
csv_handler = CSVErrorHandler()

def get_processed_csv_data():
    """Get processed CSV data for API endpoints"""
    return csv_handler.processed_data

def get_fleet_metrics():
    """Get real fleet metrics from CSV data"""
    return csv_handler.get_fleet_summary()