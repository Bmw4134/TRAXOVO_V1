"""
TRAXORA GENIUS CORE | Enhanced Data Ingestion

This module provides advanced data ingestion capabilities for mixed-format Gauge reports,
handling both CSV and Excel formats with intelligent detection and normalization.
"""
import os
import csv
import json
import logging
import datetime
import pandas as pd
import numpy as np
import re
from typing import List, Dict, Any, Union, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
FLUFF_PATTERNS = [
    r"^[-—–]+$",  # Various dash characters
    r"^$",        # Empty string
    r"^#Error$",  # Error strings
    r"^N/A$",     # Not available
    r"^None$",    # None values
    r"^Unknown$"  # Unknown values
]

TIME_PATTERNS = [
    # 12-hour format with AM/PM and optional timezone
    r"(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)(?:\s*[A-Z]{1,3})?",
    # 24-hour format with optional timezone
    r"(\d{1,2}):(\d{2})(?:\s*[A-Z]{1,3})?"
]

# Asset/Vehicle ID column aliases (exact matches or contains)
ASSET_ID_COLUMN_ALIASES = [
    'asset_id', 'assetid', 'vehicle_id', 'vehicleid', 'asset', 'vehicle', 
    'asset no', 'vehicle no', 'unit', 'unit no', 'equipment', 'equipment no'
]

def is_fluff_row(row: Union[List, Dict]) -> bool:
    """
    Check if a row is a fluff row (header, separator, etc.)
    
    Args:
        row: The row to check
        
    Returns:
        bool: True if the row is a fluff row, False otherwise
    """
    if not row:
        return True
    
    # For list-type rows
    if isinstance(row, list):
        # Check if all values are empty or fluff
        for cell in row:
            cell_str = str(cell).strip() if cell is not None else ""
            if cell_str and not any(re.match(pattern, cell_str) for pattern in FLUFF_PATTERNS):
                return False
        return True
    
    # For dict-type rows
    elif isinstance(row, dict):
        # Check if all values are empty or fluff
        for key, value in row.items():
            value_str = str(value).strip() if value is not None else ""
            if value_str and not any(re.match(pattern, value_str) for pattern in FLUFF_PATTERNS):
                return False
        return True
    
    return False

def normalize_time(time_str: Optional[str]) -> Optional[str]:
    """
    Normalize time strings to 24-hour format
    
    Args:
        time_str: The time string to normalize
        
    Returns:
        str: The normalized time string in HH:MM format (24-hour)
    """
    if not time_str or not isinstance(time_str, str):
        return None
    
    time_str = time_str.strip()
    
    # Try 12-hour format first (with AM/PM)
    match = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)", time_str)
    if match:
        hour, minute, period = match.groups()
        hour = int(hour)
        minute = int(minute)
        
        # Convert to 24-hour format
        if period.upper() == "PM" and hour < 12:
            hour += 12
        elif period.upper() == "AM" and hour == 12:
            hour = 0
            
        return f"{hour:02d}:{minute:02d}"
    
    # Try 24-hour format
    match = re.match(r"(\d{1,2}):(\d{2})", time_str)
    if match:
        hour, minute = match.groups()
        hour = int(hour)
        minute = int(minute)
        
        return f"{hour:02d}:{minute:02d}"
    
    # Couldn't parse the time string
    logger.warning(f"Could not normalize time string: {time_str}")
    return None

def detect_tabular_sheet(df: pd.DataFrame) -> bool:
    """
    Detect if a DataFrame represents a tabular sheet
    
    Args:
        df: The DataFrame to check
        
    Returns:
        bool: True if the DataFrame is tabular, False otherwise
    """
    # A tabular sheet should have a reasonable number of columns and rows
    if df.shape[0] < 2 or df.shape[1] < 3:
        return False
    
    # Check for consistent data types in columns (excluding headers)
    for col in df.columns:
        unique_types = df[col].apply(type).nunique()
        if unique_types > 3:  # Allow for mixed types due to headers and nulls
            return False
    
    # Check for a reasonable number of non-null values
    non_null_density = df.count().sum() / (df.shape[0] * df.shape[1])
    if non_null_density < 0.5:  # At least 50% of cells should have values
        return False
    
    return True

def identify_asset_id_column(df: pd.DataFrame) -> Optional[str]:
    """
    Identify the asset/vehicle ID column in a DataFrame
    
    Args:
        df: The DataFrame to analyze
        
    Returns:
        str: The name of the asset ID column, or None if not found
    """
    # First, try to find an exact match in column names
    for col in df.columns:
        col_lower = str(col).lower()
        
        # Check for exact matches
        if col_lower in ASSET_ID_COLUMN_ALIASES:
            return col
        
        # Check for partial matches
        for alias in ASSET_ID_COLUMN_ALIASES:
            if alias in col_lower:
                return col
    
    # If no matches found, try to use the first column if it seems like an ID column
    if len(df.columns) > 0:
        first_col = df.columns[0]
        # Check if the first column contains ID-like values (alphanumeric with dashes or spaces)
        if df[first_col].dtype == 'object' and pd.notna(df[first_col]).sum() > 0:
            sample_values = df[first_col].dropna().astype(str)
            if all(re.match(r'^[A-Za-z0-9\-\s]+$', val) for val in sample_values.iloc[:5]):
                return first_col
    
    return None

