#!/usr/bin/env python3
"""
System Test Runner

This script automates end-to-end testing of the attendance reporting system.
It generates test data, processes it through the attendance processor,
and validates the resulting report with comprehensive checks.
"""

import os
import sys
import json
import argparse
import random
from datetime import datetime, timedelta

def run_test(date=None, count=50, include_all_edge_cases=False, 
            include_duplicates=False, include_null_divisions=False,
            include_overnight_shifts=False, include_null_assets=False):
    """
    Run a complete system test with the specified options
    
    Args:
        date (str): Date for the test (YYYY-MM-DD format)
        count (int): Number of records to generate
        include_all_edge_cases (bool): Whether to enable all edge cases
        include_duplicates (bool): Whether to include duplicate employee IDs
        include_null_divisions (bool): Whether to include missing division data
        include_overnight_shifts (bool): Whether to include overnight shifts
        include_null_assets (bool): Whether to include missing asset data
    """
    # Set a default date if none provided
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # Create test data file path
    test_file = 'mock_system_test.csv'
    
    # If include_all_edge_cases is True, enable all edge cases
    if include_all_edge_cases:
        include_duplicates = True
        include_null_divisions = True
        include_overnight_shifts = True
        include_null_assets = True
    
    # Build the command to generate test data
    command = f'python test_data_generator.py -d {date} -c {count} -o {test_file}'
    
    # Add edge case flags
    if include_duplicates:
        command += ' --include-duplicates'
    if include_null_divisions:
        command += ' --include-null-divisions'
    if include_overnight_shifts:
        command += ' --include-overnight-shifts'
    if include_null_assets:
        command += ' --include-null-assets'
    
    # Generate the test data
    print(f"Generating test data with command: {command}")
    os.system(command)
    
    # Process the test data and validate it
    print("\nProcessing and validating test data...")
    
    try:
        # Import necessary components
        sys.path.append('.')
        from utils.attendance_processor import read_daily_usage_file
        from report_validator import validate_report
        
        # Process the test data
        result = read_daily_usage_file(test_file)
        
        # Save the report data for reference
        with open('system_test_report.json', 'w') as f:
            json.dump(result, f, default=str, indent=2)
        
        print(f"Report data saved to system_test_report.json")
        
        # Validate the report
        print("\nValidating generated report...")
        validation_result = validate_report(result)
        
        # Save validation results
        with open('system_test_validation.json', 'w') as f:
            json.dump(validation_result, f, default=str, indent=2)
        
        # Display results
        print("\nSystem Test Results:")
        print(f"Test date: {date}")
        print(f"Records generated: {count}")
        print(f"Edge cases included: {include_all_edge_cases}")
        
        if include_duplicates or include_all_edge_cases:
            print("- Duplicate employee IDs across assets")
        if include_null_divisions or include_all_edge_cases:
            print("- Missing division/region data")
        if include_overnight_shifts or include_all_edge_cases:
            print("- Overnight shifts spanning midnight")
        if include_null_assets or include_all_edge_cases:
            print("- Missing/malformed asset labels")
        
        print(f"\nValidation result: {'PASSED' if validation_result['is_valid'] else 'FAILED'}")
        
        # Display statistics
        if validation_result.get('statistics'):
            stats = validation_result['statistics']
            print("\nReport Statistics:")
            print(f"Total drivers: {stats.get('total_unique_drivers', 0)}")
            print(f"Total issues: {stats.get('total_issues', 0)}")
            print(f"Late drivers: {stats.get('late_drivers', 0)}")
            print(f"Early end drivers: {stats.get('early_end_drivers', 0)}")
            print(f"Not on job drivers: {stats.get('not_on_job_drivers', 0)}")
            print(f"Drivers with multiple issues: {stats.get('drivers_with_multiple_issues', 0)}")
        
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
        
        # Final result
        if validation_result['is_valid']:
            print("\n✅ SYSTEM TEST PASSED: All validation checks successful!")
        else:
            print("\n❌ SYSTEM TEST FAILED: Validation identified issues that need fixing.")
        
        return validation_result['is_valid']
    
    except Exception as e:
        print(f"\n❌ SYSTEM TEST ERROR: {str(e)}")
        return False

def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(description='Run an end-to-end system test of the attendance reporting system.')
    parser.add_argument('-d', '--date', help='Date to use for test records (YYYY-MM-DD format)')
    parser.add_argument('-c', '--count', type=int, default=50, help='Number of records to generate (default: 50)')
    parser.add_argument('--all-edge-cases', action='store_true', help='Enable all edge cases')
    parser.add_argument('--duplicates', action='store_true', help='Include duplicate employee IDs')
    parser.add_argument('--null-divisions', action='store_true', help='Include missing division data')
    parser.add_argument('--overnight-shifts', action='store_true', help='Include overnight shifts')
    parser.add_argument('--null-assets', action='store_true', help='Include missing asset data')
    
    args = parser.parse_args()
    
    # Run the system test
    success = run_test(
        args.date,
        args.count,
        args.all_edge_cases,
        args.duplicates,
        args.null_divisions,
        args.overnight_shifts,
        args.null_assets
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()