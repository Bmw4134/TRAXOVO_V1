#!/usr/bin/env python3
"""
Complex Test Validation Script

This script processes complex test data with edge cases and validates the results.
"""

import sys
import json
from datetime import datetime

def process_complex_test():
    """Process complex test data and validate results"""
    print("Processing complex test data with edge cases...")
    
    # Import necessary modules
    from utils.attendance_processor import read_daily_usage_file
    from report_validator import validate_report
    
    # Process the test data
    test_file = 'complex_test.csv'
    result = read_daily_usage_file(test_file)
    
    # Save the results
    with open('complex_test_report.json', 'w') as f:
        json.dump(result, f, default=str, indent=2)
    print(f"Report data saved to complex_test_report.json")
    
    # Validate the report
    print("\nValidating complex test report...")
    validation_result = validate_report(result)
    
    # Save validation results
    with open('complex_test_validation.json', 'w') as f:
        json.dump(validation_result, f, default=str, indent=2)
    
    # Display validation results
    print("\nValidation Results:")
    print(f"Is valid: {validation_result['is_valid']}")
    
    # Display any warnings
    if validation_result.get('warnings'):
        print("\nWarnings:")
        for i, warning in enumerate(validation_result['warnings'], 1):
            print(f"  {i}. {warning.get('message', '')}")
    
    # Display any errors
    if validation_result.get('errors'):
        print("\nErrors:")
        for i, error in enumerate(validation_result['errors'], 1):
            print(f"  {i}. {error.get('message', '')}")
    
    # Display statistics
    if validation_result.get('statistics'):
        stats = validation_result['statistics']
        print("\nReport Statistics:")
        for key, value in stats.items():
            if key != 'multiple_issue_details':
                print(f"  {key}: {value}")
    
    # Display any drivers with multiple issues
    if validation_result.get('statistics', {}).get('multiple_issue_details'):
        print("\nDrivers with multiple issues:")
        for driver_details in validation_result['statistics']['multiple_issue_details']:
            print(f"  {driver_details}")
    
    # Analyze edge cases
    print("\nEdge Case Analysis:")
    
    # 1. Analyze overnight shifts
    overnight_shifts = []
    for driver in result.get('late_drivers', []) + result.get('early_end_drivers', []) + result.get('not_on_job_drivers', []):
        time_start = driver.get('time_start', '')
        time_stop = driver.get('time_stop', '')
        if any(marker in time_start or marker in time_stop for marker in ['(+1)', '(Next Day)']):
            overnight_shifts.append(driver)
    
    print(f"  Overnight shifts: {len(overnight_shifts)} detected")
    if overnight_shifts:
        print("  Samples:")
        for i, shift in enumerate(overnight_shifts[:3], 1):
            print(f"    {i}. {shift.get('driver', 'Unknown')} - Start: {shift.get('time_start', 'N/A')}, Stop: {shift.get('time_stop', 'N/A')}")
    
    # 2. Analyze missing division data
    missing_divisions = []
    for driver in result.get('late_drivers', []) + result.get('early_end_drivers', []) + result.get('not_on_job_drivers', []):
        asset_label = driver.get('asset_label', '')
        if '[' not in asset_label:
            missing_divisions.append(driver)
    
    print(f"  Missing division data: {len(missing_divisions)} detected")
    if missing_divisions:
        print("  Samples:")
        for i, driver in enumerate(missing_divisions[:3], 1):
            print(f"    {i}. {driver.get('driver', 'Unknown')} - Asset: {driver.get('asset_label', 'N/A')}")
    
    # 3. Analyze duplicate employee IDs
    employee_ids = {}
    for driver in result.get('late_drivers', []) + result.get('early_end_drivers', []) + result.get('not_on_job_drivers', []):
        driver_name = driver.get('driver', '')
        if driver_name:
            if driver_name in employee_ids:
                employee_ids[driver_name].append(driver)
            else:
                employee_ids[driver_name] = [driver]
    
    duplicates = {name: instances for name, instances in employee_ids.items() if len(instances) > 1}
    print(f"  Duplicate employee IDs: {len(duplicates)} detected")
    if duplicates:
        print("  Samples:")
        for i, (name, instances) in enumerate(list(duplicates.items())[:3], 1):
            assets = [driver.get('asset', 'Unknown') for driver in instances]
            print(f"    {i}. {name} found on {len(instances)} assets: {', '.join(assets[:2])}" + 
                  (f" and {len(assets)-2} more" if len(assets) > 2 else ""))
    
    # 4. Analyze null/malformed asset labels
    null_assets = []
    for driver in result.get('late_drivers', []) + result.get('early_end_drivers', []) + result.get('not_on_job_drivers', []):
        asset_label = driver.get('asset_label', '')
        if not asset_label or asset_label in ['???', 'UNKNOWN', 'UNASSIGNED']:
            null_assets.append(driver)
    
    print(f"  Null/malformed asset labels: {len(null_assets)} detected")
    if null_assets:
        print("  Samples:")
        for i, driver in enumerate(null_assets[:3], 1):
            print(f"    {i}. Driver: {driver.get('driver', 'Unknown')}, Asset: '{driver.get('asset_label', 'N/A')}'")
    
    # Overall result
    if validation_result['is_valid']:
        print("\n✅ COMPLEX TEST PASSED: Edge case handling is robust!")
    else:
        print("\n❌ COMPLEX TEST FAILED: Edge case handling needs improvement!")
    
    return validation_result['is_valid']

if __name__ == "__main__":
    sys.path.append('.')
    process_complex_test()