def fill_down_asset_ids(df: pd.DataFrame, file_path: str) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Fill down blank asset IDs in the first column of a DataFrame,
    using Excel-style filling (last known value)
    
    Args:
        df: The DataFrame to process
        file_path: Path to the original file (for logging)
        
    Returns:
        tuple: (Processed DataFrame, List of fill-down patches)
    """
    # Skip if the DataFrame is empty
    if df.empty:
        return df, []
    
    # Try to identify the asset ID column
    asset_id_col = identify_asset_id_column(df)
    if not asset_id_col:
        # If we can't find a specific asset ID column, use the first column
        if len(df.columns) > 0:
            asset_id_col = df.columns[0]
        else:
            # No columns at all, just return the DataFrame unchanged
            return df, []
    
    # Track filled rows
    filled_rows = []
    
    # Make a copy of the DataFrame to avoid modifying the original
    df_filled = df.copy()
    
    # Get the index of the asset ID column for the nullity check
    col_idx = list(df.columns).index(asset_id_col)
    
    # Keep track of the last valid asset ID
    last_valid_id = None
    
    # Iterate through rows and fill down asset IDs
    for idx, row in df.iterrows():
        # Check if the asset ID is missing
        current_id = row[asset_id_col]
        
        if pd.isna(current_id) or str(current_id).strip() == '':
            # Check if there's data in adjacent columns (indicates a valid row that needs filling)
            has_data_in_other_cols = False
            for col_name, value in row.items():
                if col_name != asset_id_col and not (pd.isna(value) or str(value).strip() == ''):
                    has_data_in_other_cols = True
                    break
            
            # Only fill down if there's data in other columns and we have a valid ID to use
            if has_data_in_other_cols and last_valid_id is not None:
                # Fill down the asset ID
                df_filled.at[idx, asset_id_col] = last_valid_id
                
                # Record this fill-down for logging
                filled_rows.append({
                    "file": os.path.basename(file_path),
                    "row": idx + 2,  # Excel/CSV row number (1-based, +1 for header)
                    "type": "filldown_patch",
                    "column": asset_id_col,
                    "filled_value": last_valid_id
                })
        else:
            # Update the last valid ID
            last_valid_id = current_id
    
    # Log the filled rows
    if filled_rows:
        logger.info(f"Filled down {len(filled_rows)} blank {asset_id_col} cells in {os.path.basename(file_path)}")
    
    return df_filled, filled_rows

def process_dataframe(df: pd.DataFrame, file_path: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Process a DataFrame to extract records and handle missing asset IDs
    
    Args:
        df: The DataFrame to process
        file_path: Path to the original file (for logging)
        
    Returns:
        tuple: (List of data records, List of skipped rows and fill-down patches)
    """
    # Fill down blank asset IDs in the asset ID column
    df_filled, filled_rows = fill_down_asset_ids(df, file_path)
    
    # Extract records from the processed DataFrame
    records = []
    skipped_rows = []
    
    for idx, row in df_filled.iterrows():
        row_dict = row.to_dict()
        
        # Skip fluff rows
        if is_fluff_row(row_dict):
            skipped_rows.append({
                "file": os.path.basename(file_path),
                "row": idx + 2,  # Excel/CSV row number (1-based, +1 for header)
                "reason": "fluff_row",
                "content": {k: str(v) if not pd.isna(v) else "" for k, v in row_dict.items()}
            })
            continue
        
        # Clean and normalize values
        clean_row = {}
        for key, value in row_dict.items():
            if pd.isna(value):
                continue
            
            # Convert to string for further processing
            if isinstance(value, (int, float)):
                # Keep numbers as is
                clean_row[key] = value
            elif isinstance(value, (datetime.date, datetime.datetime)):
                # Format dates consistently
                clean_row[key] = value.isoformat()
            else:
                value_str = str(value).strip()
                
                # Skip error values for numeric fields
                if any(num_key in str(key).lower() for num_key in ["amount", "count", "total", "id", "number"]) and \
                   any(err_val in value_str.lower() for err_val in ["error", "n/a", "none", "unknown"]):
                    continue
                
                # Normalize time values
                if "time" in str(key).lower() and re.search(r"\d{1,2}:\d{2}", value_str):
                    clean_row[key] = normalize_time(value_str)
                else:
                    clean_row[key] = value_str
        
        # Add the cleaned record if it's not empty
        if clean_row:
            records.append(clean_row)
    
    # Combine skipped rows and filled rows for logging
    all_log_entries = filled_rows + skipped_rows
    
    return records, all_log_entries

