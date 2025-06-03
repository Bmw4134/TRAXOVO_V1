#!/usr/bin/env python3
"""
Validate Test Data Script

This script processes test data through the attendance processor
and validates it with the report validator.
"""

import os
import sys
import json
from datetime import datetime

from utils.attendance_processor import read_daily_usage_file
from report_validator import validate_report

def main():
    """Main function to process and validate test data"""
    # Process test data
    print("Processing test data...")
    result = read_daily_usage_file('mock_data_test.csv')
    
    # Save the report data
    with open('report_data.json', 'w') as f:
        json.dump(result, f, default=str, indent=2)
    print(f"Report data saved to report_data.json")
    
    # Validate the report
    print("\nValidating report data...")
    validation_result = validate_report(result)
    
    # Display validation results
    print("\nValidation Results:")
    print(f"Is valid: {validation_result['is_valid']}")
    
    # Display any errors
    if validation_result.get('errors'):
        print("\nErrors:")
        for i, error in enumerate(validation_result['errors'], 1):
            print(f"  {i}. {error.get('message', '')}")
    
    # Display any warnings
    if validation_result.get('warnings'):
        print("\nWarnings:")
        for i, warning in enumerate(validation_result['warnings'], 1):
            print(f"  {i}. {warning.get('message', '')}")
    
    # Display statistics
    print("\nReport Statistics:")
    for key, value in validation_result.get('statistics', {}).items():
        if key != 'multiple_issue_details':
            print(f"  {key}: {value}")
    
    # Display any drivers with multiple issues
    if validation_result.get('statistics', {}).get('multiple_issue_details'):
        print("\nDrivers with multiple issues:")
        for driver_details in validation_result['statistics']['multiple_issue_details']:
            print(f"  {driver_details}")
    
    # Save validation results
    with open('validation_results.json', 'w') as f:
        json.dump(validation_result, f, default=str, indent=2)
    print(f"\nValidation results saved to validation_results.json")
    
    # Overall result
    if validation_result['is_valid']:
        print("\n✅ SYSTEM TEST PASSED: Report data is valid and consistent!")
    else:
        print("\n❌ SYSTEM TEST FAILED: Report data has validation issues!")

if __name__ == "__main__":
    main()