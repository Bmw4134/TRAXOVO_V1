"""
Adaptive Excel Processor

This module provides functionality for intelligently processing Excel files
with varying formats, column names, and data structures.
"""

import re
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Union

logger = logging.getLogger(__name__)

class AdaptiveExcelProcessor:
    """
    Class for processing Excel files with varying formats
    """
    
    def __init__(self, file_path: str):
        """
        Initialize with an Excel file path
        
        Args:
            file_path: Path to the Excel file
        """
        self.file_path = file_path
        self.df = None
        self.sheet_names = []
        self.active_sheet = None
        self.column_mappings = {}
        
        # Load the file
        self._load_file()
    
    def _load_file(self) -> None:
        """Load the Excel file and get sheet names"""
        try:
            # Get all sheet names
            self.sheet_names = pd.ExcelFile(self.file_path).sheet_names
            
            # Load the first sheet by default
            if self.sheet_names:
                self.load_sheet(self.sheet_names[0])
            else:
                raise ValueError("No sheets found in the Excel file")
                
        except Exception as e:
            logger.error(f"Error loading Excel file {self.file_path}: {str(e)}")
            raise
    
    def load_sheet(self, sheet_name: str) -> pd.DataFrame:
        """
        Load a specific sheet from the Excel file
        
        Args:
            sheet_name: Name of the sheet to load
            
        Returns:
            DataFrame containing the sheet data
        """
        try:
            # Load the sheet into a DataFrame
            self.df = pd.read_excel(self.file_path, sheet_name=sheet_name)
            self.active_sheet = sheet_name
            
            # Clean column names
            self.df.columns = [str(col).strip() for col in self.df.columns]
            
            return self.df
        except Exception as e:
            logger.error(f"Error loading sheet {sheet_name}: {str(e)}")
            raise
    
    def identify_columns(self, column_patterns: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Identify columns based on patterns
        
        Args:
            column_patterns: Dictionary mapping column types to patterns
            
        Returns:
            Dictionary mapping column types to actual column names
        """
        if self.df is None:
            raise ValueError("No DataFrame loaded")
        
        # Reset column mappings
        self.column_mappings = {}
        
        # Iterate through column types and their patterns
        for col_type, patterns in column_patterns.items():
            for col in self.df.columns:
                col_lower = str(col).lower()
                
                # Check if any pattern matches
                if any(pattern.lower() in col_lower for pattern in patterns):
                    self.column_mappings[col_type] = col
                    break
        
        return self.column_mappings
    
    def get_column(self, col_type: str) -> Optional[str]:
        """
        Get the identified column name for a column type
        
        Args:
            col_type: The type of column to get
            
        Returns:
            The column name or None if not found
        """
        return self.column_mappings.get(col_type)
    
    def find_data_rows(self, start_pattern: Optional[str] = None, end_pattern: Optional[str] = None) -> Tuple[int, int]:
        """
        Identify the start and end rows of actual data
        
        Args:
            start_pattern: Pattern to identify the start of data
            end_pattern: Pattern to identify the end of data
            
        Returns:
            Tuple of (start_row, end_row)
        """
        if self.df is None:
            raise ValueError("No DataFrame loaded")
        
        # Default to the entire dataframe
        start_row = 0
        end_row = len(self.df) - 1
        
        # Find start row if pattern provided
        if start_pattern:
            for i, row in self.df.iterrows():
                # Convert row to string and check for pattern
                row_str = ' '.join(str(val) for val in row.values if pd.notna(val))
                if re.search(start_pattern, row_str, re.IGNORECASE):
                    start_row = i + 1  # Data starts after this row
                    break
        
        # Find end row if pattern provided
        if end_pattern:
            for i in range(start_row, len(self.df)):
                row = self.df.iloc[i]
                row_str = ' '.join(str(val) for val in row.values if pd.notna(val))
                if re.search(end_pattern, row_str, re.IGNORECASE):
                    end_row = i - 1  # Data ends before this row
                    break
        
        return start_row, end_row
    
    def normalize_data(self, column_mappings: Optional[Dict[str, str]] = None) -> pd.DataFrame:
        """
        Normalize the data using the identified columns
        
        Args:
            column_mappings: Optional override for column mappings
            
        Returns:
            DataFrame with normalized data
        """
        if self.df is None:
            raise ValueError("No DataFrame loaded")
        
        mappings = column_mappings or self.column_mappings
        if not mappings:
            raise ValueError("No column mappings defined")
        
        # Create a new DataFrame with the mapped columns
        result = pd.DataFrame()
        
        for target_col, source_col in mappings.items():
            if source_col in self.df.columns:
                result[target_col] = self.df[source_col]
        
        return result
    
    def clean_numeric_column(self, column_name: str) -> pd.Series:
        """
        Clean a numeric column by removing non-numeric characters
        
        Args:
            column_name: Name of the column to clean
            
        Returns:
            Series with cleaned numeric values
        """
        if self.df is None:
            raise ValueError("No DataFrame loaded")
        
        if column_name not in self.df.columns:
            raise ValueError(f"Column {column_name} not found")
        
        # Get the column data
        col_data = self.df[column_name]
        
        # Clean numeric values
        def clean_numeric(val):
            if pd.isna(val):
                return 0.0
            
            if isinstance(val, (int, float)):
                return float(val)
            
            # Convert to string and clean
            val_str = str(val)
            
            # Remove currency symbols and commas
            val_str = re.sub(r'[$,]', '', val_str)
            
            # Try to convert to float
            try:
                return float(val_str)
            except ValueError:
                return 0.0
        
        # Apply cleaning to each value
        return col_data.apply(clean_numeric)
    
    def find_matching_rows(self, df1: pd.DataFrame, df2: pd.DataFrame, key_column: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Find matching and non-matching rows between two DataFrames
        
        Args:
            df1: First DataFrame
            df2: Second DataFrame
            key_column: Column to use as the key for matching
            
        Returns:
            Tuple of (common_rows, only_in_df1, only_in_df2)
        """
        # Convert key column to string
        df1[key_column] = df1[key_column].astype(str)
        df2[key_column] = df2[key_column].astype(str)
        
        # Find common keys
        keys1 = set(df1[key_column])
        keys2 = set(df2[key_column])
        
        common_keys = keys1.intersection(keys2)
        only_df1_keys = keys1 - keys2
        only_df2_keys = keys2 - keys1
        
        # Filter DataFrames
        common_df1 = df1[df1[key_column].isin(common_keys)]
        common_df2 = df2[df2[key_column].isin(common_keys)]
        only_df1 = df1[df1[key_column].isin(only_df1_keys)]
        only_df2 = df2[df2[key_column].isin(only_df2_keys)]
        
        return common_df1, common_df2, only_df1, only_df2
    
    def compare_values(self, df1: pd.DataFrame, df2: pd.DataFrame, key_column: str, value_column: str) -> pd.DataFrame:
        """
        Compare values between two DataFrames
        
        Args:
            df1: First DataFrame
            df2: Second DataFrame
            key_column: Column to use as the key for matching
            value_column: Column to compare
            
        Returns:
            DataFrame with key, original value, new value, and difference
        """
        # Find matching rows
        common_df1, common_df2, only_df1, only_df2 = self.find_matching_rows(df1, df2, key_column)
        
        # Create result DataFrames
        changes = []
        
        # Additions (only in df2)
        for _, row in only_df2.iterrows():
            changes.append({
                key_column: row[key_column],
                'original_value': 0,
                'new_value': row[value_column],
                'difference': row[value_column],
                'change_type': 'Added'
            })
        
        # Deletions (only in df1)
        for _, row in only_df1.iterrows():
            changes.append({
                key_column: row[key_column],
                'original_value': row[value_column],
                'new_value': 0,
                'difference': -row[value_column],
                'change_type': 'Deleted'
            })
        
        # Modifications (in both but values differ)
        for key in common_df1[key_column]:
            val1 = common_df1[common_df1[key_column] == key][value_column].values[0]
            val2 = common_df2[common_df2[key_column] == key][value_column].values[0]
            
            # Check for significant difference
            if abs(val1 - val2) > 0.01:  # Allow for small floating point differences
                changes.append({
                    key_column: key,
                    'original_value': val1,
                    'new_value': val2,
                    'difference': val2 - val1,
                    'change_type': 'Modified'
                })
        
        # Create changes DataFrame
        if changes:
            changes_df = pd.DataFrame(changes)
            
            # Sort by change type and difference magnitude
            changes_df['abs_difference'] = changes_df['difference'].abs()
            changes_df = changes_df.sort_values(['change_type', 'abs_difference'], ascending=[True, False])
            changes_df = changes_df.drop(columns=['abs_difference'])
            
            return changes_df
        else:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=[key_column, 'original_value', 'new_value', 'difference', 'change_type'])