def load_csv_file(file_path: str) -> List[Dict]:
    """
    Load data from a CSV file, handling blank asset IDs and skipping fluff rows
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        list: List of data records (dictionaries)
    """
    logger.info(f"Loading CSV file: {file_path}")
    
    try:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(file_path)
        
        # Process the DataFrame to extract records
        records, log_entries = process_dataframe(df, file_path)
        
        logger.info(f"Loaded {len(records)} records from CSV file {os.path.basename(file_path)}")
        
        # Log skipped rows and fill-down patches
        log_skipped_rows(log_entries)
        
        return records
    
    except Exception as e:
        logger.error(f"Error loading CSV file {file_path}: {str(e)}")
        return []

def load_excel_file(file_path: str) -> List[Dict]:
    """
    Load data from an Excel file, trying all sheets and using the most tabular one
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        list: List of data records (dictionaries)
    """
    logger.info(f"Loading Excel file: {file_path}")
    
    try:
        # List all sheets in the Excel file
        excel = pd.ExcelFile(file_path)
        sheet_names = excel.sheet_names
        
        # Check if "DrivingHistory" is in any sheet name
        driving_history_sheets = [sheet for sheet in sheet_names if "driving" in sheet.lower() or "history" in sheet.lower()]
        
        # If we found a DrivingHistory sheet, prioritize it
        if driving_history_sheets:
            sheet_to_use = driving_history_sheets[0]
            logger.info(f"Found DrivingHistory sheet: {sheet_to_use}")
            
            # Read the sheet
            df = pd.read_excel(file_path, sheet_name=sheet_to_use)
            
            # Process the DataFrame to extract records
            records, log_entries = process_dataframe(df, file_path)
            
            logger.info(f"Loaded {len(records)} records from Excel sheet '{sheet_to_use}' in {os.path.basename(file_path)}")
            
            # Log skipped rows and fill-down patches
            log_skipped_rows(log_entries)
            
            return records
        
        # Otherwise, select the best sheet for tabular data
        best_sheet = None
        best_score = 0
        
        for sheet_name in sheet_names:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Skip empty sheets
                if df.empty:
                    continue
                
                # Check if this sheet is tabular
                if detect_tabular_sheet(df):
                    # Calculate a "tabular score" based on non-null density and rows
                    non_null_density = df.count().sum() / (df.shape[0] * df.shape[1])
                    score = non_null_density * df.shape[0]
                    
                    if score > best_score:
                        best_score = score
                        best_sheet = sheet_name
            except Exception as e:
                logger.warning(f"Error reading sheet {sheet_name}: {str(e)}")
        
        if best_sheet is None:
            logger.warning(f"No tabular sheets found in {file_path}")
            return []
        
        logger.info(f"Using sheet '{best_sheet}' for data")
        
        # Read the best sheet
        df = pd.read_excel(file_path, sheet_name=best_sheet)
        
        # Process the DataFrame to extract records
        records, log_entries = process_dataframe(df, file_path)
        
        logger.info(f"Loaded {len(records)} records from Excel sheet '{best_sheet}' in {os.path.basename(file_path)}")
        
        # Log skipped rows and fill-down patches
        log_skipped_rows(log_entries)
        
        return records
    
    except Exception as e:
        logger.error(f"Error loading Excel file {file_path}: {str(e)}")
        return []

def log_skipped_rows(log_entries: List[Dict]) -> None:
    """
    Log skipped rows and fill-down patches to a JSONL file
    
    Args:
        log_entries: List of log entries (skipped rows and fill-down patches)
    """
    if not log_entries:
        return
    
    try:
        # Ensure log directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Write to the skipped rows log
        with open("logs/skipped_rows.jsonl", "a") as f:
            for entry in log_entries:
                f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.error(f"Error logging entries: {str(e)}")

def load_data_file(file_path: str) -> List[Dict]:
    """
    Load data from a file (CSV or Excel), detecting the file type
    
    Args:
        file_path: Path to the data file
        
    Returns:
        list: List of data records (dictionaries)
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return []
    
    file_name = os.path.basename(file_path)
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Check if filename contains driving history or asset time keywords
    is_driving_history = any(keyword in file_name.lower() 
                            for keyword in ['driving', 'history', 'timesite', 'timeonsite', 'driver'])
    
    logger.info(f"Loading {'DrivingHistory' if is_driving_history else 'regular'} file: {file_name}")
    
    if file_ext == ".csv":
        return load_csv_file(file_path)
    elif file_ext in [".xlsx", ".xls"]:
        return load_excel_file(file_path)
    else:
        logger.error(f"Unsupported file type: {file_ext}")
        return []

def batch_load_data_files(file_paths: List[str]) -> List[Dict]:
    """
    Load data from multiple files
    
    Args:
        file_paths: List of file paths
        
    Returns:
        list: Combined list of data records (dictionaries)
    """
    all_data = []
    
    for file_path in file_paths:
        data = load_data_file(file_path)
        if data:
            all_data.extend(data)
    
    return all_data