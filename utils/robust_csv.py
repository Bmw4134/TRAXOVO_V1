"""
Robust CSV Handling Module for TRAXORA

This module provides enhanced CSV parsing capabilities with error-resilience
for the TRAXORA fleet management system. It handles inconsistent field counts
and format issues in CSV files.
"""
import os
import csv
import logging
import pandas as pd
from io import StringIO
from typing import List, Dict, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)

def smart_parse_csv(file_path: str, expected_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Parse a CSV file with smart error handling and field count detection.
    
    Args:
        file_path (str): Path to the CSV file
        expected_columns (list): Optional list of expected column names
        
    Returns:
        DataFrame: Parsed DataFrame, potentially with adjusted columns
    """
    try:
        # Hyper robust CSV parsing for May 2025
        # First attempt: Use pandas with error_bad_lines=False
        try:
            # For pandas version compatibility
            try:
                # Newer pandas versions
                df = pd.read_csv(file_path, on_bad_lines='skip')
            except TypeError:
                # Older pandas versions
                df = pd.read_csv(file_path, error_bad_lines=False)
                
            if not df.empty:
                logger.info(f"Successfully parsed {file_path} with error skipping")
                
                # If we have expected columns and fewer columns than expected, add missing columns
                if expected_columns and len(df.columns) < len(expected_columns):
                    for col in expected_columns:
                        if col not in df.columns:
                            df[col] = None
                
                return df
        except Exception as e:
            logger.warning(f"Error skipping method failed for {file_path}: {str(e)}")
        
        # Second attempt: Use pd.read_csv with delimiters explicitly specified
        for delimiter in [',', ';', '\t', '|']:
            try:
                df = pd.read_csv(file_path, delimiter=delimiter)
                if not df.empty:
                    logger.info(f"Successfully parsed {file_path} with delimiter '{delimiter}'")
                    
                    # If we have expected columns and fewer columns than expected, add missing columns
                    if expected_columns and len(df.columns) < len(expected_columns):
                        for col in expected_columns:
                            if col not in df.columns:
                                df[col] = None
                    
                    return df
            except Exception:
                continue
        
        # Third attempt: Use ultra-robust manual parsing approach
        with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
            content = f.read()
        
        # Try multiple delimiters with csv.Sniffer
        dialect = None
        for delimiter in [',', ';', '\t', '|']:
            try:
                # Check if this delimiter creates at least some multicolumn rows
                test_reader = csv.reader(StringIO(content[:2000]), delimiter=delimiter)
                test_rows = list(test_reader)
                if any(len(row) > 1 for row in test_rows):
                    dialect = csv.excel
                    dialect.delimiter = delimiter
                    break
            except Exception:
                continue
        
        if dialect is None:
            logger.warning(f"Could not detect delimiter for {file_path}, using comma")
            dialect = csv.excel
        
        # Process the content line by line to handle inconsistencies
        reader = csv.reader(StringIO(content), dialect)
        rows = []
        max_fields = 0
        
        try:
            for row in reader:
                # Skip completely empty rows
                if not row or all(not cell.strip() for cell in row):
                    continue
                
                # Update max field count
                max_fields = max(max_fields, len(row))
                rows.append(row)
        except Exception as e:
            logger.warning(f"Error during CSV reading: {str(e)}")
        
        # Ensure we have some data
        if not rows:
            logger.warning(f"No valid data found in {file_path}")
            if expected_columns:
                return pd.DataFrame(columns=expected_columns)
            return pd.DataFrame()
        
        # Extract and normalize header
        header = rows[0] if rows else []
        if len(header) < max_fields:
            header.extend([f'Column{j+1}' for j in range(len(header), max_fields)])
        
        # Replace header with expected columns if provided
        if expected_columns:
            # Ensure expected_columns has at least max_fields elements
            if len(expected_columns) < max_fields:
                expected_columns = expected_columns + [f'Column{j+1}' for j in range(len(expected_columns), max_fields)]
            header = expected_columns[:max_fields]
        
        # Normalize all data rows to have consistent field count
        data_rows = []
        for row in rows[1:]:  # Skip header
            normalized_row = row + [''] * (max_fields - len(row))
            data_rows.append(normalized_row)
        
        # Create DataFrame using normalized data
        df = pd.DataFrame(data_rows, columns=header[:max_fields])
        logger.info(f"Successfully parsed {file_path} with ultra-robust method - found {len(df)} rows")
        return df
        
    except Exception as e:
        logger.error(f"All parsing methods failed for {file_path}: {str(e)}")
        # Return empty DataFrame with expected columns if provided
        if expected_columns:
            return pd.DataFrame(columns=expected_columns)
        return pd.DataFrame()

def parse_driving_history(file_path: str) -> pd.DataFrame:
    """
    Parse a driving history CSV file with expected column structure.
    
    Args:
        file_path (str): Path to the driving history CSV file
        
    Returns:
        DataFrame: Parsed driving history data
    """
    expected_columns = [
        'DriverID', 'DriverName', 'AssetID', 'AssetName', 'Date',
        'StartTime', 'EndTime', 'Duration', 'Distance', 'MaxSpeed',
        'AvgSpeed'
    ]
    return smart_parse_csv(file_path, expected_columns)

def parse_activity_detail(file_path: str) -> pd.DataFrame:
    """
    Parse an activity detail CSV file with expected column structure.
    
    Args:
        file_path (str): Path to the activity detail CSV file
        
    Returns:
        DataFrame: Parsed activity detail data
    """
    expected_columns = [
        'DriverID', 'DriverName', 'AssetID', 'AssetName', 'ActivityDate',
        'StartTime', 'EndTime', 'DurationMinutes', 'Activity', 'Location',
        'Latitude', 'Longitude', 'JobNumber', 'JobName', 'Notes'
    ]
    return smart_parse_csv(file_path, expected_columns)

def parse_asset_time_on_site(file_path: str) -> pd.DataFrame:
    """
    Parse an asset time on site CSV file with expected column structure.
    
    Args:
        file_path (str): Path to the asset time on site CSV file
        
    Returns:
        DataFrame: Parsed asset time on site data
    """
    expected_columns = [
        'AssetID', 'AssetName', 'JobSite', 'JobNumber', 'Date',
        'TimeIn', 'TimeOut', 'Duration', 'WorkHours', 'AfterHours'
    ]
    return smart_parse_csv(file_path, expected_columns)

def find_and_parse_csv_files(directory: str, file_type: str) -> pd.DataFrame:
    """
    Find and parse all CSV files of a specific type in a directory.
    
    Args:
        directory (str): Directory to search
        file_type (str): Type of files to parse ('driving_history', 'activity_detail', or 'asset_time_on_site')
        
    Returns:
        DataFrame: Combined DataFrame from all matching files
    """
    parser_map = {
        'driving_history': parse_driving_history,
        'activity_detail': parse_activity_detail,
        'asset_time_on_site': parse_asset_time_on_site
    }
    
    if file_type not in parser_map:
        logger.error(f"Unknown file type: {file_type}")
        return pd.DataFrame()
    
    parser_func = parser_map[file_type]
    pattern_map = {
        'driving_history': 'DrivingHistory',
        'activity_detail': 'ActivityDetail',
        'asset_time_on_site': 'AssetsTimeOnSite'
    }
    
    pattern = pattern_map.get(file_type, file_type)
    all_data = []
    
    if not os.path.exists(directory):
        logger.warning(f"Directory {directory} does not exist")
        return pd.DataFrame()
    
    for filename in os.listdir(directory):
        if pattern in filename and filename.lower().endswith('.csv'):
            file_path = os.path.join(directory, filename)
            logger.info(f"Processing {file_type} file: {file_path}")
            
            df = parser_func(file_path)
            if df is not None and not df.empty:
                all_data.append(df)
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    
    logger.warning(f"No valid {file_type} data found in {directory}")
    return pd.DataFrame()