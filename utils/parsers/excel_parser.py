"""
Advanced Excel Parser

This module provides functionality to intelligently parse Excel files with varying formats,
multi-sheet structures, and different header positions.
"""

import os
import re
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional, Union

# Setup logging
logger = logging.getLogger(__name__)

class ExcelParser:
    """Advanced Excel parser for handling complex file formats"""
    
    # Common patterns for column standardization
    COLUMN_PATTERNS = {
        # Employee/driver patterns
        'employee': [
            r'emp(?:loyee)?[\s_-]*(?:name|id)?',
            r'driver(?:[\s_-]*name)?',
            r'operator',
            r'(?:assigned[\s_-]*)?(?:to|user)',
            r'(?:assigned[\s_-]*)(?:person|name)',
            r'assigned',
            r'name'
        ],
        'employee_id': [
            r'emp(?:loyee)?[\s_-]*(?:id|number|#|code)',
            r'(?:id|#|no|num)[\s_-]*(?:emp|employee|number)',
            r'driver[\s_-]*(?:id|number|#)',
            r'personnel[\s_-]*(?:id|number)',
            r'(?:emp|employee|personnel|driver)[\s_-]*code'
        ],
        
        # Asset patterns
        'asset': [
            r'(?:equipment|asset|unit|eq)[\s_-]*(?:id|number|#|code)?',
            r'(?:id|#|no|num)[\s_-]*(?:equipment|asset|unit|eq)',
            r'unit[\s_-]*(?:id|number|#)?',
            r'vehicle[\s_-]*(?:id|number|#)?',
            r'id',
            r'num(?:ber)?',
            r'eq(?:[\s_-]*)(?:id|num)',
            r'eq[\s_-]*unit'
        ],
        'asset_type': [
            r'(?:equipment|asset|unit)[\s_-]*type',
            r'type[\s_-]*(?:of[\s_-]*)?(?:equipment|asset|unit)',
            r'equipment',
            r'category',
            r'class'
        ],
        'asset_description': [
            r'(?:equipment|asset|unit)[\s_-]*desc(?:ription)?',
            r'desc(?:ription)?',
            r'details',
            r'model',
            r'make[\s_-]*model'
        ],
        
        # Hours/utilization patterns
        'hours': [
            r'(?:total[\s_-]*)?hours',
            r'hrs',
            r'engine[\s_-]*hours',
            r'run[\s_-]*time',
            r'usage[\s_-]*hours',
            r'time'
        ],
        'idle_hours': [
            r'idle[\s_-]*(?:hours|hrs|time)',
            r'hours[\s_-]*idle',
            r'standby[\s_-]*(?:hours|hrs|time)'
        ],
        'run_hours': [
            r'run(?:ning)?[\s_-]*(?:hours|hrs|time)',
            r'active[\s_-]*(?:hours|hrs|time)',
            r'work(?:ing)?[\s_-]*(?:hours|hrs|time)'
        ],
        
        # Date patterns
        'date': [
            r'date',
            r'day',
            r'period',
            r'time[\s_-]*frame',
            r'report[\s_-]*date',
            r'as[\s_-]*of'
        ],
        'start_date': [
            r'start[\s_-]*date',
            r'from[\s_-]*date',
            r'begin(?:ning)?[\s_-]*date',
            r'period[\s_-]*start'
        ],
        'end_date': [
            r'end[\s_-]*date',
            r'to[\s_-]*date',
            r'period[\s_-]*end'
        ],
        
        # Location patterns
        'location': [
            r'location',
            r'site',
            r'job[\s_-]*site',
            r'project[\s_-]*(?:site|location)',
            r'area',
            r'region',
            r'address'
        ],
        'job_code': [
            r'job[\s_-]*(?:code|id|number|#)',
            r'project[\s_-]*(?:code|id|number|#)',
            r'job',
            r'project'
        ],
        'district': [
            r'district',
            r'division',
            r'region',
            r'area',
            r'sector'
        ],
        
        # Cost/billing patterns
        'cost': [
            r'cost',
            r'amount',
            r'charge',
            r'billing',
            r'price',
            r'value'
        ],
        'rate': [
            r'rate',
            r'(?:hourly|daily|monthly)[\s_-]*rate',
            r'price[\s_-]*per[\s_-]*(?:hour|day|month)',
            r'unit[\s_-]*(?:price|cost)'
        ],
        'total': [
            r'total',
            r'sum',
            r'amount',
            r'(?:grand|final)[\s_-]*total'
        ]
    }
    
    # Known header formats
    HEADER_INDICATORS = [
        'employee', 'driver', 'asset', 'equipment', 'unit', 'job', 'project', 
        'date', 'hours', 'location', 'cost', 'rate', 'total', 'id', 'description',
        'make', 'model', 'serial'
    ]
    
    def __init__(self):
        """Initialize the Excel parser"""
        # Statistics tracking
        self.stats = {
            'files_processed': 0,
            'sheets_processed': 0,
            'rows_processed': 0,
            'normalized_columns': 0,
            'detected_headers': 0,
            'detected_ids': 0
        }
        
        # Parsed data storage
        self.parsed_data = {}
        
        # Detected column mappings
        self.column_mappings = {}
        
    def _get_file_type_from_name(self, filename: str) -> str:
        """
        Determine file type from filename pattern
        
        Args:
            filename (str): Name of the file
            
        Returns:
            str: Detected file type
        """
        filename = filename.lower()
        
        # Determine file type based on patterns in the name
        if any(term in filename for term in ['fringe', 'auto fringe', 'autofringe']):
            return 'fringe'
        elif any(term in filename for term in ['daily', 'late start', 'noj report']):
            return 'attendance'
        elif any(term in filename for term in ['eq billing', 'eq monthly', 'billing', 'allocations']):
            return 'billing'
        elif any(term in filename for term in ['wex', 'fuel', 'transaction']):
            return 'fuel'
        elif any(term in filename for term in ['gps', 'efficiency', 'work zone', 'workzone']):
            return 'gps'
        elif any(term in filename for term in ['utilization', 'fleet']):
            return 'utilization'
        elif any(term in filename for term in ['profit', 'expense', 'ytd']):
            return 'financial'
        elif any(term in filename for term in ['ntta', 'toll', 'trx']):
            return 'tolls'
        elif any(term in filename for term in ['wo detail', 'maintenance', 'uvc']):
            return 'maintenance'
        else:
            return 'unknown'
        
    def _detect_header_row(self, df: pd.DataFrame) -> int:
        """
        Detect the header row in a dataframe
        
        Args:
            df (pd.DataFrame): DataFrame to analyze
            
        Returns:
            int: Detected header row index
        """
        # Check each row for header-like characteristics
        for i in range(min(20, len(df))):  # Check first 20 rows at most
            row = df.iloc[i].astype(str)
            
            # Count how many header indicators match the row values
            indicator_matches = sum(
                1 for val in row if any(
                    indicator.lower() in val.lower() 
                    for indicator in self.HEADER_INDICATORS
                )
            )
            
            # Count how many values in the row are strings vs numeric
            string_values = sum(1 for val in row if not self._is_numeric(val))
            
            # If more than 30% of columns match header indicators and most values are strings
            if (indicator_matches / len(row) > 0.3 and string_values / len(row) > 0.7):
                self.stats['detected_headers'] += 1
                return i
            
        # Default to first row if no clear header row found
        return 0
    
    def _is_numeric(self, val: Any) -> bool:
        """
        Check if a value is numeric
        
        Args:
            val (Any): Value to check
            
        Returns:
            bool: True if numeric, False otherwise
        """
        if isinstance(val, (int, float)):
            return True
        
        if isinstance(val, str):
            try:
                float(val.replace(',', ''))
                return True
            except (ValueError, TypeError):
                return False
        
        return False
    
    def _clean_column_name(self, name: str) -> str:
        """
        Clean and standardize column names
        
        Args:
            name (str): Original column name
            
        Returns:
            str: Cleaned column name
        """
        if not isinstance(name, str):
            return str(name)
        
        # Convert to lowercase and replace non-alphanumeric with spaces
        name = re.sub(r'[^a-zA-Z0-9\s]', ' ', name.lower())
        
        # Replace multiple spaces with a single space
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def _normalize_column_names(self, columns: List[str]) -> Dict[str, str]:
        """
        Normalize column names based on known patterns
        
        Args:
            columns (List[str]): Original column names
            
        Returns:
            Dict[str, str]: Mapping of original to normalized column names
        """
        normalized_map = {}
        
        for col in columns:
            cleaned_col = self._clean_column_name(col)
            matched = False
            
            # Check against known patterns
            for category, patterns in self.COLUMN_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, cleaned_col, re.IGNORECASE):
                        normalized_map[col] = category
                        self.stats['normalized_columns'] += 1
                        matched = True
                        break
                if matched:
                    break
            
            # If no match found, keep original
            if not matched:
                normalized_map[col] = cleaned_col
        
        return normalized_map
    
    def _detect_asset_id_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Detect columns that likely contain asset IDs
        
        Args:
            df (pd.DataFrame): DataFrame to analyze
            
        Returns:
            List[str]: List of column names that likely contain asset IDs
        """
        possible_id_columns = []
        
        for col in df.columns:
            # Skip obviously non-ID columns
            if df[col].dtype == 'float64' or df[col].dtype == 'int64':
                continue
                
            # Skip columns with all missing values
            if df[col].isna().all():
                continue
                
            # Get non-NaN sample values
            sample_values = df[col].dropna().astype(str).sample(min(10, len(df[col].dropna()))).values
            
            # Check for ID patterns in sample values
            id_pattern_matches = 0
            for val in sample_values:
                # Check for asset ID patterns (usually contains letters and numbers)
                if re.search(r'^[A-Za-z]{1,4}-\d{1,3}', val):  # e.g., EX-01, WL-12
                    id_pattern_matches += 1
                elif re.search(r'^\d{6}', val):  # e.g., 210013
                    id_pattern_matches += 1
                elif re.search(r'^[A-Za-z]{2,6}-\d{2,}[sS]?$', val):  # e.g., MB-13S, PT-20S
                    id_pattern_matches += 1
            
            # If more than 30% of samples match ID patterns
            if id_pattern_matches / len(sample_values) > 0.3:
                possible_id_columns.append(col)
                self.stats['detected_ids'] += 1
        
        return possible_id_columns
    
    def _detect_date_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Detect columns that contain dates
        
        Args:
            df (pd.DataFrame): DataFrame to analyze
            
        Returns:
            List[str]: List of column names containing dates
        """
        date_columns = []
        
        for col in df.columns:
            # If already a datetime type
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                date_columns.append(col)
                continue
                
            # Check string columns
            if df[col].dtype == 'object':
                # Get non-NaN sample values
                sample_values = df[col].dropna().astype(str).sample(min(10, len(df[col].dropna()))).values
                
                # Check for date patterns
                date_pattern_matches = 0
                for val in sample_values:
                    # Check various date formats
                    if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', val):  # e.g., 05/15/2025, 5-15-25
                        date_pattern_matches += 1
                    elif re.search(r'\d{4}[/-]\d{1,2}[/-]\d{1,2}', val):  # e.g., 2025/05/15
                        date_pattern_matches += 1
                    elif re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,]+\d{1,2}(?:st|nd|rd|th)?[\s,]+\d{2,4}', val, re.IGNORECASE):
                        # e.g., January 15, 2025, Jan 15th 2025
                        date_pattern_matches += 1
                
                # If more than 50% of samples match date patterns
                if date_pattern_matches / len(sample_values) > 0.5:
                    date_columns.append(col)
        
        return date_columns
    
    def _detect_numeric_columns(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Detect and categorize numeric columns
        
        Args:
            df (pd.DataFrame): DataFrame to analyze
            
        Returns:
            Dict[str, List[str]]: Categorized numeric columns
        """
        numeric_columns = {
            'hours': [],
            'cost': [],
            'rate': [],
            'count': [],
            'percentage': [],
            'other_numeric': []
        }
        
        for col in df.columns:
            # Check if column is numeric
            if pd.api.types.is_numeric_dtype(df[col]) or (
                df[col].dtype == 'object' and 
                df[col].dropna().apply(lambda x: self._is_numeric(x)).mean() > 0.8
            ):
                # Try to categorize based on column name
                col_lower = str(col).lower()
                
                if any(term in col_lower for term in ['hour', 'hrs', 'runtime', 'time']):
                    numeric_columns['hours'].append(col)
                elif any(term in col_lower for term in ['cost', 'amount', 'charge', 'billing', '$', 'dollar']):
                    numeric_columns['cost'].append(col)
                elif any(term in col_lower for term in ['rate', 'price per']):
                    numeric_columns['rate'].append(col)
                elif any(term in col_lower for term in ['count', 'number of', 'quantity', 'qty']):
                    numeric_columns['count'].append(col)
                elif any(term in col_lower for term in ['percent', '%', 'ratio']):
                    numeric_columns['percentage'].append(col)
                else:
                    numeric_columns['other_numeric'].append(col)
        
        return numeric_columns
    
    def _analyze_sheet_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze the structure of a dataframe/sheet
        
        Args:
            df (pd.DataFrame): DataFrame to analyze
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        # Detect header row
        header_row = self._detect_header_row(df)
        
        # If header row is not the first row, reread with correct header
        if header_row > 0:
            # Assume everything before the header is metadata/title info
            metadata_rows = df.iloc[:header_row].to_dict('records')
            
            # Use the detected header row
            df.columns = df.iloc[header_row]
            df = df.iloc[header_row+1:].reset_index(drop=True)
        else:
            metadata_rows = []
        
        # Clean column names
        df.columns = [str(col).strip() for col in df.columns]
        
        # Normalize column names
        column_mapping = self._normalize_column_names(df.columns)
        
        # Detect asset ID columns
        asset_id_columns = self._detect_asset_id_columns(df)
        
        # Detect date columns
        date_columns = self._detect_date_columns(df)
        
        # Detect numeric columns
        numeric_columns = self._detect_numeric_columns(df)
        
        # Check if sheet has summary/total rows
        last_rows = df.iloc[-5:] if len(df) > 5 else df
        has_summary_rows = any(
            last_row.astype(str).str.contains('total|sum|average|mean|grand', case=False).any()
            for _, last_row in last_rows.iterrows()
        )
        
        # Basic statistics
        row_count = len(df)
        self.stats['rows_processed'] += row_count
        
        # Detect sheet type based on column names and data
        sheet_type = self._detect_sheet_type(df, column_mapping)
        
        analysis = {
            'header_row': header_row,
            'metadata_rows': metadata_rows,
            'column_mapping': column_mapping,
            'asset_id_columns': asset_id_columns,
            'date_columns': date_columns,
            'numeric_columns': numeric_columns,
            'has_summary_rows': has_summary_rows,
            'row_count': row_count,
            'sheet_type': sheet_type,
            'data': df
        }
        
        return analysis
    
    def _detect_sheet_type(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> str:
        """
        Detect the type of data in a sheet
        
        Args:
            df (pd.DataFrame): DataFrame to analyze
            column_mapping (Dict[str, str]): Mapping of original to normalized column names
            
        Returns:
            str: Detected sheet type
        """
        # Check for normalized column names
        normalized_cols = list(column_mapping.values())
        
        # Count occurrences of key categories
        category_counts = {
            'employee': sum(1 for col in normalized_cols if col in ['employee', 'employee_id']),
            'asset': sum(1 for col in normalized_cols if col in ['asset', 'asset_type', 'asset_description']),
            'hours': sum(1 for col in normalized_cols if col in ['hours', 'idle_hours', 'run_hours']),
            'cost': sum(1 for col in normalized_cols if col in ['cost', 'rate', 'total']),
            'location': sum(1 for col in normalized_cols if col in ['location', 'job_code', 'district']),
            'date': sum(1 for col in normalized_cols if col in ['date', 'start_date', 'end_date'])
        }
        
        # Determine predominant category
        if category_counts['employee'] >= 2 and category_counts['asset'] >= 1:
            return 'employee_asset_assignment'
        elif category_counts['asset'] >= 2 and category_counts['hours'] >= 1:
            return 'asset_utilization'
        elif category_counts['asset'] >= 1 and category_counts['cost'] >= 2:
            return 'asset_billing'
        elif category_counts['location'] >= 2:
            return 'location_data'
        elif category_counts['date'] >= 1 and category_counts['hours'] >= 1:
            return 'time_tracking'
        else:
            return 'general'
    
    def _extract_sheet_metadata(self, sheet_name: str, metadata_rows: List[Dict]) -> Dict[str, Any]:
        """
        Extract metadata information from the rows above the header
        
        Args:
            sheet_name (str): Name of the sheet
            metadata_rows (List[Dict]): Rows from above the header
            
        Returns:
            Dict[str, Any]: Extracted metadata
        """
        metadata = {
            'sheet_name': sheet_name,
            'title': None,
            'date_range': None,
            'report_date': None,
            'job_info': None
        }
        
        # Convert metadata rows to strings for easier pattern matching
        metadata_text = '\n'.join([
            ' '.join([str(val) for val in row.values()])
            for row in metadata_rows
        ])
        
        # Extract title - usually in the first few rows
        title_patterns = [
            r'(?i)(?:report|summary):?\s*(.+?)(?:\s*for|\s*from|\s*as of|\s*$)',
            r'(?i)(.+?)\s*report',
            r'(?i)(.+?)\s*summary'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, metadata_text)
            if match:
                metadata['title'] = match.group(1).strip()
                break
        
        # If no title found, use sheet name
        if not metadata['title']:
            metadata['title'] = sheet_name
        
        # Extract date range
        date_range_patterns = [
            r'(?i)(?:period|date range|range|dates):\s*(.+?)\s*(?:to|through|-)\s*(.+?)(?:\s|$)',
            r'(?i)(?:from|beginning)\s*(.+?)\s*(?:to|through|-)\s*(.+?)(?:\s|$)',
            r'(?i)(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*(?:to|through|-)\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in date_range_patterns:
            match = re.search(pattern, metadata_text)
            if match:
                metadata['date_range'] = {
                    'start': match.group(1).strip(),
                    'end': match.group(2).strip()
                }
                break
        
        # Extract report date
        report_date_patterns = [
            r'(?i)(?:report date|as of|generated on):\s*(.+?)(?:\s|$)',
            r'(?i)(?:date):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in report_date_patterns:
            match = re.search(pattern, metadata_text)
            if match:
                metadata['report_date'] = match.group(1).strip()
                break
        
        # Extract job information
        job_patterns = [
            r'(?i)(?:job|project)(?:\s*code|\s*number|\s*id)?:\s*(.+?)(?:\s|$)',
            r'(?i)(?:job|project):\s*(.+?)(?:\s|$)'
        ]
        
        for pattern in job_patterns:
            match = re.search(pattern, metadata_text)
            if match:
                metadata['job_info'] = match.group(1).strip()
                break
        
        return metadata
    
    def _clean_and_standardize_df(self, df: pd.DataFrame, analysis: Dict[str, Any]) -> pd.DataFrame:
        """
        Clean and standardize a dataframe
        
        Args:
            df (pd.DataFrame): DataFrame to clean
            analysis (Dict[str, Any]): Analysis results
            
        Returns:
            pd.DataFrame: Cleaned DataFrame
        """
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Skip empty dataframes
        if df.empty:
            return df
        
        # Standardize column names
        std_columns = {}
        for orig_col, norm_col in analysis['column_mapping'].items():
            if orig_col in df.columns:
                # Use normalized name if it's a recognized category, otherwise use original
                if norm_col in self.COLUMN_PATTERNS.keys():
                    std_columns[orig_col] = norm_col
                else:
                    std_columns[orig_col] = orig_col
        
        df = df.rename(columns=std_columns)
        
        # Convert date columns to datetime
        for col in analysis['date_columns']:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except:
                    pass  # Keep original if conversion fails
        
        # Convert numeric columns that might be stored as strings
        for cat, cols in analysis['numeric_columns'].items():
            for col in cols:
                if col in df.columns and df[col].dtype == 'object':
                    try:
                        # Convert to numeric, handling commas in numbers
                        df[col] = df[col].astype(str).str.replace(',', '').str.replace('$', '').astype(float)
                    except:
                        pass  # Keep original if conversion fails
        
        # Remove summary rows if detected
        if analysis['has_summary_rows']:
            # Look for rows that likely contain summary information
            summary_indicators = ['total', 'sum', 'grand', 'average', 'mean', 'subtotal']
            
            # Find rows with summary indicators
            summary_rows = []
            for idx, row in df.iterrows():
                if any(
                    indicator in str(val).lower() 
                    for val in row 
                    for indicator in summary_indicators
                ):
                    summary_rows.append(idx)
            
            # Drop summary rows if found
            if summary_rows:
                df = df.drop(summary_rows)
        
        # Drop rows that are completely empty
        df = df.dropna(how='all')
        
        # Reset index
        df = df.reset_index(drop=True)
        
        return df
    
    def parse_excel(self, file_path: str, detect_file_type: bool = True) -> Dict[str, Any]:
        """
        Parse an Excel file and extract structured data
        
        Args:
            file_path (str): Path to the Excel file
            detect_file_type (bool): Whether to detect file type from name
            
        Returns:
            Dict[str, Any]: Parsed data and metadata
        """
        try:
            file_name = os.path.basename(file_path)
            file_type = self._get_file_type_from_name(file_name) if detect_file_type else 'unknown'
            
            logger.info(f"Parsing Excel file: {file_name} (detected type: {file_type})")
            
            # Load the Excel file
            try:
                xls = pd.ExcelFile(file_path)
            except Exception as e:
                logger.error(f"Error loading Excel file: {e}")
                return {
                    'success': False,
                    'error': f"Failed to load Excel file: {str(e)}",
                    'file_path': file_path,
                    'file_type': file_type
                }
            
            # Process each sheet
            sheets_data = {}
            sheet_names = xls.sheet_names
            
            for sheet_name in sheet_names:
                try:
                    # Load sheet data
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # Skip empty sheets
                    if df.empty:
                        logger.warning(f"Skipping empty sheet: {sheet_name}")
                        continue
                    
                    # Analyze sheet structure
                    analysis = self._analyze_sheet_structure(df)
                    
                    # Extract metadata from rows above header
                    metadata = self._extract_sheet_metadata(sheet_name, analysis['metadata_rows'])
                    
                    # Clean and standardize the data
                    clean_df = self._clean_and_standardize_df(analysis['data'], analysis)
                    
                    # Create sheet result
                    sheet_result = {
                        'metadata': metadata,
                        'analysis': {k: v for k, v in analysis.items() if k != 'data'},  # Exclude raw data
                        'data': clean_df,
                        'column_mapping': analysis['column_mapping']
                    }
                    
                    sheets_data[sheet_name] = sheet_result
                    self.stats['sheets_processed'] += 1
                    
                    logger.info(f"Processed sheet '{sheet_name}' with {len(clean_df)} rows")
                    
                except Exception as e:
                    logger.error(f"Error processing sheet '{sheet_name}': {e}")
                    continue
            
            # Update stats
            self.stats['files_processed'] += 1
            
            # Build result
            result = {
                'success': True,
                'file_path': file_path,
                'file_name': file_name,
                'file_type': file_type,
                'timestamp': datetime.now().isoformat(),
                'sheets': sheets_data,
                'sheet_count': len(sheets_data),
                'stats': self.stats
            }
            
            # Store in parsed data storage
            self.parsed_data[file_path] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing Excel file {file_path}: {e}")
            return {
                'success': False,
                'error': f"Failed to parse Excel file: {str(e)}",
                'file_path': file_path
            }
    
    def extract_column_data(self, parsed_file: Dict[str, Any], column_type: str) -> Dict[str, Any]:
        """
        Extract data for a specific column type from parsed file
        
        Args:
            parsed_file (Dict[str, Any]): Result from parse_excel
            column_type (str): Column type to extract (e.g., 'employee', 'asset', 'hours')
            
        Returns:
            Dict[str, Any]: Extracted data
        """
        result = {
            'file_path': parsed_file.get('file_path'),
            'file_type': parsed_file.get('file_type'),
            'column_type': column_type,
            'data': {}
        }
        
        if not parsed_file.get('success', False):
            result['error'] = parsed_file.get('error', 'Unknown error')
            return result
        
        # Go through each sheet
        for sheet_name, sheet_data in parsed_file.get('sheets', {}).items():
            # Check if the column type exists in this sheet
            df = sheet_data.get('data')
            column_mapping = sheet_data.get('column_mapping', {})
            
            if df is not None and not df.empty:
                # Get columns that map to the requested type
                matched_columns = [
                    orig_col for orig_col, norm_col in column_mapping.items()
                    if norm_col == column_type and orig_col in df.columns
                ]
                
                if matched_columns:
                    # Extract data from these columns
                    sheet_result = {
                        'sheet_name': sheet_name,
                        'columns': matched_columns,
                        'values': {}
                    }
                    
                    for col in matched_columns:
                        unique_values = df[col].dropna().unique().tolist()
                        
                        # For numeric columns, provide statistics instead of all values
                        if df[col].dtype in ['float64', 'int64']:
                            sheet_result['values'][col] = {
                                'min': df[col].min(),
                                'max': df[col].max(),
                                'mean': df[col].mean(),
                                'median': df[col].median(),
                                'sample': unique_values[:10] if len(unique_values) > 10 else unique_values
                            }
                        else:
                            sheet_result['values'][col] = unique_values[:100] if len(unique_values) > 100 else unique_values
                    
                    result['data'][sheet_name] = sheet_result
        
        return result
    
    def extract_asset_info(self, parsed_file: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract asset information from parsed file
        
        Args:
            parsed_file (Dict[str, Any]): Result from parse_excel
            
        Returns:
            Dict[str, Any]: Extracted asset information
        """
        result = {
            'file_path': parsed_file.get('file_path'),
            'file_type': parsed_file.get('file_type'),
            'asset_info': {}
        }
        
        if not parsed_file.get('success', False):
            result['error'] = parsed_file.get('error', 'Unknown error')
            return result
        
        # Go through each sheet
        for sheet_name, sheet_data in parsed_file.get('sheets', {}).items():
            df = sheet_data.get('data')
            column_mapping = sheet_data.get('column_mapping', {})
            
            if df is not None and not df.empty:
                # Get asset ID columns
                asset_id_columns = [
                    orig_col for orig_col, norm_col in column_mapping.items()
                    if norm_col == 'asset' and orig_col in df.columns
                ]
                
                # If no explicit asset columns, use detected asset ID columns
                if not asset_id_columns:
                    asset_id_columns = sheet_data.get('analysis', {}).get('asset_id_columns', [])
                
                if asset_id_columns:
                    # Extract asset information
                    assets = {}
                    
                    for col in asset_id_columns:
                        # Get unique asset IDs
                        asset_ids = df[col].dropna().unique()
                        
                        for asset_id in asset_ids:
                            if not isinstance(asset_id, str) and pd.isna(asset_id):
                                continue
                                
                            asset_id = str(asset_id).strip()
                            if not asset_id:
                                continue
                                
                            # Get rows for this asset
                            asset_rows = df[df[col] == asset_id]
                            
                            # Skip if no rows found
                            if asset_rows.empty:
                                continue
                                
                            # Prepare asset info
                            asset_info = {
                                'id': asset_id,
                                'source_column': col,
                                'source_sheet': sheet_name,
                                'data': {}
                            }
                            
                            # Extract other information about this asset
                            for data_col, data_type in column_mapping.items():
                                if data_col in df.columns and data_col != col:
                                    # Skip if all values for this asset are NaN
                                    if asset_rows[data_col].isna().all():
                                        continue
                                        
                                    # Extract unique values
                                    values = asset_rows[data_col].dropna().unique()
                                    
                                    # If single value, use that directly
                                    if len(values) == 1:
                                        asset_info['data'][data_type] = values[0]
                                    # Otherwise, store as list (limited to 10 values)
                                    else:
                                        asset_info['data'][data_type] = values[:10].tolist()
                            
                            # Add to results
                            assets[asset_id] = asset_info
                    
                    result['asset_info'][sheet_name] = assets
        
        return result
    
    def extract_employee_asset_mapping(self, parsed_file: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract employee to asset mappings from parsed file
        
        Args:
            parsed_file (Dict[str, Any]): Result from parse_excel
            
        Returns:
            Dict[str, Any]: Extracted employee-asset mappings
        """
        result = {
            'file_path': parsed_file.get('file_path'),
            'file_type': parsed_file.get('file_type'),
            'mappings': []
        }
        
        if not parsed_file.get('success', False):
            result['error'] = parsed_file.get('error', 'Unknown error')
            return result
        
        # Go through each sheet
        for sheet_name, sheet_data in parsed_file.get('sheets', {}).items():
            df = sheet_data.get('data')
            column_mapping = sheet_data.get('column_mapping', {})
            
            if df is not None and not df.empty:
                # Get employee and asset columns
                employee_columns = [
                    orig_col for orig_col, norm_col in column_mapping.items()
                    if norm_col in ['employee', 'employee_id'] and orig_col in df.columns
                ]
                
                asset_columns = [
                    orig_col for orig_col, norm_col in column_mapping.items()
                    if norm_col == 'asset' and orig_col in df.columns
                ]
                
                # If no explicit asset columns, use detected asset ID columns
                if not asset_columns:
                    asset_columns = sheet_data.get('analysis', {}).get('asset_id_columns', [])
                
                if employee_columns and asset_columns:
                    # Extract employee-asset mappings
                    for _, row in df.iterrows():
                        for emp_col in employee_columns:
                            employee = row[emp_col]
                            if pd.isna(employee) or str(employee).strip() == '':
                                continue
                                
                            # Normalize employee value
                            employee = str(employee).strip()
                            
                            for asset_col in asset_columns:
                                asset = row[asset_col]
                                if pd.isna(asset) or str(asset).strip() == '':
                                    continue
                                    
                                # Normalize asset value
                                asset = str(asset).strip()
                                
                                # Create mapping
                                mapping = {
                                    'employee': employee,
                                    'employee_column': emp_col,
                                    'asset': asset,
                                    'asset_column': asset_col,
                                    'sheet': sheet_name,
                                    'metadata': {}
                                }
                                
                                # Add any additional context
                                for meta_col in ['date', 'job_code', 'location']:
                                    meta_cols = [
                                        orig_col for orig_col, norm_col in column_mapping.items()
                                        if norm_col == meta_col and orig_col in df.columns
                                    ]
                                    
                                    for col in meta_cols:
                                        if not pd.isna(row[col]):
                                            mapping['metadata'][meta_col] = row[col]
                                
                                result['mappings'].append(mapping)
        
        return result
    
    def save_parsing_results(self, parsed_result: Dict[str, Any], output_path: str = None) -> str:
        """
        Save parsing results to a JSON file
        
        Args:
            parsed_result (Dict[str, Any]): Result from parse_excel
            output_path (str, optional): Path to save the results file. If None, generates one.
            
        Returns:
            str: Path to the saved results file
        """
        if not parsed_result.get('success', False):
            logger.error(f"Cannot save unsuccessful parsing result")
            return None
        
        # Generate output path if not provided
        if output_path is None:
            file_name = os.path.basename(parsed_result.get('file_path', 'unknown'))
            file_base, _ = os.path.splitext(file_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join('data', 'processed', f"{file_base}_{timestamp}_parsed.json")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Prepare serializable result
        # Convert DataFrames to dict records
        serializable_result = parsed_result.copy()
        
        for sheet_name, sheet_data in serializable_result.get('sheets', {}).items():
            if 'data' in sheet_data and isinstance(sheet_data['data'], pd.DataFrame):
                sheet_data['data'] = sheet_data['data'].to_dict('records')
        
        # Save to file
        try:
            with open(output_path, 'w') as f:
                json.dump(serializable_result, f, indent=2, default=str)
            
            logger.info(f"Saved parsing results to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to save parsing results: {e}")
            return None