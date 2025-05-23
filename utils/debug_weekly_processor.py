"""
Debug Weekly Processor

This script debugs the weekly processor to identify why drivers are not showing up in the report.
"""

import os
import json
import logging
from datetime import datetime
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_csv_file(file_path):
    """Debug the CSV file structure and data"""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None
    
    try:
        import csv
        
        # Determine sample data and column structure
        with open(file_path, 'r', newline='', encoding='utf-8-sig') as f:
            # Try to read the first few lines to see structure
            sample = f.read(4096)
            logger.debug(f"Sample data from {file_path}:\n{sample[:500]}...")
            
            # Check CSV structure
            f.seek(0)
            sample_lines = []
            for i, line in enumerate(f):
                if i < 5:  # Get first 5 lines
                    sample_lines.append(line.strip())
                else:
                    break
            
            logger.debug(f"First 5 lines from {file_path}:")
            for i, line in enumerate(sample_lines):
                logger.debug(f"Line {i}: {line}")
            
            # Try to detect CSV dialect
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(f.read(4096))
                logger.debug(f"Detected dialect: delimiter='{dialect.delimiter}', quotechar='{dialect.quotechar}'")
            except csv.Error:
                logger.warning(f"Could not detect CSV dialect for {file_path}")
            
            # Try to read with DictReader
            f.seek(0)
            try:
                reader = csv.DictReader(f)
                logger.debug(f"CSV headers: {reader.fieldnames}")
                
                # Read some rows
                rows = []
                for i, row in enumerate(reader):
                    if i < 5:  # Get first 5 rows
                        rows.append(row)
                    else:
                        break
                
                logger.debug(f"Found {len(rows)} rows (showing first 5)")
                for i, row in enumerate(rows):
                    logger.debug(f"Row {i}: {row}")
                
                # Count total rows
                f.seek(0)
                reader = csv.DictReader(f)
                row_count = sum(1 for _ in reader)
                logger.debug(f"Total rows in file: {row_count}")
                
                # Try to find driver column
                if reader.fieldnames:
                    driver_col = None
                    for col in reader.fieldnames:
                        if 'driver' in col.lower():
                            driver_col = col
                            break
                    
                    if driver_col:
                        logger.debug(f"Found driver column: {driver_col}")
                        
                        # Count unique drivers
                        f.seek(0)
                        reader = csv.DictReader(f)
                        drivers = set()
                        for row in reader:
                            if row.get(driver_col):
                                drivers.add(row[driver_col])
                        
                        logger.debug(f"Found {len(drivers)} unique drivers")
                        logger.debug(f"Sample drivers: {list(drivers)[:5]}")
                    else:
                        logger.warning(f"Could not find driver column in {file_path}")
                
                return {
                    "file_path": file_path,
                    "headers": reader.fieldnames,
                    "row_count": row_count,
                    "driver_column": driver_col,
                    "driver_count": len(drivers) if 'drivers' in locals() else 0
                }
            except Exception as e:
                logger.error(f"Error reading CSV with DictReader: {str(e)}")
                return None
    except Exception as e:
        logger.error(f"Error debugging CSV file {file_path}: {str(e)}")
        return None

def debug_excel_file(file_path):
    """Debug the Excel file structure and data"""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None
    
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        logger.debug(f"Excel file {file_path} has shape: {df.shape}")
        logger.debug(f"Columns: {df.columns.tolist()}")
        
        # Look for date and driver columns
        date_col = None
        driver_col = None
        
        for col in df.columns:
            if 'date' in col.lower():
                date_col = col
            if 'driver' in col.lower() or 'employee' in col.lower() or 'name' in col.lower():
                driver_col = col
        
        logger.debug(f"Found date column: {date_col}")
        logger.debug(f"Found driver column: {driver_col}")
        
        # Show sample data
        if not df.empty:
            logger.debug(f"Sample data:\n{df.head(5)}")
            
            # Count unique drivers if driver column found
            if driver_col:
                drivers = df[driver_col].dropna().unique()
                logger.debug(f"Found {len(drivers)} unique drivers")
                logger.debug(f"Sample drivers: {drivers[:5].tolist()}")
            
            # Check date ranges if date column found
            if date_col:
                try:
                    min_date = df[date_col].min()
                    max_date = df[date_col].max()
                    logger.debug(f"Date range: {min_date} to {max_date}")
                except Exception as e:
                    logger.warning(f"Could not determine date range: {str(e)}")
        
        return {
            "file_path": file_path,
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "date_column": date_col,
            "driver_column": driver_col,
            "driver_count": len(drivers) if 'drivers' in locals() else 0
        }
    except Exception as e:
        logger.error(f"Error debugging Excel file {file_path}: {str(e)}")
        return None

def debug_may_weekly_report():
    """Debug the May weekly report processing"""
    # Define paths
    attached_assets_dir = os.path.join(os.getcwd(), 'attached_assets')
    
    # Define specific files to debug
    files_to_debug = {
        'driving_history': os.path.join(attached_assets_dir, 'DrivingHistory (13).csv'),
        'activity_detail': os.path.join(attached_assets_dir, 'ActivityDetail (13).csv'),
        'time_on_site': os.path.join(attached_assets_dir, 'AssetsTimeOnSite (3).csv'),
        'timecard1': os.path.join(attached_assets_dir, 'Timecards - 2025-05-18 - 2025-05-24 (3).xlsx'),
        'timecard2': os.path.join(attached_assets_dir, 'Timecards - 2025-05-18 - 2025-05-24 (4).xlsx')
    }
    
    # Debug each file
    results = {}
    
    for file_type, file_path in files_to_debug.items():
        logger.info(f"Debugging {file_type} file: {file_path}")
        
        if file_path.endswith('.csv'):
            result = debug_csv_file(file_path)
        elif file_path.endswith('.xlsx'):
            result = debug_excel_file(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_path}")
            continue
        
        if result:
            results[file_type] = result
    
    # Generate debug report
    debug_report = {
        "timestamp": datetime.now().isoformat(),
        "file_results": results
    }
    
    # Save debug report
    report_path = os.path.join(os.getcwd(), 'reports', 'weekly_driver_debug.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(debug_report, f, indent=2)
    
    logger.info(f"Debug report saved to {report_path}")
    return debug_report

if __name__ == "__main__":
    logger.info("Starting weekly processor debug")
    debug_may_weekly_report()
    logger.info("Debug complete")