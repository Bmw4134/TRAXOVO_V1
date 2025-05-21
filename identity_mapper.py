#!/usr/bin/env python3
"""
TRAXORA GENIUS CORE | Driver Identity Mapper

This module implements a robust identity mapping system that:
1. Extracts authentic driver identities from Equipment Billings Working Spreadsheets
2. Creates a centralized asset-to-driver mapping
3. Ensures all reports use real driver names with proper IDs
4. Prevents injection of fake/placeholder names
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import traceback
from typing import Dict, List, Tuple, Any, Optional, Set, Union
import hashlib

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Create identity mapper log file
file_handler = logging.FileHandler('logs/identity_mapper.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Path to Equipment Billings Working Spreadsheet
EQUIPMENT_BILLINGS_PATH = 'attached_assets/EQ MONTHLY BILLINGS WORKING SPREADSHEET - APRIL 2025.xlsx'

# Alternate equipment lists for fallback
EQUIPMENT_LIST_ALTERNATES = [
    'attached_assets/EQ PROFIT REPORT_01.01.25-04.30.25.xlsx',
    'attached_assets/HEAVY EQ EXPENSES YTD_04.10.2025 (WO SUMMARY UPDATED TO 4.30.2025).xlsx'
]

# Identity map cache file
IDENTITY_MAP_CACHE_FILE = 'data/driver_identity_map.json'

# Sheet names to check for driver assignments
ASSET_LIST_SHEET_NAMES = ['Asset List', 'Equipment List', 'Asset-Driver', 'Assets', 'Vehicles']
DRIVER_LIST_SHEET_NAMES = ['Drivers', 'Employees', 'Personnel', 'Driver List']

class IdentityError(Exception):
    """Custom exception for identity mapping errors"""
    pass

def extract_driver_identity_mappings() -> Dict[str, Dict[str, Any]]:
    """
    Extract driver identity mappings from the Equipment Billings Working Spreadsheet
    
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary mapping asset IDs to driver identities
    """
    identity_map = {}
    source_files_used = []
    total_mappings = 0
    
    # Check if primary file exists
    primary_file_exists = os.path.exists(EQUIPMENT_BILLINGS_PATH)
    
    # Determine which files to process
    files_to_process = []
    if primary_file_exists:
        files_to_process.append(EQUIPMENT_BILLINGS_PATH)
        logger.info(f"Using primary equipment billings file: {EQUIPMENT_BILLINGS_PATH}")
    else:
        logger.warning(f"Primary equipment billings file not found: {EQUIPMENT_BILLINGS_PATH}")
        
        # Add alternates
        for alt_file in EQUIPMENT_LIST_ALTERNATES:
            if os.path.exists(alt_file):
                files_to_process.append(alt_file)
                logger.info(f"Using alternate equipment file: {alt_file}")
    
    if not files_to_process:
        logger.error("No equipment files found to extract driver identities")
        return identity_map
    
    # Process each file
    for file_path in files_to_process:
        try:
            # Load Excel workbook
            workbook = pd.ExcelFile(file_path)
            
            # Track if we found asset list in this file
            asset_list_found = False
            
            # Check for Asset List sheet
            for sheet_name in ASSET_LIST_SHEET_NAMES:
                if sheet_name in workbook.sheet_names:
                    logger.info(f"Found {sheet_name} sheet in {file_path}")
                    
                    # Load sheet
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # Standardize column names
                    df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
                    
                    # Look for asset ID and driver columns
                    asset_cols = ['asset_id', 'asset', 'equipment_id', 'equipment', 'vehicle_id', 'vehicle', 'id', 'asset_number']
                    driver_name_cols = ['driver_name', 'driver', 'employee_name', 'employee', 'operator_name', 'operator', 'assigned_to']
                    employee_id_cols = ['employee_id', 'driver_id', 'operator_id', 'personnel_id', 'emp_id', 'id']
                    
                    # Find columns
                    asset_col = None
                    driver_name_col = None
                    employee_id_col = None
                    
                    for col in asset_cols:
                        if col in df.columns:
                            asset_col = col
                            break
                    
                    for col in driver_name_cols:
                        if col in df.columns:
                            driver_name_col = col
                            break
                    
                    for col in employee_id_cols:
                        if col in df.columns:
                            employee_id_col = col
                            break
                    
                    # If we have asset and driver columns, process the data
                    if asset_col and (driver_name_col or employee_id_col):
                        asset_list_found = True
                        file_mappings = 0
                        
                        # Process each row
                        for _, row in df.iterrows():
                            asset_id = str(row[asset_col]).strip()
                            
                            # Skip empty asset IDs
                            if not asset_id or asset_id.lower() in ['nan', 'none', 'null', '']:
                                continue
                            
                            # Normalize asset ID
                            normalized_asset_id = asset_id.upper()
                            
                            # Extract driver name if available
                            driver_name = None
                            if driver_name_col:
                                driver_name = str(row[driver_name_col]).strip()
                                if driver_name.lower() in ['nan', 'none', 'null', '']:
                                    driver_name = None
                            
                            # Extract employee ID if available
                            employee_id = None
                            if employee_id_col:
                                employee_id = str(row[employee_id_col]).strip()
                                if employee_id.lower() in ['nan', 'none', 'null', '']:
                                    employee_id = None
                            
                            # Only add if we have either driver name or employee ID
                            if driver_name or employee_id:
                                # Create identity record
                                identity_record = {
                                    'asset_id': asset_id,
                                    'normalized_asset_id': normalized_asset_id
                                }
                                
                                if driver_name:
                                    identity_record['name'] = driver_name
                                    identity_record['normalized_name'] = driver_name.lower()
                                
                                if employee_id:
                                    identity_record['employee_id'] = employee_id
                                
                                # Add source file info
                                identity_record['source_file'] = os.path.basename(file_path)
                                identity_record['source_sheet'] = sheet_name
                                
                                # Add to identity map
                                identity_map[normalized_asset_id] = identity_record
                                file_mappings += 1
                        
                        logger.info(f"Extracted {file_mappings} driver identities from {sheet_name} sheet")
                        total_mappings += file_mappings
                        
                        # Add to source files used
                        if file_mappings > 0:
                            source_files_used.append({
                                'file': os.path.basename(file_path),
                                'sheet': sheet_name,
                                'mappings': file_mappings
                            })
            
            # Also check for Drivers sheet if available
            for sheet_name in DRIVER_LIST_SHEET_NAMES:
                if sheet_name in workbook.sheet_names:
                    logger.info(f"Found {sheet_name} sheet in {file_path}")
                    
                    # Load sheet
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # Standardize column names
                    df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
                    
                    # Look for driver name, employee ID, and asset columns
                    driver_name_cols = ['driver_name', 'driver', 'employee_name', 'employee', 'operator_name', 'operator', 'name', 'full_name']
                    employee_id_cols = ['employee_id', 'driver_id', 'operator_id', 'personnel_id', 'emp_id', 'id']
                    asset_cols = ['asset_id', 'asset', 'equipment_id', 'equipment', 'vehicle_id', 'vehicle', 'assigned_equipment']
                    
                    # Find columns
                    driver_name_col = None
                    employee_id_col = None
                    asset_col = None
                    
                    for col in driver_name_cols:
                        if col in df.columns:
                            driver_name_col = col
                            break
                    
                    for col in employee_id_cols:
                        if col in df.columns:
                            employee_id_col = col
                            break
                    
                    for col in asset_cols:
                        if col in df.columns:
                            asset_col = col
                            break
                    
                    # If we have driver name and asset columns, process the data
                    if driver_name_col and asset_col:
                        file_mappings = 0
                        
                        # Process each row
                        for _, row in df.iterrows():
                            driver_name = str(row[driver_name_col]).strip()
                            asset_id = str(row[asset_col]).strip()
                            
                            # Skip empty entries
                            if (not driver_name or driver_name.lower() in ['nan', 'none', 'null', ''] or
                                not asset_id or asset_id.lower() in ['nan', 'none', 'null', '']):
                                continue
                            
                            # Normalize asset ID
                            normalized_asset_id = asset_id.upper()
                            
                            # Extract employee ID if available
                            employee_id = None
                            if employee_id_col:
                                employee_id = str(row[employee_id_col]).strip()
                                if employee_id.lower() in ['nan', 'none', 'null', '']:
                                    employee_id = None
                            
                            # Create identity record
                            identity_record = {
                                'asset_id': asset_id,
                                'normalized_asset_id': normalized_asset_id,
                                'name': driver_name,
                                'normalized_name': driver_name.lower()
                            }
                            
                            if employee_id:
                                identity_record['employee_id'] = employee_id
                            
                            # Add source file info
                            identity_record['source_file'] = os.path.basename(file_path)
                            identity_record['source_sheet'] = sheet_name
                            
                            # Add to identity map if not already present
                            if normalized_asset_id not in identity_map:
                                identity_map[normalized_asset_id] = identity_record
                                file_mappings += 1
                            elif not identity_map[normalized_asset_id].get('name'):
                                # Update existing entry if it's missing name
                                identity_map[normalized_asset_id]['name'] = driver_name
                                identity_map[normalized_asset_id]['normalized_name'] = driver_name.lower()
                                identity_map[normalized_asset_id]['source_sheet'] += f", {sheet_name}"
                                file_mappings += 1
                        
                        logger.info(f"Extracted {file_mappings} additional driver identities from {sheet_name} sheet")
                        total_mappings += file_mappings
                        
                        # Add to source files used
                        if file_mappings > 0:
                            source_files_used.append({
                                'file': os.path.basename(file_path),
                                'sheet': sheet_name,
                                'mappings': file_mappings
                            })
            
            # If we didn't find an asset list in this file, note it
            if not asset_list_found:
                logger.warning(f"No asset list found in {file_path}")
                
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            logger.error(traceback.format_exc())
    
    # Add metadata
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'source_files': source_files_used,
        'total_mappings': total_mappings
    }
    
    # Save to cache
    try:
        os.makedirs(os.path.dirname(IDENTITY_MAP_CACHE_FILE), exist_ok=True)
        with open(IDENTITY_MAP_CACHE_FILE, 'w') as f:
            json.dump({
                'metadata': metadata,
                'identity_map': identity_map
            }, f, indent=2)
        logger.info(f"Saved {total_mappings} driver identities to cache: {IDENTITY_MAP_CACHE_FILE}")
    except Exception as e:
        logger.error(f"Error saving identity map to cache: {e}")
    
    return identity_map

def get_driver_identity_map() -> Dict[str, Dict[str, Any]]:
    """
    Get driver identity map, loading from cache if available and recent
    
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary mapping asset IDs to driver identities
    """
    # Check if cache exists and is recent
    if os.path.exists(IDENTITY_MAP_CACHE_FILE):
        try:
            cache_stat = os.stat(IDENTITY_MAP_CACHE_FILE)
            cache_age = datetime.now().timestamp() - cache_stat.st_mtime
            
            # Use cache if less than 24 hours old
            if cache_age < 24 * 3600:
                with open(IDENTITY_MAP_CACHE_FILE, 'r') as f:
                    cache_data = json.load(f)
                
                identity_map = cache_data.get('identity_map', {})
                metadata = cache_data.get('metadata', {})
                
                logger.info(f"Loaded {len(identity_map)} driver identities from cache")
                logger.info(f"Cache age: {cache_age / 3600:.1f} hours")
                
                return identity_map
            else:
                logger.info(f"Cache is too old ({cache_age / 3600:.1f} hours), extracting fresh identities")
        except Exception as e:
            logger.error(f"Error loading identity map from cache: {e}")
    
    # Extract fresh identity mappings
    return extract_driver_identity_mappings()

def validate_identity_map(identity_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate the identity map for completeness and integrity
    
    Args:
        identity_map (Dict[str, Dict[str, Any]]): Dictionary mapping asset IDs to driver identities
        
    Returns:
        Dict[str, Any]: Validation results
    """
    # Count mappings
    total_mappings = len(identity_map)
    
    # Count mappings with employee IDs
    mappings_with_employee_ids = sum(1 for mapping in identity_map.values() if 'employee_id' in mapping)
    
    # Count mappings with names
    mappings_with_names = sum(1 for mapping in identity_map.values() if 'name' in mapping)
    
    # Count complete mappings (with both name and employee ID)
    complete_mappings = sum(1 for mapping in identity_map.values() if 'name' in mapping and 'employee_id' in mapping)
    
    # Check for duplicate names
    names = {}
    duplicate_names = []
    
    for asset_id, mapping in identity_map.items():
        if 'name' in mapping:
            name = mapping['name']
            if name in names:
                duplicate_names.append({
                    'name': name,
                    'assets': [names[name], asset_id]
                })
            else:
                names[name] = asset_id
    
    # Calculate statistics
    validation_stats = {
        'total_mappings': total_mappings,
        'mappings_with_employee_ids': mappings_with_employee_ids,
        'mappings_with_names': mappings_with_names,
        'complete_mappings': complete_mappings,
        'duplicate_names': len(duplicate_names),
        'duplicate_name_details': duplicate_names,
        'timestamp': datetime.now().isoformat()
    }
    
    # Calculate coverage percentages
    if total_mappings > 0:
        validation_stats['employee_id_coverage'] = mappings_with_employee_ids / total_mappings * 100
        validation_stats['name_coverage'] = mappings_with_names / total_mappings * 100
        validation_stats['complete_coverage'] = complete_mappings / total_mappings * 100
    
    return validation_stats

