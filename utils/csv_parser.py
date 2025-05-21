"""
Enhanced CSV Parser for TRAXORA

This module provides robust CSV parsing functions that can handle inconsistent field counts
and format issues in CSV files, critical for the GENIUS CORE CONTINUITY MODE.
"""
import os
import csv
import logging
import pandas as pd
from io import StringIO

logger = logging.getLogger(__name__)

def robust_csv_parse(file_path, expected_columns=None, infer_columns=True):
    """
    Parse a CSV file with tolerance for inconsistent field counts.
    
    Args:
        file_path (str): Path to the CSV file
        expected_columns (list): List of expected column names
        infer_columns (bool): Whether to try to infer column names from the first line
        
    Returns:
        DataFrame or None: Parsed DataFrame or None if parsing failed
    """
    try:
        # First try with pandas standard parser
        try:
            df = pd.read_csv(file_path)
            return df
        except pd.errors.ParserError as e:
            logger.warning(f"Standard parsing failed, trying robust method: {str(e)}")
        
        # If standard parsing fails, use custom robust parsing
        raw_data = []
        max_fields = 0
        
        # First pass to determine max field count
        with open(file_path, 'r', newline='', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if i == 0 and infer_columns:
                    # Store header row
                    header = row
                max_fields = max(max_fields, len(row))
                raw_data.append(row)
        
        # Create normalized data with consistent field count
        normalized_data = []
        for row in raw_data:
            # Pad row to max_fields length
            normalized_row = row + [''] * (max_fields - len(row))
            normalized_data.append(normalized_row)
        
        # Convert to DataFrame
        if infer_columns and len(normalized_data) > 0:
            # Use header from first row, extending if needed
            header = normalized_data[0]
            if expected_columns:
                # Use expected columns if provided
                if len(expected_columns) < max_fields:
                    # Extend expected columns if needed
                    expected_columns = expected_columns + [f'Column{i+1}' for i in range(len(expected_columns), max_fields)]
                elif len(expected_columns) > max_fields:
                    # Truncate expected columns if needed
                    expected_columns = expected_columns[:max_fields]
                header = expected_columns
            data = normalized_data[1:]  # Skip header row
            df = pd.DataFrame(data, columns=header)
        else:
            # No header inference, use generic column names
            columns = [f'Column{i+1}' for i in range(max_fields)]
            df = pd.DataFrame(normalized_data, columns=columns)
        
        return df
    
    except Exception as e:
        logger.error(f"Error parsing CSV file {file_path}: {str(e)}")
        return None

def parse_activity_detail(file_path):
    """
    Parse activity detail CSV file with specific expected columns.
    
    Args:
        file_path (str): Path to the activity detail CSV file
        
    Returns:
        DataFrame or None: Parsed DataFrame or None if parsing failed
    """
    expected_columns = [
        'DriverID', 'DriverName', 'AssetID', 'AssetName', 'ActivityDate',
        'StartTime', 'EndTime', 'DurationMinutes', 'Activity', 'Location',
        'Latitude', 'Longitude', 'JobNumber', 'JobName', 'Notes'
    ]
    return robust_csv_parse(file_path, expected_columns=expected_columns)

def parse_driving_history(file_path):
    """
    Parse driving history CSV file with specific expected columns.
    
    Args:
        file_path (str): Path to the driving history CSV file
        
    Returns:
        DataFrame or None: Parsed DataFrame or None if parsing failed
    """
    expected_columns = [
        'DriverID', 'DriverName', 'AssetID', 'AssetName', 'Date',
        'StartTime', 'EndTime', 'Duration', 'Distance', 'MaxSpeed',
        'AvgSpeed'
    ]
    return robust_csv_parse(file_path, expected_columns=expected_columns)

def extract_csv_data(directory, pattern, parser_func):
    """
    Extract data from all CSV files in a directory matching a pattern.
    
    Args:
        directory (str): Directory to search for CSV files
        pattern (str): Pattern to match in file names
        parser_func (function): Function to parse each file
        
    Returns:
        DataFrame: Combined DataFrame from all matching files
    """
    all_data = []
    
    if not os.path.exists(directory):
        logger.warning(f"Directory {directory} does not exist")
        return pd.DataFrame()
    
    for filename in os.listdir(directory):
        if pattern in filename.lower() and filename.endswith('.csv'):
            file_path = os.path.join(directory, filename)
            logger.info(f"Processing file: {file_path}")
            
            df = parser_func(file_path)
            if df is not None and not df.empty:
                all_data.append(df)
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()