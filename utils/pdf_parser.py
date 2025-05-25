"""
PDF Parser Utility

This module provides functions to extract text from PDF files,
which can be used as an alternative data source for report generation.
"""

import os
import re
import io
import csv
import logging
import pandas as pd
from PyPDF2 import PdfReader

# Configure logging
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path):
    """
    Extract all text from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
    
    Returns:
        str: Extracted text content
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return None

def extract_structured_text(pdf_path):
    """
    Extract text from a PDF and attempt to identify structured data.
    
    Args:
        pdf_path (str): Path to the PDF file
    
    Returns:
        dict: Dictionary with extracted structured information
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return None
    
    # Define patterns for recognizing structured data
    date_pattern = r'(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})'
    time_pattern = r'(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)'
    driver_pattern = r'(?:Driver|Name|Employee):\s*([A-Za-z\s]+)'
    
    # Extract structured data
    structured_data = {
        'dates': re.findall(date_pattern, text),
        'times': re.findall(time_pattern, text),
        'possible_drivers': re.findall(driver_pattern, text)
    }
    
    return structured_data

def extract_table_like_data(pdf_path):
    """
    Extract text from PDF and attempt to identify table-like structures.
    This works by looking for consistent patterns in the text that might indicate rows of data.
    
    Args:
        pdf_path (str): Path to the PDF file
    
    Returns:
        list: List of possible data tables (as lists of rows)
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return []
    
    # Split into lines and look for table-like patterns
    lines = text.split('\n')
    tables = []
    current_table = []
    
    # Look for lines with multiple separators (spaces, tabs, or commas) that might be table rows
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            if current_table:
                # End of a table possibly
                if len(current_table) > 3:  # At least 3 rows to be considered a table
                    tables.append(current_table)
                current_table = []
            continue
        
        # Check if line looks like a table row
        parts = re.split(r'\s{2,}|\t|,', line)
        if len(parts) >= 3:  # At least 3 columns to be considered a table row
            current_table.append(parts)
    
    # Check if there's a table being built
    if current_table and len(current_table) > 3:
        tables.append(current_table)
    
    return tables

def convert_text_to_dataframe(text, delimiter=None):
    """
    Convert text with delimited format to a pandas DataFrame.
    
    Args:
        text (str): Delimited text
        delimiter (str, optional): Delimiter character. If None, auto-detect.
    
    Returns:
        DataFrame: Pandas DataFrame containing the parsed data
    """
    try:
        # Split text into lines
        lines = text.strip().split('\n')
        
        if not lines:
            return None
        
        # If no delimiter is specified, try to detect common ones
        if delimiter is None:
            for delim in [',', '\t', '|', ';']:
                if delim in lines[0]:
                    delimiter = delim
                    break
            
            # If still no delimiter, try splitting by multiple spaces
            if delimiter is None:
                delimiter = r'\s+'
        
        # Parse lines into CSV format
        csv_data = io.StringIO()
        csv_writer = csv.writer(csv_data)
        
        for line in lines:
            if delimiter == r'\s+':
                # Split by multiple spaces
                row = re.split(delimiter, line.strip())
            else:
                row = line.split(delimiter)
            
            # Skip empty rows
            if row and any(cell.strip() for cell in row):
                csv_writer.writerow(row)
        
        # Reset position for reading
        csv_data.seek(0)
        
        # Convert to DataFrame
        df = pd.read_csv(csv_data)
        return df
    
    except Exception as e:
        logger.error(f"Error converting text to DataFrame: {str(e)}")
        return None

def extract_driving_data_from_pdf(pdf_path):
    """
    Extract text from PDF and identify driving-related data.
    
    Args:
        pdf_path (str): Path to the PDF file
    
    Returns:
        dict: Dictionary with extracted driving data
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return None
    
    # Look for table-like structures
    tables = extract_table_like_data(pdf_path)
    
    # Look for specific driving-related patterns
    driver_pattern = r'Driver:\s*([A-Za-z\s]+)'
    vehicle_pattern = r'Vehicle[:\s]+([A-Za-z0-9\s\-]+)'
    start_time_pattern = r'Start(?:ed)?(?:\s+Time)?:\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)'
    end_time_pattern = r'End(?:ed)?(?:\s+Time)?:\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)'
    
    # Extract structured data
    driving_data = {
        'drivers': re.findall(driver_pattern, text),
        'vehicles': re.findall(vehicle_pattern, text),
        'start_times': re.findall(start_time_pattern, text),
        'end_times': re.findall(end_time_pattern, text),
        'tables': tables
    }
    
    return driving_data

def try_convert_pdf_to_csv(pdf_path, output_dir='pdf_extracted'):
    """
    Try to extract structured data from a PDF and save as CSV.
    
    Args:
        pdf_path (str): Path to the PDF file
        output_dir (str, optional): Directory to save the extracted data. Defaults to 'pdf_extracted'.
    
    Returns:
        list: List of paths to the saved CSV files
    """
    try:
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Get the base filename without extension
        base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        
        # Extract table-like data
        tables = extract_table_like_data(pdf_path)
        
        # Save each table as a CSV file
        csv_paths = []
        for i, table in enumerate(tables):
            if not table:
                continue
            
            # Convert to DataFrame and save as CSV
            headers = table[0] if len(table) > 0 else None
            data = table[1:] if len(table) > 1 else []
            
            if data:
                df = pd.DataFrame(data, columns=headers)
                csv_path = os.path.join(output_dir, f"{base_filename}_table_{i+1}.csv")
                df.to_csv(csv_path, index=False)
                csv_paths.append(csv_path)
        
        # If no tables were found, save structured text
        if not csv_paths:
            text = extract_text_from_pdf(pdf_path)
            if text:
                text_path = os.path.join(output_dir, f"{base_filename}_extracted.txt")
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                csv_paths.append(text_path)
        
        return csv_paths
    except Exception as e:
        logger.error(f"Error converting PDF to CSV: {str(e)}")
        return []