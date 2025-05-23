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
    
    # First, let's look at some sample lines to better understand the file structure
    sample_lines = []
    with open(file_path, 'r', newline='', encoding='utf-8-sig') as f:
        for i, line in enumerate(f):
            if i < 50:  # Get first 50 lines to sample
                sample_lines.append(line.strip())
            else:
                break
    
    # Identify the type of file and the data start line
    is_driving_history = 'DrivingHistory' in file_path
    is_activity_detail = 'ActivityDetail' in file_path
    is_time_on_site = 'TimeOnSite' in file_path or 'AssetsTimeOnSite' in file_path
    
    # Look for headers based on file type
    actual_data_line = None
    header_line = None
    
    # For DrivingHistory files
    if is_driving_history:
        for i, line in enumerate(sample_lines):
            # DrivingHistory headers typically contain these fields
            if 'Textbox53' in line and 'Contact' in line and 'EventDateTime' in line:
                header_line = i
                actual_data_line = i + 1
                logger.debug(f"Found DrivingHistory headers at line {header_line}: {line}")
                break
            # Alternative header format
            elif 'Asset' in line and 'Contact' in line and 'Timestamp' in line:
                header_line = i
                actual_data_line = i + 1
                logger.debug(f"Found alternative DrivingHistory headers at line {header_line}: {line}")
                break
    
    # For ActivityDetail files
    elif is_activity_detail:
        for i, line in enumerate(sample_lines):
            # ActivityDetail headers typically contain these fields
            if 'AssetLabel' in line and 'Contact' in line:
                header_line = i
                actual_data_line = i + 1
                logger.debug(f"Found ActivityDetail headers at line {header_line}: {line}")
                break
            # Alternative header format
            elif 'Asset' in line and 'Driver' in line and 'Timestamp' in line:
                header_line = i
                actual_data_line = i + 1
                logger.debug(f"Found alternative ActivityDetail headers at line {header_line}: {line}")
                break
    
    # If we couldn't identify the header line, look for common patterns
    if header_line is None:
        for i, line in enumerate(sample_lines):
            # Look for common field names that indicate the header row
            if ('Contact' in line or 'Driver' in line) and ('Timestamp' in line or 'DateTime' in line):
                header_line = i
                actual_data_line = i + 1
                logger.debug(f"Found generic headers at line {header_line}: {line}")
                break
    
    # If we still can't find a header, let's try a more aggressive approach
    if header_line is None:
        # For GaugeHR, headers often come after metadata which contains "ReportParameters" and "Values"
        metadata_section = False
        for i, line in enumerate(sample_lines):
            if "ReportParameters" in line and "Values" in line:
                metadata_section = True
            # The real data often starts after a blank line following metadata
            elif metadata_section and not line:
                # The next non-empty line could be headers
                for j in range(i+1, len(sample_lines)):
                    if sample_lines[j]:  # Non-empty line
                        header_line = j
                        actual_data_line = j + 1
                        logger.debug(f"Found potential header after metadata at line {header_line}: {sample_lines[j]}")
                        break
                if header_line is not None:
                    break
    
    # If we still haven't found headers, look for column-like structures
    if header_line is None:
        for i, line in enumerate(sample_lines):
            fields = line.split(',')
            if len(fields) > 5:  # Typical CSV has many columns
                potential_header = True
                for field in fields:
                    # Headers typically don't have many numeric values
                    if field.strip().replace('.', '').isdigit():
                        potential_header = False
                        break
                if potential_header:
                    header_line = i
                    actual_data_line = i + 1
                    logger.debug(f"Found potential structured header at line {header_line}: {line}")
                    break
    
    if header_line is None:
        logger.warning(f"Could not find header line in {file_path}. Using first line as fallback.")
        header_line = 0
        actual_data_line = 1
    
    # Now, let's re-read the file and process it using our identified header line
    results = []
    with open(file_path, 'r', newline='', encoding='utf-8-sig') as f:
        # Skip to the header line
        for _ in range(header_line):
            next(f)
        
        # Read the header
        reader = csv.reader(f)
        header_row = next(reader)
        
        # Create a mapping for relevant fields
        field_map = {}
        driver_field_idx = None
        timestamp_field_idx = None
        
        for i, field in enumerate(header_row):
            field = field.strip()
            field_map[i] = field
            
            # Look for driver field
            if field.lower() == 'contact' or field.lower() == 'driver':
                driver_field_idx = i
                logger.debug(f"Found driver field at index {i}: {field}")
                
            # Look for timestamp field
            if any(time_word in field.lower() for time_word in 
                  ['timestamp', 'eventdatetime', 'eventdatetimex', 'date']):
                timestamp_field_idx = i
                logger.debug(f"Found timestamp field at index {i}: {field}")
        
        # If we failed to find critical fields, try a more aggressive approach
        if driver_field_idx is None:
            logger.warning(f"No driver field found in header. Looking in all rows for driver info.")
            for i, field in enumerate(header_row):
                # Name or contact fields often contain driver information
                if any(name_word in field.lower() for name_word in 
                      ['name', 'employee', 'person', 'operator']):
                    driver_field_idx = i
                    logger.debug(f"Found potential driver field at index {i}: {field}")
                    break
        
        if timestamp_field_idx is None:
            logger.warning(f"No timestamp field found in header. Looking for date/time field.")
            for i, field in enumerate(header_row):
                # Date or time fields can help identify records
                if any(date_word in field.lower() for date_word in 
                      ['date', 'time', 'datetime', 'period']):
                    timestamp_field_idx = i
                    logger.debug(f"Found potential timestamp field at index {i}: {field}")
                    break
        
        # Process each row of data
        row_count = 0
        driver_count = 0
        for row in reader:
            row_count += 1
            if not row or len(row) <= 1:  # Skip empty rows
                continue
                
            data = {}
            for i, value in enumerate(row):
                if i < len(field_map):
                    field_name = field_map[i]
                    if field_name:  # Skip empty field names
                        data[field_name] = value.strip()
            
            # Extract driver name from the identified field
            driver_name = None
            if driver_field_idx is not None and len(row) > driver_field_idx:
                contact = row[driver_field_idx].strip()
                if contact:
                    # Try to extract just the name portion from formats like "Name (ID)"
                    if '(' in contact and ')' in contact:
                        driver_name = contact.split('(')[0].strip()
                    else:
                        driver_name = contact
                    
                    data['Driver'] = driver_name
                    driver_count += 1
            
            # If no driver field identified but we're processing DrivingHistory,
            # try to extract driver from asset name
            if driver_name is None and is_driving_history:
                for field, value in data.items():
                    if isinstance(value, str) and ' - ' in value and any(word in field.lower() for word in ['asset', 'vehicle', 'equipment']):
                        parts = value.split(' - ', 1)
                        if len(parts) > 1:
                            driver_name = parts[1].split(' ')[0]  # Take first part after the dash
                            if len(parts[1].split(' ')) > 1:
                                driver_name += ' ' + parts[1].split(' ')[1]  # Add second part if available
                            data['Driver'] = driver_name
                            driver_count += 1
                            break
            
            # Filter by date range if provided
            include_record = True
            if date_range and timestamp_field_idx is not None and len(row) > timestamp_field_idx:
                timestamp = row[timestamp_field_idx].strip()
                date_str = None
                
                if timestamp:
                    try:
                        # Try different date formats
                        date_obj = None
                        for fmt in ['%m/%d/%Y %I:%M:%S %p', '%m/%d/%Y %I:%M:%S%p', 
                                   '%Y-%m-%d %H:%M:%S', '%m/%d/%Y', '%Y-%m-%d']:
                            try:
                                date_obj = datetime.strptime(timestamp, fmt)
                                break
                            except ValueError:
                                continue
                        
                        if date_obj:
                            date_str = date_obj.strftime('%Y-%m-%d')
                            if date_str not in date_range:
                                include_record = False
                    except Exception as e:
                        logger.debug(f"Could not parse timestamp {timestamp}: {str(e)}")
            
            # Only include records with driver information
            if include_record and 'Driver' in data:
                results.append(data)
        
        logger.info(f"Processed {row_count} rows with {driver_count} driver entries")
        logger.info(f"Parsed {len(results)} valid records from {file_path}")
        
        if len(results) == 0:
            logger.warning(f"No valid records found in {file_path} - check file format and parser logic")
            
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