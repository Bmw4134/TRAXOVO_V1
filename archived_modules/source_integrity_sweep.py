#!/usr/bin/env python3
"""
Source Integrity Sweep

This utility performs a comprehensive integrity check on all source files
to detect and remove any fabricated or dummy data.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import csv
import openpyxl
from datetime import datetime
from typing import Dict, List, Set, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Define known authentic sources
BASELINE_FILE = 'data/start_time_job/baseline.csv'
COMPANY_EMPLOYEE_FILE = 'attached_assets/Consolidated_Employee_And_Job_Lists_Corrected.xlsx'

def load_verified_drivers() -> Set[str]:
    """
    Load verified driver names from authentic sources
    
    Returns:
        Set[str]: Set of normalized verified driver names
    """
    verified_drivers = set()
    
    # Load drivers from baseline
    if os.path.exists(BASELINE_FILE):
        try:
            df = pd.read_csv(BASELINE_FILE)
            driver_col = 'driver_name' if 'driver_name' in df.columns else None
            if driver_col:
                for driver in df[driver_col].astype(str).str.strip():
                    if driver and driver.lower() not in ['nan', 'none', 'null', '']:
                        verified_drivers.add(driver.strip().lower())
        except Exception as e:
            logger.error(f"Error loading baseline file: {e}")
    
    # Load drivers from company employee file
    if os.path.exists(COMPANY_EMPLOYEE_FILE):
        try:
            # Try to load as Excel
            try:
                df = pd.read_excel(COMPANY_EMPLOYEE_FILE)
                
                # Look for employee name column (try various possible names)
                employee_cols = ['name', 'employee_name', 'full_name', 'driver_name', 'employee']
                employee_col = None
                for col in employee_cols:
                    if col in df.columns:
                        employee_col = col
                        break
                
                if employee_col:
                    for employee in df[employee_col].astype(str).str.strip():
                        if employee and employee.lower() not in ['nan', 'none', 'null', '']:
                            verified_drivers.add(employee.strip().lower())
            except Exception as e:
                logger.warning(f"Error loading employee file as Excel: {e}")
        except Exception as e:
            logger.error(f"Error loading employee file: {e}")
    
    return verified_drivers

def scan_source_files(date_str: str, verified_drivers: Set[str]) -> Dict[str, Any]:
    """
    Scan all source files for the specified date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        verified_drivers (Set[str]): Set of verified driver names
        
    Returns:
        Dict[str, Any]: Scan results
    """
    # Source file directories to scan
    source_dirs = {
        'driving_history': 'data/driving_history',
        'activity_detail': 'data/activity_detail'
    }
    
    # Initialize results
    scan_results = {
        'date': date_str,
        'files': {},
        'unverified_drivers': {},
        'verified_file_map': {},
        'verified_drivers': len(verified_drivers)
    }
    
    # Scan each source directory
    for source_type, dir_path in source_dirs.items():
        if not os.path.exists(dir_path):
            continue
            
        for file_name in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file_name)
            
            # Only process files for the specified date
            if not (date_str.replace('-', '') in file_name or date_str in file_name):
                continue
                
            # Process the file
            try:
                # Determine file type and load
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                elif file_path.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(file_path)
                else:
                    continue
                    
                # Get row count
                row_count = len(df)
                
                # Standardize column names
                df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
                
                # Determine driver column
                driver_cols = ['driver', 'driver_name', 'drivername', 'employee', 'employee_name', 'name']
                driver_col = None
                for col in driver_cols:
                    if col in df.columns:
                        driver_col = col
                        break
                
                if not driver_col:
                    scan_results['files'][file_path] = {
                        'row_count': row_count,
                        'driver_column': None,
                        'error': 'No driver column found'
                    }
                    continue
                
                # Extract driver names
                driver_names = []
                unverified_drivers = []
                
                for driver in df[driver_col].astype(str).str.strip():
                    if driver and driver.lower() not in ['nan', 'none', 'null', '']:
                        normalized_name = driver.strip().lower()
                        driver_names.append(driver)
                        
                        # Check if driver is verified
                        if normalized_name not in verified_drivers:
                            unverified_drivers.append(driver)
                
                # Add to scan results
                scan_results['files'][file_path] = {
                    'row_count': row_count,
                    'driver_column': driver_col,
                    'driver_sample': driver_names[:10],
                    'unverified_count': len(unverified_drivers),
                    'total_drivers': len(driver_names)
                }
                
                # Add unverified drivers
                if unverified_drivers:
                    scan_results['unverified_drivers'][file_path] = unverified_drivers
                    
                # Create clean version without unverified drivers
                if unverified_drivers:
                    # Isolate unverified driver rows
                    mask = ~df[driver_col].astype(str).str.strip().str.lower().isin([d.lower() for d in unverified_drivers])
                    cleaned_df = df[mask].copy()
                    
                    # Save cleaned file
                    cleaned_path = file_path.replace('.csv', '_verified.csv').replace('.xlsx', '_verified.csv')
                    cleaned_df.to_csv(cleaned_path, index=False)
                    
                    # Add to verified file map
                    scan_results['verified_file_map'][file_path] = cleaned_path
                else:
                    # If no unverified drivers, use original file
                    scan_results['verified_file_map'][file_path] = file_path
                    
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                scan_results['files'][file_path] = {
                    'error': str(e)
                }
    
    # Add summary
    scan_results['summary'] = {
        'total_files': len(scan_results['files']),
        'files_with_unverified_drivers': len(scan_results['unverified_drivers']),
        'total_unverified_drivers': sum(len(drivers) for drivers in scan_results['unverified_drivers'].values())
    }
    
    return scan_results

def rebuild_daily_report(date_str: str, scan_results: Dict[str, Any]) -> bool:
    """
    Rebuild daily report using only verified drivers
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        scan_results (Dict[str, Any]): Scan results
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get verified file map
    verified_file_map = scan_results.get('verified_file_map', {})
    if not verified_file_map:
        logger.error(f"No verified files found for {date_str}")
        return False
    
    # First, make a backup of the genius_processor output directories
    backup_suffix = datetime.now().strftime('%Y%m%d%H%M%S')
    for dir_path in ['reports/daily_drivers', 'exports/daily_reports']:
        if os.path.exists(dir_path):
            for file_name in os.listdir(dir_path):
                if date_str in file_name:
                    src_path = os.path.join(dir_path, file_name)
                    dst_path = os.path.join(dir_path, f"{file_name}.backup_{backup_suffix}")
                    try:
                        import shutil
                        shutil.copy2(src_path, dst_path)
                        logger.info(f"Backed up {src_path} to {dst_path}")
                    except Exception as e:
                        logger.error(f"Error backing up {src_path}: {e}")
    
    # Modified genius_processor import and run
    try:
        # Import the genius_processor
        sys.path.append('.')
        from genius_processor import load_source_data, process_date, export_report
        
        # Override the scan for source files function in the validation module
        import validation_core
        original_validate_source_files = validation_core.validate_source_files
        
        def patched_validate_source_files(date_str):
            """Patched function to use only verified files"""
            result = original_validate_source_files(date_str)
            
            # Replace files with verified versions
            for category in result:
                result[category] = [verified_file_map.get(f, f) for f in result[category]]
                
            return result
        
        # Apply the patch
        validation_core.validate_source_files = patched_validate_source_files
        
        # Process the data
        logger.info(f"Processing data for {date_str} with verified sources only")
        report_data = process_date(date_str)
        
        if not report_data:
            logger.error(f"Failed to process data for {date_str}")
            return False
        
        # Export the report
        logger.info(f"Exporting report for {date_str}")
        export_results = export_report(report_data, date_str)
        
        if export_results.get('status') != 'SUCCESS':
            logger.error(f"Failed to export report for {date_str}: {export_results.get('error')}")
            return False
        
        logger.info(f"Successfully rebuilt report for {date_str} with verified drivers only")
        return True
    
    except Exception as e:
        logger.error(f"Error rebuilding report for {date_str}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def create_integrity_log(date_str: str, scan_results: Dict[str, Any], rebuild_success: bool) -> str:
    """
    Create integrity log for the specified date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        scan_results (Dict[str, Any]): Scan results
        rebuild_success (bool): Whether the report was successfully rebuilt
        
    Returns:
        str: Path to the integrity log
    """
    log_path = f"integrity_audit_{date_str}.txt"
    
    with open(log_path, 'w') as f:
        f.write(f"INTEGRITY AUDIT FOR {date_str}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("SUMMARY:\n")
        f.write("-" * 80 + "\n")
        f.write(f"Verified Drivers: {scan_results['verified_drivers']}\n")
        f.write(f"Total Files Scanned: {scan_results['summary']['total_files']}\n")
        f.write(f"Files with Unverified Drivers: {scan_results['summary']['files_with_unverified_drivers']}\n")
        f.write(f"Total Unverified Drivers: {scan_results['summary']['total_unverified_drivers']}\n")
        f.write(f"Report Rebuild Status: {'SUCCESS' if rebuild_success else 'FAILURE'}\n\n")
        
        f.write("FILE DETAILS:\n")
        f.write("-" * 80 + "\n")
        for file_path, file_info in scan_results['files'].items():
            f.write(f"File: {file_path}\n")
            
            if 'error' in file_info:
                f.write(f"  Error: {file_info['error']}\n")
                continue
                
            f.write(f"  Row Count: {file_info['row_count']}\n")
            f.write(f"  Driver Column: {file_info['driver_column']}\n")
            f.write(f"  Driver Sample: {', '.join(file_info['driver_sample'][:10])}\n")
            f.write(f"  Unverified Drivers: {file_info['unverified_count']} / {file_info['total_drivers']}\n")
            
            if file_path in scan_results['unverified_drivers']:
                f.write(f"  Unverified Driver Names: {', '.join(scan_results['unverified_drivers'][file_path])}\n")
                
            if file_path in scan_results['verified_file_map']:
                f.write(f"  Verified File: {scan_results['verified_file_map'][file_path]}\n")
                
            f.write("\n")
            
        f.write("UNVERIFIED DRIVERS DETECTED:\n")
        f.write("-" * 80 + "\n")
        if scan_results['unverified_drivers']:
            for file_path, drivers in scan_results['unverified_drivers'].items():
                f.write(f"File: {file_path}\n")
                f.write(f"  Unverified Drivers: {len(drivers)}\n")
                for i, driver in enumerate(drivers, 1):
                    f.write(f"  {i}. {driver}\n")
                f.write("\n")
        else:
            f.write("No unverified drivers detected.\n\n")
            
        f.write("REBUILD DETAILS:\n")
        f.write("-" * 80 + "\n")
        if rebuild_success:
            f.write("Daily report successfully rebuilt using only verified drivers.\n")
        else:
            f.write("Failed to rebuild daily report. See logs for details.\n")
            
    logger.info(f"Integrity log saved to {log_path}")
    return log_path

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python source_integrity_sweep.py <date>")
        print("Example: python source_integrity_sweep.py 2025-05-16")
        return
        
    date_str = sys.argv[1]
    
    # Load verified drivers
    verified_drivers = load_verified_drivers()
    logger.info(f"Loaded {len(verified_drivers)} verified drivers")
    
    # Scan source files
    scan_results = scan_source_files(date_str, verified_drivers)
    logger.info(f"Scanned {scan_results['summary']['total_files']} files")
    logger.info(f"Found {scan_results['summary']['total_unverified_drivers']} unverified drivers")
    
    # Rebuild daily report
    rebuild_success = rebuild_daily_report(date_str, scan_results)
    
    # Create integrity log
    log_path = create_integrity_log(date_str, scan_results, rebuild_success)
    
    # Print summary
    print(f"\nSource Integrity Sweep for {date_str}:")
    print("=" * 70)
    print(f"Verified Drivers: {scan_results['verified_drivers']}")
    print(f"Total Files Scanned: {scan_results['summary']['total_files']}")
    print(f"Files with Unverified Drivers: {scan_results['summary']['files_with_unverified_drivers']}")
    print(f"Total Unverified Drivers: {scan_results['summary']['total_unverified_drivers']}")
    print(f"Report Rebuild Status: {'SUCCESS' if rebuild_success else 'FAILURE'}")
    print(f"Integrity Log: {log_path}")
    
    # Print unverified drivers if found
    if scan_results['unverified_drivers']:
        print("\nUnverified Drivers Detected:")
        print("-" * 70)
        for file_path, drivers in scan_results['unverified_drivers'].items():
            print(f"File: {os.path.basename(file_path)}")
            print(f"Unverified Drivers: {', '.join(drivers[:10])}" + ("..." if len(drivers) > 10 else ""))
    else:
        print("\nNo unverified drivers detected. All data passed integrity checks.")

if __name__ == '__main__':
    main()