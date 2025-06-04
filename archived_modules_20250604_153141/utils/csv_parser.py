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
    
    # First pass: find the line with the most comma-separated fields (likely the header)
    for i, line in enumerate(lines):
        # Handle quoted fields correctly
        fields = list(csv.reader([line]))[0]  # Parse line using csv module
        field_count = len(fields)
        
        # Skip empty lines or minimal metadata rows
        if field_count <= 3 and i < 10:
            continue
        
        # If this line has more fields than we've seen before
        if field_count > max_fields:
            max_fields = field_count
            header_row = i
            data_start_row = i + 1  # Data usually starts right after the header
            potential_columns = fields
    
    # Special handling for Driving History files which often have metadata headers
    # Look for common header names that indicate this is the real header row
    header_keywords = ['driver', 'vehicle', 'asset', 'time', 'date', 'location', 'event', 'contact']
    for i in range(max(0, header_row-5), min(len(lines), header_row+10)):
        # Skip empty lines
        if not lines[i].strip():
            continue
            
        fields = list(csv.reader([lines[i]]))[0]  # Parse line using csv module
        field_str = ','.join(fields).lower()
        
        # Check if this line contains multiple header keywords
        keyword_count = sum(1 for keyword in header_keywords if keyword in field_str)
        if keyword_count >= 2 and len(fields) >= max_fields * 0.7:
            header_row = i
            data_start_row = i + 1
            potential_columns = fields
            break
    
    # Second pass: identify the actual data rows
    data_pattern_matches = 0
    for i in range(data_start_row, min(len(lines), data_start_row + 15)):
        # Skip empty lines
        if not lines[i].strip():
            continue
            
        fields = list(csv.reader([lines[i]]))[0]  # Parse line using csv module
        
        # Check if this looks like a data row (has dates, numbers, etc.)
        has_date = any(re.search(r'\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}', field) for field in fields)
        has_time = any(re.search(r'\d{1,2}:\d{2}(:\d{2})?(\s*[AP]M)?', field) for field in fields)
        has_name = any(re.search(r'[A-Z][a-z]+ [A-Z][a-z]+', field) for field in fields)
        has_numeric = any(re.search(r'^\d+(\.\d+)?$', field) for field in fields)
        
        if (has_date or has_time or has_name) and has_numeric:
            data_pattern_matches += 1
            if data_pattern_matches == 1:  # First data row
                data_start_row = i
            
        # If we've found 2+ rows matching data patterns, we're confident
        if data_pattern_matches >= 2:
            break
    
    logger.debug(f"CSV Detection: header_row={header_row}, data_start_row={data_start_row}, columns={potential_columns}")
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
                         on_bad_lines='skip',
                         low_memory=False)
        
        # Clean up the column names
        df.columns = [str(col).strip() for col in df.columns]
        
        # Check if dataframe is empty or only has header
        if df.empty or len(df) <= 1:
            logger.warning(f"Empty dataframe after initial parsing. Trying alternative approach.")
            
            # Try reading from data_start_row instead
            df = pd.read_csv(file_path, 
                             skiprows=data_start_row-1,  # -1 because we want to include the header
                             header=0,
                             encoding='utf-8',
                             engine='python',
                             on_bad_lines='skip',
                             low_memory=False)
            
            # Clean up the column names again
            df.columns = [str(col).strip() for col in df.columns]
        
        # Standardize common column names for driving history
        column_mapping = {
            'Contact': 'Driver',
            'DriverName': 'Driver',
            'Name': 'Driver',
            'Driver Name': 'Driver',
            'Employee': 'Driver',
            'EventDateTime': 'Timestamp',
            'Event DateTime': 'Timestamp',
            'DateTime': 'Timestamp',
            'Event Time': 'Timestamp',
            'Event_Time': 'Timestamp',
            'Time': 'Timestamp',
            'Date/Time': 'Timestamp',
            'EventDescription': 'Event',
            'Event Description': 'Event',
            'Description': 'Event',
            'Event_Description': 'Event',
            'Activity': 'Event',
            'EventType': 'EventType',
            'Event Type': 'EventType',
            'Type': 'EventType',
            'Asset': 'Vehicle',
            'AssetName': 'Vehicle',
            'Asset Name': 'Vehicle',
            'Vehicle Name': 'Vehicle',
            'Equipment': 'Vehicle',
            'Location': 'Address',
            'LocationName': 'Address',
            'Place': 'Address'
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df[new_col] = df[old_col]
        
        # Extract driver information from various formats
        if 'Driver' in df.columns:
            # Format 1: "John Doe (12345)"
            driver_pattern1 = r'(.*?)\s*\('
            id_pattern1 = r'\((\d+)\)'
            
            # Format 2: "12345 - John Doe"
            driver_pattern2 = r'\d+\s*-\s*(.*)'
            id_pattern2 = r'(\d+)\s*-'
            
            # Extract using the first pattern
            df['Driver Name'] = df['Driver'].str.extract(driver_pattern1, expand=False).str.strip()
            df['Employee ID'] = df['Driver'].str.extract(id_pattern1, expand=False)
            
            # If the first pattern didn't work for some rows, try the second pattern
            name_mask = df['Driver Name'].isna()
            if name_mask.any():
                df.loc[name_mask, 'Driver Name'] = df.loc[name_mask, 'Driver'].str.extract(driver_pattern2, expand=False).str.strip()
                id_mask = df['Employee ID'].isna()
                df.loc[id_mask, 'Employee ID'] = df.loc[id_mask, 'Driver'].str.extract(id_pattern2, expand=False)
        
        # Extract date and time information
        if 'Timestamp' in df.columns:
            try:
                # Try to parse as datetime directly
                df['DateTime'] = pd.to_datetime(df['Timestamp'], errors='coerce')
                df['Date'] = df['DateTime'].dt.date
                df['Time'] = df['DateTime'].dt.time
            except Exception as e:
                logger.warning(f"Error parsing datetime: {str(e)}")
                # If datetime parsing fails, try string-based extraction
                date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})'
                time_pattern = r'(\d{1,2}:\d{2}(:\d{2})?\s*([AP]M)?)'
                
                df['Date'] = df['Timestamp'].str.extract(date_pattern, expand=False)
                df['Time'] = df['Timestamp'].str.extract(time_pattern, expand=False)
        
        # Ensure we have standard event type classification
        if 'EventType' in df.columns or 'Event' in df.columns:
            event_col = 'EventType' if 'EventType' in df.columns else 'Event'
            
            # Define key event types
            ignition_on_patterns = ['ignition on', 'start', 'vehicle start', 'key on']
            ignition_off_patterns = ['ignition off', 'stop', 'vehicle stop', 'key off']
            
            # Create a standardized event type column
            df['Standard Event'] = 'other'
            
            # Mark ignition on/off events
            for pattern in ignition_on_patterns:
                mask = df[event_col].str.lower().str.contains(pattern, na=False)
                if isinstance(mask, pd.Series):
                    df.loc[mask, 'Standard Event'] = 'ignition_on'
            
            for pattern in ignition_off_patterns:
                mask = df[event_col].str.lower().str.contains(pattern, na=False)
                if isinstance(mask, pd.Series):
                    df.loc[mask, 'Standard Event'] = 'ignition_off'
        
        # Extract location information for job site matching
        if 'Address' in df.columns:
            # Extract job site information from address
            job_number_pattern = r'(?:job|site)\s*(?:#|number|)\s*[:#]?\s*(\d+)'
            df['Job Number'] = df['Address'].str.extract(job_number_pattern, expand=False, flags=re.IGNORECASE)
        
        return df
    
    except Exception as e:
        logger.error(f"Error parsing driving history file: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
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
                         on_bad_lines='skip',
                         low_memory=False)
        
        # Clean up the column names
        df.columns = [str(col).strip() for col in df.columns]
        
        # Check if dataframe is empty or only has header
        if df.empty or len(df) <= 1:
            logger.warning(f"Empty dataframe after initial parsing. Trying alternative approach.")
            
            # Try reading from data_start_row instead
            df = pd.read_csv(file_path, 
                             skiprows=data_start_row-1,  # -1 because we want to include the header
                             header=0,
                             encoding='utf-8',
                             engine='python',
                             on_bad_lines='skip',
                             low_memory=False)
            
            # Clean up the column names again
            df.columns = [str(col).strip() for col in df.columns]
        
        # Standardize column names for activity detail
        column_mapping = {
            'Driver': 'Driver Name',
            'DriverName': 'Driver Name',
            'Employee': 'Driver Name',
            'Employee Name': 'Driver Name',
            'Operator': 'Driver Name',
            'StartTime': 'Start Time',
            'Start Time': 'Start Time',
            'TimeIn': 'Start Time',
            'Time In': 'Start Time',
            'Clock In': 'Start Time',
            'ClockIn': 'Start Time',
            'EndTime': 'End Time',
            'End Time': 'End Time',
            'TimeOut': 'End Time',
            'Time Out': 'End Time',
            'Clock Out': 'End Time',
            'ClockOut': 'End Time',
            'StopTime': 'End Time',
            'Stop Time': 'End Time',
            'Asset': 'Asset ID',
            'AssetID': 'Asset ID',
            'Asset ID': 'Asset ID',
            'Equipment': 'Asset ID',
            'Vehicle': 'Asset ID',
            'AssetName': 'Asset Name',
            'Asset Name': 'Asset Name',
            'EquipmentName': 'Asset Name',
            'Equipment Name': 'Asset Name',
            'VehicleName': 'Asset Name',
            'Vehicle Name': 'Asset Name',
            'JobSite': 'Job Site',
            'Job Site': 'Job Site',
            'Site': 'Job Site',
            'Location': 'Job Site',
            'WorkSite': 'Job Site',
            'Work Site': 'Job Site',
            'JobNumber': 'Job Number',
            'Job Number': 'Job Number',
            'Job #': 'Job Number',
            'Site #': 'Job Number',
            'Project': 'Job Number',
            'Project #': 'Job Number'
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df[new_col] = df[old_col]
        
        # If there are no standardized column names, try to identify them from the existing columns
        if 'Driver Name' not in df.columns:
            for col in df.columns:
                if 'driver' in col.lower() or 'employee' in col.lower() or 'operator' in col.lower():
                    df['Driver Name'] = df[col]
                    break
        
        if 'Start Time' not in df.columns:
            for col in df.columns:
                if ('start' in col.lower() and 'time' in col.lower()) or 'in' in col.lower() and 'time' in col.lower():
                    df['Start Time'] = df[col]
                    break
        
        if 'End Time' not in df.columns:
            for col in df.columns:
                if ('end' in col.lower() and 'time' in col.lower()) or ('stop' in col.lower() and 'time' in col.lower()) or ('out' in col.lower() and 'time' in col.lower()):
                    df['End Time'] = df[col]
                    break
        
        if 'Asset ID' not in df.columns and 'Asset Name' not in df.columns:
            for col in df.columns:
                if 'asset' in col.lower() or 'vehicle' in col.lower() or 'equipment' in col.lower():
                    if 'id' in col.lower() or 'number' in col.lower() or '#' in col:
                        df['Asset ID'] = df[col]
                    else:
                        df['Asset Name'] = df[col]
        
        if 'Job Site' not in df.columns:
            for col in df.columns:
                if 'job' in col.lower() and 'site' in col.lower() or 'location' in col.lower() or 'site' in col.lower():
                    df['Job Site'] = df[col]
                    break
        
        if 'Job Number' not in df.columns:
            for col in df.columns:
                if ('job' in col.lower() and 'number' in col.lower()) or 'project' in col.lower() or '#' in col:
                    df['Job Number'] = df[col]
                    break
                    
            # If still not found, try to extract job number from job site
            if 'Job Site' in df.columns and 'Job Number' not in df.columns:
                job_number_pattern = r'.*?(\d{4,6})'  # Typically job numbers are 4-6 digits
                df['Job Number'] = df['Job Site'].str.extract(job_number_pattern, expand=False)
        
        # Parse date and time information
        time_columns = ['Start Time', 'End Time']
        for col in time_columns:
            if col in df.columns:
                try:
                    # Try to parse as time directly
                    df[f'{col}_Parsed'] = pd.to_datetime(df[col], errors='coerce').dt.time
                except Exception as e:
                    logger.warning(f"Error parsing time column {col}: {str(e)}")
                    # If time parsing fails, try string-based extraction
                    time_pattern = r'(\d{1,2}:\d{2}(:\d{2})?\s*([AP]M)?)'
                    df[f'{col}_Parsed'] = df[col].str.extract(time_pattern, expand=False)
        
        # Extract driver information from Driver Name if it contains ID
        if 'Driver Name' in df.columns:
            # Check for pattern "ID - Name" or "Name (ID)"
            id_name_pattern = r'^(\d+)\s*-\s*(.*)$'
            name_id_pattern = r'^(.*?)\s*\((\d+)\)$'
            
            # Try first pattern
            id_name_match = df['Driver Name'].str.extract(id_name_pattern, expand=True)
            if not id_name_match.empty and not id_name_match[0].isna().all():
                df['Employee ID'] = id_name_match[0]
                df['Driver Name_Clean'] = id_name_match[1]
            else:
                # Try second pattern
                name_id_match = df['Driver Name'].str.extract(name_id_pattern, expand=True)
                if not name_id_match.empty and not name_id_match[0].isna().all():
                    df['Driver Name_Clean'] = name_id_match[0]
                    df['Employee ID'] = name_id_match[1]
                else:
                    # No pattern matched, just use the original name
                    df['Driver Name_Clean'] = df['Driver Name']
        
        return df
    
    except Exception as e:
        logger.error(f"Error parsing activity detail file: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
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