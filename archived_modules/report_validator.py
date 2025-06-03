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
from datetime import datetime, timedelta

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

def get_trend_analysis_data(start_date=None, end_date=None, dates=None):
    """
    Get attendance trend analysis data for a date range
    
    Args:
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
        dates (list, optional): List of specific dates to analyze
        
    Returns:
        dict: Trend analysis data
    """
    try:
        # Import trend analyzer module
        sys.path.append('.')
        from utils.trend_analyzer import analyze_trends
        
        # Process the date range or specific dates
        if dates:
            return analyze_trends(specific_dates=dates)
        elif start_date and end_date:
            return analyze_trends(date_range=(start_date, end_date))
        elif start_date:
            # Single date analysis
            return analyze_trends(specific_dates=[start_date])
        else:
            # Default to last 5 days
            return analyze_trends()
    except Exception as e:
        logger.error(f"Error getting trend analysis data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def print_trend_report(trend_data):
    """
    Print a human-readable trend report
    
    Args:
        trend_data (dict): Trend analysis data
    """
    if not trend_data:
        print("❌ No trend data available")
        return
    
    date_range = trend_data.get('date_range', {})
    trend_summary = trend_data.get('trend_summary', {})
    driver_trends = trend_data.get('driver_trends', [])
    
    print(f"\n📊 ATTENDANCE TREND ANALYSIS REPORT")
    print(f"{'=' * 40}")
    print(f"Period: {date_range.get('start', 'N/A')} to {date_range.get('end', 'N/A')}")
    print(f"Days Analyzed: {trend_summary.get('days_analyzed', 0)}")
    print(f"Total Drivers: {trend_summary.get('total_drivers_analyzed', 0)}")
    print(f"{'=' * 40}")
    
    print(f"\nTREND SUMMARY:")
    print(f"  Drivers with chronic lateness: {trend_summary.get('chronic_late_count', 0)}")
    print(f"  Drivers with repeated absences: {trend_summary.get('repeated_absence_count', 0)}")
    print(f"  Drivers with unstable shifts: {trend_summary.get('unstable_shift_count', 0)}")
    
    if driver_trends:
        print(f"\nDRIVERS WITH FLAGS:")
        drivers_with_flags = [d for d in driver_trends if d.get('flags')]
        
        if drivers_with_flags:
            print(f"{'ID':<8} {'Name':<25} {'Flags':<30} {'Late':<5} {'Early':<5} {'Absent':<5}")
            print(f"{'-'*8} {'-'*25} {'-'*30} {'-'*5} {'-'*5} {'-'*5}")
            
            for driver in drivers_with_flags:
                flags_str = ', '.join(driver.get('flags', []))
                print(f"{driver.get('employee_id', ''):<8} {driver.get('name', '')[:25]:<25} {flags_str[:30]:<30} {driver.get('late_count', 0):<5} {driver.get('early_end_count', 0):<5} {driver.get('absence_count', 0):<5}")
        else:
            print("  No drivers with trend flags in this period.")
    
def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(description='Validate attendance report data and analyze trends.')
    parser.add_argument('-d', '--date', help='Date to validate in YYYY-MM-DD format (default: today)')
    parser.add_argument('-f', '--file', help='JSON file containing report data to validate')
    parser.add_argument('-t', '--trend', action='store_true', help='Run trend analysis instead of validation')
    parser.add_argument('-r', '--range', nargs='+', help='Date range for trend analysis (e.g., -r 2025-05-14 2025-05-18) or list of dates')
    parser.add_argument('-o', '--output', help='Output file for trend analysis results')
    
    args = parser.parse_args()
    
    # Handle trend analysis
    if args.trend:
        if args.range:
            # Check if range has one or two dates
            if len(args.range) == 1:
                # Single date
                trend_data = get_trend_analysis_data(args.range[0])
            elif len(args.range) == 2:
                # Start and end date
                trend_data = get_trend_analysis_data(args.range[0], args.range[1])
            else:
                # List of specific dates
                trend_data = get_trend_analysis_data(None, None, args.range)
        else:
            # Default to the last 5 days
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d')
            trend_data = get_trend_analysis_data(start_date, end_date)
        
        if not trend_data:
            print("❌ Error: Could not get trend analysis data")
            return
        
        # Print trend report
        print_trend_report(trend_data)
        
        # Save trend data to file
        output_file = args.output
        if not output_file:
            # Generate default filename
            date_str = datetime.now().strftime('%Y-%m-%d')
            output_file = f"trend_report_{date_str}.json"
        
        with open(output_file, 'w') as f:
            json.dump(trend_data, f, indent=2)
        
        print(f"\nDetailed trend report saved to {output_file}")
        return
    
    # Regular validation mode
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