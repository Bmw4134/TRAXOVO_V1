#!/usr/bin/env python3
"""
GENIUS CORE | Permanent Integrity Enforcement Chain
Purpose: Prevent ghost/fake driver entries, enforce traceable inputs, and clean reports on every run
"""

import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Create logs and quarantine directories
os.makedirs('logs/integrity', exist_ok=True)
os.makedirs('data/quarantine', exist_ok=True)

# Set up file handler for this script
file_handler = logging.FileHandler('logs/integrity/integrity_enforcement.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Constants
VERIFIED_DRIVERS_CACHE_FILE = 'data/verified_drivers_cache.json'
BASELINE_FILE = 'data/start_time_job/baseline.csv'
COMPANY_EMPLOYEE_FILE = 'attached_assets/Consolidated_Employee_And_Job_Lists_Corrected.xlsx'

def load_verified_drivers_cache() -> Set[str]:
    """
    Load cached verified driver names, or rebuild if necessary
    
    Returns:
        Set[str]: Set of normalized verified driver names
    """
    # Check if cache exists and is recent (less than 24 hours old)
    if os.path.exists(VERIFIED_DRIVERS_CACHE_FILE):
        cache_mtime = os.path.getmtime(VERIFIED_DRIVERS_CACHE_FILE)
        cache_age = datetime.now().timestamp() - cache_mtime
        
        if cache_age < 24 * 3600:  # Less than 24 hours old
            try:
                with open(VERIFIED_DRIVERS_CACHE_FILE, 'r') as f:
                    cache_data = json.load(f)
                    return set(cache_data.get('verified_drivers', []))
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
    
    # Rebuild cache
    verified_drivers = rebuild_verified_drivers_cache()
    return verified_drivers

def rebuild_verified_drivers_cache() -> Set[str]:
    """
    Rebuild the verified drivers cache from authentic sources
    
    Returns:
        Set[str]: Set of normalized verified driver names
    """
    logger.info("Rebuilding verified drivers cache")
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
                logger.info(f"Added {len(verified_drivers)} drivers from baseline file")
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
                    initial_count = len(verified_drivers)
                    for employee in df[employee_col].astype(str).str.strip():
                        if employee and employee.lower() not in ['nan', 'none', 'null', '']:
                            verified_drivers.add(employee.strip().lower())
                    logger.info(f"Added {len(verified_drivers) - initial_count} drivers from employee list")
            except Exception as e:
                logger.warning(f"Error loading employee file as Excel: {e}")
        except Exception as e:
            logger.error(f"Error loading employee file: {e}")
    
    # Save cache
    try:
        with open(VERIFIED_DRIVERS_CACHE_FILE, 'w') as f:
            json.dump({
                'verified_drivers': list(verified_drivers),
                'timestamp': datetime.now().isoformat(),
                'source_files': [BASELINE_FILE, COMPANY_EMPLOYEE_FILE]
            }, f, indent=2)
        logger.info(f"Saved {len(verified_drivers)} verified drivers to cache")
    except Exception as e:
        logger.error(f"Error saving cache: {e}")
    
    return verified_drivers

def scan_source_file(file_path: str, verified_drivers: Set[str]) -> Dict[str, Any]:
    """
    Scan a source file for unverified drivers
    
    Args:
        file_path (str): Path to the source file
        verified_drivers (Set[str]): Set of verified driver names
        
    Returns:
        Dict[str, Any]: Scan results
    """
    try:
        # Determine file type and load
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            return {
                'status': 'error',
                'error': 'Unsupported file type',
                'file_path': file_path
            }
            
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
            return {
                'status': 'error',
                'error': 'No driver column found',
                'file_path': file_path,
                'row_count': row_count
            }
        
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
        
        # If unverified drivers found, create clean version
        cleaned_file_path = None
        if unverified_drivers:
            # Isolate unverified driver rows
            mask = ~df[driver_col].astype(str).str.strip().str.lower().isin([d.lower() for d in unverified_drivers])
            cleaned_df = df[mask].copy()
            
            # Save cleaned file
            cleaned_file_path = file_path.replace('.csv', '_verified.csv').replace('.xlsx', '_verified.csv')
            cleaned_df.to_csv(cleaned_file_path, index=False)
            
            # Move original to quarantine
            quarantine_path = os.path.join('data/quarantine', os.path.basename(file_path))
            try:
                import shutil
                shutil.copy2(file_path, quarantine_path)
                logger.info(f"Quarantined original file: {quarantine_path}")
            except Exception as e:
                logger.error(f"Error quarantining file: {e}")
        
        return {
            'status': 'success',
            'file_path': file_path,
            'row_count': row_count,
            'driver_column': driver_col,
            'driver_sample': driver_names[:10],
            'unverified_count': len(unverified_drivers),
            'unverified_drivers': unverified_drivers,
            'total_drivers': len(driver_names),
            'cleaned_file_path': cleaned_file_path
        }
        
    except Exception as e:
        logger.error(f"Error scanning file {file_path}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'status': 'error',
            'error': str(e),
            'file_path': file_path
        }

def find_source_files_for_date(date_str: str) -> List[str]:
    """
    Find all source files for a specific date
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        List[str]: List of file paths
    """
    source_files = []
    
    # Source file directories to scan
    source_dirs = {
        'driving_history': 'data/driving_history',
        'activity_detail': 'data/activity_detail'
    }
    
    # Find files for each source type
    for source_type, dir_path in source_dirs.items():
        if not os.path.exists(dir_path):
            continue
            
        for file_name in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file_name)
            
            # Only include files for the specified date
            if (date_str.replace('-', '') in file_name or date_str in file_name) and '_verified' not in file_name:
                source_files.append(file_path)
    
    return source_files

