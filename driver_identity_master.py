#!/usr/bin/env python3
"""
TRAXORA GENIUS CORE | Driver Identity Master

This module implements the comprehensive driver identity master system that:
1. Uses the employee master list as the source of truth
2. Maps assets to authorized drivers
3. Verifies all data against this master source
4. Prevents any unverified/fabricated driver data in reports
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
import traceback
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple

# Create logs directory if it doesn't exist
os.makedirs('logs/identity', exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Create identity mapper log file
file_handler = logging.FileHandler('logs/identity/driver_identity_master.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Path to employee master list
EMPLOYEE_MASTER_LIST = 'data/employee_master_list.csv'

# Output paths
IDENTITY_MAP_FILE = 'data/driver_identity_map.json'
ASSET_DRIVER_MAP_FILE = 'data/asset_driver_map.json'

def load_employee_master_list() -> Dict[str, Dict[str, Any]]:
    """
    Load the employee master list
    
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary mapping employee IDs to employee data
    """
    employee_data = {}
    
    if not os.path.exists(EMPLOYEE_MASTER_LIST):
        logger.error(f"Employee master list not found: {EMPLOYEE_MASTER_LIST}")
        return employee_data
    
    try:
        # Load employee list
        df = pd.read_csv(EMPLOYEE_MASTER_LIST)
        
        # Check for required columns
        required_columns = ['employee_id', 'employee_name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns in employee master list: {missing_columns}")
            return employee_data
        
        # Create driver name lookup for normalization
        driver_name_lookup = {}
        
        # Process each employee
        for _, row in df.iterrows():
            employee_id = str(row['employee_id']).strip()
            name = str(row['employee_name']).strip()
            
            # Skip invalid entries
            if not employee_id or not name or name.lower() in ['nan', 'none', 'null', '']:
                continue
            
            # Create normalized name
            normalized_name = name.lower()
            
            # Create employee record
            employee_record = {
                'employee_id': employee_id,
                'name': name,
                'normalized_name': normalized_name
            }
            
            # Add any additional columns
            for column in df.columns:
                if column not in ['employee_id', 'employee_name']:
                    employee_record[column] = row[column]
            
            # Add to employee data by ID
            employee_data[employee_id] = employee_record
            
            # Add to driver name lookup
            driver_name_lookup[normalized_name] = employee_id
        
        # Add lookups to each employee record
        for employee_id, record in employee_data.items():
            record['name_lookup'] = driver_name_lookup
        
        logger.info(f"Loaded {len(employee_data)} employees from master list")
        
    except Exception as e:
        logger.error(f"Error loading employee master list: {e}")
        logger.error(traceback.format_exc())
    
    return employee_data

def create_asset_driver_map(employee_data: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Create a mapping from asset IDs to authorized drivers
    
    Args:
        employee_data (Dict[str, Dict[str, Any]]): Employee data from master list
        
    Returns:
        Dict[str, Dict[str, Any]]: Mapping from asset IDs to authorized drivers
    """
    asset_driver_map = {}
    
    # Create mapping from asset IDs to employee records
    for employee_id, record in employee_data.items():
        if 'asset_id' in record and record['asset_id']:
            asset_id = str(record['asset_id']).strip()
            
            if asset_id and asset_id.lower() not in ['nan', 'none', 'null', '']:
                # Normalize asset ID
                normalized_asset_id = asset_id.upper()
                
                # Create asset record
                asset_record = {
                    'asset_id': asset_id,
                    'normalized_asset_id': normalized_asset_id,
                    'employee_id': employee_id,
                    'driver_name': record['name'],
                    'normalized_name': record['normalized_name']
                }
                
                # Add to asset mapping
                asset_driver_map[normalized_asset_id] = asset_record
    
    logger.info(f"Created asset driver map with {len(asset_driver_map)} entries")
    
    # Save asset driver map to file
    try:
        os.makedirs(os.path.dirname(ASSET_DRIVER_MAP_FILE), exist_ok=True)
        
        with open(ASSET_DRIVER_MAP_FILE, 'w') as f:
            json.dump({
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'source': EMPLOYEE_MASTER_LIST,
                    'count': len(asset_driver_map)
                },
                'asset_driver_map': asset_driver_map
            }, f, indent=2)
            
        logger.info(f"Saved asset driver map to {ASSET_DRIVER_MAP_FILE}")
    except Exception as e:
        logger.error(f"Error saving asset driver map: {e}")
    
    return asset_driver_map