def create_identity_verification_report(date_str: str, validation_stats: Dict[str, Any], identity_map: Dict[str, Dict[str, Any]]) -> str:
    """
    Create a detailed identity verification report
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        validation_stats (Dict[str, Any]): Validation statistics
        identity_map (Dict[str, Dict[str, Any]]): Dictionary mapping asset IDs to driver identities
        
    Returns:
        str: Path to the verification report
    """
    report_path = f"logs/identity_map_verification_{date_str}.txt"
    
    with open(report_path, 'w') as f:
        f.write(f"TRAXORA GENIUS CORE | DRIVER IDENTITY VERIFICATION REPORT\n")
        f.write(f"Date: {date_str}\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("IDENTITY MAP VALIDATION\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total asset-to-driver mappings: {validation_stats['total_mappings']}\n")
        f.write(f"Mappings with employee IDs: {validation_stats['mappings_with_employee_ids']} ({validation_stats.get('employee_id_coverage', 0):.1f}%)\n")
        f.write(f"Mappings with driver names: {validation_stats['mappings_with_names']} ({validation_stats.get('name_coverage', 0):.1f}%)\n")
        f.write(f"Complete mappings: {validation_stats['complete_mappings']} ({validation_stats.get('complete_coverage', 0):.1f}%)\n")
        f.write(f"Duplicate names detected: {validation_stats['duplicate_names']}\n\n")
        
        if validation_stats['duplicate_names'] > 0:
            f.write("DUPLICATE NAME DETAILS\n")
            f.write("-" * 80 + "\n")
            for i, duplicate in enumerate(validation_stats['duplicate_name_details'], 1):
                f.write(f"{i}. {duplicate['name']} assigned to multiple assets: {', '.join(duplicate['assets'])}\n")
            f.write("\n")
        
        f.write("IDENTITY MAP DETAILS\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Asset ID':<15} {'Employee ID':<15} {'Driver Name':<30} {'Source':<30}\n")
        f.write("-" * 80 + "\n")
        
        for asset_id, mapping in sorted(identity_map.items()):
            employee_id = mapping.get('employee_id', 'N/A')
            name = mapping.get('name', 'N/A')
            source = f"{mapping.get('source_file', 'Unknown')} ({mapping.get('source_sheet', 'Unknown')})"
            f.write(f"{asset_id:<15} {employee_id:<15} {name:<30} {source:<30}\n")
    
    logger.info(f"Identity verification report saved to {report_path}")
    return report_path

def apply_identity_mapping_to_report(report_data: Dict[str, Any], identity_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Apply identity mapping to a Daily Driver Report
    
    Args:
        report_data (Dict[str, Any]): Report data
        identity_map (Dict[str, Dict[str, Any]]): Dictionary mapping asset IDs to driver identities
        
    Returns:
        Dict[str, Any]: Updated report data
    """
    # Create a copy of the report data
    updated_report = report_data.copy()
    
    # Process drivers list
    drivers = updated_report.get('drivers', [])
    identity_stats = {
        'total_drivers': len(drivers),
        'matched': 0,
        'unmatched': 0
    }
    
    for driver in drivers:
        asset_id = driver.get('asset_id', '')
        normalized_asset_id = asset_id.upper() if asset_id else ''
        
        # Check if asset ID is in identity map
        if normalized_asset_id in identity_map:
            # Get identity information
            identity = identity_map[normalized_asset_id]
            
            # Update driver with identity information
            if 'employee_id' in identity:
                driver['employee_id'] = identity['employee_id']
            
            if 'name' in identity and identity['name'] != driver.get('driver_name', ''):
                driver['original_name'] = driver.get('driver_name', '')
                driver['driver_name'] = identity['name']
            
            # Add identity verified flag
            driver['identity_verified'] = True
            
            # Add identity source
            driver['identity_source'] = f"{identity.get('source_file', 'Unknown')} ({identity.get('source_sheet', 'Unknown')})"
            
            identity_stats['matched'] += 1
        else:
            # Mark as unverified identity
            driver['identity_verified'] = False
            identity_stats['unmatched'] += 1
    
    # Add identity verification signature to metadata
    if 'metadata' not in updated_report:
        updated_report['metadata'] = {}
    
    # Create verification signature using report data hash
    report_hash = hashlib.sha256(json.dumps(report_data).encode()).hexdigest()
    
    updated_report['metadata']['identity_verification'] = {
        'timestamp': datetime.now().isoformat(),
        'identity_map_size': len(identity_map),
        'identity_stats': identity_stats,
        'signature': f"IDENTITY-VERIFIED-{report_hash[:8]}"
    }
    
    return updated_report

def rebuild_report_with_identity_mapping(date_str: str) -> Dict[str, Any]:
    """
    Rebuild a Daily Driver Report with proper identity mapping
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        Dict[str, Any]: Result of the rebuild operation
    """
    logger.info(f"Rebuilding report for {date_str} with identity mapping")
    
    # Create result structure
    result = {
        'date': date_str,
        'status': 'FAILED',
        'error': None,
        'report_paths': {},
        'identity_stats': {},
        'identity_verification_report': None
    }
    
    try:
        # Step 1: Get driver identity map
        identity_map = get_driver_identity_map()
        
        if not identity_map:
            raise IdentityError("Failed to get driver identity map")
        
        # Step 2: Validate identity map
        validation_stats = validate_identity_map(identity_map)
        result['identity_stats'] = validation_stats
        
        # Step 3: Create identity verification report
        verification_report = create_identity_verification_report(date_str, validation_stats, identity_map)
        result['identity_verification_report'] = verification_report
        
        # Step 4: Load existing report
        report_path = f"reports/daily_drivers/daily_report_{date_str}.json"
        
        if not os.path.exists(report_path):
            # If report doesn't exist, we'll need to generate it
            logger.warning(f"Report not found for {date_str}, will need to be generated")
            
            # Import and use enhanced genius processor
            try:
                from enhanced_genius_processor import process_and_export
                
                logger.info(f"Generating report for {date_str} using enhanced genius processor")
                process_result = process_and_export(date_str)
                
                if process_result['status'] != 'SUCCESS':
                    raise IdentityError(f"Failed to generate report: {process_result.get('error', 'Unknown error')}")
                
                logger.info(f"Report generated successfully for {date_str}")
                
                # Now load the generated report
                with open(report_path, 'r') as f:
                    report_data = json.load(f)
            except ImportError:
                raise IdentityError("Enhanced genius processor not available")
        else:
            # Load existing report
            try:
                with open(report_path, 'r') as f:
                    report_data = json.load(f)
            except Exception as e:
                raise IdentityError(f"Error loading report: {e}")
        
        # Step 5: Apply identity mapping
        updated_report = apply_identity_mapping_to_report(report_data, identity_map)
        
        # Step 6: Save updated report
        identity_verified_path = f"reports/daily_drivers/daily_report_{date_str}_identity_verified.json"
        exports_path = f"exports/daily_reports/daily_report_{date_str}.json"
        
        # Make sure directories exist
        os.makedirs(os.path.dirname(identity_verified_path), exist_ok=True)
        os.makedirs(os.path.dirname(exports_path), exist_ok=True)
        
        # Save reports
        with open(identity_verified_path, 'w') as f:
            json.dump(updated_report, f, indent=2, default=str)
        
        with open(exports_path, 'w') as f:
            json.dump(updated_report, f, indent=2, default=str)
        
        # Step 7: Generate Excel reports
        excel_path = f"reports/daily_drivers/daily_report_{date_str}_identity_verified.xlsx"
        exports_excel_path = f"exports/daily_reports/{date_str}_DailyDriverReport.xlsx"
        
        # Convert drivers list to DataFrame
        df = pd.DataFrame(updated_report.get('drivers', []))
        
        # Save Excel reports
        df.to_excel(excel_path, index=False)
        df.to_excel(exports_excel_path, index=False)
        
        # Add paths to result
        result['report_paths'] = {
            'json': identity_verified_path,
            'excel': excel_path,
            'exports_json': exports_path,
            'exports_excel': exports_excel_path
        }
        
        # Update status
        result['status'] = 'SUCCESS'
        
        logger.info(f"Report rebuilt successfully for {date_str}")
        return result
        
    except Exception as e:
        logger.error(f"Error rebuilding report: {e}")
        logger.error(traceback.format_exc())
        
        result['error'] = str(e)
        return result

def run_identity_verification(date_str: str) -> Dict[str, Any]:
    """
    Run identity verification for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        Dict[str, Any]: Verification results
    """
    logger.info(f"Running identity verification for {date_str}")
    
    # Get driver identity map
    identity_map = get_driver_identity_map()
    
    # Validate identity map
    validation_stats = validate_identity_map(identity_map)
    
    # Create identity verification report
    verification_report = create_identity_verification_report(date_str, validation_stats, identity_map)
    
    # Return results
    return {
        'date': date_str,
        'identity_map_size': len(identity_map),
        'validation_stats': validation_stats,
        'verification_report': verification_report
    }

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TRAXORA GENIUS CORE | Driver Identity Mapper')
    parser.add_argument('date', help='Date to process in YYYY-MM-DD format')
    parser.add_argument('--verify-only', action='store_true', help='Only verify identities without rebuilding report')
    parser.add_argument('--extract-only', action='store_true', help='Only extract identity mappings without rebuilding report')
    
    args = parser.parse_args()
    
    if args.extract_only:
        # Extract identity mappings
        identity_map = extract_driver_identity_mappings()
        print(f"Extracted {len(identity_map)} driver identities")
        
        # Validate and print statistics
        validation_stats = validate_identity_map(identity_map)
        print(f"Validation statistics:")
        print(f"  - Total mappings: {validation_stats['total_mappings']}")
        print(f"  - Mappings with employee IDs: {validation_stats['mappings_with_employee_ids']} ({validation_stats.get('employee_id_coverage', 0):.1f}%)")
        print(f"  - Mappings with driver names: {validation_stats['mappings_with_names']} ({validation_stats.get('name_coverage', 0):.1f}%)")
        print(f"  - Complete mappings: {validation_stats['complete_mappings']} ({validation_stats.get('complete_coverage', 0):.1f}%)")
        print(f"  - Duplicate names detected: {validation_stats['duplicate_names']}")
        
    elif args.verify_only:
        # Run identity verification
        results = run_identity_verification(args.date)
        print(f"Identity verification completed for {args.date}")
        print(f"Verification report saved to {results['verification_report']}")
        print(f"Identity map size: {results['identity_map_size']}")
        print(f"Validation statistics:")
        print(f"  - Total mappings: {results['validation_stats']['total_mappings']}")
        print(f"  - Mappings with employee IDs: {results['validation_stats']['mappings_with_employee_ids']} ({results['validation_stats'].get('employee_id_coverage', 0):.1f}%)")
        print(f"  - Mappings with driver names: {results['validation_stats']['mappings_with_names']} ({results['validation_stats'].get('name_coverage', 0):.1f}%)")
        print(f"  - Complete mappings: {results['validation_stats']['complete_mappings']} ({results['validation_stats'].get('complete_coverage', 0):.1f}%)")
        print(f"  - Duplicate names detected: {results['validation_stats']['duplicate_names']}")
        
    else:
        # Rebuild report with identity mapping
        results = rebuild_report_with_identity_mapping(args.date)
        
        if results['status'] == 'SUCCESS':
            print(f"Report rebuilt successfully for {args.date}")
            print(f"Identity verification report saved to {results['identity_verification_report']}")
            print(f"Identity-verified report saved to {results['report_paths']['json']}")
            print(f"Identity statistics:")
            print(f"  - Total mappings: {results['identity_stats']['total_mappings']}")
            print(f"  - Mappings with employee IDs: {results['identity_stats']['mappings_with_employee_ids']} ({results['identity_stats'].get('employee_id_coverage', 0):.1f}%)")
            print(f"  - Mappings with driver names: {results['identity_stats']['mappings_with_names']} ({results['identity_stats'].get('name_coverage', 0):.1f}%)")
            print(f"  - Complete mappings: {results['identity_stats']['complete_mappings']} ({results['identity_stats'].get('complete_coverage', 0):.1f}%)")
        else:
            print(f"Error rebuilding report: {results['error']}")

if __name__ == '__main__':
    main()