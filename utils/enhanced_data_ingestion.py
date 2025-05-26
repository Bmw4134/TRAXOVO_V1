"""
Enhanced Data Ingestion Module

This module provides utilities for loading and processing data files from various sources,
with smart format detection and data cleaning capabilities.
"""

import os
import re
import csv
import json
import logging
import pandas as pd
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def detect_header_rows(df):
    """
    Detect and skip header/fluff rows in uploaded files.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        int: Number of rows to skip
    """
    # Look for common header patterns
    for i, row in df.head(10).iterrows():
        row_str = ' '.join(str(val).lower() for val in row if pd.notna(val))
        
        # Check for data-like content (dates, times, driver names)
        if any(pattern in row_str for pattern in [
            'driver', 'vehicle', 'asset', 'time', 'date', 'location', 'job'
        ]) and not any(pattern in row_str for pattern in [
            'report', 'generated', 'summary', 'company', 'period'
        ]):
            return i
    
    return 0

def infer_file_type(file_obj):
    """
    Infer file type based on file name and contents with smart header detection.
    
    Args:
        file_obj: The file object
        
    Returns:
        str: Inferred file type or None if unknown
    """
    filename = file_obj.filename.lower()
    
    # Check file extension
    if filename.endswith('.csv'):
        # Try to determine CSV type from filename
        if any(term in filename for term in ['driving', 'driver']):
            return 'Driving History'
        elif any(term in filename for term in ['time_on_site', 'timeonsite', 'assettimeonsite']):
            return 'Assets Time On Site'
        elif any(term in filename for term in ['activity', 'activitydetail']):
            return 'Activity Detail'
        elif any(term in filename for term in ['timecard', 'hours']):
            return 'Timecard'
        else:
            return 'CSV Data'
    
    elif filename.endswith(('.xlsx', '.xls')):
        # Try to determine Excel type from filename
        if any(term in filename for term in ['timecard', 'hours', 'payroll']):
            return 'Timecard'
        elif any(term in filename for term in ['job', 'jobsite']):
            return 'Job Data'
        else:
            return 'Excel Data'
    
    # Could not determine file type
    return None

def clean_column_names(columns):
    """
    Clean column names for consistency.
    
    Args:
        columns: List of column names
        
    Returns:
        list: Cleaned column names
    """
    cleaned = []
    
    for col in columns:
        if not col:
            cleaned.append('unnamed')
            continue
        
        # Convert to string
        col = str(col).strip()
        
        # Replace spaces with underscores
        col = col.replace(' ', '_')
        
        # Remove special characters
        col = re.sub(r'[^\w_]', '', col)
        
        # Convert to lowercase
        col = col.lower()
        
        cleaned.append(col)
    
    return cleaned

def load_csv_file(file_path):
    """
    Load and parse a CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        list: List of records as dictionaries
    """
    try:
        # First, try to determine if the file has a header
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            # Read a sample of the file
            sample = f.read(4096)
            dialect = csv.Sniffer().sniff(sample)
            has_header = csv.Sniffer().has_header(sample)
            f.seek(0)
            
            # Use pandas to read the CSV
            if has_header:
                df = pd.read_csv(file_path, dialect=dialect)
                
                # Clean column names
                df.columns = clean_column_names(df.columns)
            else:
                # No header, use default column names
                df = pd.read_csv(file_path, dialect=dialect, header=None)
                df.columns = [f'col_{i}' for i in range(len(df.columns))]
        
        # Handle empty dataframe
        if df.empty:
            return []
        
        # Convert to list of dictionaries
        records = df.to_dict('records')
        
        # Clean up any NaN values
        for record in records:
            for key, value in list(record.items()):
                if pd.isna(value):
                    record[key] = None
        
        return records
    
    except Exception as e:
        logger.error(f"Error loading CSV file {file_path}: {str(e)}")
        return []

def load_excel_file(file_path):
    """
    Load and parse an Excel file.
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        list: List of records as dictionaries
    """
    try:
        # Load Excel file with pandas
        df = pd.read_excel(file_path)
        
        # Handle empty dataframe
        if df.empty:
            return []
        
        # Clean column names
        df.columns = clean_column_names(df.columns)
        
        # Convert to list of dictionaries
        records = df.to_dict('records')
        
        # Clean up any NaN values
        for record in records:
            for key, value in list(record.items()):
                if pd.isna(value):
                    record[key] = None
        
        return records
    
    except Exception as e:
        logger.error(f"Error loading Excel file {file_path}: {str(e)}")
        return []

