"""
Start Time & Job Parser

Utility for extracting and processing data from the "Start Time & Job" sheet
in the Daily Late Start-Early End & NOJ Report Excel files.
"""

import os
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

def find_daily_report_file(date_str):
    """
    Find the daily report Excel file for a specific date.
    
    Args:
        date_str (str): Report date in YYYY-MM-DD format
        
    Returns:
        str: Path to the daily report file, or None if not found
    """
    # Convert date string to date object for comparison
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        logger.error(f"Invalid date format: {date_str}")
        return None
    
    # Look for daily report files in the attached_assets directory
    asset_dir = Path('attached_assets')
    
    # Patterns for potential daily report files
    patterns = [
        f"DAILY LATE START-EARLY END & NOJ REPORT_{target_date.strftime('%m.%d.%Y')}.xlsx",  # MM.DD.YYYY format
        f"DAILY LATE START_{target_date.strftime('%m.%d.%Y')}.xlsx",  # Alternative format
        f"DAILY_DRIVER_REPORT_{target_date.strftime('%m.%d.%Y')}.xlsx"  # Another alternative format
    ]
    
    # Try exact matches first
    for pattern in patterns:
        file_path = asset_dir / pattern
        if file_path.exists():
            logger.info(f"Found daily report file: {file_path}")
            return str(file_path)
    
    # If exact match not found, search for any daily report file with date in filename
    daily_files = [
        f for f in os.listdir(asset_dir) 
        if f.endswith('.xlsx') and 
        ('DAILY' in f.upper() or 'LATE' in f.upper() or 'START' in f.upper())
    ]
    
    # Log available files for debugging
    if daily_files:
        logger.debug(f"Found {len(daily_files)} potential daily report files")
        for file in daily_files:
            logger.debug(f"  - {file}")
    else:
        logger.warning(f"No daily report files found in {asset_dir}")
        return None
    
    # Use the most recent file if multiple are found
    if daily_files:
        # Sort by creation time, newest first
        daily_files.sort(key=lambda f: os.path.getctime(os.path.join(asset_dir, f)), reverse=True)
        file_path = asset_dir / daily_files[0]
        logger.info(f"Using most recent daily report file: {file_path}")
        return str(file_path)
    
    return None


