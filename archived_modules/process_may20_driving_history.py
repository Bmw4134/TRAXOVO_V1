#!/usr/bin/env python3
"""
Process May 20 Driving History

This script processes the new driving history data through May 20, 2025
and updates the attendance records in the database.
"""

import os
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

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

def process_driving_history_file():
    """
    Process the driving history file and extract daily data
    """
    if not os.path.exists(DRIVING_HISTORY_FILE):
        logger.error(f"Driving history file not found: {DRIVING_HISTORY_FILE}")
        return False
    
    try:
        logger.info(f"Processing driving history file: {DRIVING_HISTORY_FILE}")
        
        # Read the file manually since it has a custom format
        with open(DRIVING_HISTORY_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Skip header lines and find where the actual data starts
        header_line = 0
        for i, line in enumerate(lines):
            if 'EventDateTime' in line:
                header_line = i
                break
        
        # Extract column names
        columns = lines[header_line].strip().split(',')
        
        # Process data rows
        data_rows = []
        for line in lines[header_line+1:]:
            # Skip empty lines
            if not line.strip():
                continue
                
            # Split by comma, handling quoted values that might contain commas
            values = []
            in_quotes = False
            current_value = ""
            
            for char in line:
                if char == '"' and not in_quotes:
                    in_quotes = True
                elif char == '"' and in_quotes:
                    in_quotes = False
                elif char == ',' and not in_quotes:
                    values.append(current_value)
                    current_value = ""
                else:
                    current_value += char
            
            # Add the last value
            values.append(current_value)
            
            # Make sure we have the right number of values
            if len(values) >= 7:  # Ensure we have at least the key columns
                data_rows.append(values[:len(columns)])
            
        # Create DataFrame
        df = pd.DataFrame(data_rows, columns=columns)
        
        # Check if required columns exist
        required_columns = ['EventDateTime', 'Contact', 'MsgType', 'Location']
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"Required column missing: {col}")
        
        # Convert EventDateTime to datetime
        df['EventDateTime'] = pd.to_datetime(df['EventDateTime'], errors='coerce')
        
        # Create a new Date column
        df['Date'] = df['EventDateTime'].dt.date
        
        # Filter out rows with missing dates
        df = df.dropna(subset=['Date'])
        
        # Count events by date
        date_counts = df.groupby('Date').size().reset_index(name='EventCount')
        logger.info(f"Found data for {len(date_counts)} dates")
        
        # Get unique drivers
        driver_counts = df['Contact'].nunique()
        logger.info(f"Found {driver_counts} unique drivers")
        
        # Process each date in May 2025
        for day in range(15, 21):  # May 15-20
            date_str = f"2025-05-{day:02d}"
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Filter data for this date
            day_data = df[df['Date'] == date_obj]
            
            if len(day_data) > 0:
                logger.info(f"Processing data for {date_str}: {len(day_data)} records")
                
                # Get unique drivers for this date
                day_drivers = day_data['Contact'].unique()
                logger.info(f"Found {len(day_drivers)} drivers on {date_str}")
                
                # Create a structured dataset
                structured_data = []
                
                for driver in day_drivers:
                    driver_data = day_data[day_data['Contact'] == driver]
                    
                    # Get driver activity
                    key_on_events = driver_data[driver_data['MsgType'] == 'Key On']
                    key_off_events = driver_data[driver_data['MsgType'] == 'Key Off']
                    
                    # Extract the employee ID from the contact name if available
                    employee_id = None
                    if '(' in driver and ')' in driver:
                        emp_id_part = driver.split('(')[1].split(')')[0]
                        if emp_id_part.isdigit():
                            employee_id = emp_id_part
                    
                    # Get first key on and last key off
                    first_key_on = None
                    last_key_off = None
                    
                    if not key_on_events.empty:
                        first_key_on = key_on_events.iloc[0]['EventDateTime']
                    
                    if not key_off_events.empty:
                        last_key_off = key_off_events.iloc[-1]['EventDateTime']
                    
                    # Only include drivers with activity
                    if first_key_on is not None:
                        driver_record = {
                            'date': date_str,
                            'driver_name': driver.split('(')[0].strip() if '(' in driver else driver,
                            'employee_id': employee_id,
                            'first_key_on': first_key_on,
                            'last_key_off': last_key_off,
                            'event_count': len(driver_data),
                            'source': 'driving_history_may20'
                        }
                        
                        structured_data.append(driver_record)
                
                # Save structured data
                output_file = OUTPUT_DIR / f"driving_history_{date_str}.csv"
                pd.DataFrame(structured_data).to_csv(output_file, index=False)
                logger.info(f"Saved structured data to {output_file}")
            else:
                logger.warning(f"No data found for {date_str}")
        
        logger.info("Driving history processing complete")
        return True
    
    except Exception as e:
        logger.error(f"Error processing driving history: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def regenerate_reports():
    """
    Trigger regeneration of reports for the processed dates
    """
    try:
        from rebuild_attendance_data import rebuild_attendance_data
        
        # Define the date range
        date_list = [f"2025-05-{day:02d}" for day in range(15, 21)]
        
        logger.info(f"Regenerating reports for dates: {date_list}")
        
        # Call the rebuild function
        success = rebuild_attendance_data(date_list)
        
        if success:
            logger.info("Successfully regenerated all reports")
        else:
            logger.warning("Some reports could not be regenerated")
        
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
    logger.info("Starting May 20 driving history processing")
    
    # Process the driving history file
    if process_driving_history_file():
        # Regenerate reports
        regenerate_reports()
    
    logger.info("Processing complete")

if __name__ == "__main__":
    main()