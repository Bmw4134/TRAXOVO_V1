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
        # First attempt with pandas default parser
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Successfully parsed {file_path} with standard parser")
            return df
        except pd.errors.ParserError as e:
            logger.warning(f"Standard parsing failed for {file_path}, trying robust method: {str(e)}")
        
        # If standard parsing fails, use custom robust parsing with sniffer
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # Try to detect dialect
        try:
            dialect = csv.Sniffer().sniff(content[:1000])
            logger.info(f"Detected dialect for {file_path}: delimiter='{dialect.delimiter}'")
        except csv.Error:
            logger.warning(f"Could not detect dialect for {file_path}, using comma delimiter")
            dialect = csv.excel
        
        # Find the maximum number of fields in any row
        max_fields = 0
        rows = []
        
        for line in content.splitlines():
            if line.strip():  # Skip empty lines
                reader = csv.reader([line], dialect)
                for row in reader:
                    max_fields = max(max_fields, len(row))
                    rows.append(row)
        
        logger.info(f"Maximum field count in {file_path}: {max_fields}")
        
        # Normalize rows to have consistent field count
        normalized_rows = []
        header = None
        
        for i, row in enumerate(rows):
            if i == 0:
                # This is the header row
                header = row
                # If header has fewer fields than max_fields, extend it
                if len(header) < max_fields:
                    header.extend([f'Field{j+1}' for j in range(len(header), max_fields)])
                normalized_rows.append(header)
            else:
                # Data row - pad to match max_fields
                normalized_row = row + [''] * (max_fields - len(row))
                normalized_rows.append(normalized_row)
        
        # If we have expected columns, use them
        if expected_columns and len(normalized_rows) > 0:
            if len(expected_columns) < max_fields:
                # Extend expected columns if needed
                expected_columns = expected_columns + [f'Field{j+1}' for j in range(len(expected_columns), max_fields)]
            elif len(expected_columns) > max_fields:
                # Truncate expected columns if they exceed max fields
                expected_columns = expected_columns[:max_fields]
            
            # Replace the header with expected columns
            normalized_rows[0] = expected_columns
            
        # Convert to DataFrame
        df = pd.DataFrame(normalized_rows[1:], columns=normalized_rows[0])
        logger.info(f"Successfully parsed {file_path} with robust method")
        return df
        
    except Exception as e:
        logger.error(f"Error parsing CSV file {file_path}: {str(e)}")
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