def extract_start_time_data(date_str):
    """
    Extract data from the "Start Time & Job" sheet for a specific date.
    
    Args:
        date_str (str): Report date in YYYY-MM-DD format
        
    Returns:
        pandas.DataFrame: DataFrame with start time and job data, or None if not found
    """
    # Find the daily report file
    report_file = find_daily_report_file(date_str)
    if not report_file:
        logger.warning(f"No daily report file found for date: {date_str}")
        return None
    
    # Extract data from the Start Time & Job sheet
    try:
        logger.info(f"Extracting data from Start Time & Job sheet in {report_file}")
        
        # Try different possible sheet names
        sheet_names = ['Start Time & Job', 'Start Time and Job', 'Start Time', 'Start Times']
        
        # List available sheets for debugging
        try:
            xl = pd.ExcelFile(report_file)
            logger.info(f"Available sheets in {report_file}: {xl.sheet_names}")
            
            # Check if any of our target sheets exist
            found_sheet = None
            for sheet in sheet_names:
                if sheet in xl.sheet_names:
                    found_sheet = sheet
                    break
            
            # Look for partial matches if exact match not found
            if not found_sheet:
                for sheet in xl.sheet_names:
                    if 'START' in sheet.upper() and 'TIME' in sheet.upper():
                        found_sheet = sheet
                        logger.info(f"Found partial match for Start Time sheet: {sheet}")
                        break
            
            if not found_sheet:
                logger.warning(f"Could not find Start Time & Job sheet in {report_file}")
                return None
            
            # Read the sheet
            logger.info(f"Reading sheet: {found_sheet}")
            df = pd.read_excel(report_file, sheet_name=found_sheet)
            
            # Clean up and normalize the DataFrame
            df = df.dropna(how='all')  # Remove empty rows
            
            # Convert column names to strings and normalize
            df.columns = [str(col).strip() if col is not None else f'col_{i}' 
                         for i, col in enumerate(df.columns)]
            
            # Log the columns we found
            logger.debug(f"Columns found: {list(df.columns)}")
            
            # Find the key column names (case-insensitive)
            asset_col = None
            driver_col = None
            job_col = None
            
            for col in df.columns:
                col_upper = col.upper()
                if 'ASSET' in col_upper:
                    asset_col = col
                elif 'DRIVER' in col_upper:
                    driver_col = col
                elif 'JOB' in col_upper and 'SR' not in col_upper:
                    job_col = col
            
            # Create standardized columns
            if asset_col:
                df['Asset ID'] = df[asset_col]
            if driver_col:
                df['Driver'] = df[driver_col]
            if job_col:
                df['Job'] = df[job_col]
            
            # Filter out rows without asset ID or driver
            if 'Asset ID' in df.columns:
                df = df[df['Asset ID'].notna()]
            if 'Driver' in df.columns:
                df = df[df['Driver'].notna()]
            
            # Add report date
            df['Report Date'] = date_str
            
            logger.info(f"Processed {len(df)} rows from Start Time & Job sheet")
            return df
            
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    except Exception as e:
        logger.error(f"Error extracting start time data: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return None


def merge_start_time_with_attendance(attendance_data, start_time_data):
    """
    Merge attendance data with start time and job data.
    
    Args:
        attendance_data (dict): Dictionary of attendance data
        start_time_data (pandas.DataFrame): DataFrame with start time and job data
        
    Returns:
        dict: Merged attendance data
    """
    if attendance_data is None:
        logger.warning("No attendance data provided for merging")
        return attendance_data
    
    if start_time_data is None or start_time_data.empty:
        logger.warning("No start time data available for merging")
        return attendance_data
    
    try:
        # Get driver records from attendance data
        drivers = attendance_data.get('drivers', [])
        if not drivers:
            logger.warning("No drivers found in attendance data")
            return attendance_data
        
        # Create a lookup table from start time data
        lookup_table = {}
        for _, row in start_time_data.iterrows():
            asset_id = str(row.get('Asset ID', '')).strip() if 'Asset ID' in row else ''
            driver_name = str(row.get('Driver', '')).strip() if 'Driver' in row else ''
            job = str(row.get('Job', '')).strip() if 'Job' in row else ''
            
            if asset_id:
                lookup_table[asset_id] = {'driver': driver_name, 'job': job}
            
            if driver_name:
                lookup_table[driver_name] = {'asset': asset_id, 'job': job}
        
        # Update driver records with start time data
        updated_count = 0
        for driver in drivers:
            asset_id = driver.get('asset_id', '')
            driver_name = driver.get('driver_name', '')
            
            # Try to find a match
            match = None
            if asset_id and asset_id in lookup_table:
                match = lookup_table[asset_id]
            elif driver_name and driver_name in lookup_table:
                match = lookup_table[driver_name]
            
            # Update with start time data if found
            if match:
                # Update job number if missing or N/A
                if match.get('job') and (not driver.get('job_number') or driver.get('job_number') == 'N/A'):
                    driver['job_number'] = match['job']
                
                # Update driver name if missing
                if match.get('driver') and not driver.get('driver_name'):
                    driver['driver_name'] = match['driver']
                
                # Update asset id if missing
                if match.get('asset') and not driver.get('asset_id'):
                    driver['asset_id'] = match['asset']
                
                updated_count += 1
        
        logger.info(f"Updated {updated_count} driver records with start time data")
        
        # Update attendance data with the enriched drivers list
        attendance_data['drivers'] = drivers
        attendance_data['start_time_data_integrated'] = True
        
        return attendance_data
    
    except Exception as e:
        logger.error(f"Error merging start time data: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return attendance_data


def get_start_time_data(date_str):
    """
    Get start time and job data for a specific date.
    
    Args:
        date_str (str): Report date in YYYY-MM-DD format
        
    Returns:
        pandas.DataFrame: DataFrame with start time and job data
    """
    return extract_start_time_data(date_str)