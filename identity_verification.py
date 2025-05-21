#!/usr/bin/env python3
"""
TRAXORA GENIUS CORE | Driver Identity Verification

This module enforces driver identity verification using the consolidated employee list
as the source of truth for driver verification.
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
from typing import Dict, List, Set, Any, Optional
import hashlib

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Create identity verification log file
file_handler = logging.FileHandler('logs/identity_verification.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Path to consolidated employee list
EMPLOYEE_LIST_PATH = 'attached_assets/Consolidated_Employee_And_Job_Lists_Corrected.xlsx'

class VerificationError(Exception):
    """Custom exception for identity verification errors"""
    pass

def load_verified_employees() -> Dict[str, Dict[str, Any]]:
    """
    Load verified employees from the consolidated employee list
    
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary mapping normalized names to employee data
    """
    employees = {}
    
    if not os.path.exists(EMPLOYEE_LIST_PATH):
        logger.error(f"Employee list not found: {EMPLOYEE_LIST_PATH}")
        raise VerificationError(f"Employee list not found: {EMPLOYEE_LIST_PATH}")
    
    try:
        # Load employee list
        df = pd.read_excel(EMPLOYEE_LIST_PATH)
        
        # Standardize column names
        df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
        
        # Look for employee name column
        employee_cols = ['name', 'employee_name', 'full_name', 'driver_name', 'employee']
        employee_col = None
        
        for col in employee_cols:
            if col in df.columns:
                employee_col = col
                break
                
        if not employee_col:
            logger.error("Employee name column not found in employee list")
            raise VerificationError("Employee name column not found in employee list")
            
        # Process each employee
        for _, row in df.iterrows():
            name = str(row[employee_col]).strip()
            if name and name.lower() not in ['nan', 'none', 'null', '']:
                normalized_name = name.lower()
                
                # Extract other employee data
                employee_record = {'name': name, 'normalized_name': normalized_name}
                
                # Add any other available fields
                for col in df.columns:
                    if col != employee_col:
                        employee_record[col] = row[col]
                
                employees[normalized_name] = employee_record
                
        logger.info(f"Loaded {len(employees)} employees from consolidated list")
        
    except Exception as e:
        logger.error(f"Error loading employee list: {e}")
        logger.error(traceback.format_exc())
        raise VerificationError(f"Error loading employee list: {e}")
    
    return employees

def verify_drivers_in_report(date_str: str) -> Dict[str, Any]:
    """
    Verify drivers in a Daily Driver Report against the consolidated employee list
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        Dict[str, Any]: Verification results
    """
    logger.info(f"Verifying drivers in report for {date_str}")
    
    # Create result structure
    result = {
        'date': date_str,
        'status': 'FAILED',
        'error': None,
        'verified_count': 0,
        'unverified_count': 0,
        'unverified_drivers': [],
        'verification_report': None
    }
    
    try:
        # Step 1: Load verified employees
        verified_employees = load_verified_employees()
        
        # Step 2: Load report
        report_path = f"reports/daily_drivers/daily_report_{date_str}.json"
        
        if not os.path.exists(report_path):
            raise VerificationError(f"Report not found: {report_path}")
            
        # Load report
        with open(report_path, 'r') as f:
            report_data = json.load(f)
            
        # Step 3: Verify drivers
        drivers = report_data.get('drivers', [])
        verified_drivers = []
        unverified_drivers = []
        
        for driver in drivers:
            driver_name = driver.get('driver_name', '').strip()
            normalized_name = driver_name.lower()
            
            # Check if driver is verified
            if normalized_name in verified_employees:
                # Mark as verified
                driver['identity_verified'] = True
                driver['verification_source'] = 'consolidated_employee_list'
                
                # Add employee data if available
                employee_data = verified_employees[normalized_name]
                for field, value in employee_data.items():
                    if field not in ['name', 'normalized_name'] and field not in driver:
                        driver[f'employee_{field}'] = value
                
                verified_drivers.append(driver)
            else:
                # Mark as unverified
                driver['identity_verified'] = False
                driver['verification_status'] = 'unverified'
                
                unverified_drivers.append(driver)
                result['unverified_drivers'].append(driver_name)
        
        # Update counts
        result['verified_count'] = len(verified_drivers)
        result['unverified_count'] = len(unverified_drivers)
        
        # Step 4: Create verification report
        verification_report_path = f"logs/identity_verification_{date_str}.txt"
        
        with open(verification_report_path, 'w') as f:
            f.write(f"TRAXORA GENIUS CORE | DRIVER IDENTITY VERIFICATION REPORT\n")
            f.write(f"Date: {date_str}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("VERIFICATION SUMMARY\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total drivers in report: {len(drivers)}\n")
            f.write(f"Verified drivers: {len(verified_drivers)} ({len(verified_drivers)/len(drivers)*100:.1f}%)\n")
            f.write(f"Unverified drivers: {len(unverified_drivers)} ({len(unverified_drivers)/len(drivers)*100:.1f}%)\n\n")
            
            if unverified_drivers:
                f.write("UNVERIFIED DRIVERS\n")
                f.write("-" * 80 + "\n")
                f.write(f"{'Driver Name':<30} {'Asset ID':<15} {'Job Site':<30}\n")
                f.write("-" * 80 + "\n")
                
                for driver in unverified_drivers:
                    name = driver.get('driver_name', 'N/A')
                    asset_id = driver.get('asset_id', 'N/A')
                    job_site = driver.get('assigned_job_site', 'N/A')
                    f.write(f"{name:<30} {asset_id:<15} {job_site:<30}\n")
                
                f.write("\n")
            
            f.write("VERIFIED DRIVERS\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'Driver Name':<30} {'Asset ID':<15} {'Job Site':<30}\n")
            f.write("-" * 80 + "\n")
            
            for driver in verified_drivers:
                name = driver.get('driver_name', 'N/A')
                asset_id = driver.get('asset_id', 'N/A')
                job_site = driver.get('assigned_job_site', 'N/A')
                f.write(f"{name:<30} {asset_id:<15} {job_site:<30}\n")
        
        result['verification_report'] = verification_report_path
        
        # Step 5: Create verified report
        verified_report = report_data.copy()
        
        # Create verification signature using report data hash
        report_hash = hashlib.sha256(json.dumps(report_data).encode()).hexdigest()
        
        # Update metadata
        if 'metadata' not in verified_report:
            verified_report['metadata'] = {}
            
        verified_report['metadata']['identity_verification'] = {
            'timestamp': datetime.now().isoformat(),
            'verified_count': len(verified_drivers),
            'unverified_count': len(unverified_drivers),
            'signature': f"IDENTITY-VERIFIED-{report_hash[:8]}"
        }
        
        # Save verified report
        verified_report_path = f"reports/daily_drivers/daily_report_{date_str}_verified.json"
        exports_path = f"exports/daily_reports/daily_report_{date_str}_verified.json"
        
        # Make sure directories exist
        os.makedirs(os.path.dirname(verified_report_path), exist_ok=True)
        os.makedirs(os.path.dirname(exports_path), exist_ok=True)
        
        # Save reports
        with open(verified_report_path, 'w') as f:
            json.dump(verified_report, f, indent=2, default=str)
            
        with open(exports_path, 'w') as f:
            json.dump(verified_report, f, indent=2, default=str)
            
        # Save Excel version
        excel_path = f"reports/daily_drivers/daily_report_{date_str}_verified.xlsx"
        
        # Convert drivers to DataFrame
        df = pd.DataFrame(verified_report.get('drivers', []))
        df.to_excel(excel_path, index=False)
        
        result['status'] = 'SUCCESS'
        result['verified_report_path'] = verified_report_path
        result['verification_report'] = verification_report_path
        
        logger.info(f"Driver verification completed for {date_str}")
        return result
        
    except Exception as e:
        logger.error(f"Error verifying drivers: {e}")
        logger.error(traceback.format_exc())
        
        result['error'] = str(e)
        return result

def verify_and_regenerate_report(date_str: str) -> Dict[str, Any]:
    """
    Verify drivers and regenerate Daily Driver Report with verification status
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        Dict[str, Any]: Result of verification and regeneration
    """
    logger.info(f"Verifying and regenerating report for {date_str}")
    
    # Create result structure
    result = {
        'date': date_str,
        'status': 'FAILED',
        'error': None,
        'verification_result': None,
        'regenerate_result': None
    }
    
    try:
        # Step 1: Verify drivers
        verification_result = verify_drivers_in_report(date_str)
        result['verification_result'] = verification_result
        
        if verification_result['status'] != 'SUCCESS':
            result['error'] = verification_result['error']
            return result
        
        # Step 2: Load verified report
        verified_report_path = verification_result.get('verified_report_path')
        
        if not verified_report_path or not os.path.exists(verified_report_path):
            result['error'] = "Verified report not found"
            return result
            
        with open(verified_report_path, 'r') as f:
            verified_report = json.load(f)
        
        # Step 3: Regenerate report using enhanced genius processor if available
        try:
            from enhanced_genius_processor import process_date, export_report
            
            # Process with original data but add verification status
            logger.info(f"Regenerating report for {date_str} using enhanced genius processor")
            
            # Process the report
            processed_report = process_date(date_str)
            
            if not processed_report:
                result['error'] = "Failed to process report"
                return result
                
            # Add verification status from verified report
            drivers = processed_report.get('drivers', [])
            verified_drivers = verified_report.get('drivers', [])
            
            # Create lookup of verified drivers
            verified_lookup = {}
            for driver in verified_drivers:
                name = driver.get('driver_name', '').lower()
                if name:
                    verified_lookup[name] = driver.get('identity_verified', False)
            
            # Update verification status
            for driver in drivers:
                name = driver.get('driver_name', '').lower()
                driver['identity_verified'] = verified_lookup.get(name, False)
            
            # Add verification metadata
            if 'metadata' not in processed_report:
                processed_report['metadata'] = {}
                
            processed_report['metadata']['identity_verification'] = verified_report.get('metadata', {}).get('identity_verification', {})
            
            # Export the report
            export_result = export_report(processed_report, date_str)
            
            if export_result['status'] != 'SUCCESS':
                result['error'] = f"Failed to export report: {export_result.get('error')}"
                return result
                
            result['regenerate_result'] = export_result
            result['status'] = 'SUCCESS'
            
            logger.info(f"Report regenerated successfully for {date_str}")
            return result
            
        except ImportError:
            logger.warning("Enhanced genius processor not available, using verified report")
            result['status'] = 'SUCCESS'
            result['regenerate_result'] = {'status': 'SKIPPED', 'reason': 'Enhanced processor not available'}
            return result
            
    except Exception as e:
        logger.error(f"Error in verification and regeneration: {e}")
        logger.error(traceback.format_exc())
        
        result['error'] = str(e)
        return result

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TRAXORA GENIUS CORE | Driver Identity Verification')
    parser.add_argument('date', help='Date to verify in YYYY-MM-DD format')
    parser.add_argument('--verify-only', action='store_true', help='Only verify identities without regenerating report')
    
    args = parser.parse_args()
    
    if args.verify_only:
        # Verify drivers
        result = verify_drivers_in_report(args.date)
        
        if result['status'] == 'SUCCESS':
            print(f"Driver verification completed for {args.date}")
            print(f"Verification report saved to {result['verification_report']}")
            print(f"Verified drivers: {result['verified_count']}")
            print(f"Unverified drivers: {result['unverified_count']}")
            
            if result['unverified_drivers']:
                print(f"Unverified drivers: {', '.join(result['unverified_drivers'])}")
        else:
            print(f"Error verifying drivers: {result['error']}")
    else:
        # Verify and regenerate
        result = verify_and_regenerate_report(args.date)
        
        if result['status'] == 'SUCCESS':
            verification_result = result['verification_result']
            print(f"Driver verification and report regeneration completed for {args.date}")
            print(f"Verification report saved to {verification_result['verification_report']}")
            print(f"Verified drivers: {verification_result['verified_count']}")
            print(f"Unverified drivers: {verification_result['unverified_count']}")
            
            if verification_result['unverified_drivers']:
                print(f"Unverified drivers: {', '.join(verification_result['unverified_drivers'])}")
        else:
            print(f"Error in verification and regeneration: {result['error']}")

if __name__ == '__main__':
    main()