def detect_date_format(date_str):
    """
    Detect the format of a date string.
    
    Args:
        date_str: Date string
        
    Returns:
        str: Date format or None if unknown
    """
    formats = [
        ('%Y-%m-%d', r'^\d{4}-\d{1,2}-\d{1,2}$'),
        ('%m/%d/%Y', r'^\d{1,2}/\d{1,2}/\d{4}$'),
        ('%d/%m/%Y', r'^\d{1,2}/\d{1,2}/\d{4}$'),
        ('%Y-%m-%d %H:%M:%S', r'^\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}$'),
        ('%m/%d/%Y %H:%M:%S', r'^\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{1,2}:\d{1,2}$'),
        ('%Y-%m-%dT%H:%M:%S', r'^\d{4}-\d{1,2}-\d{1,2}T\d{1,2}:\d{1,2}:\d{1,2}$')
    ]
    
    for fmt, pattern in formats:
        if re.match(pattern, date_str):
            try:
                datetime.strptime(date_str, fmt)
                return fmt
            except ValueError:
                continue
    
    return None

def extract_date_from_filename(filename):
    """
    Extract date from filename.
    
    Args:
        filename: Filename
        
    Returns:
        str: Date string in YYYY-MM-DD format or None if not found
    """
    # Common date formats in filenames
    patterns = [
        r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
        r'(\d{2}-\d{2}-\d{4})',  # MM-DD-YYYY or DD-MM-YYYY
        r'(\d{2}/\d{2}/\d{4})',  # MM/DD/YYYY or DD/MM/YYYY
        r'(\d{8})'               # YYYYMMDD
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            date_str = match.group(1)
            
            # Try to parse the date
            try:
                if pattern == r'(\d{4}-\d{2}-\d{2})':
                    # Already in YYYY-MM-DD format
                    return date_str
                
                elif pattern == r'(\d{2}-\d{2}-\d{4})':
                    # Convert MM-DD-YYYY or DD-MM-YYYY to YYYY-MM-DD
                    parts = date_str.split('-')
                    return f"{parts[2]}-{parts[0]}-{parts[1]}"
                
                elif pattern == r'(\d{2}/\d{2}/\d{4})':
                    # Convert MM/DD/YYYY or DD/MM/YYYY to YYYY-MM-DD
                    parts = date_str.split('/')
                    return f"{parts[2]}-{parts[0]}-{parts[1]}"
                
                elif pattern == r'(\d{8})':
                    # Convert YYYYMMDD to YYYY-MM-DD
                    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            
            except Exception:
                continue
    
    return None

def extract_metadata_from_file(file_path, file_type=None):
    """
    Extract metadata from file.
    
    Args:
        file_path: Path to the file
        file_type: Type of the file (optional)
        
    Returns:
        dict: Metadata
    """
    metadata = {
        'file_path': file_path,
        'file_name': os.path.basename(file_path),
        'file_size': os.path.getsize(file_path),
        'file_type': file_type or infer_file_type_from_path(file_path),
        'created_at': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
        'modified_at': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
    }
    
    # Extract date from filename
    date_str = extract_date_from_filename(metadata['file_name'])
    if date_str:
        metadata['date'] = date_str
    
    return metadata

def infer_file_type_from_path(file_path):
    """
    Infer file type from file path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: Inferred file type or None if unknown
    """
    filename = os.path.basename(file_path).lower()
    
    # Check file extension
    if filename.endswith('.csv'):
        # Try to determine CSV type from filename
        if any(term in filename for term in ['driving', 'driver']):
            return 'Driving History'
        elif any(term in filename for term in ['time_on_site', 'timeonsite', 'assettimeonsite']):
            return 'Assets Time On Site'
        elif any(term in filename for term in ['activity', 'activitydetail']):
            return 'Activity Detail'
        elif any(term in filename for term in ['timecard', 'hours']):
            return 'Timecard'
        else:
            return 'CSV Data'
    
    elif filename.endswith(('.xlsx', '.xls')):
        # Try to determine Excel type from filename
        if any(term in filename for term in ['timecard', 'hours', 'payroll']):
            return 'Timecard'
        elif any(term in filename for term in ['job', 'jobsite']):
            return 'Job Data'
        else:
            return 'Excel Data'
    
    # Could not determine file type
    return None

def process_file(file_path, file_type=None):
    """
    Process a file and extract its data.
    
    Args:
        file_path: Path to the file
        file_type: Type of the file (optional)
        
    Returns:
        tuple: (records, metadata)
    """
    # Extract metadata
    metadata = extract_metadata_from_file(file_path, file_type)
    
    # Determine file type if not provided
    if not file_type:
        file_type = metadata['file_type']
    
    # Load file based on type
    if file_path.endswith('.csv'):
        records = load_csv_file(file_path)
    elif file_path.endswith(('.xlsx', '.xls')):
        records = load_excel_file(file_path)
    else:
        records = []
    
    return records, metadata