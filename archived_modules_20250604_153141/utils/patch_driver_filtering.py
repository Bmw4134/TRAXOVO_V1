"""
Patch Driver Filtering

This script ensures all drivers with a valid name or Employee ID are included in the reports,
and classifies missing status as "Not On Job" to match legacy Excel logic.
"""

import pandas as pd
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def patch_driver_filtering(input_dir="raw", output_dir="data"):
    """
    Apply driver filtering patch to fix missing drivers or status
    
    Args:
        input_dir (str): Directory containing raw CSV files
        output_dir (str): Directory to save filtered JSON files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    files_processed = 0
    total_drivers_recovered = 0
    
    for file in os.listdir(input_dir):
        if file.endswith(".csv"):
            try:
                logger.info(f"Processing file: {file}")
                df = pd.read_csv(os.path.join(input_dir, file))
                
                # Determine date column (may be 'date' or capitalized 'Date')
                date_col = None
                for col in ['date', 'Date']:
                    if col in df.columns:
                        date_col = col
                        break
                
                if not date_col:
                    logger.warning(f"Date column not found in {file}, using first column")
                    date_col = df.columns[0]
                
                # Convert date to datetime
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                
                # Normalize column names to handle mixed case
                df_cols = {col: col.lower() for col in df.columns}
                df = df.rename(columns=df_cols)
                
                # Look for driver name columns (may be different formats)
                driver_col = None
                for col in ['driver_name', 'driver name', 'driver', 'contact']:
                    if col in df.columns:
                        driver_col = col
                        break
                
                if not driver_col:
                    logger.warning(f"Driver column not found in {file}, skipping")
                    continue
                
                # Look for employee ID columns
                emp_id_col = None
                for col in ['emp id', 'employee_id', 'employee id', 'employeeid']:
                    if col in df.columns:
                        emp_id_col = col
                        break
                
                # Filter to include only records with driver name or employee ID
                initial_count = len(df)
                
                if emp_id_col:
                    df_filtered = df[(df[driver_col].notna()) | (df[emp_id_col].notna())]
                else:
                    df_filtered = df[df[driver_col].notna()]
                
                df_filtered = df_filtered.copy()
                
                # Fill missing status with "Not On Job"
                status_col = None
                for col in ['status', 'attendance_status', 'attendance']:
                    if col in df_filtered.columns:
                        status_col = col
                        break
                
                if status_col:
                    missing_status_count = df_filtered[status_col].isna().sum()
                    df_filtered[status_col] = df_filtered[status_col].fillna("Not On Job")
                    logger.info(f"Fixed {missing_status_count} missing status values in {file}")
                
                # Save filtered data by date
                drivers_recovered = initial_count - len(df_filtered)
                total_drivers_recovered += drivers_recovered
                
                for date in df_filtered[date_col].dt.date.unique():
                    df_day = df_filtered[df_filtered[date_col].dt.date == date]
                    day_file = f"filtered_driving_data_{date}.json"
                    
                    # Convert to records format and ensure proper field mapping
                    records = []
                    for _, row in df_day.iterrows():
                        record = {
                            'Driver': row.get(driver_col, ''),
                            'EmployeeID': row.get(emp_id_col, '') if emp_id_col else '',
                            'Status': row.get(status_col, 'Not On Job') if status_col else 'Not On Job',
                            'JobSite': row.get('job_site', row.get('job site', 'Unknown')),
                            'FirstSeen': row.get('first_seen', row.get('first seen', '')),
                            'LastSeen': row.get('last_seen', row.get('last seen', '')),
                            'Hours': row.get('hours', '0'),
                            'Source': row.get('source', 'gps'),
                            'Date': str(date),
                            'EventDateTime': row.get('eventdatetime', str(date) + ' 07:00:00'),
                            'Location': row.get('location', row.get('job_site', 'Unknown'))
                        }
                        records.append(record)
                    
                    with open(os.path.join(output_dir, day_file), 'w') as f:
                        json.dump(records, f, indent=2)
                    
                    logger.info(f"Created {day_file} with {len(records)} driver records")
                
                files_processed += 1
                
            except Exception as e:
                logger.error(f"Error processing {file}: {str(e)}")
    
    logger.info(f"Driver filtering patch complete. Processed {files_processed} files.")
    logger.info(f"Total drivers recovered: {total_drivers_recovered}")
    logger.info(f"New files in {output_dir}/")
    
    return files_processed

if __name__ == "__main__":
    patch_driver_filtering()