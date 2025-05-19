"""
Report Validator for Attendance System

This script validates the output of the attendance reporting system
to ensure data integrity and consistency across all metrics.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_attendance_data(date=None):
    """
    Get attendance data for the specified date from the attendance processor
    
    Args:
        date (str): Date in YYYY-MM-DD format
        
    Returns:
        dict: Attendance data dictionary
    """
    try:
        # Import attendance processor
        sys.path.append('.')
        from utils.attendance_processor import process_attendance_data
        
        # Get attendance data
        return process_attendance_data(date)
    except Exception as e:
        logger.error(f"Error getting attendance data: {e}")
        return None

def validate_report(report_data):
    """
    Validate the attendance report data for consistency and integrity
    
    Args:
        report_data (dict): The report data dictionary
        
    Returns:
        dict: Validation results including is_valid flag and any errors or warnings
    """
    results = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'statistics': {}
    }
    
    # Check if report_data is valid
    if not report_data or not isinstance(report_data, dict):
        results['is_valid'] = False
        results['errors'].append({
            'type': 'data_format',
            'message': 'Report data is not a valid dictionary'
        })
        return results
    
    # Check for required keys
    required_keys = ['date', 'summary', 'late_drivers', 'early_end_drivers', 'not_on_job_drivers', 'exception_drivers']
    for key in required_keys:
        if key not in report_data:
            results['is_valid'] = False
            results['errors'].append({
                'type': 'missing_key',
                'message': f'Report is missing required key: {key}'
            })
    
    # If missing critical keys, return early
    if not results['is_valid']:
        return results
    
    # Extract key data for validation
    summary = report_data.get('summary', {})
    late_drivers = report_data.get('late_drivers', [])
    early_end_drivers = report_data.get('early_end_drivers', [])
    not_on_job_drivers = report_data.get('not_on_job_drivers', [])
    exception_drivers = report_data.get('exception_drivers', [])
    
    # 1. Check summary totals match list counts
    reported_late_count = summary.get('late_count', 0)
    actual_late_count = len(late_drivers)
    
    reported_early_end_count = summary.get('early_end_count', 0)
    actual_early_end_count = len(early_end_drivers)
    
    reported_not_on_job_count = summary.get('not_on_job_count', 0)
    actual_not_on_job_count = len(not_on_job_drivers)
    
    reported_exception_count = summary.get('exception_count', 0)
    actual_exception_count = len(exception_drivers)
    
    reported_total_issues = summary.get('total_issues', 0)
    actual_total_issues = actual_late_count + actual_early_end_count + actual_not_on_job_count + actual_exception_count
    
    # Check for discrepancies
    if reported_late_count != actual_late_count:
        results['is_valid'] = False
        results['errors'].append({
            'type': 'count_mismatch',
            'message': f'Late driver count mismatch: Summary shows {reported_late_count}, but list contains {actual_late_count}'
        })
    
    if reported_early_end_count != actual_early_end_count:
        results['is_valid'] = False
        results['errors'].append({
            'type': 'count_mismatch',
            'message': f'Early end driver count mismatch: Summary shows {reported_early_end_count}, but list contains {actual_early_end_count}'
        })
    
    if reported_not_on_job_count != actual_not_on_job_count:
        results['is_valid'] = False
        results['errors'].append({
            'type': 'count_mismatch',
            'message': f'Not on job driver count mismatch: Summary shows {reported_not_on_job_count}, but list contains {actual_not_on_job_count}'
        })
    
    if reported_exception_count != actual_exception_count:
        results['is_valid'] = False
        results['errors'].append({
            'type': 'count_mismatch',
            'message': f'Exception driver count mismatch: Summary shows {reported_exception_count}, but list contains {actual_exception_count}'
        })
    
    # 2. Check total_issues matches sum of individual issue counts
    reported_total_drivers = summary.get('total_drivers', 0)
    
    # A driver could have multiple issues (e.g., late and early end)
    # So we need to get unique drivers across all categories
    all_drivers = set()
    for driver_list in [late_drivers, early_end_drivers, not_on_job_drivers, exception_drivers]:
        for driver in driver_list:
            if 'name' in driver:
                all_drivers.add(driver['name'])
            elif 'driver' in driver:
                all_drivers.add(driver['driver'])
    
    actual_unique_drivers = len(all_drivers)
    
    if reported_total_drivers != actual_unique_drivers:
        results['warnings'].append({
            'type': 'total_drivers_mismatch',
            'message': f'Total drivers count may be inaccurate: Summary shows {reported_total_drivers}, but there are {actual_unique_drivers} unique drivers with issues'
        })
    
    if reported_total_issues != actual_total_issues:
        results['is_valid'] = False
        results['errors'].append({
            'type': 'total_issues_mismatch',
            'message': f'Total issues count mismatch: Summary shows {reported_total_issues}, but actual sum is {actual_total_issues}'
        })
    
    # 3. Check for required fields in driver records
    if late_drivers and 'name' in late_drivers[0]:
        required_driver_fields = ['name', 'asset_id']
    else:
        required_driver_fields = ['driver', 'asset'] 
    missing_fields = []
    
    for category in ['late_drivers', 'early_end_drivers', 'not_on_job_drivers', 'exception_drivers']:
        for i, driver in enumerate(report_data.get(category, [])):
            for field in required_driver_fields:
                if field not in driver:
                    missing_fields.append(f"{category}[{i}] missing '{field}'")
    
    if missing_fields:
        results['warnings'].append({
            'type': 'missing_fields',
            'message': f'Some driver records are missing required fields: {", ".join(missing_fields[:5])}{"..." if len(missing_fields) > 5 else ""}'
        })
    
    # 4. Check for drivers with multiple issues (this is allowed but worth noting)
    drivers_with_multiple_issues = []
    driver_issues = {}
    
    for category in ['late_drivers', 'early_end_drivers', 'not_on_job_drivers', 'exception_drivers']:
        for driver in report_data.get(category, []):
            driver_id = driver.get('name', driver.get('driver', ''))
            if driver_id:
                if driver_id in driver_issues:
                    driver_issues[driver_id].append(category)
                else:
                    driver_issues[driver_id] = [category]
    
    for driver_id, issues in driver_issues.items():
        if len(issues) > 1:
            drivers_with_multiple_issues.append(f"{driver_id}: {', '.join(issues)}")
    
    # Add all statistics to the results
    results['statistics'] = {
        'report_date': report_data.get('date', ''),
        'total_unique_drivers': actual_unique_drivers,
        'total_issues': actual_total_issues,
        'late_drivers': actual_late_count,
        'early_end_drivers': actual_early_end_count,
        'not_on_job_drivers': actual_not_on_job_count,
        'exception_drivers': actual_exception_count,
        'drivers_with_multiple_issues': len(drivers_with_multiple_issues)
    }
    
    # Add detailed info about multiple-issue drivers
    if drivers_with_multiple_issues:
        results['statistics']['multiple_issue_details'] = drivers_with_multiple_issues
    
    return results

def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(description='Validate attendance report data.')
    parser.add_argument('-d', '--date', help='Date to validate in YYYY-MM-DD format (default: today)')
    parser.add_argument('-f', '--file', help='JSON file containing report data to validate')
    
    args = parser.parse_args()
    
    # Get report data from file or by date
    report_data = None
    if args.file:
        try:
            with open(args.file, 'r') as f:
                report_data = json.load(f)
        except Exception as e:
            print(f"❌ Error loading report data from file: {e}")
            return
    else:
        report_data = get_attendance_data(args.date)
        if not report_data:
            print(f"❌ Error: Could not get attendance data for date {args.date or 'today'}: {report_data}")
            return
    
    # Validate the report data
    validation_results = validate_report(report_data)
    
    # Print results
    if validation_results['is_valid']:
        print("✅ Report data is valid!")
    else:
        print("❌ Report data has validation issues:")
        for error in validation_results['errors']:
            print(f"  - {error.get('message', '')}")
    
    if validation_results.get('warnings'):
        print("\nWarnings:")
        for warning in validation_results['warnings']:
            print(f"  - {warning.get('message', '')}")
    
    # Print statistics
    print("\nReport Statistics:")
    for key, value in validation_results.get('statistics', {}).items():
        if key != 'multiple_issue_details':
            print(f"  {key}: {value}")
    
    # Save validation results
    if args.date:
        output_file = f"validation_{args.date}.json"
    elif args.file:
        output_file = f"validation_{os.path.basename(args.file)}"
    else:
        output_file = f"validation_{datetime.now().strftime('%Y-%m-%d')}.json"
    
    with open(output_file, 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    print(f"\nDetailed validation results saved to {output_file}")

if __name__ == "__main__":
    main()