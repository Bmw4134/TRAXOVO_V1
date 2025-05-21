#!/usr/bin/env python3
"""
TRAXORA GENIUS CORE | Rebuild Verified Reports

This module rebuilds Daily Driver Reports using only verified driver data from authentic sources.
"""

import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
import traceback
from typing import Dict, List, Any, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Make sure logs directory exists
os.makedirs('logs/integrity', exist_ok=True)

# Add file handler for this script
file_handler = logging.FileHandler('logs/integrity/rebuild_verified_reports.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Driver verification constants
BASELINE_FILE = 'data/start_time_job/baseline.csv'
JOB_LIST_FILES = ['attached_assets/01 - DFW APR 2025.csv',
                 'attached_assets/02 - HOU APR 2025.csv',
                 'attached_assets/03 - WT APR 2025.csv']
DRIVING_HISTORY_DIR = 'data/driving_history'
ACTIVITY_DETAIL_DIR = 'data/activity_detail'
ASSETS_TIME_ONSITE_DIR = 'data/assets_time_on_site'

def load_authorized_drivers() -> Set[str]:
    """
    Load all authorized drivers from authentic data sources
    
    Returns:
        Set[str]: Set of normalized authorized driver names
    """
    logger.info("Loading authorized drivers from authentic sources")
    authorized_drivers = set()
    
    # Try to load from baseline file
    if os.path.exists(BASELINE_FILE):
        try:
            df = pd.read_csv(BASELINE_FILE)
            if 'driver_name' in df.columns:
                for driver in df['driver_name'].astype(str).str.strip():
                    if driver and driver.lower() not in ['nan', 'none', 'null', '']:
                        authorized_drivers.add(driver.lower())
                logger.info(f"Loaded {len(authorized_drivers)} drivers from baseline file")
        except Exception as e:
            logger.error(f"Error loading baseline file: {e}")
    
    # Try to load from job list files
    for job_file in JOB_LIST_FILES:
        if os.path.exists(job_file):
            try:
                df = pd.read_csv(job_file)
                
                # Look for driver name column
                driver_cols = ['driver', 'driver_name', 'employee', 'employee_name', 'operator']
                driver_col = None
                
                for col in driver_cols:
                    if col in df.columns:
                        driver_col = col
                        break
                
                if driver_col:
                    for driver in df[driver_col].astype(str).str.strip():
                        if driver and driver.lower() not in ['nan', 'none', 'null', '']:
                            authorized_drivers.add(driver.lower())
                
                logger.info(f"Processed job file: {job_file}")
            except Exception as e:
                logger.error(f"Error loading job file {job_file}: {e}")
    
    # If still no drivers, try to build from DrivingHistory and ActivityDetail
    if not authorized_drivers:
        logger.warning("No authorized drivers from standard sources, building from telemetry data")
        
        # Process driving history files
        if os.path.exists(DRIVING_HISTORY_DIR):
            for filename in os.listdir(DRIVING_HISTORY_DIR):
                if filename.endswith('.csv'):
                    filepath = os.path.join(DRIVING_HISTORY_DIR, filename)
                    try:
                        df = pd.read_csv(filepath)
                        
                        # Normalize column names
                        df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
                        
                        # Look for driver name column
                        driver_cols = ['driver', 'driver_name', 'employee', 'employee_name', 'operator']
                        driver_col = None
                        
                        for col in driver_cols:
                            if col in df.columns:
                                driver_col = col
                                break
                        
                        if driver_col:
                            for driver in df[driver_col].astype(str).str.strip():
                                if driver and driver.lower() not in ['nan', 'none', 'null', '']:
                                    authorized_drivers.add(driver.lower())
                        
                        logger.info(f"Processed driving history file: {filename}")
                    except Exception as e:
                        logger.error(f"Error loading driving history file {filename}: {e}")
        
        # Process activity detail files
        if os.path.exists(ACTIVITY_DETAIL_DIR):
            for filename in os.listdir(ACTIVITY_DETAIL_DIR):
                if filename.endswith('.csv'):
                    filepath = os.path.join(ACTIVITY_DETAIL_DIR, filename)
                    try:
                        df = pd.read_csv(filepath)
                        
                        # Normalize column names
                        df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
                        
                        # Look for driver name column
                        driver_cols = ['driver', 'driver_name', 'employee', 'employee_name', 'operator']
                        driver_col = None
                        
                        for col in driver_cols:
                            if col in df.columns:
                                driver_col = col
                                break
                        
                        if driver_col:
                            for driver in df[driver_col].astype(str).str.strip():
                                if driver and driver.lower() not in ['nan', 'none', 'null', '']:
                                    authorized_drivers.add(driver.lower())
                        
                        logger.info(f"Processed activity detail file: {filename}")
                    except Exception as e:
                        logger.error(f"Error loading activity detail file {filename}: {e}")
    
    logger.info(f"Identified {len(authorized_drivers)} authorized drivers from all sources")
    return authorized_drivers

def identify_fabricated_drivers(all_drivers: List[str], authorized_drivers: Set[str]) -> List[str]:
    """
    Identify potentially fabricated driver names
    
    Args:
        all_drivers (List[str]): List of all driver names
        authorized_drivers (Set[str]): Set of authorized driver names
        
    Returns:
        List[str]: List of potentially fabricated driver names
    """
    # Common fake/placeholder names to detect
    known_fake_patterns = [
        "test", "demo", "placeholder", "sample", "dummy",
        "john doe", "jane doe", "first last", "example"
    ]
    
    fabricated = []
    
    for driver in all_drivers:
        normalized = driver.lower()
        
        # Check if not in authorized list
        if normalized not in authorized_drivers:
            # Check for common patterns
            if any(pattern in normalized for pattern in known_fake_patterns):
                fabricated.append(driver)
                continue
                
            # Check for common fake first-last combinations
            parts = normalized.split()
            if len(parts) == 2:
                first, last = parts
                
                # List of common placeholder first/last names
                common_firsts = ["john", "jane", "bob", "steve", "mary", "sarah", "michael", "david", "robert", "jennifer"]
                common_lasts = ["doe", "smith", "johnson", "williams", "jones", "brown", "davis", "miller", "wilson", "taylor"]
                
                if first in common_firsts and last in common_lasts:
                    fabricated.append(driver)
    
    return fabricated

def scan_driving_history_file(filepath: str) -> Dict[str, Any]:
    """
    Scan a driving history file and extract driver information
    
    Args:
        filepath (str): Path to the driving history file
        
    Returns:
        Dict[str, Any]: Scan results
    """
    result = {
        'filename': os.path.basename(filepath),
        'driver_count': 0,
        'driver_sample': [],
        'asset_ids': set(),
        'driver_asset_map': {}
    }
    
    try:
        df = pd.read_csv(filepath)
        
        # Normalize column names
        df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
        
        # Look for driver and asset columns
        driver_cols = ['driver', 'driver_name', 'employee', 'employee_name', 'operator']
        asset_cols = ['asset', 'asset_id', 'vehicle', 'vehicle_id', 'equipment']
        
        driver_col = None
        asset_col = None
        
        for col in driver_cols:
            if col in df.columns:
                driver_col = col
                break
                
        for col in asset_cols:
            if col in df.columns:
                asset_col = col
                break
        
        if driver_col:
            # Extract driver information
            all_drivers = {}
            
            for _, row in df.iterrows():
                driver = str(row[driver_col]).strip()
                if driver and driver.lower() not in ['nan', 'none', 'null', '']:
                    normalized_driver = driver.lower()
                    
                    # Add to all drivers
                    if normalized_driver not in all_drivers:
                        all_drivers[normalized_driver] = {
                            'name': driver,
                            'count': 1
                        }
                    else:
                        all_drivers[normalized_driver]['count'] += 1
                    
                    # Map driver to asset if available
                    if asset_col:
                        asset = str(row[asset_col]).strip()
                        if asset and asset.lower() not in ['nan', 'none', 'null', '']:
                            result['asset_ids'].add(asset)
                            
                            if normalized_driver not in result['driver_asset_map']:
                                result['driver_asset_map'][normalized_driver] = asset
            
            # Update result
            result['driver_count'] = len(all_drivers)
            result['driver_sample'] = [info['name'] for name, info in list(all_drivers.items())[:10]]
            
        return result
    
    except Exception as e:
        logger.error(f"Error scanning driving history file {filepath}: {e}")
        return result

def collect_report_data(date_str: str) -> Dict[str, Any]:
    """
    Collect all data needed for report rebuilding
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        Dict[str, Any]: Collected report data
    """
    logger.info(f"Collecting report data for {date_str}")
    
    data = {
        'date': date_str,
        'report_data': None,
        'authorized_drivers': set(),
        'fabricated_drivers': [],
        'driving_history_files': [],
        'all_drivers': set()
    }
    
    # Load authorized drivers
    data['authorized_drivers'] = load_authorized_drivers()
    
    # Load existing report if available
    report_path = f"reports/daily_drivers/daily_report_{date_str}.json"
    if os.path.exists(report_path):
        try:
            with open(report_path, 'r') as f:
                data['report_data'] = json.load(f)
            
            # Extract all drivers from report
            if data['report_data']:
                drivers = data['report_data'].get('drivers', [])
                for driver in drivers:
                    name = driver.get('driver_name', '')
                    if name:
                        data['all_drivers'].add(name)
            
            logger.info(f"Loaded existing report for {date_str} with {len(data['all_drivers'])} drivers")
        except Exception as e:
            logger.error(f"Error loading report {report_path}: {e}")
    
    # Identify potentially fabricated drivers
    data['fabricated_drivers'] = identify_fabricated_drivers(list(data['all_drivers']), data['authorized_drivers'])
    
    # Scan driving history files
    if os.path.exists(DRIVING_HISTORY_DIR):
        for filename in os.listdir(DRIVING_HISTORY_DIR):
            # Check if file is for the specified date
            date_part = date_str.replace('-', '')
            if date_part in filename and filename.endswith('.csv'):
                filepath = os.path.join(DRIVING_HISTORY_DIR, filename)
                result = scan_driving_history_file(filepath)
                data['driving_history_files'].append(result)
    
    return data

def create_integrity_report(date_str: str, report_data: Dict[str, Any]) -> str:
    """
    Create a detailed integrity report
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        report_data (Dict[str, Any]): Report data
        
    Returns:
        str: Path to the integrity report
    """
    report_path = f"integrity_audit_{date_str}.txt"
    
    with open(report_path, 'w') as f:
        f.write(f"TRAXORA GENIUS CORE | SOURCE INTEGRITY AUDIT\n")
        f.write(f"Date: {date_str}\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("SOURCE FILE ANALYSIS\n")
        f.write("-" * 80 + "\n")
        
        for file_data in report_data['driving_history_files']:
            f.write(f"File: {file_data['filename']}\n")
            f.write(f"  Driver Count: {file_data['driver_count']}\n")
            f.write(f"  Asset Count: {len(file_data['asset_ids'])}\n")
            f.write(f"  Driver Sample: {', '.join(file_data['driver_sample'])}\n\n")
        
        f.write("DRIVER VERIFICATION\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total Authorized Drivers: {len(report_data['authorized_drivers'])}\n")
        
        if report_data['report_data']:
            drivers = report_data['report_data'].get('drivers', [])
            f.write(f"Drivers in Report: {len(drivers)}\n")
            
            # Count verified and unverified
            verified = sum(1 for d in drivers if d.get('driver_name', '').lower() in report_data['authorized_drivers'])
            unverified = len(drivers) - verified
            
            f.write(f"Verified Drivers: {verified}\n")
            f.write(f"Unverified Drivers: {unverified}\n")
        
        if report_data['fabricated_drivers']:
            f.write("\nPOTENTIALLY FABRICATED DRIVERS\n")
            f.write("-" * 80 + "\n")
            for driver in report_data['fabricated_drivers']:
                f.write(f"- {driver}\n")
        
        f.write("\nAUTHORIZED DRIVER LIST\n")
        f.write("-" * 80 + "\n")
        for driver in sorted(report_data['authorized_drivers']):
            f.write(f"- {driver}\n")
    
    logger.info(f"Integrity report saved to {report_path}")
    return report_path

def rebuild_report(date_str: str, report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rebuild a Daily Driver Report with only verified drivers
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        report_data (Dict[str, Any]): Report data
        
    Returns:
        Dict[str, Any]: Results of rebuilding
    """
    logger.info(f"Rebuilding report for {date_str}")
    
    result = {
        'date': date_str,
        'status': 'FAILED',
        'error': None,
        'changes': {
            'removed_drivers': [],
            'verified_drivers': 0
        }
    }
    
    try:
        # Check if we have report data
        if not report_data['report_data']:
            result['error'] = "No report data available to rebuild"
            return result
        
        # Create a copy of the report
        verified_report = report_data['report_data'].copy()
        
        # Filter drivers to include only verified ones
        original_drivers = verified_report.get('drivers', [])
        verified_drivers = []
        
        for driver in original_drivers:
            driver_name = driver.get('driver_name', '')
            
            if driver_name.lower() in report_data['authorized_drivers']:
                # Mark as verified
                driver['identity_verified'] = True
                verified_drivers.append(driver)
            else:
                # Track removed drivers
                result['changes']['removed_drivers'].append(driver_name)
        
        # Update report with verified drivers
        verified_report['drivers'] = verified_drivers
        
        # Update summary
        if 'summary' in verified_report:
            summary = verified_report['summary']
            
            # Recalculate counts
            summary['total'] = len(verified_drivers)
            summary['late'] = sum(1 for d in verified_drivers if d.get('status') == 'Late')
            summary['early_end'] = sum(1 for d in verified_drivers if d.get('status') == 'Early End')
            summary['not_on_job'] = sum(1 for d in verified_drivers if d.get('status') == 'Not On Job')
            summary['on_time'] = sum(1 for d in verified_drivers if d.get('status') == 'On Time')
        
        # Add verification metadata
        if 'metadata' not in verified_report:
            verified_report['metadata'] = {}
            
        verified_report['metadata']['identity_verification'] = {
            'timestamp': datetime.now().isoformat(),
            'drivers_before_verification': len(original_drivers),
            'verified_drivers': len(verified_drivers),
            'removed_drivers': len(result['changes']['removed_drivers']),
            'signature': "IDENTITY-VERIFIED"
        }
        
        # Save rebuilt report
        output_dir = Path('reports/daily_drivers')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / f"daily_report_{date_str}_verified.json"
        with open(output_path, 'w') as f:
            json.dump(verified_report, f, indent=2, default=str)
            
        # Save Excel version
        excel_path = output_dir / f"daily_report_{date_str}_verified.xlsx"
        pd.DataFrame(verified_drivers).to_excel(excel_path, index=False)
        
        # Update result
        result['status'] = 'SUCCESS'
        result['output_path'] = str(output_path)
        result['excel_path'] = str(excel_path)
        result['changes']['verified_drivers'] = len(verified_drivers)
        
        logger.info(f"Report rebuilt successfully with {len(verified_drivers)} verified drivers")
        return result
    
    except Exception as e:
        logger.error(f"Error rebuilding report: {e}")
        logger.error(traceback.format_exc())
        
        result['error'] = str(e)
        return result

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TRAXORA GENIUS CORE | Rebuild Verified Reports')
    parser.add_argument('date', help='Date to process in YYYY-MM-DD format')
    
    args = parser.parse_args()
    
    # Collect report data
    report_data = collect_report_data(args.date)
    
    # Create integrity report
    integrity_report = create_integrity_report(args.date, report_data)
    
    # Rebuild report
    rebuild_result = rebuild_report(args.date, report_data)
    
    # Print results
    print(f"\nSource Integrity Audit for {args.date}:")
    print("=" * 70)
    print(f"Integrity Report: {integrity_report}")
    
    if rebuild_result['status'] == 'SUCCESS':
        print(f"\nReport Rebuilt Successfully:")
        print("-" * 70)
        print(f"Verified Drivers: {rebuild_result['changes']['verified_drivers']}")
        print(f"Removed Drivers: {len(rebuild_result['changes']['removed_drivers'])}")
        
        if rebuild_result['changes']['removed_drivers']:
            print(f"\nRemoved Drivers:")
            for driver in rebuild_result['changes']['removed_drivers']:
                print(f"- {driver}")
                
        print(f"\nVerified Report: {rebuild_result['output_path']}")
    else:
        print(f"\nReport Rebuild Failed:")
        print("-" * 70)
        print(f"Error: {rebuild_result['error']}")

if __name__ == '__main__':
    main()