def send_alert(date_str: str, unverified_count: int, files_affected: List[str], sample_names: List[str]):
    """
    Send alert if unverified drivers are found
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        unverified_count (int): Number of unverified drivers
        files_affected (List[str]): List of affected files
        sample_names (List[str]): Sample of unverified driver names
    """
    logger.warning(f"Alert: {unverified_count} unverified drivers found in {len(files_affected)} files for {date_str}")
    
    # Write alert to file
    alert_path = f"logs/integrity/alert_{date_str}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    with open(alert_path, 'w') as f:
        json.dump({
            'date': date_str,
            'timestamp': datetime.now().isoformat(),
            'unverified_count': unverified_count,
            'files_affected': files_affected,
            'sample_names': sample_names
        }, f, indent=2)
    
    # Here you would typically send an email or webhook notification
    # Example:
    # if 'SENDGRID_API_KEY' in os.environ:
    #     from sendgrid import SendGridAPIClient
    #     from sendgrid.helpers.mail import Mail
    #     message = Mail(
    #         from_email='alerts@traxora.com',
    #         to_emails='admin@example.com',
    #         subject=f'ALERT: {unverified_count} unverified drivers in TRAXORA data for {date_str}',
    #         html_content=f'<p>Found {unverified_count} unverified drivers in files: {", ".join(files_affected)}</p>'
    #     )
    #     sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    #     sg.send(message)
    
    logger.info(f"Alert saved to {alert_path}")

