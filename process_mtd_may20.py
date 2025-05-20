#!/usr/bin/env python3
"""
Process MTD May 20 Data

This script processes the month-to-date driving history data for May 2025
including the new data through May 20th.
"""

import os
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
import csv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DRIVING_HISTORY_FILE = 'attached_assets/Pasted-StartDate-ReportParameters-1-Values-1-05-01-2025-Company-Ragle-Texas-EndDate-ReportParameters-1747753965972.txt'
OUTPUT_DIR = Path('processed')
OUTPUT_DIR.mkdir(exist_ok=True)

def extract_driving_history():
    """
    Extract driving history data from the provided MTD file
    """
    if not os.path.exists(DRIVING_HISTORY_FILE):
        logger.error(f"Driving history file not found: {DRIVING_HISTORY_FILE}")
        return None
    
    try:
        logger.info(f"Extracting data from driving history file: {DRIVING_HISTORY_FILE}")
        
        # Read the file in text mode
        with open(DRIVING_HISTORY_FILE, 'r', encoding='utf-8') as f:
            # Find the header line
            header_line = 0
            lines = f.readlines()
            for i, line in enumerate(lines):
                if 'EventDateTime' in line and 'MsgType' in line:
                    header_line = i
                    break
        
        # Extract data using csv.reader to handle quoted fields
        data = []
        headers = lines[header_line].strip().split(',')
        
        # Process relevant data lines
        for line in lines[header_line+1:]:
            if not line.strip():
                continue
            
            # Process the line using csv.reader to handle quoted fields
            reader = csv.reader([line])
            row = next(reader)
            
            # Only include rows with the right number of fields
            if len(row) >= 7:  # Make sure we have enough fields
                # Create a dict from the row
                row_dict = {}
                for i, col in enumerate(headers):
                    if i < len(row):
                        row_dict[col] = row[i]
                    else:
                        row_dict[col] = ''
                data.append(row_dict)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Process the EventDateTime column
        if 'EventDateTime' in df.columns:
            # Convert to datetime
            df['EventDateTime'] = pd.to_datetime(df['EventDateTime'], errors='coerce')
            # Create a date column
            df['Date'] = df['EventDateTime'].dt.date
            
            # Filter out rows with no date
            df = df[df['EventDateTime'].notna()]
            
            logger.info(f"Extracted {len(df)} driving history records")
            return df
        else:
            logger.error("EventDateTime column not found in data")
            return None
    
    except Exception as e:
        logger.error(f"Error extracting driving history: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def process_driving_history_by_date(df, target_date):
    """
    Process driving history data for a specific date
    
    Args:
        df (DataFrame): The driving history DataFrame
        target_date (str): The target date in YYYY-MM-DD format
        
    Returns:
        list: A list of driver records for the specified date
    """
    try:
        # Convert target_date to datetime
        date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        # Filter data for this date
        df_date = df[df['Date'] == date_obj]
        
        if len(df_date) == 0:
            logger.warning(f"No driving history data found for {target_date}")
            return []
        
        logger.info(f"Processing {len(df_date)} driving records for {target_date}")
        
        # Get unique drivers
        drivers = df_date['Contact'].unique()
        logger.info(f"Found {len(drivers)} unique drivers on {target_date}")
        
        # Process each driver
        driver_records = []
        
        for driver_name in drivers:
            if not driver_name or pd.isna(driver_name):
                continue
                
            df_driver = df_date[df_date['Contact'] == driver_name]
            
            # Extract key events
            key_on_events = df_driver[df_driver['MsgType'] == 'Key On']
            key_off_events = df_driver[df_driver['MsgType'] == 'Key Off']
            
            # Extract employee ID if available
            employee_id = None
            if isinstance(driver_name, str) and '(' in driver_name and ')' in driver_name:
                id_part = driver_name.split('(')[1].split(')')[0]
                if id_part.isdigit():
                    employee_id = id_part
            
            # Extract location information
            locations = []
            for _, row in df_driver.iterrows():
                if 'Location' in row and row['Location']:
                    locations.append(row['Location'])
            
            # Create a driver record
            driver_record = {
                'date': target_date,
                'driver_name': driver_name.split('(')[0].strip() if isinstance(driver_name, str) and '(' in driver_name else driver_name,
                'employee_id': employee_id,
                'event_count': len(df_driver),
                'key_on_count': len(key_on_events),
                'key_off_count': len(key_off_events),
                'source': 'driving_history_may20'
            }
            
            # Add first and last events
            if len(key_on_events) > 0:
                first_key_on = key_on_events['EventDateTime'].min()
                driver_record['first_activity'] = first_key_on
                driver_record['first_key_on'] = first_key_on
            
            if len(key_off_events) > 0:
                last_key_off = key_off_events['EventDateTime'].max()
                driver_record['last_activity'] = last_key_off
                driver_record['last_key_off'] = last_key_off
            
            # Add location information
            if locations:
                driver_record['locations'] = '; '.join(locations[:3])  # Include first few locations
            
            # Only include drivers with real activity
            if driver_record.get('first_activity') is not None:
                driver_records.append(driver_record)
        
        logger.info(f"Processed {len(driver_records)} driver records for {target_date}")
        return driver_records
    
    except Exception as e:
        logger.error(f"Error processing driving history for {target_date}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def save_processed_data(driver_records, date_str):
    """
    Save processed driver records to a file
    
    Args:
        driver_records (list): List of driver records
        date_str (str): The date string in YYYY-MM-DD format
    """
    try:
        if not driver_records:
            logger.warning(f"No driver records to save for {date_str}")
            return
        
        # Create the output directory
        OUTPUT_DIR.mkdir(exist_ok=True)
        
        # Save to CSV
        output_file = OUTPUT_DIR / f"driving_history_{date_str}.csv"
        pd.DataFrame(driver_records).to_csv(output_file, index=False)
        logger.info(f"Saved {len(driver_records)} driver records to {output_file}")
        
        # Also save as JSON for easier consumption
        json_file = OUTPUT_DIR / f"driving_history_{date_str}.json"
        pd.DataFrame(driver_records).to_json(json_file, orient='records')
        logger.info(f"Saved JSON version to {json_file}")
    
    except Exception as e:
        logger.error(f"Error saving processed data for {date_str}: {e}")
        import traceback
        logger.error(traceback.format_exc())

def process_may20_data():
    """
    Process driving history data for the dates in May 2025
    """
    # Extract driving history data
    driving_history = extract_driving_history()
    
    if driving_history is None:
        logger.error("Failed to extract driving history data")
        return False
    
    # Process each target date
    target_dates = [f"2025-05-{day:02d}" for day in range(15, 21)]  # May 15-20, 2025
    
    for date_str in target_dates:
        logger.info(f"Processing data for {date_str}")
        
        # Process data for this date
        driver_records = process_driving_history_by_date(driving_history, date_str)
        
        # Save processed data
        save_processed_data(driver_records, date_str)
    
    return True

def regenerate_reports():
    """
    Trigger the attendance data rebuild for the processed dates
    """
    try:
        from rebuild_attendance_data import rebuild_attendance_data
        
        # Define the date range
        target_dates = [f"2025-05-{day:02d}" for day in range(15, 21)]  # May 15-20, 2025
        
        logger.info(f"Regenerating attendance reports for dates: {target_dates}")
        success = rebuild_attendance_data(target_dates)
        
        if success:
            logger.info("Successfully regenerated all attendance reports")
        else:
            logger.warning("Some attendance reports could not be regenerated")
        
        return success
    
    except Exception as e:
        logger.error(f"Error regenerating reports: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """
    Main function
    """
    logger.info("Starting May 20 MTD data processing")
    
    # Process the driving history data
    if process_may20_data():
        # Regenerate attendance reports
        regenerate_reports()
    
    logger.info("Processing complete")

if __name__ == "__main__":
    main()