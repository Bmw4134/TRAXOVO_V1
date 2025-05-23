"""
CSV Parser Fix for Fleet Reports

This module provides specialized parsing for Gauge fleet report CSV files that have a
non-standard format with metadata at the top.
"""

import csv
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

def parse_gauge_csv(file_path, date_range=None):
    """
    Parse a Gauge CSV file with metadata at the top.
    
    Args:
        file_path (str): Path to the CSV file
        date_range (list): Optional list of date strings to filter data by
        
    Returns:
        list: List of dictionaries with the parsed data
    """
    logger.info(f"Parsing Gauge CSV file: {file_path}")
    
    # Find the actual data start
    data_start_line = 0
    actual_headers = None
    with open(file_path, 'r', newline='', encoding='utf-8-sig') as f:
        line_num = 0
        for line in f:
            line_num += 1
            
            # Check if this line might be the headers
            if 'Contact' in line and 'EventDateTime' in line:
                data_start_line = line_num
                actual_headers = line.strip().split(',')
                logger.debug(f"Found DrivingHistory headers at line {line_num}: {actual_headers}")
                break
            
            # Check alternative headers for ActivityDetail
            if 'EventDateTimex' in line and 'Contact' in line:
                data_start_line = line_num
                actual_headers = line.strip().split(',')
                logger.debug(f"Found ActivityDetail headers at line {line_num}: {actual_headers}")
                break
                
            # Check alternative headers for TimeOnSite
            if 'Asset' in line and 'StartTime' in line and 'EndTime' in line:
                data_start_line = line_num
                actual_headers = line.strip().split(',')
                logger.debug(f"Found TimeOnSite headers at line {line_num}: {actual_headers}")
                break
    
    if data_start_line == 0:
        logger.warning(f"Could not find data headers in {file_path}")
        return []
    
    # Read the file again, skipping to the data section
    results = []
    with open(file_path, 'r', newline='', encoding='utf-8-sig') as f:
        # Skip to the headers
        for _ in range(data_start_line):
            next(f)
        
        # Use a lower-level reader because headers may have commas in quotes
        reader = csv.reader(f)
        header_row = next(reader)
        
        # Create a mapping for relevant fields
        field_map = {}
        driver_field = None
        timestamp_field = None
        
        for i, field in enumerate(header_row):
            field_map[i] = field.strip()
            if field.lower() == 'contact':
                driver_field = i
            elif field.lower() in ('eventdatetime', 'eventdatetimex'):
                timestamp_field = i
                
        if driver_field is None:
            logger.warning(f"Could not find driver field in {file_path}")
        
        if timestamp_field is None:
            logger.warning(f"Could not find timestamp field in {file_path}")
            
        # Process each row
        for row in reader:
            if not row:
                continue
                
            data = {}
            for i, value in enumerate(row):
                if i in field_map:
                    data[field_map[i]] = value.strip()
            
            # Extract driver name from Contact field (format: "Name (ID)")
            if driver_field is not None and len(row) > driver_field:
                contact = row[driver_field].strip()
                if contact:
                    # Try to extract just the name portion
                    if '(' in contact and ')' in contact:
                        name = contact.split('(')[0].strip()
                        data['Driver'] = name
                    else:
                        data['Driver'] = contact
            
            # Filter by date if requested
            if date_range and timestamp_field is not None and len(row) > timestamp_field:
                timestamp = row[timestamp_field].strip()
                if timestamp:
                    try:
                        # Try different date formats
                        date_obj = None
                        for fmt in ['%m/%d/%Y %I:%M:%S %p', '%m/%d/%Y %I:%M:%S%p', '%Y-%m-%d %H:%M:%S']:
                            try:
                                date_obj = datetime.strptime(timestamp, fmt)
                                break
                            except ValueError:
                                continue
                        
                        if date_obj:
                            date_str = date_obj.strftime('%Y-%m-%d')
                            if date_str not in date_range:
                                continue
                        
                    except Exception as e:
                        logger.debug(f"Could not parse timestamp {timestamp}: {str(e)}")
            
            # Add the processed data
            if 'Driver' in data:
                results.append(data)
                
    logger.info(f"Parsed {len(results)} records from {file_path}")
    return results

def parse_time_on_site_csv(file_path, date_range=None):
    """
    Parse a Time On Site CSV file with metadata at the top.
    
    Args:
        file_path (str): Path to the CSV file
        date_range (list): Optional list of date strings to filter data by
        
    Returns:
        list: List of dictionaries with the parsed data
    """
    logger.info(f"Parsing Time On Site CSV file: {file_path}")
    
    # Find the actual data start
    data_start_line = 0
    with open(file_path, 'r', newline='', encoding='utf-8-sig') as f:
        line_num = 0
        for line in f:
            line_num += 1
            
            # Check if this line might be the headers
            if 'Location' in line and 'Asset' in line and 'StartTime' in line:
                data_start_line = line_num
                logger.debug(f"Found TimeOnSite headers at line {line_num}")
                break
    
    if data_start_line == 0:
        logger.warning(f"Could not find data headers in {file_path}")
        return []
    
    # Read the file again, skipping to the data section
    try:
        # Skip the metadata rows
        df = pd.read_csv(file_path, skiprows=data_start_line-1)
        
        # Convert to list of dictionaries
        records = df.to_dict('records')
        
        # Extract driver names from Asset column (format typically includes driver name)
        for record in records:
            asset = record.get('Asset', '')
            if asset and isinstance(asset, str) and ' - ' in asset:
                # Format is typically like "#ID - NAME TYPE"
                parts = asset.split(' - ', 1)
                if len(parts) > 1:
                    name_parts = parts[1].split(' ', 1)
                    if len(name_parts) > 1:
                        driver_name = name_parts[0]
                        if len(name_parts) > 1 and len(name_parts[1].split()) > 0:
                            driver_name += ' ' + name_parts[1].split()[0]
                        record['Driver'] = driver_name
        
        # Filter by date if requested
        if date_range:
            filtered_records = []
            for record in records:
                date = record.get('Date')
                if date:
                    try:
                        if isinstance(date, str):
                            date_obj = datetime.strptime(date, '%m/%d/%Y')
                        else:
                            date_obj = date
                        date_str = date_obj.strftime('%Y-%m-%d')
                        if date_str in date_range:
                            filtered_records.append(record)
                    except Exception as e:
                        logger.debug(f"Could not parse date {date}: {str(e)}")
            records = filtered_records
        
        logger.info(f"Parsed {len(records)} records from {file_path}")
        return records
    except Exception as e:
        logger.error(f"Error parsing TimeOnSite file {file_path}: {str(e)}")
        return []