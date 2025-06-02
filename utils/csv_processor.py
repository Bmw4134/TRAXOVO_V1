"""
TRAXOVO CSV Processing Utilities
Complete CSV parsing for GAUGE reports, attendance data, and billing files
"""
import pandas as pd
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class TRAXOVOCSVProcessor:
    """Enterprise CSV processor for all TRAXOVO data sources"""
    
    def __init__(self):
        self.required_columns = {
            'driving_history': ['VIN', 'Date', 'Driver', 'Hours', 'Location'],
            'assets_time_on_site': ['Asset', 'JobSite', 'TimeIn', 'TimeOut', 'TotalHours'],
            'activity_detail': ['DateTime', 'Asset', 'Activity', 'Driver', 'Location'],
            'ragle_billing': ['JobNumber', 'Equipment', 'Hours', 'Rate', 'Amount']
        }
    
    def process_csv_with_fallback(self, file_path: str, data_type: str = 'auto') -> Dict[str, Any]:
        """Process CSV with intelligent fallback and error recovery"""
        try:
            # Determine file type
            if data_type == 'auto':
                data_type = self._detect_file_type(file_path)
            
            # Read file with multiple encodings
            df = self._read_file_safe(file_path)
            
            # Validate and normalize
            df = self.validate_required_columns(df, data_type)
            df = self.normalize_field_counts(df)
            
            # Process by type
            if data_type == 'driving_history':
                return self._process_driving_history(df, file_path)
            elif data_type == 'assets_time_on_site':
                return self._process_assets_time_on_site(df, file_path)
            elif data_type == 'activity_detail':
                return self._process_activity_detail(df, file_path)
            elif data_type == 'ragle_billing':
                return self._process_ragle_billing(df, file_path)
            else:
                return self._process_generic(df, file_path)
                
        except Exception as e:
            logger.error(f"CSV processing error for {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path,
                'records_processed': 0,
                'data': []
            }
    
    def _read_file_safe(self, file_path: str) -> pd.DataFrame:
        """Read file with multiple encoding attempts"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                    return pd.read_excel(file_path, engine='openpyxl')
                else:
                    return pd.read_csv(file_path, encoding=encoding)
            except Exception as e:
                continue
        
        raise Exception(f"Could not read file {file_path} with any encoding")
    
    def _detect_file_type(self, file_path: str) -> str:
        """Detect file type from filename patterns"""
        filename = os.path.basename(file_path).lower()
        
        if 'driving' in filename or 'driver' in filename:
            return 'driving_history'
        elif 'time on site' in filename or 'timesite' in filename:
            return 'assets_time_on_site'
        elif 'activity' in filename:
            return 'activity_detail'
        elif 'ragle' in filename or 'billing' in filename:
            return 'ragle_billing'
        else:
            return 'generic'
    
    def validate_required_columns(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """Validate and map columns to required structure"""
        if data_type not in self.required_columns:
            return df
        
        required = self.required_columns[data_type]
        df_columns = df.columns.tolist()
        
        # Map common column variations
        column_mappings = {
            'VIN': ['vin', 'vehicle_id', 'asset_id', 'unit_id'],
            'Date': ['date', 'datetime', 'timestamp', 'event_date'],
            'Driver': ['driver', 'operator', 'employee', 'person'],
            'Hours': ['hours', 'total_hours', 'time', 'duration'],
            'Location': ['location', 'job_site', 'site', 'address'],
            'Asset': ['asset', 'equipment', 'unit', 'vehicle'],
            'JobSite': ['job_site', 'jobsite', 'site', 'location'],
            'TimeIn': ['time_in', 'start_time', 'arrival'],
            'TimeOut': ['time_out', 'end_time', 'departure'],
            'TotalHours': ['total_hours', 'hours', 'duration'],
            'Activity': ['activity', 'event', 'action', 'status'],
            'JobNumber': ['job_number', 'job', 'project', 'work_order'],
            'Equipment': ['equipment', 'asset', 'unit', 'vehicle'],
            'Rate': ['rate', 'hourly_rate', 'cost_rate'],
            'Amount': ['amount', 'total', 'cost', 'revenue']
        }
        
        # Attempt to map columns
        for req_col in required:
            if req_col not in df_columns:
                # Look for similar columns
                possible_matches = column_mappings.get(req_col, [])
                for df_col in df_columns:
                    if df_col.lower() in possible_matches:
                        df = df.rename(columns={df_col: req_col})
                        break
        
        return df
    
    def normalize_field_counts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize field counts and clean data"""
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Clean whitespace
        for col in df.select_dtypes(include=['object']):
            df[col] = df[col].astype(str).str.strip()
        
        # Replace 'nan' strings with actual NaN
        df = df.replace('nan', pd.NA)
        
        return df
    
    def _process_driving_history(self, df: pd.DataFrame, file_path: str) -> Dict[str, Any]:
        """Process driving history data for attendance matrix"""
        processed_records = []
        
        for _, row in df.iterrows():
            try:
                record = {
                    'vin': str(row.get('VIN', '')),
                    'date': str(row.get('Date', '')),
                    'driver': str(row.get('Driver', '')),
                    'hours': float(row.get('Hours', 0)),
                    'location': str(row.get('Location', '')),
                    'source_file': os.path.basename(file_path)
                }
                processed_records.append(record)
            except Exception as e:
                logger.warning(f"Error processing driving history row: {e}")
                continue
        
        return {
            'success': True,
            'data_type': 'driving_history',
            'records_processed': len(processed_records),
            'data': processed_records,
            'file_path': file_path
        }
    
    def _process_assets_time_on_site(self, df: pd.DataFrame, file_path: str) -> Dict[str, Any]:
        """Process assets time on site data"""
        processed_records = []
        
        for _, row in df.iterrows():
            try:
                record = {
                    'asset': str(row.get('Asset', '')),
                    'job_site': str(row.get('JobSite', '')),
                    'time_in': str(row.get('TimeIn', '')),
                    'time_out': str(row.get('TimeOut', '')),
                    'total_hours': float(row.get('TotalHours', 0)),
                    'source_file': os.path.basename(file_path)
                }
                processed_records.append(record)
            except Exception as e:
                logger.warning(f"Error processing time on site row: {e}")
                continue
        
        return {
            'success': True,
            'data_type': 'assets_time_on_site',
            'records_processed': len(processed_records),
            'data': processed_records,
            'file_path': file_path
        }
    
    def _process_activity_detail(self, df: pd.DataFrame, file_path: str) -> Dict[str, Any]:
        """Process activity detail data"""
        processed_records = []
        
        for _, row in df.iterrows():
            try:
                record = {
                    'datetime': str(row.get('DateTime', '')),
                    'asset': str(row.get('Asset', '')),
                    'activity': str(row.get('Activity', '')),
                    'driver': str(row.get('Driver', '')),
                    'location': str(row.get('Location', '')),
                    'source_file': os.path.basename(file_path)
                }
                processed_records.append(record)
            except Exception as e:
                logger.warning(f"Error processing activity detail row: {e}")
                continue
        
        return {
            'success': True,
            'data_type': 'activity_detail',
            'records_processed': len(processed_records),
            'data': processed_records,
            'file_path': file_path
        }
    
    def _process_ragle_billing(self, df: pd.DataFrame, file_path: str) -> Dict[str, Any]:
        """Process RAGLE billing data"""
        processed_records = []
        
        for _, row in df.iterrows():
            try:
                record = {
                    'job_number': str(row.get('JobNumber', '')),
                    'equipment': str(row.get('Equipment', '')),
                    'hours': float(row.get('Hours', 0)),
                    'rate': float(row.get('Rate', 0)),
                    'amount': float(row.get('Amount', 0)),
                    'source_file': os.path.basename(file_path)
                }
                processed_records.append(record)
            except Exception as e:
                logger.warning(f"Error processing billing row: {e}")
                continue
        
        return {
            'success': True,
            'data_type': 'ragle_billing',
            'records_processed': len(processed_records),
            'data': processed_records,
            'file_path': file_path
        }
    
    def _process_generic(self, df: pd.DataFrame, file_path: str) -> Dict[str, Any]:
        """Process generic CSV data"""
        try:
            records = df.to_dict('records')
            
            return {
                'success': True,
                'data_type': 'generic',
                'records_processed': len(records),
                'data': records,
                'file_path': file_path,
                'columns': df.columns.tolist()
            }
        except Exception as e:
            logger.error(f"Error processing generic CSV: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path,
                'records_processed': 0,
                'data': []
            }

# Global processor instance
csv_processor = TRAXOVOCSVProcessor()