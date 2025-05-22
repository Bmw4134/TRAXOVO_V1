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

def normalize_time(time_str: str) -> str:
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

def load_csv_file(file_path: str) -> List[Dict]:
    """
    Load data from a CSV file, skipping fluff rows
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        list: List of data records (dictionaries)
    """
    logger.info(f"Loading CSV file: {file_path}")
    
    data = []
    skipped_rows = []
    
    try:
        # First read header row
        with open(file_path, 'r', newline='', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            headers = next(reader)
            
            # Skip if header row is fluff
            if is_fluff_row(headers):
                # Try to find the first non-fluff row to use as headers
                for row in reader:
                    if not is_fluff_row(row):
                        headers = row
                        break
            
            # Normalize headers
            headers = [h.strip() for h in headers]
        
        # Now read the data rows
        with open(file_path, 'r', newline='', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            
            row_num = 1  # Start from 1 for easier human reading (0 is header)
            for row in reader:
                row_num += 1
                
                # Skip fluff rows
                if is_fluff_row(row):
                    skipped_rows.append({
                        "file": os.path.basename(file_path),
                        "row": row_num,
                        "reason": "fluff_row",
                        "content": row
                    })
                    continue
                
                # Create record from row data
                record = {}
                for i, value in enumerate(row):
                    if i < len(headers):
                        # Skip empty values
                        if value is None or value.strip() == "":
                            continue
                            
                        # Normalize value
                        header = headers[i]
                        
                        # Handle special cases
                        if "time" in header.lower():
                            value = normalize_time(value)
                        elif "error" in value.lower() or value.lower() in ["n/a", "none", "unknown"]:
                            # Replace error strings with None for numeric fields
                            # For non-numeric fields, keep the original value
                            if any(num_key in header.lower() for num_key in ["amount", "count", "total", "id", "number"]):
                                value = None
                            
                        record[header] = value
                
                # Only add records with actual content
                if record:
                    data.append(record)
        
        logger.info(f"Loaded {len(data)} records from CSV, skipped {len(skipped_rows)} rows")
        
        # Log skipped rows
        log_skipped_rows(skipped_rows)
        
        return data
    
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
    
    data = []
    skipped_rows = []
    
    try:
        # List all sheets in the Excel file
        excel = pd.ExcelFile(file_path)
        sheet_names = excel.sheet_names
        
        # Select the best sheet for tabular data
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
        
        # Convert to dictionary records, skipping fluff rows
        for index, row in df.iterrows():
            row_dict = row.to_dict()
            
            if is_fluff_row(row_dict):
                skipped_rows.append({
                    "file": os.path.basename(file_path),
                    "sheet": best_sheet,
                    "row": index + 2,  # Excel row number (1-based, +1 for header)
                    "reason": "fluff_row",
                    "content": row_dict
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
            
            if clean_row:
                data.append(clean_row)
        
        logger.info(f"Loaded {len(data)} records from Excel, skipped {len(skipped_rows)} rows")
        
        # Log skipped rows
        log_skipped_rows(skipped_rows)
        
        return data
    
    except Exception as e:
        logger.error(f"Error loading Excel file {file_path}: {str(e)}")
        return []

def log_skipped_rows(skipped_rows: List[Dict]) -> None:
    """
    Log skipped rows to a JSONL file
    
    Args:
        skipped_rows: List of skipped row records
    """
    if not skipped_rows:
        return
    
    try:
        # Ensure log directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Write to the skipped rows log
        with open("logs/skipped_rows.jsonl", "a") as f:
            for row in skipped_rows:
                f.write(json.dumps(row) + "\n")
    except Exception as e:
        logger.error(f"Error logging skipped rows: {str(e)}")

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
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
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