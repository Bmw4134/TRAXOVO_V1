"""
Full System Test for TRAXORA Attendance System

This script performs an end-to-end test of the attendance data processing pipeline:
1. Generates mock test data
2. Processes the data through the attendance processor
3. Validates the generated report for integrity
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Import the test data generator and other modules
import test_data_generator
from utils.attendance_processor import read_daily_usage_file, process_attendance_data
from report_validator import validate_report

def generate_test_data(date, count=100, output_file='temp_test_data.csv'):
    """Generate test data for the given date"""
    print(f"\n=== GENERATING TEST DATA FOR {date} ===")
    test_data = test_data_generator.generate_test_data(date, count)
    if not test_data:
        print("Error generating test data!")
        return False
    
    success = test_data_generator.write_csv(test_data, output_file)
    if success:
        print(f"Successfully generated {len(test_data)} test records in {output_file}")
        return output_file
    return False

def process_data(file_path, date=None):
    """Process the test data file using the attendance processor"""
    print(f"\n=== PROCESSING TEST DATA ===")
    print(f"Input file: {file_path}")
    
    # Process the data file
    result = read_daily_usage_file(file_path, date)
    
    if 'error' in result:
        print(f"Error processing data: {result['error']}")
        return None
    
    # Print summary
    print("\nReport Summary:")
    print(f"Date: {result.get('date')}")
    print(f"Total drivers with issues: {result.get('summary', {}).get('total_drivers', 0)}")
    print(f"Total issues: {result.get('summary', {}).get('total_issues', 0)}")
    print(f"Late drivers: {len(result.get('late_drivers', []))}")
    print(f"Early end drivers: {len(result.get('early_end_drivers', []))}")
    print(f"Not on job drivers: {len(result.get('not_on_job_drivers', []))}")
    print(f"Exception drivers: {len(result.get('exception_drivers', []))}")
    
    # Write the complete report to a JSON file for reference
    output_file = f"report_{result.get('date')}.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nComplete report saved to {output_file}")
    
    return result

def validate_data(report_data):
    """Validate the processed report data for integrity"""
    print(f"\n=== VALIDATING REPORT DATA ===")
    
    if not report_data:
        print("No report data to validate!")
        return False
    
    validation_results = validate_report(report_data)
    
    print("\nValidation Results:")
    print(f"Is valid: {validation_results['is_valid']}")
    
    # Print statistics
    print("\nSTATISTICS:")
    for key, value in validation_results.get('statistics', {}).items():
        print(f"  • {key.replace('_', ' ').title()}: {value}")
    
    # Print any errors
    if validation_results.get('errors'):
        print("\nERRORS:")
        for i, error in enumerate(validation_results['errors'], 1):
            print(f"  {i}. {error.get('message', '')}")
    
    # Print any warnings
    if validation_results.get('warnings'):
        print("\nWARNINGS:")
        for i, warning in enumerate(validation_results['warnings'], 1):
            print(f"  {i}. {warning.get('message', '')}")
    
    print("\n" + "="*80)
    if validation_results['is_valid']:
        print("✅ SYSTEM TEST PASSED: Report data is valid and consistent!")
    else:
        print("❌ SYSTEM TEST FAILED: Report data has validation issues!")
    print("="*80)
    
    # Save validation results to a JSON file
    output_file = f"validation_{report_data.get('date')}.json"
    with open(output_file, 'w') as f:
        json.dump(validation_results, f, indent=2, default=str)
    print(f"\nDetailed validation results saved to {output_file}")
    
    return validation_results['is_valid']

def run_full_test(date=None, count=100):
    """Run the full end-to-end test pipeline"""
    # Use the specified date or today's date
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    print("\n" + "="*80)
    print(f"STARTING FULL SYSTEM TEST FOR DATE: {date}")
    print("="*80)
    
    # Step 1: Generate test data
    test_file = generate_test_data(date, count)
    if not test_file:
        print("System test failed at data generation step!")
        return False
    
    # Step 2: Process the data
    report_data = process_data(test_file, date)
    if not report_data:
        print("System test failed at data processing step!")
        return False
    
    # Step 3: Validate the report
    validation_passed = validate_data(report_data)
    
    # Print end-of-test summary
    print("\nTEST SUMMARY:")
    print(f"Date tested: {date}")
    print(f"Records generated: {count}")
    print(f"Validation result: {'Passed' if validation_passed else 'Failed'}")
    
    return validation_passed

def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(description='Run a full system test for the attendance reporting system.')
    parser.add_argument('-d', '--date', help='Date to test in YYYY-MM-DD format (default: today)')
    parser.add_argument('-c', '--count', type=int, default=100, help='Number of test records to generate (default: 100)')
    
    args = parser.parse_args()
    run_full_test(args.date, args.count)

if __name__ == "__main__":
    main()