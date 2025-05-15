"""
Excel Parser Module for SYSTEMSMITH

Provides intelligent parsing of various Excel file formats with automatic:
- Format detection
- Sheet selection
- Column mapping
- Data normalization

Supports single and multi-sheet Excel files from various sources.
"""

import os
import logging
import re
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Union, Optional, Any
from datetime import datetime
from utils.cya import backup_file, log_event

logger = logging.getLogger(__name__)

# Excel Parser Constants
SUPPORTED_EXTENSIONS = ['.xlsx', '.xls', '.xlsm', '.csv']
DEFAULT_SHEET_NAMES = ['Data', 'Sheet1', 'Summary', 'Raw Data']

class ExcelParserException(Exception):
    """Exception raised for errors in the Excel parser."""
    pass

class ExcelParser:
    """Intelligent Excel Parser for various file formats"""
    
    def __init__(self, file_path: str, file_type: str = None, sheet_name: str = None, user_id: int = None):
        """
        Initialize the Excel parser.
        
        Args:
            file_path: Path to the Excel file
            file_type: Type of file (billing, utilization, etc.). If None, will attempt to detect.
            sheet_name: Name of the sheet to parse. If None, will attempt to detect.
            user_id: ID of the user who uploaded the file
        """
        if not os.path.exists(file_path):
            raise ExcelParserException(f"File not found: {file_path}")
        
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.file_extension = os.path.splitext(file_path)[1].lower()
        self.file_type = file_type
        self.sheet_name = sheet_name
        self.user_id = user_id
        self.df = None
        self.all_sheets = {}
        self.sheet_names = []
        self.detected_type = None
        self.column_mapping = {}
        
        # Check if file is supported
        if self.file_extension not in SUPPORTED_EXTENSIONS:
            raise ExcelParserException(f"Unsupported file format: {self.file_extension}")
        
        # Backup the file
        self._backup_file()
        
        # Log the file upload
        log_event(
            "FILE_UPLOAD", 
            f"Uploaded file: {self.file_name}",
            user_id=self.user_id,
            data_path=self.file_path,
            metadata={"file_type": file_type}
        )
    
    def _backup_file(self):
        """Backup the file to the CYA system"""
        try:
            backup_file(self.file_path, "uploads", self.user_id)
        except Exception as e:
            logger.warning(f"Failed to backup file: {e}")
    
    def _detect_file_type(self) -> str:
        """
        Detect the type of file based on filename and content.
        
        Returns:
            str: Detected file type
        """
        file_name_lower = self.file_name.lower()
        
        # Check for billing files
        if "billing" in file_name_lower or "ragle eq" in file_name_lower or "select eq" in file_name_lower:
            return "billing"
        
        # Check for utilization files
        if "utilization" in file_name_lower or "fleet" in file_name_lower:
            return "utilization"
        
        # Check for work order files
        if "work order" in file_name_lower or "wo " in file_name_lower or "rag wo" in file_name_lower:
            return "work_order"
        
        # Check for attendance files
        if "attendance" in file_name_lower or "late start" in file_name_lower or "early end" in file_name_lower:
            return "attendance"
        
        # Check for GPS files
        if "gps" in file_name_lower or "gauge" in file_name_lower or "efficiency" in file_name_lower:
            return "gps"
        
        # If we can't detect from the filename, try to detect from the content
        if self.df is not None:
            columns = [col.lower() if isinstance(col, str) else "" for col in self.df.columns]
            
            # Check for billing patterns
            if any("billed" in col for col in columns) or any("invoice" in col for col in columns):
                return "billing"
            
            # Check for utilization patterns
            if any("usage" in col for col in columns) or any("hours" in col for col in columns):
                return "utilization"
            
            # Check for work order patterns
            if any("work order" in col for col in columns) or any("repair" in col for col in columns):
                return "work_order"
            
            # Check for attendance patterns
            if any("late" in col for col in columns) or any("attendance" in col for col in columns):
                return "attendance"
            
            # Check for GPS patterns
            if any("location" in col for col in columns) or any("coordinate" in col for col in columns):
                return "gps"
        
        # Default to unknown
        return "unknown"
    
    def _detect_sheet(self) -> str:
        """
        Detect the best sheet to use based on content.
        
        Returns:
            str: Name of the best sheet to use
        """
        if self.file_extension == '.csv':
            return None  # CSV files don't have sheets
        
        # If there's only one sheet, use it
        if len(self.sheet_names) == 1:
            return self.sheet_names[0]
        
        # Try to find a sheet that matches the file type
        if self.file_type:
            for sheet in self.sheet_names:
                sheet_lower = sheet.lower()
                if self.file_type in sheet_lower:
                    return sheet
        
        # Try common sheet names
        for name in DEFAULT_SHEET_NAMES:
            if name in self.sheet_names:
                return name
        
        # Look for the sheet with the most rows
        sheet_rows = {}
        for name in self.sheet_names:
            try:
                sheet_df = pd.read_excel(self.file_path, sheet_name=name)
                sheet_rows[name] = len(sheet_df)
            except Exception:
                sheet_rows[name] = 0
        
        if sheet_rows:
            return max(sheet_rows.items(), key=lambda x: x[1])[0]
        
        # Default to the first sheet
        return self.sheet_names[0]
    
    def _clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize column names.
        
        Args:
            df: DataFrame with columns to clean
            
        Returns:
            DataFrame with cleaned column names
        """
        # Ensure all column names are strings
        df.columns = [str(col) for col in df.columns]
        
        # Clean column names
        clean_columns = {}
        for col in df.columns:
            # Convert to lowercase
            clean_col = col.lower()
            
            # Remove special characters and replace with underscore
            clean_col = re.sub(r'[^a-z0-9]', '_', clean_col)
            
            # Replace multiple underscores with single underscore
            clean_col = re.sub(r'_+', '_', clean_col)
            
            # Remove leading/trailing underscores
            clean_col = clean_col.strip('_')
            
            # If empty after cleaning, use 'column_X'
            if not clean_col:
                clean_col = f"column_{df.columns.get_loc(col)}"
            
            clean_columns[col] = clean_col
        
        # Rename columns
        df = df.rename(columns=clean_columns)
        
        return df
    
    def _infer_column_types(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Infer the types of columns in the DataFrame.
        
        Args:
            df: DataFrame to infer column types from
            
        Returns:
            Dictionary mapping column names to inferred types
        """
        column_types = {}
        
        for col in df.columns:
            # Skip completely empty columns
            if df[col].isna().all():
                column_types[col] = 'empty'
                continue
            
            # Try to detect date columns
            if df[col].dtype == 'object':
                # Check if column appears to contain dates
                date_sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if date_sample and isinstance(date_sample, str):
                    try:
                        pd.to_datetime(date_sample)
                        column_types[col] = 'date'
                        continue
                    except:
                        pass
            
            # Check for numeric columns
            if pd.api.types.is_numeric_dtype(df[col]):
                # Check if it's likely an ID column
                if 'id' in col or 'number' in col:
                    column_types[col] = 'id'
                # Check if it's a monetary column
                elif 'cost' in col or 'price' in col or 'amount' in col or 'rate' in col:
                    column_types[col] = 'money'
                # Check if it's a percentage
                elif 'percent' in col or 'pct' in col or 'rate' in col:
                    column_types[col] = 'percent'
                # Default to numeric
                else:
                    column_types[col] = 'numeric'
            else:
                # Check for boolean columns
                if set(df[col].dropna().unique()).issubset({'Y', 'N', 'Yes', 'No', 'TRUE', 'FALSE', True, False, 1, 0}):
                    column_types[col] = 'boolean'
                # Check for ID columns
                elif any(id_term in col for id_term in ['id', 'code', 'number', 'identifier']):
                    column_types[col] = 'id'
                # Default to text
                else:
                    column_types[col] = 'text'
        
        return column_types
    
    def _apply_column_mapping(self, df: pd.DataFrame, mapping_type: str) -> pd.DataFrame:
        """
        Apply column mapping based on file type.
        
        Args:
            df: DataFrame to map columns for
            mapping_type: Type of mapping to apply
            
        Returns:
            DataFrame with standardized column names
        """
        # Define standard column mappings for different file types
        standard_mappings = {
            'billing': {
                'asset_id': ['asset_id', 'asset_identifier', 'asset_number', 'equipment_id', 'eq_id', 'unit_number', 'eq_number'],
                'asset_description': ['asset_description', 'description', 'asset_name', 'equipment_name', 'equipment_description'],
                'job_id': ['job_id', 'job_number', 'job_code', 'project_id', 'project_number', 'project_code', 'work_order'],
                'job_name': ['job_name', 'job_description', 'project_name', 'project_description', 'location', 'site'],
                'hours': ['hours', 'billed_hours', 'engine_hours', 'equipment_hours', 'usage_hours', 'run_hours', 'meter_hours'],
                'rate': ['rate', 'billing_rate', 'hourly_rate', 'charge_rate', 'price', 'hourly_price'],
                'total': ['total', 'total_amount', 'extended', 'extended_amount', 'amount', 'billed_amount'],
                'start_date': ['start_date', 'period_start', 'from_date', 'begin_date', 'date_from'],
                'end_date': ['end_date', 'period_end', 'to_date', 'finish_date', 'date_to']
            },
            'work_order': {
                'wo_number': ['wo_number', 'work_order_number', 'work_order_id', 'wo_id', 'order_number', 'ticket_number'],
                'asset_id': ['asset_id', 'asset_identifier', 'asset_number', 'equipment_id', 'eq_id', 'unit_number', 'eq_number'],
                'service_date': ['service_date', 'repair_date', 'work_date', 'completion_date', 'date'],
                'service_type': ['service_type', 'repair_type', 'work_type', 'maintenance_type', 'type'],
                'description': ['description', 'work_description', 'repair_description', 'notes', 'comments'],
                'cost': ['cost', 'total_cost', 'repair_cost', 'amount', 'total_amount', 'invoice_amount'],
                'labor_hours': ['labor_hours', 'hours', 'tech_hours', 'mechanic_hours', 'technician_hours'],
                'parts_cost': ['parts_cost', 'parts_amount', 'part_cost', 'materials_cost', 'materials_amount']
            },
            'utilization': {
                'asset_id': ['asset_id', 'asset_identifier', 'asset_number', 'equipment_id', 'eq_id', 'unit_number', 'eq_number'],
                'date': ['date', 'usage_date', 'work_date', 'log_date'],
                'hours': ['hours', 'usage_hours', 'engine_hours', 'meter_hours', 'run_hours'],
                'job_id': ['job_id', 'job_number', 'job_code', 'project_id', 'project_number', 'project_code'],
                'operator': ['operator', 'driver', 'employee', 'operator_name', 'driver_name', 'employee_name']
            },
            'attendance': {
                'employee': ['employee', 'employee_name', 'driver', 'driver_name', 'operator', 'operator_name', 'name'],
                'asset_id': ['asset_id', 'asset_identifier', 'asset_number', 'equipment_id', 'eq_id', 'unit_number', 'eq_number'],
                'date': ['date', 'attendance_date', 'work_date', 'report_date'],
                'start_time': ['start_time', 'time_in', 'clock_in', 'in_time', 'arrival_time'],
                'end_time': ['end_time', 'time_out', 'clock_out', 'out_time', 'departure_time'],
                'status': ['status', 'attendance_status', 'flag', 'issue', 'violation', 'problem'],
                'job_id': ['job_id', 'job_number', 'job_code', 'project_id', 'project_number', 'project_code'],
                'location': ['location', 'site', 'job_site', 'work_location', 'site_name', 'job_location']
            },
            'gps': {
                'asset_id': ['asset_id', 'asset_identifier', 'asset_number', 'equipment_id', 'eq_id', 'unit_number', 'eq_number'],
                'latitude': ['latitude', 'lat', 'y_coordinate', 'y_coord'],
                'longitude': ['longitude', 'lon', 'long', 'x_coordinate', 'x_coord'],
                'timestamp': ['timestamp', 'date_time', 'event_time', 'gps_time', 'time', 'event_date_time'],
                'speed': ['speed', 'velocity', 'rate'],
                'heading': ['heading', 'direction', 'bearing'],
                'ignition': ['ignition', 'ignition_status', 'engine', 'engine_status'],
                'location': ['location', 'place', 'address', 'site', 'job_site', 'location_name']
            }
        }
        
        # Get the mapping for the specified type
        if mapping_type not in standard_mappings:
            logger.warning(f"No standard mapping for type: {mapping_type}")
            return df
        
        mapping = standard_mappings[mapping_type]
        column_mapping = {}
        
        # Find the best match for each standard column
        for std_col, possible_matches in mapping.items():
            for col in df.columns:
                if col in possible_matches or any(match in col for match in possible_matches):
                    column_mapping[col] = std_col
                    break
        
        # Save the column mapping
        self.column_mapping = column_mapping
        
        # Apply the mapping
        if column_mapping:
            df = df.rename(columns=column_mapping)
        
        return df
    
    def load(self) -> pd.DataFrame:
        """
        Load the Excel file into a pandas DataFrame.
        
        Returns:
            DataFrame containing the parsed data
        """
        try:
            # Load the file based on extension
            if self.file_extension == '.csv':
                # Try different delimiters
                try:
                    self.df = pd.read_csv(self.file_path, sep=',')
                except:
                    try:
                        self.df = pd.read_csv(self.file_path, sep=';')
                    except:
                        try:
                            self.df = pd.read_csv(self.file_path, sep='\t')
                        except:
                            raise ExcelParserException("Failed to parse CSV file with common delimiters")
            else:
                # Get available sheets
                excel_file = pd.ExcelFile(self.file_path)
                self.sheet_names = excel_file.sheet_names
                
                # Detect the sheet to use if not specified
                if not self.sheet_name:
                    self.sheet_name = self._detect_sheet()
                
                # Load the selected sheet
                self.df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)
                
                # Load all sheets for reference
                for sheet in self.sheet_names:
                    try:
                        self.all_sheets[sheet] = pd.read_excel(self.file_path, sheet_name=sheet)
                    except Exception as e:
                        logger.warning(f"Failed to load sheet '{sheet}': {e}")
            
            # Clean up the DataFrame
            self.df = self._clean_dataframe(self.df)
            
            # Detect file type if not specified
            if not self.file_type:
                self.file_type = self._detect_file_type()
                self.detected_type = self.file_type
            
            # Apply standard column mappings
            self.df = self._apply_column_mapping(self.df, self.file_type)
            
            return self.df
            
        except Exception as e:
            logger.error(f"Failed to load Excel file: {e}")
            raise ExcelParserException(f"Failed to load Excel file: {e}")
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and prepare the DataFrame for analysis.
        
        Args:
            df: DataFrame to clean
            
        Returns:
            Cleaned DataFrame
        """
        # Clean column names
        df = self._clean_column_names(df)
        
        # Drop completely empty rows and columns
        df = df.dropna(how='all')
        df = df.dropna(axis=1, how='all')
        
        # Replace common null values
        null_values = ['N/A', 'n/a', 'NA', 'na', 'NULL', 'null', '--', '—', '-', '#N/A', '#REF!', '#VALUE!']
        df = df.replace(null_values, np.nan)
        
        # Trim whitespace from string columns
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
        
        return df
    
    def normalize(self) -> pd.DataFrame:
        """
        Normalize the DataFrame based on file type.
        
        Returns:
            Normalized DataFrame
        """
        if self.df is None:
            raise ExcelParserException("No data loaded. Call load() first.")
        
        try:
            # Apply normalization based on file type
            normalizer_method = f"_normalize_{self.file_type}_data"
            if hasattr(self, normalizer_method):
                self.df = getattr(self, normalizer_method)(self.df)
            else:
                logger.warning(f"No normalizer found for file type: {self.file_type}")
            
            return self.df
            
        except Exception as e:
            logger.error(f"Failed to normalize data: {e}")
            raise ExcelParserException(f"Failed to normalize data: {e}")
    
    def _normalize_billing_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize billing data.
        
        Args:
            df: DataFrame with billing data
            
        Returns:
            Normalized DataFrame
        """
        # Handle date columns
        for date_col in ['start_date', 'end_date']:
            if date_col in df.columns:
                try:
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                except:
                    pass
        
        # Ensure numeric columns
        for num_col in ['hours', 'rate', 'total']:
            if num_col in df.columns:
                df[num_col] = pd.to_numeric(df[num_col], errors='coerce')
        
        # Calculate missing values
        if 'hours' in df.columns and 'rate' in df.columns and 'total' not in df.columns:
            df['total'] = df['hours'] * df['rate']
        elif 'hours' in df.columns and 'total' in df.columns and 'rate' not in df.columns:
            mask = df['hours'] > 0
            df.loc[mask, 'rate'] = df.loc[mask, 'total'] / df.loc[mask, 'hours']
        
        return df
    
    def _normalize_work_order_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize work order data.
        
        Args:
            df: DataFrame with work order data
            
        Returns:
            Normalized DataFrame
        """
        # Handle date columns
        if 'service_date' in df.columns:
            try:
                df['service_date'] = pd.to_datetime(df['service_date'], errors='coerce')
            except:
                pass
        
        # Ensure numeric columns
        for num_col in ['cost', 'labor_hours', 'parts_cost']:
            if num_col in df.columns:
                df[num_col] = pd.to_numeric(df[num_col], errors='coerce')
        
        # Calculate missing values
        if 'cost' in df.columns and 'parts_cost' in df.columns and 'labor_cost' not in df.columns:
            df['labor_cost'] = df['cost'] - df['parts_cost']
        
        return df
    
    def _normalize_utilization_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize utilization data.
        
        Args:
            df: DataFrame with utilization data
            
        Returns:
            Normalized DataFrame
        """
        # Handle date columns
        if 'date' in df.columns:
            try:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            except:
                pass
        
        # Ensure numeric columns
        if 'hours' in df.columns:
            df['hours'] = pd.to_numeric(df['hours'], errors='coerce')
        
        return df
    
    def _normalize_attendance_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize attendance data.
        
        Args:
            df: DataFrame with attendance data
            
        Returns:
            Normalized DataFrame
        """
        # Handle date columns
        if 'date' in df.columns:
            try:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            except:
                pass
        
        # Handle time columns
        for time_col in ['start_time', 'end_time']:
            if time_col in df.columns:
                try:
                    # Convert to pandas time type if possible
                    df[time_col] = pd.to_datetime(df[time_col], errors='coerce').dt.time
                except:
                    pass
        
        return df
    
    def _normalize_gps_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize GPS data.
        
        Args:
            df: DataFrame with GPS data
            
        Returns:
            Normalized DataFrame
        """
        # Handle timestamp column
        if 'timestamp' in df.columns:
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            except:
                pass
        
        # Ensure numeric columns
        for num_col in ['latitude', 'longitude', 'speed']:
            if num_col in df.columns:
                df[num_col] = pd.to_numeric(df[num_col], errors='coerce')
        
        # Normalize ignition status
        if 'ignition' in df.columns:
            # Convert to boolean
            ignition_map = {
                'on': True, 'off': False,
                'true': True, 'false': False,
                '1': True, '0': False,
                1: True, 0: False,
                'yes': True, 'no': False,
                'y': True, 'n': False
            }
            
            df['ignition'] = df['ignition'].astype(str).str.lower().map(ignition_map)
        
        return df
    
    def save_to_csv(self, output_path: str = None) -> str:
        """
        Save the normalized DataFrame to a CSV file.
        
        Args:
            output_path: Path to save the CSV file. If None, will use a default path.
            
        Returns:
            Path to the saved CSV file
        """
        if self.df is None:
            raise ExcelParserException("No data loaded. Call load() first.")
        
        if not output_path:
            # Create a default output path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            directory = os.path.join("data", "normalized", self.file_type)
            os.makedirs(directory, exist_ok=True)
            
            file_name = f"{os.path.splitext(self.file_name)[0]}_{timestamp}.csv"
            output_path = os.path.join(directory, file_name)
        
        try:
            # Save to CSV
            self.df.to_csv(output_path, index=False)
            
            # Log the event
            log_event(
                "FILE_NORMALIZED", 
                f"Normalized file saved: {os.path.basename(output_path)}",
                user_id=self.user_id,
                data_path=output_path,
                metadata={
                    "original_file": self.file_name,
                    "file_type": self.file_type,
                    "row_count": len(self.df),
                    "column_count": len(self.df.columns)
                }
            )
            
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to save CSV file: {e}")
            raise ExcelParserException(f"Failed to save CSV file: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the parsed data.
        
        Returns:
            Dictionary with summary information
        """
        if self.df is None:
            raise ExcelParserException("No data loaded. Call load() first.")
        
        # Get basic stats
        row_count = len(self.df)
        column_count = len(self.df.columns)
        
        # Get column info
        column_types = self._infer_column_types(self.df)
        
        # Get mapped columns
        mapped_columns = {v: k for k, v in self.column_mapping.items()} if self.column_mapping else {}
        
        # Get date range if applicable
        date_range = None
        date_columns = [col for col, type_ in column_types.items() if type_ == 'date']
        if date_columns:
            for col in date_columns:
                try:
                    min_date = pd.to_datetime(self.df[col].min()).strftime("%Y-%m-%d")
                    max_date = pd.to_datetime(self.df[col].max()).strftime("%Y-%m-%d")
                    date_range = {"column": col, "min": min_date, "max": max_date}
                    break
                except:
                    continue
        
        # Build summary
        summary = {
            "file_name": self.file_name,
            "file_type": self.file_type,
            "detected_type": self.detected_type,
            "sheet_name": self.sheet_name,
            "available_sheets": self.sheet_names,
            "row_count": row_count,
            "column_count": column_count,
            "column_types": column_types,
            "mapped_columns": mapped_columns,
            "date_range": date_range
        }
        
        return summary