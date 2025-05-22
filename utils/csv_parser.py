"""
Advanced CSV Parser for Driver Reports

This module provides functions to parse complex CSV files with varying formats,
headers, and structures as used in the driving history and activity detail reports.
"""

import csv
import pandas as pd
import logging
from io import StringIO
import re

logger = logging.getLogger(__name__)

def detect_data_rows(file_path):
    """
    Detect where the actual data rows begin in a complex CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        tuple: (header_row_index, data_start_row_index, detected_columns)
    """
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    # Look for lines that have more fields and could be headers
    max_fields = 0
    header_row = 0
    data_start_row = 0
    potential_columns = []
    
    for i, line in enumerate(lines):
        fields = line.strip().split(',')
        field_count = len(fields)
        
        # Skip empty lines or metadata rows
        if field_count <= 3 and i < 10:
            continue
        
        # If this line has more fields than we've seen before
        if field_count > max_fields:
            max_fields = field_count
            header_row = i
            data_start_row = i + 1  # Data usually starts right after the header
            potential_columns = fields
        
        # Check if this looks like a data row after a header (has dates, numbers, etc.)
        if i > header_row and field_count >= max_fields * 0.8:
            # Detect if it has actual data patterns (dates, numbers, etc.)
            has_date = any(re.search(r'\d{1,2}/\d{1,2}/\d{2,4}', field) for field in fields)
            has_location = any(re.search(r'[A-Z]{2}|Road|St|Ave', field) for field in fields)
            has_coordinates = any(re.search(r'-?\d{1,3}\.\d+', field) for field in fields)
            
            if has_date or has_location or has_coordinates:
                data_start_row = i
                break
    
    return header_row, data_start_row, potential_columns

def parse_driving_history(file_path):
    """
    Parse driving history file with special handling for its complex format.
    
    Args:
        file_path: Path to the driving history file
        
    Returns:
        DataFrame: Parsed driving history data
    """
    try:
        # First pass: detect where the real data begins
        header_row, data_start_row, detected_columns = detect_data_rows(file_path)
        
        logger.info(f"Detected header at row {header_row}, data starts at row {data_start_row}")
        
        # Read the file with pandas, skipping to the header row
        df = pd.read_csv(file_path, 
                         skiprows=header_row,
                         header=0,
                         encoding='utf-8',
                         engine='python',
                         on_bad_lines='skip')
        
        # Clean up the column names
        df.columns = [str(col).strip() for col in df.columns]
        
        # Extract driver information from the 'Contact' column or similar
        if 'Contact' in df.columns:
            # Often contains format like "John Doe (12345)"
            df['Driver Name'] = df['Contact'].str.extract(r'(.*?)\s*\(', expand=False).str.strip()
            df['Employee ID'] = df['Contact'].str.extract(r'\((\d+)\)', expand=False)
        
        # Extract date and time information
        if 'EventDateTime' in df.columns:
            try:
                df['Date'] = pd.to_datetime(df['EventDateTime']).dt.date
                df['Time'] = pd.to_datetime(df['EventDateTime']).dt.time
            except:
                # If datetime parsing fails, try string-based extraction
                df['Date'] = df['EventDateTime'].str.extract(r'(\d{1,2}/\d{1,2}/\d{2,4})', expand=False)
                df['Time'] = df['EventDateTime'].str.extract(r'(\d{1,2}:\d{2}:\d{2}\s*[AP]M)', expand=False)
        
        return df
    
    except Exception as e:
        logger.error(f"Error parsing driving history file: {str(e)}")
        # Fallback: try a more robust approach for severely malformed files
        return parse_malformed_csv(file_path)

def parse_activity_detail(file_path):
    """
    Parse activity detail file with special handling for its complex format.
    
    Args:
        file_path: Path to the activity detail file
        
    Returns:
        DataFrame: Parsed activity detail data
    """
    try:
        # First pass: detect where the real data begins
        header_row, data_start_row, detected_columns = detect_data_rows(file_path)
        
        logger.info(f"Detected header at row {header_row}, data starts at row {data_start_row}")
        
        # Read the file with pandas, skipping to the header row
        df = pd.read_csv(file_path, 
                         skiprows=header_row,
                         header=0,
                         encoding='utf-8',
                         engine='python',
                         on_bad_lines='skip')
        
        # Clean up the column names
        df.columns = [str(col).strip() for col in df.columns]
        
        # Look for columns containing driver name, start time, end time
        for col in df.columns:
            if 'driver' in col.lower() or 'employee' in col.lower() or 'operator' in col.lower():
                df['Driver Name'] = df[col]
            
            if 'start' in col.lower() and 'time' in col.lower():
                df['Start Time'] = df[col]
            
            if 'end' in col.lower() and 'time' in col.lower() or 'stop' in col.lower() and 'time' in col.lower():
                df['End Time'] = df[col]
                
            if 'asset' in col.lower() or 'vehicle' in col.lower() or 'equipment' in col.lower():
                df['Asset'] = df[col]
                
            if 'job' in col.lower() and 'site' in col.lower() or 'location' in col.lower():
                df['Job Site'] = df[col]
        
        return df
    
    except Exception as e:
        logger.error(f"Error parsing activity detail file: {str(e)}")
        # Fallback: try a more robust approach for severely malformed files
        return parse_malformed_csv(file_path)

def parse_malformed_csv(file_path):
    """
    Parse a severely malformed CSV file using a line-by-line approach.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        DataFrame: Parsed data or empty DataFrame if parsing fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        # Find header line (the one with the most commas)
        header_index = 0
        max_commas = 0
        for i, line in enumerate(lines):
            commas = line.count(',')
            if commas > max_commas:
                max_commas = commas
                header_index = i
        
        # Extract header and data rows
        header = lines[header_index].strip().split(',')
        data_rows = []
        
        # Process each line after the header
        for i in range(header_index + 1, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
                
            # Split the line and make sure it matches the header length
            fields = line.split(',')
            if len(fields) >= len(header):
                data_rows.append(fields[:len(header)])  # Truncate extra fields
            else:
                # Pad missing fields
                data_rows.append(fields + [''] * (len(header) - len(fields)))
        
        # Create a DataFrame
        df = pd.DataFrame(data_rows, columns=header)
        return df
        
    except Exception as e:
        logger.error(f"Error in fallback CSV parsing: {str(e)}")
        # Return an empty DataFrame as a last resort
        return pd.DataFrame()