def log_integrity_result(date_str: str, result: Dict[str, Any]):
    """
    Log integrity check result
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        result (Dict[str, Any]): Integrity check result
    """
    log_path = f"logs/integrity/integrity_check_{date_str}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    with open(log_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    logger.info(f"Integrity check result logged to {log_path}")
    
    # Create human-readable audit log
    audit_path = f"integrity_audit_{date_str}.txt"
    with open(audit_path, 'w') as f:
        f.write(f"INTEGRITY AUDIT FOR {date_str}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("SUMMARY:\n")
        f.write("-" * 80 + "\n")
        f.write(f"Verified Drivers in System: {result['verified_driver_count']}\n")
        f.write(f"Total Files Scanned: {len(result['scanned_files'])}\n")
        f.write(f"Files with Unverified Drivers: {len(result['problematic_files'])}\n")
        f.write(f"Total Unverified Drivers: {result['total_unverified']}\n\n")
        
        f.write("FILE DETAILS:\n")
        f.write("-" * 80 + "\n")
        for file_result in result['scanned_files']:
            f.write(f"File: {file_result['file_path']}\n")
            
            if file_result['status'] == 'error':
                f.write(f"  Error: {file_result['error']}\n")
                continue
                
            f.write(f"  Row Count: {file_result['row_count']}\n")
            f.write(f"  Driver Column: {file_result['driver_column']}\n")
            f.write(f"  Driver Sample: {', '.join(file_result['driver_sample'][:10])}\n")
            f.write(f"  Unverified Drivers: {file_result['unverified_count']} / {file_result['total_drivers']}\n")
            
            if file_result['unverified_count'] > 0:
                f.write(f"  Unverified Driver Names: {', '.join(file_result['unverified_drivers'][:10])}")
                if len(file_result['unverified_drivers']) > 10:
                    f.write(f" and {len(file_result['unverified_drivers']) - 10} more")
                f.write("\n")
                
            if file_result['cleaned_file_path']:
                f.write(f"  Cleaned File: {file_result['cleaned_file_path']}\n")
                
            f.write("\n")
    
    logger.info(f"Audit log created at {audit_path}")

def run_sweep(date_str: str) -> Dict[str, Any]:
    """
    Run integrity sweep for a specific date
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        Dict[str, Any]: Sweep results
    """
    logger.info(f"Running integrity sweep for {date_str}")
    
    # Load verified drivers
    verified_drivers = load_verified_drivers_cache()
    logger.info(f"Loaded {len(verified_drivers)} verified drivers")
    
    # Find source files
    source_files = find_source_files_for_date(date_str)
    logger.info(f"Found {len(source_files)} source files for {date_str}")
    
    # Scan each file
    scan_results = []
    problematic_files = []
    all_unverified_drivers = []
    
    for file_path in source_files:
        result = scan_source_file(file_path, verified_drivers)
        scan_results.append(result)
        
        if result['status'] == 'success' and result['unverified_count'] > 0:
            problematic_files.append(file_path)
            all_unverified_drivers.extend(result['unverified_drivers'])
    
    # Send alert if unverified drivers found
    if all_unverified_drivers:
        send_alert(
            date_str,
            len(all_unverified_drivers),
            problematic_files,
            all_unverified_drivers[:10]
        )
    
    # Prepare result
    sweep_result = {
        'date': date_str,
        'timestamp': datetime.now().isoformat(),
        'verified_driver_count': len(verified_drivers),
        'source_file_count': len(source_files),
        'problematic_files': problematic_files,
        'total_unverified': len(all_unverified_drivers),
        'unverified_count': len(all_unverified_drivers),
        'scanned_files': scan_results
    }
    
    # Log result
    log_integrity_result(date_str, sweep_result)
    
    return sweep_result

def enforce_integrity_before_report(date_str: str):
    """
    Enforce integrity before generating a report
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
    """
    print(f"Running GENIUS CORE integrity sweep for {date_str}")
    sweep_result = run_sweep(date_str)

    if sweep_result['unverified_count'] > 0:
        print(f"[!] ALERT: {sweep_result['unverified_count']} unverified drivers found for {date_str}")
        print(f"[!] Removing contaminated records and rebuilding clean input set")

    print(f"Generating validated report for {date_str}...")
    
    # Import the genius_processor
    sys.path.append('.')
    from genius_processor import process_and_export
    
    # Process and export report
    result = process_and_export(date_str)
    
    if result['status'] == 'SUCCESS':
        print(f"[✓] Daily report for {date_str} rebuilt with verified data only.")
    else:
        print(f"[×] Error generating report for {date_str}: {result.get('error', 'Unknown error')}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        # Run for today and yesterday if no date provided
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        dates = [today.strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d")]
        
        for date_str in dates:
            enforce_integrity_before_report(date_str)
    else:
        # Run for the specified date
        date_str = sys.argv[1]
        enforce_integrity_before_report(date_str)

if __name__ == "__main__":
    main()