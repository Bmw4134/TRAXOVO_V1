"""
Start Time Parser Module

This module provides functions for parsing the "Start Time & Job" sheet
from daily report Excel files, extracting structured job assignments,
scheduled times, and driver information.
"""

import re
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

def parse_start_time_sheet(file_path, sheet_name=None):
    """
    Parse the Start Time & Job sheet from an Excel file
    
    Args:
        file_path (str): Path to the Excel file
        sheet_name (str): Name of the sheet to parse
        
    Returns:
        dict: Parsed data
    """
    try:
        # Load Excel file
        xl = pd.ExcelFile(file_path)
        
        # Find the right sheet
        if sheet_name and sheet_name in xl.sheet_names:
            # Use specified sheet
            sheet = sheet_name
        else:
            # Try to find the right sheet
            potential_names = [
                'Start Time & Job', 'Start Time and Job', 
                'START TIME & JOB', 'Start Times', 'START TIMES',
                'Daily Report', 'DAILY REPORT'
            ]
            
            found_sheet = None
            for name in potential_names:
                if name in xl.sheet_names:
                    found_sheet = name
                    break
            
            # If no exact match, look for any sheet with "Start" and "Time" or "Daily" and "Report"
            if not found_sheet:
                for name in xl.sheet_names:
                    if ('START' in name.upper() and 'TIME' in name.upper()) or \
                       ('DAILY' in name.upper() and 'REPORT' in name.upper()):
                        found_sheet = name
                        break
            
            # If still no match, try first sheet
            if not found_sheet and len(xl.sheet_names) > 0:
                found_sheet = xl.sheet_names[0]
            
            # Use found sheet or default to first sheet
            sheet = found_sheet or xl.sheet_names[0]
        
        logger.info(f"Using sheet '{sheet}' from {file_path}")
        
        # Read the sheet
        df = pd.read_excel(file_path, sheet_name=sheet)
        
        # Clean up and normalize columns
        df.columns = [str(col).upper().strip() if col else f'UNNAMED_{i}' for i, col in enumerate(df.columns)]
        
        # Find key columns
        driver_col = None
        job_col = None
        asset_col = None
        start_col = None
        
        # Search for column names
        for col in df.columns:
            if 'DRIVER' in col or 'EMPLOYEE' in col or 'NAME' in col:
                driver_col = col
            elif 'JOB' in col or 'PROJECT' in col or 'SITE' in col:
                job_col = col
            elif 'ASSET' in col or 'VEHICLE' in col or 'EQUIPMENT' in col or 'UNIT' in col:
                asset_col = col
            elif 'START' in col and ('TIME' in col or 'HOUR' in col):
                start_col = col
        
        # Create parsed data structure
        data = {
            'file_path': file_path,
            'sheet_name': sheet,
            'date': extract_date_from_filename(file_path),
            'parsed_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'assignments': []
        }
        
        # Validate required columns
        if not driver_col or not job_col:
            logger.warning(f"Missing required columns in {file_path}: Driver={driver_col}, Job={job_col}")
            return data
        
        # Process each row
        for _, row in df.iterrows():
            driver_name = row.get(driver_col, '')
            job_number = row.get(job_col, '')
            
            # Skip empty rows
            if pd.isna(driver_name) or pd.isna(job_number) or not str(driver_name).strip() or not str(job_number).strip():
                continue
            
            # Clean up values
            driver_name = str(driver_name).strip()
            job_number = str(job_number).strip()
            
            # Extract asset ID
            asset_id = ''
            if asset_col and not pd.isna(row.get(asset_col, '')):
                asset_id = str(row.get(asset_col, '')).strip()
            
            # Extract start time
            start_time = ''
            if start_col and not pd.isna(row.get(start_col, '')):
                start_time_raw = row.get(start_col, '')
                start_time = format_time(start_time_raw)
            
            # Add assignment
            assignment = {
                'driver_name': driver_name,
                'job_number': format_job_number(job_number),
                'asset_id': asset_id,
                'start_time': start_time
            }
            
            # Extract division from job number
            division = extract_division_from_job(job_number)
            if division:
                assignment['division'] = division
            
            # Add to assignments list
            data['assignments'].append(assignment)
        
        logger.info(f"Parsed {len(data['assignments'])} assignments from {file_path}")
        return data
    
    except Exception as e:
        logger.error(f"Error parsing Start Time & Job sheet: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'file_path': file_path,
            'sheet_name': sheet_name,
            'date': extract_date_from_filename(file_path),
            'parsed_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error': str(e),
            'assignments': []
        }

