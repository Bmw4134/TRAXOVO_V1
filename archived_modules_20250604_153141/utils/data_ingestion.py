"""
TRAXORA Data Ingestion Module

This module provides robust data ingestion capabilities for multiple file formats,
with intelligent detection of data structures and automatic handling of various
Gauge report formats.
"""
import os
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Union, Optional, Tuple
import re

logger = logging.getLogger(__name__)

class DataIngestionError(Exception):
    """Exception raised for errors during data ingestion process"""
    pass

def is_valid_tabular_data(df: pd.DataFrame, min_columns: int = 3, min_rows: int = 5) -> bool:
    """
    Check if a DataFrame contains valid tabular data
    
    Args:
        df (DataFrame): DataFrame to check
        min_columns (int): Minimum number of columns required
        min_rows (int): Minimum number of rows required
        
    Returns:
        bool: True if DataFrame contains valid tabular data
    """
    # Check if DataFrame has minimum dimensions
    if df.shape[0] < min_rows or df.shape[1] < min_columns:
        return False
    
    # Check if DataFrame has more than 50% non-null values
    if df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) > 0.5:
        return False
    
    # Check if all columns are not NaN/None
    if df.columns.isnull().any():
        return False
    
    return True

def detect_header_row(df: pd.DataFrame, max_header_row: int = 10) -> int:
    """
    Detect the row that contains headers in the DataFrame
    
    Args:
        df (DataFrame): DataFrame to check
        max_header_row (int): Maximum row to check for headers
        
    Returns:
        int: Row index that contains headers, or -1 if not found
    """
    # Check each row up to max_header_row
    for i in range(min(max_header_row, df.shape[0])):
        row = df.iloc[i]
        
        # Check if row has mostly string values (potential headers)
        string_count = sum(1 for x in row if isinstance(x, str))
        if string_count / len(row) > 0.7:
            # Check if strings are relatively short (typical for headers)
            avg_len = sum(len(str(x)) for x in row if isinstance(x, str)) / string_count
            if avg_len < 30:
                return i
    
    return -1