def create_driver_identity_map(employee_data: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Create the comprehensive driver identity mapping
    
    Args:
        employee_data (Dict[str, Dict[str, Any]]): Employee data from master list
        
    Returns:
        Dict[str, Dict[str, Any]]: Driver identity map
    """
    identity_map = {}
    
    # Create identity mapping for each driver name
    for employee_id, record in employee_data.items():
        normalized_name = record['normalized_name']
        
        # Create identity record
        identity_record = {
            'employee_id': employee_id,
            'name': record['name'],
            'normalized_name': normalized_name
        }
        
        # Add any additional fields
        for field, value in record.items():
            if field not in ['employee_id', 'name', 'normalized_name', 'name_lookup']:
                identity_record[field] = value
        
        # Add to identity map
        identity_map[normalized_name] = identity_record
    
    logger.info(f"Created driver identity map with {len(identity_map)} entries")
    
    # Save identity map to file
    try:
        os.makedirs(os.path.dirname(IDENTITY_MAP_FILE), exist_ok=True)
        
        with open(IDENTITY_MAP_FILE, 'w') as f:
            json.dump({
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'source': EMPLOYEE_MASTER_LIST,
                    'count': len(identity_map)
                },
                'identity_map': identity_map
            }, f, indent=2)
            
        logger.info(f"Saved driver identity map to {IDENTITY_MAP_FILE}")
    except Exception as e:
        logger.error(f"Error saving driver identity map: {e}")
    
    return identity_map

def verify_driver_name(driver_name: str, identity_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verify a driver name against the identity map
    
    Args:
        driver_name (str): Driver name to verify
        identity_map (Dict[str, Dict[str, Any]]): Driver identity map
        
    Returns:
        Dict[str, Any]: Verification result
    """
    result = {
        'driver_name': driver_name,
        'normalized_name': driver_name.lower(),
        'verified': False,
        'employee_id': None,
        'identity': None
    }
    
    # Check if driver is in identity map
    if driver_name.lower() in identity_map:
        # Get identity record
        identity = identity_map[driver_name.lower()]
        
        # Update result
        result['verified'] = True
        result['employee_id'] = identity['employee_id']
        result['identity'] = identity
    
    return result

def verify_asset_id(asset_id: str, asset_driver_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verify an asset ID against the asset driver map
    
    Args:
        asset_id (str): Asset ID to verify
        asset_driver_map (Dict[str, Dict[str, Any]]): Asset driver map
        
    Returns:
        Dict[str, Any]: Verification result
    """
    result = {
        'asset_id': asset_id,
        'normalized_asset_id': asset_id.upper(),
        'verified': False,
        'driver_name': None,
        'employee_id': None,
        'asset_data': None
    }
    
    # Check if asset is in asset driver map
    if asset_id.upper() in asset_driver_map:
        # Get asset record
        asset_data = asset_driver_map[asset_id.upper()]
        
        # Update result
        result['verified'] = True
        result['driver_name'] = asset_data['driver_name']
        result['employee_id'] = asset_data['employee_id']
        result['asset_data'] = asset_data
    
    return result

def scan_source_file_for_unverified_drivers(
    file_path: str, 
    identity_map: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Scan a source file for unverified drivers
    
    Args:
        file_path (str): Path to the source file
        identity_map (Dict[str, Dict[str, Any]]): Driver identity map
        
    Returns:
        Dict[str, Any]: Scan results
    """
    result = {
        'file_path': file_path,
        'verified_drivers': [],
        'unverified_drivers': [],
        'total_drivers': 0,
        'verification_rate': 0.0
    }
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return result
        
        # Determine file type and load
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_path}")
            return result
        
        # Standardize column names
        df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
        
        # Look for driver column
        driver_cols = ['driver', 'driver_name', 'drivername', 'employee', 'employee_name', 'name']
        driver_col = None
        
        for col in driver_cols:
            if col in df.columns:
                driver_col = col
                break
        
        if not driver_col:
            logger.warning(f"No driver column found in {file_path}")
            return result
        
        # Scan for drivers
        for _, row in df.iterrows():
            driver_name = str(row[driver_col]).strip()
            
            # Skip empty driver names
            if not driver_name or driver_name.lower() in ['nan', 'none', 'null', '']:
                continue
            
            # Verify driver name
            verification = verify_driver_name(driver_name, identity_map)
            
            if verification['verified']:
                if driver_name not in result['verified_drivers']:
                    result['verified_drivers'].append(driver_name)
            else:
                if driver_name not in result['unverified_drivers']:
                    result['unverified_drivers'].append(driver_name)
        
        # Update statistics
        result['total_drivers'] = len(result['verified_drivers']) + len(result['unverified_drivers'])
        
        if result['total_drivers'] > 0:
            result['verification_rate'] = len(result['verified_drivers']) / result['total_drivers'] * 100
        
    except Exception as e:
        logger.error(f"Error scanning file {file_path}: {e}")
        logger.error(traceback.format_exc())
    
    return result

def scan_report_for_unverified_drivers(
    date_str: str,
    identity_map: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Scan a Daily Driver Report for unverified drivers
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        identity_map (Dict[str, Dict[str, Any]]): Driver identity map
        
    Returns:
        Dict[str, Any]: Scan results
    """
    result = {
        'date': date_str,
        'report_path': None,
        'verified_drivers': [],
        'unverified_drivers': [],
        'total_drivers': 0,
        'verification_rate': 0.0,
        'report_data': None
    }
    
    try:
        # Check for report file
        report_path = f"reports/daily_drivers/daily_report_{date_str}.json"
        
        if not os.path.exists(report_path):
            logger.warning(f"Report not found: {report_path}")
            return result
        
        result['report_path'] = report_path
        
        # Load report
        with open(report_path, 'r') as f:
            report_data = json.load(f)
            
        result['report_data'] = report_data
        
        # Check for drivers
        drivers = report_data.get('drivers', [])
        
        # Scan for drivers
        for driver in drivers:
            driver_name = driver.get('driver_name', '').strip()
            
            # Skip empty driver names
            if not driver_name:
                continue
            
            # Verify driver name
            verification = verify_driver_name(driver_name, identity_map)
            
            if verification['verified']:
                if driver_name not in result['verified_drivers']:
                    result['verified_drivers'].append(driver_name)
            else:
                if driver_name not in result['unverified_drivers']:
                    result['unverified_drivers'].append(driver_name)
        
        # Update statistics
        result['total_drivers'] = len(result['verified_drivers']) + len(result['unverified_drivers'])
        
        if result['total_drivers'] > 0:
            result['verification_rate'] = len(result['verified_drivers']) / result['total_drivers'] * 100
        
    except Exception as e:
        logger.error(f"Error scanning report for {date_str}: {e}")
        logger.error(traceback.format_exc())
    
    return result

def rebuild_report_with_verified_drivers(
    date_str: str,
    identity_map: Dict[str, Dict[str, Any]],
    asset_driver_map: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Rebuild a Daily Driver Report with only verified drivers
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        identity_map (Dict[str, Dict[str, Any]]): Driver identity map
        asset_driver_map (Dict[str, Dict[str, Any]]): Asset driver map
        
    Returns:
        Dict[str, Any]: Rebuild results
    """
    result = {
        'date': date_str,
        'success': False,
        'error': None,
        'original_report': None,
        'verified_report': None,
        'removed_drivers': [],
        'verified_drivers': [],
        'changes': {
            'original_count': 0,
            'verified_count': 0,
            'removed_count': 0
        }
    }
    
    try:
        # Check for report file
        report_path = f"reports/daily_drivers/daily_report_{date_str}.json"
        
        if not os.path.exists(report_path):
            result['error'] = f"Report not found: {report_path}"
            return result
        
        # Load report
        with open(report_path, 'r') as f:
            report_data = json.load(f)
            
        result['original_report'] = report_path
        
        # Get drivers
        drivers = report_data.get('drivers', [])
        result['changes']['original_count'] = len(drivers)
        
        # Create new verified drivers list
        verified_drivers = []
        
        # Process each driver
        for driver in drivers:
            driver_name = driver.get('driver_name', '').strip()
            
            # Skip empty driver names
            if not driver_name:
                continue
            
            # Verify driver name
            verification = verify_driver_name(driver_name, identity_map)
            
            if verification['verified']:
                # Add verified identity information
                driver['identity_verified'] = True
                driver['employee_id'] = verification['employee_id']
                
                # Add employee details if available
                identity = verification['identity']
                if identity:
                    for field, value in identity.items():
                        if field not in ['employee_id', 'name', 'normalized_name', 'name_lookup']:
                            driver[f'employee_{field}'] = value
                
                # Add to verified drivers
                verified_drivers.append(driver)
                result['verified_drivers'].append(driver_name)
            else:
                # Add to removed drivers
                result['removed_drivers'].append(driver_name)
        
        # Update count
        result['changes']['verified_count'] = len(verified_drivers)
        result['changes']['removed_count'] = len(result['removed_drivers'])
        
        # Update report with verified drivers
        verified_report = report_data.copy()
        verified_report['drivers'] = verified_drivers
        
        # Update summary if present
        if 'summary' in verified_report:
            summary = verified_report['summary']
            
            # Recalculate counts
            summary['total'] = len(verified_drivers)
            summary['late'] = sum(1 for d in verified_drivers if d.get('status') == 'Late')
            summary['early_end'] = sum(1 for d in verified_drivers if d.get('status') == 'Early End')
            summary['not_on_job'] = sum(1 for d in verified_drivers if d.get('status') == 'Not On Job')
            summary['on_time'] = sum(1 for d in verified_drivers if d.get('status') == 'On Time')
        
        # Add identity verification signature
        if 'metadata' not in verified_report:
            verified_report['metadata'] = {}
            
        verified_report['metadata']['identity_verification'] = {
            'timestamp': datetime.now().isoformat(),
            'source': EMPLOYEE_MASTER_LIST,
            'original_driver_count': result['changes']['original_count'],
            'verified_driver_count': result['changes']['verified_count'],
            'removed_driver_count': result['changes']['removed_count'],
            'signature': "IDENTITY-VERIFIED"
        }
        
        # Save verified report
        verified_report_path = f"reports/daily_drivers/daily_report_{date_str}_identity_verified.json"
        exports_path = f"exports/daily_reports/daily_report_{date_str}_identity_verified.json"
        
        # Make sure directories exist
        os.makedirs(os.path.dirname(verified_report_path), exist_ok=True)
        os.makedirs(os.path.dirname(exports_path), exist_ok=True)
        
        # Save reports
        with open(verified_report_path, 'w') as f:
            json.dump(verified_report, f, indent=2, default=str)
            
        with open(exports_path, 'w') as f:
            json.dump(verified_report, f, indent=2, default=str)
        
        # Save Excel version
        excel_path = f"reports/daily_drivers/daily_report_{date_str}_identity_verified.xlsx"
        
        # Convert drivers to DataFrame
        driver_df = pd.DataFrame(verified_drivers)
        driver_df.to_excel(excel_path, index=False)
        
        # Update result
        result['success'] = True
        result['verified_report'] = verified_report_path
        
        logger.info(f"Rebuilt report for {date_str} with {len(verified_drivers)} verified drivers")
        
    except Exception as e:
        logger.error(f"Error rebuilding report for {date_str}: {e}")
        logger.error(traceback.format_exc())
        
        result['error'] = str(e)
        
    return result

def create_identity_audit_report(
    date_str: str,
    scan_results: Dict[str, Any],
    source_scan_results: List[Dict[str, Any]],
    rebuild_results: Dict[str, Any]
) -> str:
    """
    Create a comprehensive identity audit report
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        scan_results (Dict[str, Any]): Report scan results
        source_scan_results (List[Dict[str, Any]]): Source file scan results
        rebuild_results (Dict[str, Any]): Report rebuild results
        
    Returns:
        str: Path to the audit report
    """
    report_path = f"integrity_audit_{date_str}.txt"
    
    with open(report_path, 'w') as f:
        f.write(f"TRAXORA GENIUS CORE | INTEGRITY AUDIT REPORT\n")
        f.write(f"Date: {date_str}\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("SOURCE FILE ANALYSIS\n")
        f.write("-" * 80 + "\n")
        
        for result in source_scan_results:
            f.write(f"File: {result['file_path']}\n")
            f.write(f"  Total Drivers: {result['total_drivers']}\n")
            f.write(f"  Verified Drivers: {len(result['verified_drivers'])} ({result['verification_rate']:.1f}%)\n")
            f.write(f"  Unverified Drivers: {len(result['unverified_drivers'])}\n")
            
            if result['unverified_drivers']:
                f.write(f"  Unverified Driver Names: {', '.join(result['unverified_drivers'])}\n")
                
            f.write("\n")
        
        f.write("REPORT ANALYSIS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Report Path: {scan_results['report_path']}\n")
        f.write(f"Total Drivers: {scan_results['total_drivers']}\n")
        f.write(f"Verified Drivers: {len(scan_results['verified_drivers'])} ({scan_results['verification_rate']:.1f}%)\n")
        f.write(f"Unverified Drivers: {len(scan_results['unverified_drivers'])}\n")
        
        if scan_results['unverified_drivers']:
            f.write(f"Unverified Driver Names: {', '.join(scan_results['unverified_drivers'])}\n")
            
        f.write("\n")
        
        f.write("REBUILD RESULTS\n")
        f.write("-" * 80 + "\n")
        
        if rebuild_results['success']:
            f.write(f"Original Driver Count: {rebuild_results['changes']['original_count']}\n")
            f.write(f"Verified Driver Count: {rebuild_results['changes']['verified_count']}\n")
            f.write(f"Removed Driver Count: {rebuild_results['changes']['removed_count']}\n")
            f.write(f"Verified Report: {rebuild_results['verified_report']}\n")
            
            if rebuild_results['removed_drivers']:
                f.write(f"\nRemoved Drivers: {', '.join(rebuild_results['removed_drivers'])}\n")
        else:
            f.write(f"Rebuild Failed: {rebuild_results['error']}\n")
        
        f.write("\n")
        
        f.write("DRIVER MAPPING SUMMARY\n")
        f.write("-" * 80 + "\n")
        f.write(f"Verified Drivers:\n")
        
        for driver in sorted(scan_results['verified_drivers']):
            f.write(f"- {driver}\n")
            
        f.write(f"\nUnverified Drivers:\n")
        
        for driver in sorted(scan_results['unverified_drivers']):
            f.write(f"- {driver}\n")
    
    logger.info(f"Created identity audit report: {report_path}")
    return report_path

def run_identity_verification(date_str: str) -> Dict[str, Any]:
    """
    Run the complete identity verification process
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        Dict[str, Any]: Verification results
    """
    logger.info(f"Running identity verification for {date_str}")
    
    result = {
        'date': date_str,
        'success': False,
        'error': None,
        'identity_map_size': 0,
        'asset_driver_map_size': 0,
        'source_scan_results': [],
        'report_scan_results': None,
        'rebuild_results': None,
        'audit_report': None
    }
    
    try:
        # Step 1: Load employee master list
        employee_data = load_employee_master_list()
        
        if not employee_data:
            result['error'] = "Failed to load employee master list"
            return result
        
        # Step 2: Create identity and asset maps
        identity_map = create_driver_identity_map(employee_data)
        asset_driver_map = create_asset_driver_map(employee_data)
        
        result['identity_map_size'] = len(identity_map)
        result['asset_driver_map_size'] = len(asset_driver_map)
        
        # Step 3: Scan source files
        source_files = []
        
        # Find driving history files
        driving_history_dir = 'data/driving_history'
        if os.path.exists(driving_history_dir):
            date_part = date_str.replace('-', '')
            for file_name in os.listdir(driving_history_dir):
                if date_part in file_name or date_str in file_name:
                    file_path = os.path.join(driving_history_dir, file_name)
                    source_files.append(file_path)
        
        # Find activity detail files
        activity_detail_dir = 'data/activity_detail'
        if os.path.exists(activity_detail_dir):
            date_part = date_str.replace('-', '')
            for file_name in os.listdir(activity_detail_dir):
                if date_part in file_name or date_str in file_name:
                    file_path = os.path.join(activity_detail_dir, file_name)
                    source_files.append(file_path)
        
        # Scan each source file
        for file_path in source_files:
            scan_result = scan_source_file_for_unverified_drivers(file_path, identity_map)
            result['source_scan_results'].append(scan_result)
        
        # Step 4: Scan report
        report_scan = scan_report_for_unverified_drivers(date_str, identity_map)
        result['report_scan_results'] = report_scan
        
        # Step 5: Rebuild report
        rebuild_result = rebuild_report_with_verified_drivers(date_str, identity_map, asset_driver_map)
        result['rebuild_results'] = rebuild_result
        
        # Step 6: Create audit report
        audit_report = create_identity_audit_report(
            date_str,
            report_scan,
            result['source_scan_results'],
            rebuild_result
        )
        result['audit_report'] = audit_report
        
        # Update success flag
        result['success'] = True
        
        logger.info(f"Identity verification completed for {date_str}")
        return result
        
    except Exception as e:
        logger.error(f"Error running identity verification: {e}")
        logger.error(traceback.format_exc())
        
        result['error'] = str(e)
        return result

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TRAXORA GENIUS CORE | Driver Identity Master')
    parser.add_argument('date', help='Date to verify in YYYY-MM-DD format')
    parser.add_argument('--scan-only', action='store_true', help='Only scan for unverified drivers without rebuilding')
    
    args = parser.parse_args()
    
    if args.scan_only:
        # Load employee data
        employee_data = load_employee_master_list()
        identity_map = create_driver_identity_map(employee_data)
        
        # Scan report
        scan_result = scan_report_for_unverified_drivers(args.date, identity_map)
        
        # Print results
        print(f"\nDriver Identity Verification for {args.date}:")
        print("=" * 70)
        print(f"Total Drivers: {scan_result['total_drivers']}")
        print(f"Verified Drivers: {len(scan_result['verified_drivers'])} ({scan_result['verification_rate']:.1f}%)")
        print(f"Unverified Drivers: {len(scan_result['unverified_drivers'])}")
        
        if scan_result['unverified_drivers']:
            print(f"\nUnverified Drivers:")
            for driver in scan_result['unverified_drivers']:
                print(f"- {driver}")
    else:
        # Run full verification
        results = run_identity_verification(args.date)
        
        if results['success']:
            print(f"\nIdentity Verification Completed for {args.date}:")
            print("=" * 70)
            print(f"Identity Map Size: {results['identity_map_size']} authorized drivers")
            print(f"Asset Driver Map Size: {results['asset_driver_map_size']} verified asset assignments")
            
            if results['report_scan_results']:
                print(f"\nReport Analysis:")
                print("-" * 70)
                scan = results['report_scan_results']
                print(f"Total Drivers: {scan['total_drivers']}")
                print(f"Verified Drivers: {len(scan['verified_drivers'])} ({scan['verification_rate']:.1f}%)")
                print(f"Unverified Drivers: {len(scan['unverified_drivers'])}")
            
            if results['rebuild_results'] and results['rebuild_results']['success']:
                print(f"\nReport Rebuild Results:")
                print("-" * 70)
                rebuild = results['rebuild_results']
                print(f"Original Driver Count: {rebuild['changes']['original_count']}")
                print(f"Verified Driver Count: {rebuild['changes']['verified_count']}")
                print(f"Removed Driver Count: {rebuild['changes']['removed_count']}")
                print(f"Verified Report: {rebuild['verified_report']}")
            
            print(f"\nAudit Report: {results['audit_report']}")
        else:
            print(f"Error running identity verification: {results['error']}")

if __name__ == '__main__':
    main()