def extract_date_from_filename(file_path):
    """
    Extract date from filename
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: Extracted date in YYYY-MM-DD format or empty string
    """
    try:
        # Convert to Path object
        path = Path(file_path)
        
        # Extract filename
        filename = path.name
        
        # Try to match date patterns
        patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{2}-\d{2}-\d{4})',  # MM-DD-YYYY
            r'(\d{2}\.\d{2}\.\d{4})',  # MM.DD.YYYY
            r'(\d{2}/\d{2}/\d{4})',  # MM/DD/YYYY
            r'_(\d{2})[\._](\d{2})[\._](\d{4})',  # _MM.DD.YYYY or _MM_DD_YYYY
            r'(\d{1,2})[\._](\d{1,2})[\._](\d{4})',  # M.D.YYYY or M_D_YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                if len(match.groups()) == 1:
                    # Already in YYYY-MM-DD format
                    date_str = match.group(1)
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        return date_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        # Try MM-DD-YYYY format
                        try:
                            date_obj = datetime.strptime(date_str, '%m-%d-%Y')
                            return date_obj.strftime('%Y-%m-%d')
                        except ValueError:
                            # Try MM.DD.YYYY format
                            try:
                                date_obj = datetime.strptime(date_str, '%m.%d.%Y')
                                return date_obj.strftime('%Y-%m-%d')
                            except ValueError:
                                # Try MM/DD/YYYY format
                                try:
                                    date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                                    return date_obj.strftime('%Y-%m-%d')
                                except ValueError:
                                    pass
                elif len(match.groups()) == 3:
                    # MM.DD.YYYY or MM_DD_YYYY format
                    month, day, year = match.groups()
                    try:
                        date_obj = datetime.strptime(f"{year}-{month}-{day}", '%Y-%m-%d')
                        return date_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        pass
        
        # If no match found, try to extract numeric parts and guess format
        numbers = re.findall(r'\d+', filename)
        if len(numbers) >= 3:
            for i in range(len(numbers) - 2):
                if len(numbers[i]) == 2 and len(numbers[i+1]) == 2 and len(numbers[i+2]) == 4:
                    # Assume MM.DD.YYYY format
                    try:
                        date_obj = datetime.strptime(f"{numbers[i+2]}-{numbers[i]}-{numbers[i+1]}", '%Y-%m-%d')
                        return date_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        pass
        
        # If all else fails, return current date
        return datetime.now().strftime('%Y-%m-%d')
    
    except Exception as e:
        logger.error(f"Error extracting date from filename: {e}")
        return datetime.now().strftime('%Y-%m-%d')

def format_time(time_value):
    """
    Format time value to HH:MM format
    
    Args:
        time_value: Time value to format
        
    Returns:
        str: Formatted time
    """
    try:
        if pd.isna(time_value) or time_value is None:
            return ''
        
        # If already a string, try to parse it
        if isinstance(time_value, str):
            time_str = time_value.strip()
            
            # Try to match time formats
            if re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', time_str):
                # Already in HH:MM or HH:MM:SS format
                if len(time_str) <= 5:
                    return time_str
                else:
                    # Extract HH:MM from HH:MM:SS
                    return time_str[:5]
            
            elif re.match(r'^\d{1,2}$', time_str):
                # Just hour, add :00
                return f"{int(time_str):02d}:00"
            
            elif re.match(r'^\d{3,4}$', time_str):
                # Military time without colon
                if len(time_str) == 3:
                    # 3-digit military time (e.g., 730)
                    hour = int(time_str[:1])
                    minute = int(time_str[1:])
                    return f"{hour:02d}:{minute:02d}"
                else:
                    # 4-digit military time (e.g., 0730)
                    hour = int(time_str[:2])
                    minute = int(time_str[2:])
                    return f"{hour:02d}:{minute:02d}"
            
            # If no match, try to parse as time
            for fmt in ['%H:%M', '%H:%M:%S', '%I:%M %p', '%I:%M:%S %p']:
                try:
                    time_obj = datetime.strptime(time_str, fmt)
                    return time_obj.strftime('%H:%M')
                except ValueError:
                    pass
        
        # If numeric, assume it's decimal hours
        elif isinstance(time_value, (int, float)):
            hours = int(time_value)
            minutes = int((time_value - hours) * 60)
            return f"{hours:02d}:{minutes:02d}"
        
        # If pandas timestamp or datetime
        elif hasattr(time_value, 'hour') and hasattr(time_value, 'minute'):
            return f"{time_value.hour:02d}:{time_value.minute:02d}"
        
        # If all else fails, return as string
        return str(time_value)
    
    except Exception as e:
        logger.error(f"Error formatting time: {e}")
        return ''