def find_valid_excel_sheet(file_path: str) -> Tuple[int, int]:
    """
    Find the first valid sheet and header row in an Excel file
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        tuple: (sheet_index, header_row_index)
    """
    # Get all sheet names
    try:
        xl = pd.ExcelFile(file_path)
        sheet_names = xl.sheet_names
    except Exception as e:
        logger.error(f"Error reading Excel file {file_path}: {str(e)}")
        raise DataIngestionError(f"Error reading Excel file: {str(e)}")
    
    # Check each sheet for valid data
    for sheet_idx, sheet_name in enumerate(sheet_names):
        try:
            # Read first 20 rows to check for headers
            preview_df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=20)
            
            # Skip empty or non-tabular sheets
            if preview_df.empty or preview_df.shape[1] < 3:
                continue
            
            # Detect header row
            header_row = detect_header_row(preview_df)
            if header_row >= 0:
                return sheet_idx, header_row
            
            # If no header row detected but data looks tabular, use first row
            if is_valid_tabular_data(preview_df):
                return sheet_idx, 0
        except Exception as e:
            logger.warning(f"Error checking sheet {sheet_name} in {file_path}: {str(e)}")
            continue
    
    # Default to second sheet (index 1) if available, otherwise first sheet
    if len(sheet_names) > 1:
        return 1, 0
    elif len(sheet_names) > 0:
        return 0, 0
    
    raise DataIngestionError(f"No valid sheets found in Excel file {file_path}")

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a DataFrame by handling common issues in Gauge reports
    
    Args:
        df (DataFrame): DataFrame to clean
        
    Returns:
        DataFrame: Cleaned DataFrame
    """
    # Make a copy to avoid modifying the original
    df_clean = df.copy()
    
    # Replace problematic values with NaN
    error_values = ['#Error', '#N/A', '#VALUE!', '—', '-', 'N/A', 'NA', 'Unknown']
    for val in error_values:
        df_clean.replace(val, np.nan, inplace=True)
    
    # Replace empty strings with NaN
    df_clean.replace('', np.nan, inplace=True)
    
    # Clean column names
    df_clean.columns = [str(col).strip() for col in df_clean.columns]
    
    # Normalize time values (e.g., "03:45 PM CT" to "15:45:00")
    time_pattern = re.compile(r'(\d{1,2}):(\d{2})\s*(AM|PM)(?:\s+\w+)?', re.IGNORECASE)
    
    for col in df_clean.columns:
        # Only process string columns
        if df_clean[col].dtype == 'object':
            # Check if column has time values
            sample = df_clean[col].dropna().astype(str).head(10).tolist()
            has_time = any(time_pattern.search(str(val)) for val in sample)
            
            if has_time:
                df_clean[col] = df_clean[col].apply(lambda x: normalize_time(x) if isinstance(x, str) else x)
    
    return df_clean

def normalize_time(time_str: str) -> str:
    """
    Normalize time strings like "03:45 PM CT" to "15:45:00"
    
    Args:
        time_str (str): Time string to normalize
        
    Returns:
        str: Normalized time string
    """
    if not isinstance(time_str, str):
        return time_str
    
    time_pattern = re.compile(r'(\d{1,2}):(\d{2})\s*(AM|PM)(?:\s+\w+)?', re.IGNORECASE)
    match = time_pattern.search(time_str)
    
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        ampm = match.group(3).upper()
        
        # Convert to 24-hour format
        if ampm == 'PM' and hour < 12:
            hour += 12
        elif ampm == 'AM' and hour == 12:
            hour = 0
        
        return f"{hour:02d}:{minute:02d}:00"
    
    return time_str

def load_excel_file(file_path: str) -> pd.DataFrame:
    """
    Load data from an Excel file with intelligent sheet and header detection
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        DataFrame: Loaded data
    """
    logger.info(f"Loading Excel file: {file_path}")
    
    try:
        # Find valid sheet and header row
        sheet_idx, header_row = find_valid_excel_sheet(file_path)
        
        # Get sheet name from index
        xl = pd.ExcelFile(file_path)
        sheet_name = xl.sheet_names[sheet_idx]
        
        logger.info(f"Using sheet '{sheet_name}' (index {sheet_idx}) with header row {header_row}")
        
        # Load the data with the detected sheet and header row
        if header_row > 0:
            df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=header_row, header=0)
        else:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # Clean the data
        df = clean_dataframe(df)
        
        return df
    
    except Exception as e:
        logger.error(f"Error loading Excel file {file_path}: {str(e)}")
        raise DataIngestionError(f"Error loading Excel file: {str(e)}")

def load_csv_file(file_path: str) -> pd.DataFrame:
    """
    Load data from a CSV file with intelligent header detection
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        DataFrame: Loaded data
    """
    logger.info(f"Loading CSV file: {file_path}")
    
    try:
        # First try to load with no skipped rows
        df_preview = pd.read_csv(file_path, nrows=10)
        
        # Check if first row is likely headers
        if is_valid_tabular_data(df_preview):
            logger.info(f"Loading CSV with headers in first row")
            df = pd.read_csv(file_path)
        else:
            # Try skipping 5 rows
            logger.info(f"Loading CSV and skipping first 5 rows")
            df = pd.read_csv(file_path, skiprows=5)
        
        # Clean the data
        df = clean_dataframe(df)
        
        return df
    
    except Exception as e:
        logger.error(f"Error loading CSV file {file_path}: {str(e)}")
        raise DataIngestionError(f"Error loading CSV file: {str(e)}")

def load_gauge_file(file_path: str) -> pd.DataFrame:
    """
    Load data from a Gauge file (Excel or CSV) with intelligent format detection
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        DataFrame: Loaded data
    """
    if not os.path.exists(file_path):
        raise DataIngestionError(f"File not found: {file_path}")
    
    # Determine file type
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.xlsx' or file_ext == '.xls':
        return load_excel_file(file_path)
    elif file_ext == '.csv':
        return load_csv_file(file_path)
    else:
        raise DataIngestionError(f"Unsupported file type: {file_ext}")

def load_gauge_files(file_paths: List[str]) -> Dict[str, pd.DataFrame]:
    """
    Load data from multiple Gauge files
    
    Args:
        file_paths (list): List of file paths
        
    Returns:
        dict: Dictionary of file names and loaded DataFrames
    """
    results = {}
    
    for file_path in file_paths:
        try:
            file_name = os.path.basename(file_path)
            results[file_name] = load_gauge_file(file_path)
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            results[file_name] = None
    
    return results