def format_job_number(job_number):
    """
    Format job number to standardized format
    
    Args:
        job_number (str): Job number to format
        
    Returns:
        str: Formatted job number
    """
    try:
        if pd.isna(job_number) or not job_number:
            return ''
        
        # Convert to string and strip whitespace
        job_str = str(job_number).strip()
        
        # Remove common prefixes
        job_str = re.sub(r'^(JOB|PROJECT|SITE)\s*', '', job_str, flags=re.IGNORECASE)
        
        # Normalize formatting
        # If it's a 4-digit number, keep as is
        if re.match(r'^\d{4}$', job_str):
            return job_str
        
        # If it's a year-number format (e.g., 2022-101), normalize to YYYY-NNN
        match = re.match(r'^(\d{4})[.-](\d+)$', job_str)
        if match:
            year, number = match.groups()
            return f"{year}-{int(number):03d}"
        
        # If it has division code (e.g., DIV2-101), normalize
        match = re.match(r'^DIV[.-]?(\d)[.-](\d+)$', job_str, re.IGNORECASE)
        if match:
            division, number = match.groups()
            return f"DIV{division}-{int(number):03d}"
        
        # Otherwise, return as is
        return job_str
    
    except Exception as e:
        logger.error(f"Error formatting job number: {e}")
        return str(job_number)

def extract_division_from_job(job_number):
    """
    Extract division from job number
    
    Args:
        job_number (str): Job number
        
    Returns:
        str: Division code or empty string
    """
    try:
        if pd.isna(job_number) or not job_number:
            return ''
        
        # Convert to string and strip whitespace
        job_str = str(job_number).strip().upper()
        
        # Check for explicit division codes
        if 'DIV' in job_str:
            match = re.search(r'DIV[.-]?(\d)', job_str, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Check for DFW prefix
        if job_str.startswith('DFW') or 'DFW' in job_str:
            return '2'
        
        # Check for HOU prefix
        elif job_str.startswith('HOU') or 'HOU' in job_str:
            return '4'
        
        # Check for WT prefix
        elif job_str.startswith('WT') or 'WT' in job_str:
            return '3'
        
        # Otherwise, try to determine from job number pattern
        # TODO: Implement logic to detect division from job pattern
        
        return ''
    
    except Exception as e:
        logger.error(f"Error extracting division from job: {e}")
        return ''

def find_assignment_for_driver(driver_name, assignments):
    """
    Find assignment for a driver in the assignments list
    
    Args:
        driver_name (str): Driver name to look for
        assignments (list): List of assignment dictionaries
        
    Returns:
        dict: Assignment for the driver or None
    """
    if not driver_name or not assignments:
        return None
    
    # Normalize driver name
    driver_name = driver_name.upper().strip()
    
    # Look for exact match
    for assignment in assignments:
        if assignment['driver_name'].upper().strip() == driver_name:
            return assignment
    
    # Look for partial match (last name)
    driver_parts = driver_name.split()
    if len(driver_parts) > 0:
        last_name = driver_parts[-1]
        for assignment in assignments:
            if last_name in assignment['driver_name'].upper().split():
                return assignment
    
    # No match found
    return None